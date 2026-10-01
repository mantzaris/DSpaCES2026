"""Development-selected established and explicit-fault-information comparators."""
import json
from pathlib import Path
import pickle
import time

import numpy as np
from scipy.special import logsumexp
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score

from .flow_data import configuration,load_data,graph_for,build_cases,sha256
from .flow_gaussian import fit_ppca,load_ppca,context_matrix,conditional_components
from .flow_math import gaussian_log_prob
from .baselines import PCADetector
from .experiment import json_save


def classifier_probability(state,features):
    """Portable numerical traversal, independent of sklearn pickle versions."""
    from scipy.special import expit
    raw=np.full(len(features),float(state['base']))
    for key in sorted(k for k in state if k.startswith('tree_')):
        nodes=state[key];index=np.zeros(len(features),int)
        active=np.ones(len(features),bool)
        while active.any():
            rows=np.flatnonzero(active);current=nodes[index[rows]]
            leaf=current['is_leaf'].astype(bool)
            raw[rows[leaf]]+=current['value'][leaf];active[rows[leaf]]=False
            rows=rows[~leaf];current=current[~leaf]
            feature=features[rows,current['feature_idx'].astype(int)]
            left=np.where(np.isfinite(feature),feature<=current['num_threshold'],current['missing_go_to_left'].astype(bool))
            index[rows]=np.where(left,current['left'],current['right'])
    return expit(raw)


def pca_model(root,dataset,name):
    lag=int(name.split('_')[1][3:])
    return PCADetector.load(Path(root)/'results/models'/dataset/(name+'.npz'),lag)


def pca_repair(model,values):
    vector=model.vectors(values[None]);vector=np.where(np.isfinite(vector),vector,model.fill)
    components=model.portable_components;mean=model.portable_mean
    reconstructed=(vector-mean)@components.T@components+mean
    return reconstructed.reshape(1,values.shape[1]*0+values.shape[-1]-model.lag+1,values.shape[0],model.lag)[0,-8:,:,-1].T


def supervised_features(values,pca):
    """Small shared fault-aware classifier. No reference truth enters features."""
    target=values[...,-8:];history=values[...,-24:-8]
    finite=np.isfinite(target);x=np.nan_to_num(target);past=np.nan_to_num(history)
    pca_scores=np.nan_to_num(pca.score(values),nan=0.,posinf=1e6)
    features=np.stack([x.mean(-1),x.std(-1),x.max(-1)-x.min(-1),x[...,-1]-x[...,0],
        np.abs(np.diff(x,axis=-1)).mean(-1),x.mean(-1)-past.mean(-1),past.std(-1),
        np.mean((x-past[...,-8:])**2,-1),np.log1p(pca_scores),finite.mean(-1)],-1)
    return features.reshape(-1,features.shape[-1])


def normal_development_nll(root,dataset,record):
    data=load_data(root,dataset,'development');values=data['x'][data['reference']]
    graph=graph_for(root,dataset);models=load_ppca(root,record);spec=record['specification'];logs=[]
    for query,model in enumerate(models):
        eligible=np.isfinite(values[:,query,-8:]).all(-1);raw=values[eligible]
        context=context_matrix(raw,query,graph,spec['length'],spec['mode'])
        for row in range(len(raw)):
            weights,components=conditional_components(model,context[row])
            logs.append(logsumexp([np.log(w)+gaussian_log_prob(raw[row,query,-8:],mean,cov) for w,(mean,cov) in zip(weights,components)]))
    return float(-np.mean(logs))


def develop_baselines(root):
    root=Path(root);config=configuration(root);output=root/'results/graph_flow_v1/development'
    for dataset in config['datasets']:
        destination=output/(dataset+'_baselines.json')
        if destination.exists():continue
        model_selection=json.loads((output/(dataset+'_models.json')).read_text())['selected']
        length=model_selection['specification']['context_length'];cases=build_cases(root,dataset,'development')
        values=np.stack([c['values'] for c in cases]);truth=np.stack([c['truth'] for c in cases]);eligible=np.isfinite(values[...,-8:]).all(-1)
        pca_grid=[]
        for lag in config['pca_lags']:
            for rank in config['pca_ranks']:
                name=f'pca_lag{lag}_rank{rank}';model=pca_model(root,dataset,name)
                scores=model.score(values);scores[~eligible]=-1e12
                pca_grid.append(dict(name=name,average_precision=float(average_precision_score(truth.ravel(),scores.ravel())),
                                     sha256=sha256(root/'results/models'/dataset/(name+'.npz'))))
        selected_pca=max(pca_grid,key=lambda row:(row['average_precision'],-int(row['name'].split('rank')[-1])))
        ppca_grid=[]
        for mode,mixtures in [('graph',1),('graph',2),('all_channels',1)]:
            for rank in config['ppca_ranks']:
                record=fit_ppca(root,dataset,length,rank,mixtures,mode)
                record=dict(record,development_nll=normal_development_nll(root,dataset,record));ppca_grid.append(record)
                print(dataset,'PPCA',mode,mixtures,rank,record['development_nll'],flush=True)
        selected={}
        for name,mode,mixtures in [('ppca','graph',1),('mixture_ppca','graph',2),('all_ppca','all_channels',1)]:
            selected[name]=min([r for r in ppca_grid if r['specification']['mode']==mode and r['specification']['mixtures']==mixtures],key=lambda r:r['development_nll'])
        pca=pca_model(root,dataset,selected_pca['name']);train_cases=build_cases(root,dataset,'train')
        train_values=np.stack([c['values'] for c in train_cases]);labels=np.stack([c['truth'] for c in train_cases]).ravel()
        train_eligible=np.isfinite(train_values[...,-8:]).all(-1).ravel()
        features=supervised_features(train_values,pca);dev_features=supervised_features(values,pca);supervised_grid=[];states=[]
        for depth in config['supervised_depths']:
            start=time.perf_counter();classifier=HistGradientBoostingClassifier(max_iter=config['supervised_iterations'],max_depth=depth,
                 learning_rate=.08,l2_regularization=1.,random_state=20261001,early_stopping=False).fit(features[train_eligible],labels[train_eligible])
            predicted=classifier.predict_proba(dev_features)[:,1];predicted[~eligible.ravel()]=-1e12
            supervised_grid.append(dict(depth=depth,average_precision=float(average_precision_score(truth.ravel(),predicted)),training_seconds=time.perf_counter()-start))
            states.append(classifier)
        index=max(range(len(states)),key=lambda i:supervised_grid[i]['average_precision'])
        path=root/'results/graph_flow_v1/models'/(dataset+'_supervised.npz')
        classifier=states[index]
        portable=dict(base=classifier._baseline_prediction.ravel()[0])
        portable.update({'tree_%03d'%i:tree[0].nodes for i,tree in enumerate(classifier._predictors)})
        np.testing.assert_allclose(classifier_probability(portable,dev_features),classifier.predict_proba(dev_features)[:,1],atol=1e-12)
        np.savez_compressed(path,**portable)
        supervised=dict(supervised_grid[index],path=str(path.relative_to(root)),sha256=sha256(path),
                        training_fault_cases=len(train_cases),training_candidates=int(train_eligible.sum()),features='target shape, own past contrast, PCA residual and target availability')
        json_save(destination,dict(pca=selected_pca,pca_grid=pca_grid,ppca_grid=ppca_grid,**selected,supervised=supervised,supervised_grid=supervised_grid,
                                  selection='PCA and classifier use development candidate AP; PPCA ranks and mixture fits use normal development NLL'))

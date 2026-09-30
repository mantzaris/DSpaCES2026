"""Check distribution matching and quantify remaining metadata-only shortcuts."""
from pathlib import Path
import json,sys
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score,average_precision_score
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.experiment import json_save
reports={}
for dataset in json.loads((ROOT/'configs/study.json').read_text())['datasets']:
    directory=ROOT/'results/study'/dataset
    base=json.loads((ROOT/'results/models'/dataset/'graph.json').read_text());arrays={};checks=0
    for split in ['development','test']:
        x=[];y=[]
        for path in sorted((directory/split).glob(split+'_*_association.json')):
            case=json.loads(path.read_text());graph=case['graph'];truth=case['association_truth']
            for field in ['source','target','lag','sign','magnitude','intercept']:
                assert sorted(e[field] for e in graph['edges'])==sorted(e[field] for e in base['edges'])
            checks+=1
            for edge,label in zip(graph['edges'],truth):
                indegree=sum(e['target']==edge['target'] for e in graph['edges']);outdegree=sum(e['source']==edge['source'] for e in graph['edges'])
                x.append([edge['lag'],edge['sign'],edge['magnitude'],edge['intercept'],edge['validation_gain'],indegree,outdegree]);y.append(label)
        arrays[split]=(np.array(x),np.array(y))
    if len(arrays['test'][1]) and len(set(arrays['development'][1]))==2:
        model=make_pipeline(StandardScaler(),LogisticRegression(C=1.,class_weight='balanced',max_iter=2000,random_state=9026)).fit(*arrays['development'])
        probability=model.predict_proba(arrays['test'][0])[:,1];truth=arrays['test'][1]
        reports[dataset]=dict(marginal_checks=checks,metadata_only_roc_auc=float(roc_auc_score(truth,probability)),metadata_only_ap=float(average_precision_score(truth,probability)),prevalence=float(truth.mean()),
            interpretation='preserved marginals do not imply complete joint-distribution matching; scalar metadata audit excludes values, graph version hashes and fault tags')
json_save(ROOT/'results/audits/association_metadata.json',reports)

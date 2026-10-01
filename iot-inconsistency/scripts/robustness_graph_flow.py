"""Registered robustness execution with a corrected local variable name.

This preserves the frozen measurements, inference, seeds and stress design.
The original stage reused the nested scoring function's name for a report array,
then attempted to call that array for the ambiguity experiment. No final primary
scores or modeling choices are changed. The original frozen module remains intact.
"""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
"""Predeclared context stress, separate association task and process semantics."""
import copy
import json
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import average_precision_score

from iot_repair.flow_data import configuration,build_cases,graph_for,inject,load_data,metadata,sha256
from iot_repair.flow_training import load_flow
from iot_repair.flow_inference import infer_case
from iot_repair.flow_baselines import pca_model
from iot_repair.flow_confidence import rank_pvalues,load_predictions
from iot_repair.associations import edge_residuals
from iot_repair.data import simulate
from iot_repair.preprocessing import transform_measurements
from iot_repair.graph_flow_model import canonicalize_known_copies
from iot_repair.experiment import json_save


def run_robustness(root):
    root=Path(root);directory=root/'results/graph_flow_v1';config=configuration(root)
    lock=json.loads((directory/'protocol_lock.json').read_text());all_results={}
    for dataset in config['datasets']:
        out=directory/dataset/'robustness';out.mkdir(parents=True,exist_ok=True)
        selection=lock['choices'][dataset];models=[load_flow(root,r) for r in selection['members']['members']]
        graph=graph_for(root,dataset);length=selection['models']['selected']['specification']['context_length']
        settings=selection['scoring'];groups=np.array(graph['groups']);channels=len(groups)
        pca=pca_model(root,dataset,selection['baselines']['pca']['name'])
        calibration=json.loads((directory/dataset/'calibration.json').read_text())['methods']
        cal_cases,cal_arrays,_,_=load_predictions(root,dataset,'calibration')
        relation_reference=[float(np.max(np.nan_to_num(a['association_direct_residual'],nan=-1e12))) for c,a in zip(cal_cases,cal_arrays)
                            if c['track']=='clean' and c['calibration_role']=='normal_window_tail']
        clean=[case for case in build_cases(root,dataset,'test') if case['track']=='clean']
        selected=[clean[i] for i in np.linspace(0,len(clean)-1,min(12,len(clean)),dtype=int)]
        conditions={};case_records=[];combined_arrays={}
        def score(case,values,g,seed):
            result=infer_case(models,values,g,length,settings['sample_count'],settings['scale'],seed=seed,times=case['target_times'])
            residual=pca.score(values[None])[0];residual[~result['eligible']]=-1e12
            return result,dict(flow_ratio=result['scores']['flow_ratio'],flow_nll=result['scores']['flow_nll'],pca=residual)
        for ordinal,case in enumerate(selected):
            target=ordinal%channels;seed=91000000+ordinal*101;reference=case['values']
            values,fault=inject(reference,target,'bias',2.,seed,times=case['target_times'])
            base_truth=np.zeros(channels,bool);base_truth[target]=fault['edited_observed_cells']>0
            experiments=[('reference',reference,graph,np.zeros(channels,bool),None),('single_source',values,graph,base_truth,None)]
            supporting=sorted(set(groups)-{groups[target]})
            rng=np.random.default_rng(seed);order=list(rng.permutation(supporting))
            for fraction in config['context_missing_fractions']:
                modified=values.copy();chosen=order[:max(1,int(np.ceil(len(order)*fraction)))];modified[np.isin(groups,chosen)]=np.nan
                experiments.append(('missing_context_'+str(fraction),modified,graph,base_truth,None))
            for fraction in config['context_corrupted_source_fractions']:
                modified=values.copy();truth=base_truth.copy();chosen=order[:max(1,int(np.ceil(len(order)*fraction)))]
                for group in chosen:
                    query=int(np.flatnonzero(groups==group)[0]);modified,f=inject(modified,query,'bias',2.,seed+query,times=case['target_times']);truth[query]=f['edited_observed_cells']>0
                experiments.append(('multiple_sources_'+str(fraction),modified,graph,truth,None))
            for fraction in config['graph_corruption_fractions']:
                changed=copy.deepcopy(graph);indices=rng.choice(len(graph['edges']),max(1,int(np.ceil(len(graph['edges'])*fraction))),replace=False)
                relation_truth=np.zeros(len(graph['edges']),bool)
                for index in indices:
                    edge=changed['edges'][int(index)];available=[c for c in range(channels) if groups[c]!=groups[edge['target']] and c!=edge['source']]
                    if available:edge['source']=int(rng.choice(available));relation_truth[index]=True
                experiments.append(('graph_error_'+str(fraction),reference,changed,np.zeros(channels,bool),relation_truth))
            # Known duplicate identity canonicalization precedes every numerical input.
            copied=np.concatenate([values,values[:1]],0)
            canonical=canonicalize_known_copies(torch.tensor(copied[None]),list(range(channels))+[0])[0].numpy()
            experiments.append(('known_copy',canonical,graph,base_truth,None))
            baseline_score=None
            for name,observed,g,truth,relation_truth in experiments:
                result,scores=score(case,observed,g,seed);record=dict(case_id=case['id'],condition=name,block=case['block'],primary_target=target,seed=seed,
                    eligible_fraction=float(result['eligible'].mean()),fault_candidates=int(truth.sum()),
                    primary_target_available=bool(result['eligible'][target]),numerical_adequate=int(result['numerical_adequate'].sum()))
                if name=='single_source':baseline_score=scores['flow_ratio']
                if name=='known_copy':record['max_score_change']=float(np.max(np.abs(scores['flow_ratio']-baseline_score)));assert record['max_score_change']==0.
                for method,value in scores.items():
                    record[method+'_maximum']=float(value.max());record[method+'_window_p']=float(rank_pvalues([value.max()],calibration[method]['normal_window_maxima'])[0])
                    record[method+'_primary_top1']=bool(np.argmax(value)==target and result['eligible'][target] and truth[target])
                    combined_arrays.setdefault(name+'__'+method,[]).append(value)
                combined_arrays.setdefault(name+'__truth',[]).append(truth)
                combined_arrays.setdefault(name+'__input',[]).append(observed)
                direct=edge_residuals(observed[None],g)[0];record['association_maximum']=float(np.max(np.nan_to_num(direct,nan=-1e12)))
                record['association_window_p']=float(rank_pvalues([record['association_maximum']],relation_reference)[0])
                reading_alarm=record['flow_ratio_window_p']<=.1;relation_alarm=record['association_window_p']<=.1
                record['cross_type_output']='both' if reading_alarm and relation_alarm else 'reading_only' if reading_alarm else 'relation_only' if relation_alarm else 'neither'
                if relation_truth is not None:
                    record['association_localization_ap']=float(average_precision_score(relation_truth,np.nan_to_num(direct,nan=-1e12)))
                    record['relation_faults']=int(relation_truth.sum())
                    record['changed_associations']=[dict(index=int(i),edge=g['edges'][int(i)]) for i in np.flatnonzero(relation_truth)]
                case_records.append(record)
        for name in sorted(set(row['condition'] for row in case_records)):
            truth=np.asarray(combined_arrays[name+'__truth']);rows=[row for row in case_records if row['condition']==name]
            conditions[name]=dict(cases=len(rows),eligible_fraction=float(np.mean([r['eligible_fraction'] for r in rows])),methods={})
            conditions[name]['cross_type_counts']={kind:sum(r['cross_type_output']==kind for r in rows) for kind in ('both','reading_only','relation_only','neither')}
            conditions[name]['association_tail_resolution']=1/(len(relation_reference)+1)
            for method in ('flow_ratio','flow_nll','pca'):
                score_array=np.asarray(combined_arrays[name+'__'+method]);conditions[name]['methods'][method]=dict(
                    candidate_ap=float(average_precision_score(truth.ravel(),score_array.ravel())) if truth.any() else None,
                    primary_top1=float(np.mean([r[method+'_primary_top1'] for r in rows])),
                    window_alarm_fraction_at_010=float(np.mean([r[method+'_window_p']<=.1 for r in rows])))
        if dataset.startswith('synthetic'):
            ambiguity=[];meta=metadata(root,dataset)
            for ordinal in range(12):
                seed=92000000+ordinal;normal,latent,_,_,_=simulate(channels,64,seed,dataset.endswith('nonlinear'))
                physical,physical_latent,_,_,_=simulate(channels,64,seed,dataset.endswith('nonlinear'),event=dict(start=56,stop=64,magnitude=3.,latent=ordinal%4))
                observed=transform_measurements(physical,meta['normalizer']).T.astype('float32')
                unmodified=transform_measurements(normal,meta['normalizer']).T.astype('float32')
                case=dict(target_times=list(range(8)))
                result,scores=score(case,observed,graph,seed)
                # A coordinated additive measurement failure can produce exactly this
                # observed array from the unmodified process, including its context.
                common_mode=unmodified.astype('float64')+(observed.astype('float64')-unmodified.astype('float64'))
                assert np.array_equal(common_mode.astype('float32'),observed)
                ambiguity.append(dict(case_id='physical_common_mode_'+str(ordinal),same_observations=True,
                    fault_vs_physical_indistinguishable=True,measurement_fault_probability_not_identifiable=True,
                    flow_maximum=float(scores['flow_ratio'].max()),pca_maximum=float(scores['pca'].max()),
                    flow_window_p=float(rank_pvalues([scores['flow_ratio'].max()],calibration['flow_ratio']['normal_window_maxima'])[0])))
                if ordinal==0:np.savez_compressed(out/'ambiguity_example.npz',observed=observed,reference=unmodified,
                     latent_process_normal=latent,latent_process_changed=physical_latent,full_candidate_score=scores['flow_ratio'],**result['raw'])
            json_save(out/'ambiguity.json',ambiguity)
        elif dataset=='skab':
            native=load_data(root,dataset,'test');native_scores={method:[] for method in ('flow_ratio','flow_nll','pca')}
            from iot_repair.flow_data import recording_timestamps
            for index,values in enumerate(native['x']):
                times=recording_timestamps(str(root.resolve()),str(native['block'][index]))[int(native['stop'][index])-8:int(native['stop'][index])]
                _,scores=score(dict(target_times=times),values,graph,93000000+index)
                for method,value in scores.items():native_scores[method].append(float(value.max()))
            labels=native['process_label'].astype(bool)
            native_report=dict(cases=len(labels),native_event_windows=int(labels.sum()),label_scope='original target-interval process anomaly, never sensor-fault truth',
                methods={method:dict(window_ap=float(average_precision_score(labels,value))) for method,value in native_scores.items()})
            np.savez_compressed(out/'native_process.npz',labels=labels,blocks=native['block'],**{m:np.array(v) for m,v in native_scores.items()})
            json_save(out/'native_process.json',native_report)
        np.savez_compressed(out/'predictions.npz',**{k:np.asarray(v) for k,v in combined_arrays.items()});json_save(out/'cases.json',case_records)
        json_save(out/'analysis.json',conditions);all_results[dataset]=conditions
        del models;torch.cuda.empty_cache()
    json_save(directory/'robustness.json',all_results)

if __name__=='__main__':
    torch.set_num_threads(4)
    run_robustness(ROOT)

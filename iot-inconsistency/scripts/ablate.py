"""Full paired repair ablations on exactly the main study cases and calibration."""
from pathlib import Path
import argparse,copy,json,sys
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.experiment import load_models,json_save
from iot_repair.pipeline import score_candidates
from iot_repair.metrics import summarize,paired_ap_interval
from iot_repair.calibration import null_tail_value
p=argparse.ArgumentParser();p.add_argument('--dataset',required=True);a=p.parse_args();torch.set_num_threads(4)
directory=ROOT/'results/study'/a.dataset;params=json.loads((directory/'frozen.json').read_text())
models,graph=load_models(ROOT,a.dataset,('diffusion','mean','no_graph'))
for model in models['no_graph']:model.disable_graph=True
out=ROOT/'results/ablations'/a.dataset;out.mkdir(parents=True,exist_ok=True);summary={}
for variant in ['deterministic','no_witness_separation','no_provenance_grouping','no_provenance_deduplication','no_graph']:
    saved_cases={}
    for split in ['calibration','test']:
        location=out/variant/split;location.mkdir(parents=True,exist_ok=True);rows=[]
        for ordinal,path in enumerate(sorted((directory/split).glob(split+'_*.json'))):
            target=location/path.name
            if target.exists():rows.append(json.loads(target.read_text()));continue
            case=json.loads(path.read_text());x=np.load(directory/split/case['raw_artifact'])['input'];candidate_graph=copy.deepcopy(case['graph'])
            if variant=='no_provenance_grouping':candidate_graph['groups']=[f'channel_{i}' for i in range(len(candidate_graph['groups']))]
            settings=dict(kappa=params['kappa'],edit_weight=params['lambda'])
            if variant=='no_provenance_deduplication':
                sources={i for kind,i in case['candidates'] if kind=='observation'}
                copies=[copy.deepcopy(e) for e in candidate_graph['edges'] if e['source'] in sources]
                candidate_graph['edges']+=copies*3;settings['deduplicate_graph']=False
            if variant=='deterministic':settings['deterministic_models']=models['mean']
            if variant=='no_witness_separation':settings['separate_witnesses']=False
            records,raw,abstentions=score_candidates(models['no_graph'] if variant=='no_graph' else models['diffusion'],x,candidate_graph,case['candidates'],
                seed=case['inference_seed'],**settings)
            for row in records:row['truth']=bool(case[row['kind']+'_truth'][row['index']])
            result=dict(case,graph=candidate_graph,records=records,abstentions=abstentions,variant=variant,
                diagnostic_only=variant in ('no_witness_separation','no_provenance_grouping','no_provenance_deduplication'))
            # Full score terms are saved for every candidate. Predictive draws are retained for the first case of each block.
            keep=not any(r['block']==case['block'] for r in rows)
            arrays=raw if keep else {k:v for k,v in raw.items() if 'samples' not in k and k!='replacement_targets'}
            np.savez_compressed(target.with_suffix('.npz'),**arrays);json_save(target,result);rows.append(result)
            if ordinal%100==0:print(a.dataset,variant,split,ordinal,flush=True)
        saved_cases[split]=rows
    metrics={}
    for kind in ['observation','association']:
        null=[c for c in saved_cases['calibration'] if c['track']=='clean' and c['calibration_fold']=='null']
        reference=[r['score'] for r in summarize(null,'proposed',kind,params)['decisions']]
        metrics[kind]=summarize(saved_cases['test'],'proposed',kind,params,reference=reference)
        main=[json.loads(p.read_text()) for p in sorted((directory/'test').glob('test_*.json'))]
        other=summarize(main,'proposed',kind,params)['decisions'];left=metrics[kind]['decisions']
        metrics[kind]['paired_main_minus_ablation']=paired_ap_interval([r['y'] for r in other],[r['score'] for r in other],[r['score'] for r in left],[r['block'] for r in other])
    summary[variant]=dict(metrics=metrics,scope='unsafe diagnostic' if variant in ('no_witness_separation','no_provenance_grouping','no_provenance_deduplication') else 'paired model ablation')
    json_save(out/'analysis.json',summary)
json_save(out/'complete.json',dict(variants=list(summary)))

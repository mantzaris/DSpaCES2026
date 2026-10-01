"""Rerun preserved diffusion/GDN comparators on the new common candidate universe."""
import json
from pathlib import Path
import time

import numpy as np
import torch

from .flow_data import configuration,build_cases,graph_for,sha256
from .experiment import load_models,neural_residuals,scaled,json_save
from .associations import edge_residuals
from .pipeline import screen_candidates,score_candidates


def run_legacy(root,splits=('calibration','test')):
    root=Path(root);config=configuration(root);directory=root/'results/graph_flow_v1'
    for dataset in config['datasets']:
        models,graph=load_models(root,dataset,kinds=('diffusion','gdn','diffad'))
        parameters=json.loads((root/'results/study'/dataset/'frozen.json').read_text())
        scales=json.loads((root/'results/study'/dataset/'residual_scales.json').read_text())
        for split in splits:
            output=directory/dataset/split;completion=output/'legacy_complete.json'
            if completion.exists():continue
            cases=build_cases(root,dataset,split);values=np.stack([c['values'] for c in cases])
            residuals,timing=neural_residuals(models,values,graph,seed=84000000+(0 if split=='calibration' else 1000000))
            normalized={name:scaled(value.mean(0),scales[name]) for name,value in residuals.items()}
            records=[]
            for ordinal,case in enumerate(cases):
                path=output/(case['id']+'.npz');arrays=dict(np.load(path,allow_pickle=False))
                if 'score_legacy_witness' in arrays:continue
                edge_scores=edge_residuals(case['values'][None],graph)[0]
                candidates=screen_candidates(normalized['gdn'][ordinal],edge_scores,graph,cap=4)
                observation_candidates=[c for c in candidates if c[0]=='observation']
                start=time.perf_counter()
                rows,raw,abstentions=score_candidates(models['diffusion'],case['values'],graph,observation_candidates,
                    replicates=8,predictive_samples=8,seed=85000000+ordinal*101+(0 if split=='calibration' else 1000000),
                    kappa=parameters['kappa'],edit_weight=parameters['lambda'])
                score=np.full(values.shape[1],-1e12);screen=np.zeros(values.shape[1],bool)
                for _,query in observation_candidates:screen[query]=True
                for row in rows:
                    if arrays['eligible'][row['index']]:score[row['index']]=row['score']
                arrays['score_legacy_witness']=score;arrays['legacy_screen']=screen
                for name,value in normalized.items():
                    selected=value[ordinal].copy();selected[~arrays['eligible']]=-1e12
                    arrays['score_legacy_'+name]=np.nan_to_num(selected,nan=-1e12)
                np.savez_compressed(path,**arrays)
                record_path=path.with_suffix('.json');record=json.loads(record_path.read_text())
                record['sha256_before_legacy_extension']=record['sha256'];record['sha256']=sha256(path)
                record['legacy']=dict(seconds=time.perf_counter()-start,rows=rows,abstentions=abstentions,
                    screened_candidates=observation_candidates,kappa=parameters['kappa'],edit_weight=parameters['lambda'],
                    opportunity='Fixed legacy top-four screen. Excluded targets remain floor-scored misses in complete candidate metrics.',
                    independence='Separate reserved witnesses retain the original masking procedure; flow conditioning sources are not witnesses.')
                json_save(record_path,record);records.append(record['legacy'])
                if ordinal%25==0:print('Legacy shared cases',dataset,split,ordinal,'/',len(cases),flush=True)
            json_save(completion,dict(cases=len(cases),residual_seconds_per_window=timing,legacy_fixed_parameters=parameters,
                   original_training_data_retained=True,old_scores_reused=False))
        del models;torch.cuda.empty_cache()

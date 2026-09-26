"""One predeclared correction; frozen exploratory fresh seeds and matched originals."""
import argparse,json,time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from replay_shock import run_episode
from evidence_fusion.shock_gaussian import ShockGaussian
from evidence_fusion.acquisition_policy import RankedProbePolicy
from evidence_fusion.shock_overlays import overlay
from evidence_fusion.refinement_access import immutable_digest

def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['smoke','calibrate','run']);args=parser.parse_args()
    root=Path('results/acquisition');out=root/args.mode;out.mkdir(exist_ok=True)
    cfg=json.loads(Path('configs/regional_shock.json').read_text());new=json.loads(Path('configs/regional_acquisition.json').read_text())
    cal=json.loads(Path('results/shock/calibration.json').read_text())
    model=dict(np.load('data/regional/refinement/model.npz'))
    torch.set_num_threads(4);torch.backends.cuda.matmul.allow_tf32=False;torch.cuda.set_per_process_memory_fraction(.70)
    engine=ShockGaussian(model,cfg['window']);start=time.perf_counter()
    kwargs=dict(policy_overrides={'M3b':RankedProbePolicy},same_trace_source={'M3b_fixed':'M3b'})
    if args.mode in ['smoke','calibrate']:
        with np.load('data/regional/shock/calibration.npz') as p:bg=p['values'];slot=p['slots']
        read,target,shift,sig,meta=overlay(bg,model,'none',0.,1049999)
        r=run_episode(engine,model,bg,slot,meta,read,target,shift,sig,cfg,cal,'correction_calibration',
            methods=['M0','M3b','M3b_fixed'] if args.mode=='smoke' else ['M0','M3b'],
            steps=8 if args.mode=='smoke' else cfg['calibration_steps'],collect_calibration=True,**kwargs)
        for k in ['metrics','alarms','costs','access','checks','score_cal']:
            pd.DataFrame(r[k]).to_csv(out/(k+'.csv.gz'),index=False,compression='gzip')
        if args.mode=='calibrate':
            sc=pd.DataFrame(r['score_cal']);a=sc[(sc.method=='M3b')&(sc.step>=8)]
            cal['fine']['M3b']=float(max(a.fine.quantile(.95),1e-8))
            cal['joint']['M3b']=float(np.quantile(np.maximum(a.macro/cal['macro'],a.fine/cal['fine']['M3b']),.98))
            values={}
            for key,vs in r['quantile_cal']:
                if key.startswith('M3b_'):values.setdefault(key,[]).extend(vs)
            for k,vs in values.items():cal['interval'][k]=float(np.quantile(vs,.9))
            for h in (2,12):cal['interval']['M3b_%s_affected'%h]=cal['interval']['M3b_%s_household'%h]
            for key in ['fine','joint']:cal[key]['M3b_fixed']=cal[key]['M3b']
            for k,v in list(cal['interval'].items()):
                if k.startswith('M3b_'):cal['interval'][k.replace('M3b_','M3b_fixed_',1)]=v
            (root/'calibration.json').write_text(json.dumps(cal,indent=2)+'\n')
    else:
        frozen=json.loads((root/'frozen.json').read_text())
        for file,digest in frozen['hashes'].items():assert immutable_digest(file)==digest,(file,'freeze changed')
        cal=json.loads((root/'calibration.json').read_text())
        if (out/'episodes.json').exists():raise RuntimeError('Preserve existing comparative outputs')
        episodes=[]
        for phase,backgrounds in [('fresh',new['backgrounds']),('original',[0])]:
            for b in backgrounds:
                with np.load('data/regional/shock/background_%02d.npz'%b) as p:bg=p['values'];slot=p['slots']
                for fi,family in enumerate(new['families']):
                    mag=0. if family=='none' else new['magnitude']
                    seed=new['seed_base']+1000*b+10*fi if phase=='fresh' else cfg['episode_seed']+(10*cfg['families'].index(family) if family!='none' else 60)
                    read,target,shift,sig,meta=overlay(bg,model,family,mag,seed)
                    eid='%s_b%02d_%s_%s'%(phase,b,family,mag)
                    meta.update(episode=eid,background=b,phase=phase,source_sha256=immutable_digest('data/regional/shock/background_%02d.npz'%b))
                    methods=new['methods'] if phase=='fresh' else ['M0','M3b','M3b_fixed']
                    r=run_episode(engine,model,bg,slot,meta,read,target,shift,sig,cfg,cal,eid,methods=methods,**kwargs)
                    meta['seconds']=r['total_seconds'];episodes.append(meta)
                    for k in ['metrics','alarms','costs','access','checks']:
                        p=out/(k+'.csv.gz');pd.DataFrame(r[k]).to_csv(p,index=False,compression='gzip',mode='a',header=not p.exists())
                    (out/'episodes.json').write_text(json.dumps(episodes,indent=2)+'\n')
                    print(eid,r['total_seconds'],flush=True)
    (out/'summary.json').write_text(json.dumps(dict(mode=args.mode,seconds=time.perf_counter()-start,
        gpu_peak_bytes=torch.cuda.max_memory_allocated(),device=torch.cuda.get_device_name(),
        config_sha256=immutable_digest('configs/regional_acquisition.json'),main_study_disabled=True),indent=2)+'\n')
    print('complete',args.mode,time.perf_counter()-start,flush=True)
if __name__=='__main__':main()

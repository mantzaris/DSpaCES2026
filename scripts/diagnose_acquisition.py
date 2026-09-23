"""Reconstruct unavailable intermediate diagnostics; original artifacts are read-only.
One FP64 GPU aggregate-only trajectory per original episode. No fine-inference rerun.
"""
import hashlib,json,time,argparse,resource
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from evidence_fusion.shock_gaussian import ShockGaussian
from evidence_fusion.shock_access import ProbePolicy,ObservationChannel,EvidenceWindow
from evidence_fusion.shock_overlays import overlay
from evidence_fusion.refinement_access import immutable_digest

class OneStep(ShockGaussian):
    horizons=(1,)

def vector(x):return json.dumps(np.asarray(x).tolist(),separators=(',',':'))
def digest(meters,timestamp,ids):
    return hashlib.sha256(('\n'.join(str(timestamp)+'|'+str(meters[i]) for i in ids)).encode()).hexdigest()
def first(rows,key,tol=1e-9):
    return next((r['step'] for r in rows if abs(r[key])>tol),None)

def reconstruct(engine,model,source,meta,cfg,cal,oldaccess,oldalarm,control=None):
    bg=source['values'];slots=source['slots'];times=source['timestamps']
    readings,targets,shift,sig,check=overlay(bg,model,meta['family'],meta['magnitude'],meta['seed'],cfg['window'])
    assert check['affected_ids']==meta['affected_ids']
    assert np.array_equal(np.isnan(readings),np.isnan(bg))
    n=len(model['meters']);groups=model['groups'];L=cfg['window'];steps=cfg['steps']
    budget=int(n*cfg['fine_budget_fraction']);probes=int(n*cfg['probe_fraction'])
    policy=ProbePolicy(groups,cfg['probe_seed'],probes,budget,cal['trigger'])
    channel=ObservationChannel(readings,groups,budget,[]);channel.cutoff=L-2
    cache=EvidenceWindow(n,L);fine=np.full((n,L),np.nan)
    prev=model['profile'][slots[L-1]].astype(float)
    var=model['detail_var']+model['measurement_var']
    rows=[]; errors=[];oldlookup={(int(r.step),r.kind):r for r in oldaccess.itertuples()}
    alarms=oldalarm.set_index('step')
    for t in range(steps):
        cutoff=L-1+t;channel.advance(cutoff);evicted=cache.advance(t)
        pids=policy.probe_ids(t);pv=channel.read(pids,'probe')
        pz=abs(pv-prev[pids])/np.sqrt(np.maximum(var[pids],1e-12))
        score_before=policy.score.copy();policy.update(pids,pz)
        extra=policy.refinement_ids(t,pids);ev=channel.read(extra,'refinement')
        ids=np.r_[pids,extra];values=np.r_[pv,ev]
        cache.add(ids,values-model['profile'][slots[cutoff],ids],t)
        oldids=[]
        for kind,selected in [('probe',pids),('refinement',extra)]:
            record=oldlookup[cutoff,kind];saved=np.fromstring(record.households,sep=' ',dtype=int)
            assert np.array_equal(saved,selected),(meta['episode'],t,kind,'trace mismatch')
            assert record.returned==int(np.isfinite(readings[cutoff,saved]).sum())
            oldids.extend(saved.tolist())
        assert len(set(ids.tolist()))==budget and np.isfinite(cache.values[:,-1]).sum()==np.isfinite(values).sum()
        err=abs(float(alarms.loc[t,'probe_score'])-float(policy.score.max()));errors.append(err)
        assert err<1e-8,(meta['episode'],t,err)
        assert int(alarms.loc[t,'active_group'])==policy.active
        affected=np.flatnonzero(shift[cutoff]!=0);ag=np.unique(groups[affected])
        hitp=np.isfinite(pv)&(shift[cutoff,pids]!=0);hitf=np.isfinite(values)&(shift[cutoff,ids]!=0)
        winning=[];increments=np.zeros(16)
        for g in range(16):
            where=np.flatnonzero((groups[pids]==g)&np.isfinite(pz))
            if len(where):
                k=where[np.argmax(pz[where])];winning.append(int(pids[k]));increments[g]=max(0.,pz[k]-2.)
        z=abs(values-prev[ids])/np.sqrt(np.maximum(var[ids],1e-12))
        c=control[t] if control is not None else None
        score=policy.score;rank=np.argsort(-score,kind='stable')
        row=dict(episode=meta['episode'],background=meta['background'],family=meta['family'],magnitude=meta['magnitude'],
            step=t,timestamp=str(times[cutoff]),onset=meta['onset'],duration=meta['duration'],
            in_event=meta['onset']<=t<meta['onset']+meta['duration'],macro_signature=float(abs(sig[cutoff]).max()),
            probe_hits=int(hitp.sum()),fine_hits=int(hitf.sum()),affected_probe_z=float(np.nanmax(pz[hitp])) if hitp.any() else 0.,
            affected_fine_z=float(np.nanmax(z[hitf])) if hitf.any() else 0.,
            affected_probe_winners=len(set(winning)&set(affected)),
            best_group=int(rank[0]),best_score=float(score.max()),trigger=bool(score.max()>cal['trigger']),
            active_group=policy.active,ttl=policy.ttl,
            affected_top_group=bool(rank[0] in ag),affected_active=bool(policy.active in ag),
            requested=budget,read=int(np.isfinite(values).sum()),assimilated=int(np.isfinite(cache.values[:,-1]).sum()),
            budget_blocked=False,action_reason='trigger_or_hold' if policy.active>=0 else 'rotate_below_trigger',
            requested_identity_hash=digest(model['meters'],times[cutoff],ids),
            canonical_identity_hash=digest(model['meters'],times[cutoff],sorted(ids.tolist())),
            assimilated_identity_hash=digest(model['meters'],times[cutoff],ids[np.isfinite(values)]),
            original_identity_hash=digest(model['meters'],times[cutoff],oldids),
            expired_cells=evicted,score_error=err,probe_ids=vector(pids),probe_values=vector(pv),
            probe_prediction=vector(prev[pids]),probe_sd=vector(np.sqrt(var[pids])),probe_z=vector(pz),
            scores=vector(score),increments=vector(increments),affected_groups=vector(ag),
            exposed_value_difference=float(np.nanmax(abs(values-np.asarray(c['_values'])))) if c else 0.,
            exposed_probe_difference=float(np.nanmax(abs(pv-np.asarray(c['_pv'])))) if c else 0.,
            innovation_difference=float(np.nanmax(abs(pz-np.asarray(c['_pz'])))) if c else 0.,
            score_difference=float(abs(score-np.asarray(c['_score'])).max()) if c else 0.,
            ranking_changed=bool(not np.array_equal(rank,c['_rank'])) if c else False,
            trigger_changed=bool((score.max()>cal['trigger'])!=c['trigger']) if c else False,
            action_changed=bool(policy.active!=c['active_group']) if c else False,
            read_identity_changed=bool(digest(model['meters'],times[cutoff],ids)!=c['requested_identity_hash']) if c else False,
            assimilation_value_difference=float(np.nanmax(abs(values-np.asarray(c['_values'])))) if c else 0.)
        row.update(_values=values.copy(),_pv=pv.copy(),_pz=pz.copy(),_score=score.copy(),_rank=rank.copy())
        rows.append(row)
        # Same aggregate-only model/reference as Stage 3, h=1 only. Values available through cutoff.
        win=readings[cutoff-L+1:cutoff+1].T;native=np.isfinite(win)
        seasonal=model['profile'][slots[cutoff-L+1:cutoff+1]].T.astype(float)
        aggregate=np.stack([np.where(native[groups==g],win[groups==g]-seasonal[groups==g],0.).sum(0) for g in range(16)])
        out,_=engine.infer(native,fine,aggregate,np.ones((1,n),bool),model['profile'][slots[[cutoff+1]]].astype(float))
        prev=out[0]['mean'].cpu().numpy();var=out[0]['variance'].cpu().numpy()
    return rows

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--smoke',action='store_true');args=parser.parse_args()
    root=Path('results/acquisition');root.mkdir(exist_ok=True)
    cfg=json.loads(Path('configs/regional_shock.json').read_text());cal=json.loads(Path('results/shock/calibration.json').read_text())
    meta=json.loads(Path('results/shock/run/episodes.json').read_text())
    model=dict(np.load('data/regional/refinement/model.npz'))
    access=pd.read_csv('results/shock/run/access.csv.gz',keep_default_na=False);access=access[access.method=='M3']
    alarms=pd.read_csv('results/shock/run/alarms.csv.gz');alarms=alarms[alarms.method=='M3']
    aa={e:a for e,a in access.groupby('episode')};al={e:a for e,a in alarms.groupby('episode')}
    torch.set_num_threads(4);torch.backends.cuda.matmul.allow_tf32=False;torch.cuda.set_per_process_memory_fraction(.70)
    engine=OneStep(model,cfg['window']);start=time.perf_counter();allrows=[];episodes=[]
    for b in range(1 if args.smoke else 8):
        with np.load('data/regional/shock/background_%02d.npz'%b) as p:source=dict(p)
        members=[m for m in meta if m['background']==b]
        members.sort(key=lambda m:(m['family']!='none',m['episode']))
        if args.smoke:members=[m for m in members if m['family']=='none' or (m['family']=='cancel_exact' and m['magnitude']==3.)]
        control=None
        for m in members:
            rows=reconstruct(engine,model,source,m,cfg,cal,aa[m['episode']],al[m['episode']],control)
            if m['family']=='none':control=rows
            event=[r for r in rows if r['in_event']]
            summary={k:m[k] for k in ['episode','background','family','magnitude','onset','duration']}
            for key in ['probe_hits','fine_hits','affected_probe_winners','affected_top_group','affected_active','trigger','ranking_changed','trigger_changed','action_changed','read_identity_changed']:
                summary[key+'_steps']=sum(bool(r[key]) for r in event)
                summary['first_'+key]=next((r['step'] for r in event if r[key]),None)
            for key in ['exposed_value_difference','exposed_probe_difference','innovation_difference','score_difference','assimilation_value_difference']:
                summary['first_'+key]=first(rows,key);summary['max_'+key]=max(r[key] for r in rows)
            summary.update(max_affected_probe_z=max(r['affected_probe_z'] for r in rows),
                max_score=max(r['best_score'] for r in event),score_reproduction_max=max(r['score_error'] for r in rows),
                budget_block_steps=sum(r['budget_blocked'] for r in rows),
                requested=sum(r['requested'] for r in rows),read=sum(r['read'] for r in rows),assimilated=sum(r['assimilated'] for r in rows))
            episodes.append(summary)
            allrows.extend({k:v for k,v in r.items() if not k.startswith('_')} for r in rows)
            print(m['episode'],json.dumps(summary),flush=True)
            folder=root/('smoke_diagnostic' if args.smoke else 'diagnostic');folder.mkdir(exist_ok=True)
            pd.DataFrame(episodes).to_csv(folder/'episodes.csv',index=False)
            pd.DataFrame(allrows).to_csv(folder/'steps.csv.gz',index=False,compression='gzip')
    (folder/'summary.json').write_text(json.dumps(dict(episodes=len(episodes),seconds=time.perf_counter()-start,
        device=torch.cuda.get_device_name(),vram_bytes=torch.cuda.get_device_properties(0).total_memory,
        gpu_peak_bytes=torch.cuda.max_memory_allocated(),host_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        source_config_sha256=immutable_digest('configs/regional_shock.json'),model_sha256=immutable_digest('data/regional/refinement/model.npz'),
        maximum_score_reproduction_error=max(e['score_reproduction_max'] for e in episodes)),indent=2)+'\n')
if __name__=='__main__':main()

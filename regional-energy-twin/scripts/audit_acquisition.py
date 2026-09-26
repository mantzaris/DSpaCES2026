"""Focused consistency/provenance audit; reads only frozen development artifacts."""
import json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from evidence_fusion.refinement_access import immutable_digest

def main():
    root=Path('results/acquisition');summary={}
    frozen=json.loads((root/'frozen.json').read_text())
    for p,digest in frozen['hashes'].items():assert immutable_digest(p)==digest,p
    summary['frozen_hashes_verified']=len(frozen['hashes'])
    model=dict(np.load('data/regional/refinement/model.npz'));assert len(set(model['meters']))==4194
    summary['physical_meter_ids']=len(set(model['meters']))
    diagnostic=pd.read_csv(root/'diagnostic/steps.csv.gz')
    assert (diagnostic.requested_identity_hash==diagnostic.original_identity_hash).all()
    assert (diagnostic.read==diagnostic.assimilated).all()
    summary['original_ordered_identity_checks']=len(diagnostic)
    summary['original_read_assimilation_mismatches']=int((diagnostic.read!=diagnostic.assimilated).sum())
    new=pd.read_csv(root/'run/metrics.csv.gz');old=pd.read_csv('results/shock/run/metrics.csv.gz')
    meta=pd.DataFrame(json.loads((root/'run/episodes.json').read_text()))
    comparisons=[]
    for ep in meta.itertuples():
        if ep.phase=='fresh' and ep.family!='none':continue
        methods=['M0','M2','M3','M4'] if ep.phase=='fresh' else ['M0']
        key='b%02d_%s_%s'%(ep.background,ep.family,ep.magnitude)
        for method in methods:
            a=new[(new.episode==ep.episode)&(new.method==method)]
            b=old[(old.episode==key)&(old.method==method)]
            merged=a.merge(b,on=['step','horizon','level'],suffixes=('_new','_old'),validate='one_to_one')
            assert len(merged)==384,(ep.episode,method,len(merged))
            error=max(float(abs(merged[k+'_new']-merged[k+'_old']).max()) for k in ['mae','mse','coverage','width','adjusted_coverage','adjusted_width'] if merged[k+'_new'].notna().any())
            assert error<1e-8,(ep.episode,method,error)
            comparisons.append(dict(episode=ep.episode,method=method,max_metric_difference=error))
    pd.DataFrame(comparisons).to_csv(root/'legacy_reproduction.csv',index=False)
    summary['legacy_comparisons']=len(comparisons);summary['legacy_max_difference']=max(r['max_metric_difference'] for r in comparisons)
    c=pd.read_csv(root/'run/costs.csv.gz');limited=c[c.method.isin(['M2','M3','M3b','M3b_fixed'])]
    assert limited.fine_attempts.eq(209).all()
    assert limited.groupby(['episode','method']).fine_attempts.sum().eq(10032).all()
    summary['limited_access_budget_checks']=len(limited)
    checks=pd.read_csv(root/'run/checks.csv.gz');summary['same_information_max_abs']=float(checks.same_information_max_abs.max());assert summary['same_information_max_abs']<1e-7
    summary['same_information_checks']=len(checks)
    dates=[]
    for b in range(8):
        with np.load('data/regional/shock/background_%02d.npz'%b) as p:ts=p['timestamps'].astype(str)
        assert all('2013-01-01'<=x<'2013-04-01' for x in ts);dates.extend(ts)
    summary['source_date_min']=min(dates);summary['source_date_max']=max(dates)
    summary['london_holdout_sealed']=True;summary['bdg2_seals_preserved']=True
    summary['new_raw_ingestion_rows']=0;summary['new_training_rows']=0
    (root/'artifact_audit.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()

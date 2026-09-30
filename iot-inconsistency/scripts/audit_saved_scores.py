"""Recompute production E4--E11 with independent NumPy scalar arithmetic."""
from pathlib import Path
import hashlib,json,sys,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'reference'));sys.path.insert(0,str(ROOT/'src'))
from reference_score import repair_score as oracle_score
from iot_repair.experiment import json_save
subprocess.run([sys.executable,str(ROOT/'scripts/finalize_saved_protocol.py')],check=True)
checks=[]
# All saved primary cases are audited, not merely a favorable example.
for directory in sorted((ROOT/'results/study').glob('*/test')):
    for path in sorted(directory.glob('test_*.json')):
        case=json.loads(path.read_text());raw=np.load(directory/case['raw_artifact']);x=raw['input'];errors=[]
        assert hashlib.sha256((directory/case['raw_artifact']).read_bytes()).hexdigest()==case['raw_sha256']
        for record in case['records']:
            i=record['raw_index'];support=record['support_count'];before=raw['loss_before'][i,:,:,:support];after=raw['loss_after'][i,:,:,:support]
            weights=raw['group_weights'][i,:support]
            # Pairwise E4 is independent of the production sorted-sample formula.
            for key,expected in [('witness_samples_before',before),('witness_samples_after',after)]:
                samples=raw[key][i,:,:,:support].astype('float64')
                target=x[np.array(record['witness_channels']),-8:].astype('float64');available=np.isfinite(target)
                observed=np.nan_to_num(target)
                cell=np.mean(np.abs(samples-observed[None,None,:,:,None]),axis=-1)-.5*np.mean(np.abs(samples[...,None,:]-samples[...,:,None]),axis=(-1,-2))
                grouped=np.array([cell[:,:,g,available[g]].mean(-1) for g in range(support)]).transpose(1,2,0)
                errors.append(float(np.max(np.abs(grouped-expected))))
            paired=np.sum((before-after)*weights,axis=-1);members=paired.mean(-1);r=members.mean();u=members.std(ddof=1)
            mc=np.sqrt(np.sum(paired.var(-1,ddof=1)/paired.shape[-1])/len(members)**2)
            if record['kind']=='observation':
                ch=record['index'];mask=np.isfinite(x[ch,-8:]);replacements=raw['replacement_targets'][i].astype('float64')
                cost=.5*mask.sum()/np.isfinite(x).sum()+.5*np.minimum(np.abs(replacements[...,mask]-x[ch,-8:][mask])/3,1).mean()
            else:cost=1/len(case['graph']['edges'])
            parameters=case['score_parameters'];kappa=parameters['kappa'];penalty=parameters['lambda']
            oracle=oracle_score(before,after,weights,cost,uncertainty_weight=kappa,edit_weight=penalty)
            for key,value in oracle.items():errors.append(abs(value-record[key]))
            for expected,actual in [(r,record['mean_gain']),(u,record['model_instability']),(mc,record['monte_carlo_standard_error']),(cost,record['edit_cost']),(r-kappa*u-penalty*cost,record['score'])]:errors.append(abs(expected-actual))
            assert record['witness_hash_before']==record['witness_hash_after']
        error=max(errors,default=0.)
        if error>1e-10:raise AssertionError((str(path),error))
        checks.append(dict(case=str(path.relative_to(ROOT)),sha256=case['raw_sha256'],max_absolute_error=error,candidates=len(case['records'])))
json_save(ROOT/'results/audits/production_equations.json',dict(cases=len(checks),candidates=sum(r['candidates'] for r in checks),
    tolerance=1e-10,max_absolute_error=max([r['max_absolute_error'] for r in checks],default=0.),checks=checks))
print('Audited',len(checks),'production cases')

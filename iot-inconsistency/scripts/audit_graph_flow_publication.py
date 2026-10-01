"""Independently replay the published compact evidence without data or checkpoints."""
from pathlib import Path
import hashlib
import io
import json
import tarfile

import numpy as np
from scipy.special import logsumexp
from sklearn.metrics import average_precision_score

ROOT=Path(__file__).resolve().parents[1];DIRECTORY=ROOT/'results/graph_flow_v1'


def digest(data):return hashlib.sha256(data).hexdigest()


def gaussian_components(raw):
    y=raw['input'][raw['query'],-8:].astype(float);z=raw['generated'].astype(float)
    dimension=y.shape[-1];identity=np.eye(dimension);one=np.ones(dimension)
    times=raw['target_times'];ramp=2*(times-times[0])/(times[-1]-times[0])-1
    scale=float(raw['corruption_scale']);floor=.25
    covariance=[scale**2*np.outer(one,one)+floor**2*identity,
                scale**2*np.outer(ramp,ramp)+floor**2*identity,
                scale**2*identity,scale**2*np.outer(one,one)+floor**2*identity]
    result=[]
    for index,noise in enumerate(covariance):
        mean=z if index!=3 else np.broadcast_to(z[...,:1],z.shape)
        delta=y[:,None,None]-mean;cholesky=np.linalg.cholesky(noise)
        whitened=np.linalg.solve(cholesky,delta.reshape(-1,dimension).T).T.reshape(delta.shape)
        result.append(-.5*(np.square(whitened).sum(-1)+2*np.log(np.diag(cholesky)).sum()+dimension*np.log(2*np.pi)))
    return logsumexp(np.stack(result,-1)-np.log(4),axis=-1)


def main():
    manifest=json.loads((DIRECTORY/'publication/manifest.json').read_text());analysis=json.loads((DIRECTORY/'analysis.json').read_text())
    predictions={};compact_rows={};count=0;maximum=0.;replays=[];json_records={};files=0
    outcomes={d:{r['case_id']:r for r in json.loads((DIRECTORY/d/'flow_ratio_repair_rows.json').read_text())} for d in analysis['datasets']}
    for bundle in manifest['bundles']:
        archive_path=ROOT/bundle['path'];assert digest(archive_path.read_bytes())==bundle['sha256']
        expected={e['path']:e for e in bundle['entries']};seen=set()
        with tarfile.open(archive_path,'r|xz') as archive:
            for item in archive:
                assert item.isfile() and item.name in expected and item.name not in seen
                content=archive.extractfile(item).read();assert digest(content)==expected[item.name]['sha256'];seen.add(item.name);files+=1
                if item.name.endswith('.json'):
                    json_records[item.name]=json.loads(content);continue
                if not item.name.endswith('.npz'):continue
                raw=dict(np.load(io.BytesIO(content),allow_pickle=False))
                if 'audit_log_normal_members' in raw:
                    normal=raw['audit_log_normal_members'].astype(float)
                    if len(normal):
                        recomputed=logsumexp(raw['audit_log_fault_components']-np.log(4),axis=1)-logsumexp(normal,axis=1)+np.log(3)
                        error=float(np.max(np.abs(recomputed-raw['audit_score'])));assert error<1e-7
                        count+=len(normal);maximum=max(maximum,error)
                        np.testing.assert_allclose(raw['score_flow_ratio'][raw['audit_query']],recomputed,atol=1e-7,rtol=0)
                    parts=Path(item.name).parts;dataset=parts[-3];split=parts[-2]
                    compact_rows[(dataset,split,Path(item.name).stem)]=raw
                    if split=='test':
                        predictions.setdefault(dataset,[]).append(raw)
                elif 'generated' in raw and 'target_times' in raw and len(raw.get('query',[])):
                    logs=gaussian_components(raw);q_error=float(np.max(np.abs(logs-raw['log_corruption'])))
                    flat=logs.reshape(len(logs),-1);normal=raw['log_normal_members'].astype(float)
                    ratio=logsumexp(flat,axis=1)-np.log(flat.shape[1])-logsumexp(normal,axis=1)+np.log(normal.shape[1])
                    error=float(np.max(np.abs(ratio-raw['score'])));assert error<1e-7 and q_error<1e-7
                    weights=np.exp(flat-logsumexp(flat,axis=1,keepdims=True));generated=raw['generated'].reshape(len(logs),-1,8)
                    means=np.sum(weights[...,None]*generated,axis=1)
                    repair_error=float(np.max(np.abs(means-raw['posterior_mean'])));assert repair_error<1e-7
                    split='calibration' if '_calibration_' in item.name else 'test'
                    dataset,case_id=Path(item.name).stem.split('_'+split+'_',1)
                    compact=compact_rows[(dataset,split,case_id)]
                    ess=1/np.sum(weights**2,axis=1)
                    ess_error=float(np.max(np.abs(ess-compact['ess'][raw['query']])));assert ess_error<1e-7
                    result=dict(path=item.name,candidates=len(logs),q_max_error=q_error,score_max_error=error,
                                repair_mean_max_error=repair_error,ess_max_error=ess_error)
                    if split=='test':
                        row=outcomes[dataset][case_id];target=int(np.argmax(compact['score_flow_ratio']))
                        assert target==row['target']
                        index=int(np.flatnonzero(raw['query']==target)[0])
                        before=raw['input'].astype(float);reference=raw['reference'].astype(float);after=before.copy()
                        after[target,-8:]=means[index];mask=np.isfinite(before)&np.isfinite(reference)
                        delta=float((np.square(before[mask]-reference[mask]).sum()-np.square(after[mask]-reference[mask]).sum())/8)
                        delta_error=abs(delta-row['improvement']);assert delta_error<1e-6
                        correct=bool(raw['truth'][target]);assert correct==row['correct_attribution']
                        assert bool(not correct or delta<=.01)==row['failed']
                        assert bool(delta<0)==row['harmful']
                        result.update(repair_outcome_max_error=delta_error,repair_action_target=target)
                    replays.append(result)
        assert seen==set(expected)
    ap_checks=[]
    for dataset,rows in predictions.items():
        truth=np.stack([r['truth'] for r in rows]);expected=analysis['datasets'][dataset]
        assert truth.size==expected['candidates'] and int(truth.sum())==expected['fault_candidates']
        for method,record in expected['methods'].items():
            score=np.stack([r['score_'+method] for r in rows]);actual=float(average_precision_score(truth.ravel(),score.ravel()))
            error=abs(actual-record['average_precision']);assert error<1e-12
            ap_checks.append(dict(dataset=dataset,method=method,average_precision=actual,absolute_error=error))
    # Verify source and generated-table hashes from the published claim ledger.
    ledger=json.loads((DIRECTORY/'paper_claims.json').read_text())
    for category in ('inputs','outputs'):
        for path,sha in ledger[category].items():assert digest((ROOT/path).read_bytes())==sha,path
    figures=json.loads((DIRECTORY/'figure_provenance.json').read_text())
    for figure in figures.values():
        for path,sha in figure['inputs'].items():assert digest((ROOT/path).read_bytes())==sha,path
        for path,sha in figure['outputs'].items():
            if path.endswith('.png') and not (ROOT/path).exists():continue
            assert digest((ROOT/path).read_bytes())==sha,path
    report=dict(status='passed',records_verified=files,compact_scores_recomputed=count,maximum_score_error=maximum,
        average_precision_checks=ap_checks,generation_replays=replays,claim_source_hashes_verified=True,figure_hashes_verified=True,
        scope='Saved-evidence replay without data acquisition or model weights. GPU model/draw replay is separately recorded in production_equation_audit.json.',
        original_sources_preserved=True,compact_omission_manifest='results/graph_flow_v1/publication/manifest.json')
    (DIRECTORY/'publication_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('average_precision_checks','generation_replays')},indent=2))


if __name__=='__main__':main()

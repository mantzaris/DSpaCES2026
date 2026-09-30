"""Export actual saved findings, fixed layouts and immutable graph evidence."""
from pathlib import Path
import argparse,hashlib,json,math,sys
import numpy as np
import networkx as nx
from scipy.special import expit
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.metrics import candidate_score
from iot_repair.calibration import null_tail_value
from iot_repair.experiment import json_save
from iot_repair.persistence import initialize,persist_bundle,transaction,statement
p=argparse.ArgumentParser();p.add_argument('--persist',action='store_true');a=p.parse_args();out=ROOT/'results/graph';out.mkdir(parents=True,exist_ok=True)
reports=[]
if a.persist:initialize()
for directory in sorted((ROOT/'results/study').iterdir()):
    if not (directory/'test/complete.json').exists():continue
    dataset=directory.name;params=json.loads((directory/'frozen.json').read_text());cal=json.loads((directory/'calibration_complete.json').read_text())
    meta=json.loads((ROOT/'data/processed'/dataset/'metadata.json').read_text())
    provenance_context={}
    for stage in ['train','development']:
        data=np.load(ROOT/'data/processed'/dataset/(stage+'.npz'))
        provenance_context[stage]=dict(decision_start=int(data['timestamp'].min()),decision_stop=int(data['timestamp'].max()),
            blocks=sorted(set(map(str,data['block']))),file=str(Path('data/processed')/dataset/(stage+'.npz')))
    provenance_context['manifest']='data/manifests/'+dataset+'.json'
    provenance_context['manifest_sha256']=hashlib.sha256((ROOT/provenance_context['manifest']).read_bytes()).hexdigest()
    cases=[json.loads(p.read_text()) for p in sorted((directory/'test').glob('test_*_observation.json'))]
    # Figures are explicitly selected illustrations, never used to estimate performance.
    def margin(case):
        rows=[r for r in case['records'] if r['kind']=='observation' and r['support_count']>=2]
        if not rows:return -1e20
        rows=sorted(rows,key=lambda r:candidate_score(r,'proposed',params['kappa'],params['lambda']),reverse=True)
        return candidate_score(rows[0],'proposed',params['kappa'],params['lambda']) if rows[0]['truth'] else -1e20
    selected=max(cases,key=margin)
    additional=min(cases,key=margin)
    for label,case in [('illustration',selected),('failure_review',additional)]:
        raw=np.load(directory/'test'/case['raw_artifact'])
        hypotheses=[]
        for record in case['records']:
            row=dict(record);score=candidate_score(row,'proposed',params['kappa'],params['lambda']);reference=cal['candidate_null_references'][row['kind']+'/'+str(row['support_count'])]
            pvalue=float(null_tail_value(reference,score)) if reference else None;prob=cal['probability'].get(row['kind']+'/proposed')
            q=float(expit(prob['coefficient']*(score-prob['mean'])/prob['scale']+prob['intercept'])) if prob and row['support_count']>=2 else None
            row.update(selected_score=score,candidate_null_tail=pvalue,fault_probability=q,probability_calibration_prevalence=prob['prevalence'] if prob else None,
                review_status='evidence accepted at 0.05' if row['support_count']>=2 and pvalue is not None and pvalue<=.05 else 'unresolved or insufficient evidence')
            intervals=[]
            for group,channel in enumerate(row['witness_channels']):
                intervals.append(dict(channel=channel,source=case['graph']['groups'][channel],unit=meta['units'][channel],
                    observed=raw['input'][channel,-8:].tolist(),
                    before=np.nanquantile(raw['witness_samples_before'][row['raw_index'],:,:,group],[.05,.5,.95],axis=(0,1,3)).tolist(),
                    after=np.nanquantile(raw['witness_samples_after'][row['raw_index'],:,:,group],[.05,.5,.95],axis=(0,1,3)).tolist()))
            row['witness_prediction_intervals']=intervals
            hypotheses.append(row)
        # Raw scores are only comparable within their hypothesis type.
        hypotheses.sort(key=lambda r:(r['kind']!='observation',-r['selected_score']))
        best_obs=next((r for r in hypotheses if r['kind']=='observation'),None);best_edge=next((r for r in hypotheses if r['kind']=='association'),None)
        relevant=[]
        for row in [best_obs,best_edge]:
            if row is None:continue
            relevant+=row['witness_channels']
            if row['kind']=='observation':relevant.append(row['index'])
            else:
                edge=case['graph']['edges'][row['index']];relevant +=[edge['source'],edge['target']]
        nodes=list(dict.fromkeys(relevant));ranked=sorted(enumerate(case['graph']['edges']),key=lambda pair:-pair[1]['validation_gain'])
        for _,edge in ranked:
            if edge['source'] in nodes or edge['target'] in nodes:
                for ch in [edge['source'],edge['target']]:
                    if ch not in nodes and len(nodes)<10:nodes.append(ch)
        for ch in range(len(case['graph']['groups'])):
            if len(nodes)>=min(8,len(case['graph']['groups'])):break
            if ch not in nodes:nodes.append(ch)
        possible=[(index,e) for index,e in ranked if e['source'] in nodes and e['target'] in nodes]
        undirected=nx.Graph();undirected.add_nodes_from(nodes)
        for index,e in possible:
            if not undirected.has_edge(e['source'],e['target']):undirected.add_edge(e['source'],e['target'],weight=-e['validation_gain'],edge_index=index)
        tree=nx.minimum_spanning_tree(undirected);retained={v['edge_index'] for _,_,v in tree.edges(data=True)}
        if best_edge:retained.add(best_edge['index'])
        for index,e in possible:
            if best_obs and e['source']==best_obs['index'] and e['target'] in best_obs['witness_channels']:retained.add(index)
        displayed=[(index,e) for index,e in possible if index in retained]
        layout=nx.spring_layout(undirected,seed=9026,k=1.5,iterations=300,weight=None)
        coordinates=np.array([layout[i] for i in nodes]);minimum=coordinates.min(0);span=np.maximum(coordinates.max(0)-minimum,1e-9)
        positions={i:np.array([80,65])+(layout[i]-minimum)/span*np.array([560,305]) for i in nodes}
        # Deterministic collision adjustment depends only on displayed topology.
        # It preserves every relevant node while keeping circle labels separate.
        for iteration in range(300):
            for first,i in enumerate(nodes):
                for j in nodes[first+1:]:
                    delta=positions[j]-positions[i];distance=np.linalg.norm(delta)
                    if distance<92:
                        direction=delta/max(distance,1e-9) if distance else np.array([1.,0.])
                        positions[i]-=direction*(92-distance)*.5;positions[j]+=direction*(92-distance)*.5
            for i in nodes:positions[i]=np.clip(positions[i],[65,55],[655,385])
        view=dict(nodes=[dict(index=i,label=f'C{i:02d}',x=positions[i][0],y=positions[i][1]) for i in nodes],
            edges=[dict(index=index,source=e['source'],target=e['target'],lag=e['lag'],sign=e['sign'],label=f"predicts C{e['target']:02d}, lag {e['lag']}") for index,e in displayed],
            pruning_rule='All selected suspects and witnesses retained. Context uses a fixed spanning forest of strong stored relations. Coordinates use seed 9026 and deterministic collision adjustment, never fault labels.',
            sample_seconds=300 if dataset=='intel' else 1,layout_seed=9026)
        artifact=str((directory/'test'/case['raw_artifact']).relative_to(ROOT));run_id=dataset+':'+hashlib.sha256((directory/'frozen.json').read_bytes()).hexdigest()[:16]
        run=dict(id=run_id,ensemble_seeds=[1101,2202,3303],members=3,replicates=8,predictive_samples=8,
            manifest=str((directory/'test/provenance.json').relative_to(ROOT)),manifest_sha256=hashlib.sha256((directory/'test/provenance.json').read_bytes()).hexdigest())
        process_p=float(null_tail_value(cal['null_references']['observation/gdn'],np.nanmax(np.asarray(case['baseline_sensor_scores']['gdn'],dtype=float))))
        bundle=dict(process_alert=process_p<=.05,process_null_tail=process_p,dataset=dataset,case=case,hypotheses=hypotheses,artifact=artifact,view=view,run=run,
            association_context=provenance_context,
            median=meta['normalizer']['median'],scale=meta['normalizer']['scale'],units=meta['units'],
            selection_rule='largest correctly localized observation score, if available' if label=='illustration' else 'first failed localization in stable file order, if available',
            raw_score_comparison='within candidate type only')
        json_save(out/(dataset+'_'+label+'.json'),bundle)
        if a.persist:reports.append(persist_bundle(bundle))
if a.persist:
    counts=transaction([statement('MATCH (n) WHERE any(label IN labels(n) WHERE label IN $labels) RETURN labels(n)[0] AS entity, count(*) AS count',labels=['Sensor','Channel','ObservationWindow','AssociationVersion','Disagreement','RepairHypothesis','EvidenceGroup','ModelRun','OperatorDecision'])])
    json_save(out/'persistence_audit.json',dict(exports=reports,counts=counts))
print('Exported',len(list(out.glob('*_illustration.json'))),'dataset illustrations')

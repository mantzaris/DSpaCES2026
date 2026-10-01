"""Export predeclared success, failure, inadequacy and ambiguity cases from saved results."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

import numpy as np
import networkx as nx
import torch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.flow_data import build_cases,graph_for,metadata,sha256,public_case
from iot_repair.flow_training import load_flow
from iot_repair.flow_inference import infer_case
from iot_repair.flow_math import summarize_repairs
from iot_repair.flow_confidence import load_predictions,predict_probability,rank_pvalues
from iot_repair.graph_flow_model import build_context
from iot_repair.flow_persistence import persist_flow_bundle
from iot_repair.persistence import transaction,statement
from iot_repair.experiment import json_save


def sensor_names(dataset,meta):
    return [source+(' '+unit if dataset=='intel' else '') for source,unit in zip(meta['groups'],meta['units'])]


def layout(graph,names,target,context):
    nodes=list(dict.fromkeys([target]+context));ranked=sorted(graph['edges'],key=lambda e:(-e['validation_gain'],e['id']))
    for edge in ranked:
        if len(nodes)>=7:break
        if edge['source'] in nodes or edge['target'] in nodes:
            for value in (edge['source'],edge['target']):
                if value not in nodes and len(nodes)<7:nodes.append(value)
    possible=[e for e in ranked if e['source'] in nodes and e['target'] in nodes]
    network=nx.Graph();network.add_nodes_from(nodes)
    for edge in possible:
        if not network.has_edge(edge['source'],edge['target']):network.add_edge(edge['source'],edge['target'],weight=-edge['validation_gain'],identity=edge['id'])
    tree=nx.minimum_spanning_tree(network);retained={props['identity'] for _,_,props in tree.edges(data=True)}
    retained.update(e['id'] for e in possible if e['target']==target and e['source'] in context)
    edges=[dict(e) for e in possible if e['id'] in retained]
    positions=nx.spring_layout(network,seed=20261001,iterations=300,weight=None,k=1.4)
    coordinates=np.array(list(positions.values()));low=coordinates.min(0);span=np.maximum(coordinates.max(0)-low,1e-6)
    positions={key:np.array([90.,75.])+(value-low)/span*np.array([560.,290.]) for key,value in positions.items()}
    for _ in range(200):
        for i,left in enumerate(nodes):
            for right in nodes[i+1:]:
                delta=positions[right]-positions[left];distance=np.linalg.norm(delta)
                if distance<125:
                    direction=delta/max(distance,1e-9) if distance else np.array([1.,0.]);positions[left]-=direction*(125-distance)/2;positions[right]+=direction*(125-distance)/2
        for node in nodes:positions[node]=np.clip(positions[node],[80,55],[650,375])
    occupied=[]
    for point in positions.values():occupied.extend([[point[0]-40,point[0]+40,point[1]-33,point[1]+33],[point[0]-90,point[0]+90,point[1]+34,point[1]+54]])
    for edge in edges:
        a=positions[edge['source']];b=positions[edge['target']];delta=b-a;perpendicular=np.array([-delta[1],delta[0]])/max(np.linalg.norm(delta),1e-6);choices=[]
        for fraction in [.5,.3,.7]:
            for offset in [-25,25,-45,45,-70,70]:
                point=np.clip(a+fraction*delta+offset*perpendicular,[110,30],[630,412]);box=[point[0]-110,point[0]+110,point[1]-15,point[1]+20]
                hits=sum(box[0]<r[1] and box[1]>r[0] and box[2]<r[3] and box[3]>r[2] for r in occupied)
                choices.append((hits*10000+abs(offset),point,box))
        # A sparse network still needs room for two-line labels. If nearby slots
        # collide, search the full canvas and retain an explicit edge connector.
        for x in np.arange(115,631,45):
            for y in np.arange(35,411,35):
                point=np.array([float(x),float(y)]);box=[x-110,x+110,y-15,y+20]
                hits=sum(box[0]<r[1] and box[1]>r[0] and box[2]<r[3] and box[3]>r[2] for r in occupied)
                fraction=np.clip((point-a)@delta/max(delta@delta,1e-9),0,1)
                distance=np.linalg.norm(point-(a+fraction*delta))
                choices.append((hits*10000+distance+80,point,box))
        _,point,box=min(choices,key=lambda item:item[0]);occupied.append(box);edge.update(label_x=float(point[0]),label_y=float(point[1]))
    return dict(nodes=[dict(index=i,name=names[i],x=float(positions[i][0]),y=float(positions[i][1])) for i in nodes],edges=edges,
        pruning_rule='Target, all allowed supporting channels, and nearby stored associations, up to seven nodes. Spanning forest plus incoming conditioning edges. Layout uses fixed topology-based seed, never fault truth.')


def make_bundle(dataset,case,arrays,raw,record,selection,lock_hash,reason,status_override=None,graph_override=None):
    graph=graph_override or graph_for(ROOT,dataset);meta=metadata(ROOT,dataset);names=sensor_names(dataset,meta)
    scores=arrays['score_flow_ratio'];target=int(np.argmax(scores));position=int(np.flatnonzero(raw['query']==target)[0])
    generations=raw['generated'][position].reshape(-1,8);weights=raw['posterior_weights'][position]
    summaries=summarize_repairs(torch.tensor(generations[None]),torch.tensor(weights[None]))
    scale=meta['normalizer']['scale'][target];median=meta['normalizer']['median'][target]
    convert=lambda values:(np.asarray(values)*scale+median).tolist()
    context=build_context(torch.tensor(raw['input'][None]),torch.tensor([target]),graph,selection['models']['selected']['specification']['context_length'])
    support=context.neighbors[0][context.support[0]].tolist()
    calibrator=json.loads((ROOT/'results/graph_flow_v1'/dataset/'calibration.json').read_text())['methods']['flow_ratio']
    probability=predict_probability(scores[None],calibrator['probability'])[0,target]
    namespace='graph_flow_v1';run=namespace+':'+dataset+':'+lock_hash[:16]+':'+graph['version'];window=run+':'+case['id'];identity=window+':measurement:'+str(target)
    subset={key:value for key,value in raw.items() if key in ('input','reference','truth','target_times','seed','corruption_scale')}
    for key in ('query','latent','generated','log_normal_members','log_corruption','log_fault_components','log_normal','log_fault','score','posterior_weights','posterior_mean'):
        subset[key]=raw[key][position:position+1]
    destination=ROOT/'results/graph_flow_v1/graph/artifacts';destination.mkdir(parents=True,exist_ok=True)
    temporary=destination/'generation.tmp.npz';np.savez_compressed(temporary,**subset);digest=sha256(temporary);artifact=destination/(digest+'.npz')
    if artifact.exists():temporary.unlink()
    else:temporary.rename(artifact)
    probability=float(probability);adequate=bool(arrays['numerical_adequate'][target])
    hypothesis=dict(id=identity,target=target,sensor_name=names[target],score=float(scores[target]),
        log_normal=float(raw['log_normal'][position]),log_fault=float(raw['log_fault'][position]),ess=float(arrays['ess'][target]),
        numerical_adequate=adequate,probability=probability,calibration_prevalence=calibrator['probability']['prevalence'],
        window_p=float(rank_pvalues([scores.max()],calibrator['normal_window_maxima'])[0]),draws_per_member=selection['scoring']['sample_count'],
        context_channels=support,status=status_override or ('requires_review' if adequate else 'numerical_abstention'),
        meaning='Observed interval conflicts with the conditional distribution under the declared fault comparison.' if scores[target]>0 else 'The declared fault model is not favored over the normal model for this interval.')
    if status_override=='ambiguous':hypothesis['meaning']='A physical change and coordinated sensor corruption produce identical available observations. This evidence cannot distinguish them.'
    sample_indices=np.linspace(0,len(generations)-1,min(12,len(generations)),dtype=int)
    return dict(namespace=namespace,dataset=dataset,run_id=run,window_id=window,protocol_sha256=lock_hash,
      model_hashes=[r['sha256'] for r in selection['members']['members']],case=public_case(case),input_sha256=record['input_sha256'],
      artifact=dict(path=str(artifact.relative_to(ROOT)),sha256=digest),seed=record['seed'],graph_version=graph['version'],
      sensors=[dict(index=i,name=name,source=meta['groups'][i],unit=meta['units'][i]) for i,name in enumerate(names)],
      associations=graph['edges'],hypothesis=hypothesis,selection_reason=reason,disputed_associations=[],
      view=layout(graph,names,target,support),trajectories=dict(observed=convert(raw['input'][target,-8:]),reference=convert(raw['reference'][target,-8:]),
        mean=convert(summaries['mean'][0].numpy()),lower=convert(summaries['lower'][0].numpy()),upper=convert(summaries['upper'][0].numpy()),
        prior=convert(generations[sample_indices]),times=raw['target_times'].tolist(),unit=meta['units'][target]))


def persist_export(bundle):
    result=persist_flow_bundle(bundle)
    for hypothesis in bundle.get('association_hypotheses',[]):
        properties=dict(hypothesis,namespace='graph_flow_v1',kind='association',status='requires_review')
        evidence=dict(namespace='graph_flow_v1',direct_window_residual=hypothesis['direct_window_residual'],window_p=hypothesis['window_p'],
                      interpretation='separate association residual, not measurement likelihood ratio')
        transaction([statement('MERGE (h:FaultHypothesis {id:$id}) ON CREATE SET h += $properties',id=hypothesis['id'],properties=properties),
            statement('MATCH (h:FaultHypothesis {id:$id}),(a:AssociationVersion {id:$edge}) MERGE (h)-[:TARGETS_ASSOCIATION]->(a)',id=hypothesis['id'],edge=bundle['run_id']+':association:'+hypothesis['edge_id']),
            statement('MERGE (s:ScoreEvidence {id:$id}) ON CREATE SET s += $properties',id=hypothesis['id']+':score',properties=evidence),
            statement('MATCH (s:ScoreEvidence {id:$evidence}),(h:FaultHypothesis {id:$hypothesis}) MERGE (s)-[:SCORES]->(h)',evidence=hypothesis['id']+':score',hypothesis=hypothesis['id'])])
    return result


def export():
    parser=argparse.ArgumentParser();parser.add_argument('--persist',action='store_true');parser.add_argument('--persist-only',action='store_true');args=parser.parse_args()
    directory=ROOT/'results/graph_flow_v1';lock=json.loads((directory/'protocol_lock.json').read_text());lock_hash=sha256(directory/'protocol_lock.json')
    output=directory/'graph/cases';output.mkdir(parents=True,exist_ok=True);exports=[]
    for dataset in ([] if args.persist_only else lock['configuration']['datasets']):
        public,arrays,scores,truth=load_predictions(ROOT,dataset,'test');actual=build_cases(ROOT,dataset,'test')
        selection=lock['choices'][dataset];models=None;chosen={}
        for index in sorted(range(len(public)),key=lambda i:public[i]['id']):
            if not truth[index].any() or not arrays[index]['eligible'].any():continue
            target=int(np.argmax(scores['flow_ratio'][index]));adequate=bool(arrays[index]['numerical_adequate'][target]);correct=bool(truth[index,target])
            label='correct_attribution' if correct else 'incorrect_attribution';chosen.setdefault(label,index)
            if not adequate:chosen.setdefault('numerical_abstention',index)
        if 'numerical_abstention' not in chosen:
            chosen['lowest_ess_diagnostic']=min((i for i in range(len(public)) if arrays[i]['eligible'].any()),key=lambda i:arrays[i]['ess'][np.argmax(scores['flow_ratio'][i])])
        for reason,index in chosen.items():
            case=actual[index];record=json.loads((directory/dataset/'test'/(case['id']+'.json')).read_text())
            existing=record.get('full_evidence')
            if existing:raw=dict(np.load(ROOT/existing['path'],allow_pickle=False))
            else:
                if models is None:models=[load_flow(ROOT,r) for r in selection['members']['members']]
                result=infer_case(models,case['values'],graph_for(ROOT,dataset),selection['models']['selected']['specification']['context_length'],
                    selection['scoring']['sample_count'],selection['scoring']['scale'],seed=record['seed'],times=case['target_times'])
                np.testing.assert_allclose(result['scores']['flow_ratio'],scores['flow_ratio'][index],atol=1e-5,rtol=1e-5)
                raw=result['raw'];raw.update(reference=case['reference'],truth=case['truth'])
            bundle=make_bundle(dataset,case,arrays[index],raw,record,selection,lock_hash,reason)
            path=output/(dataset+'_'+reason+'.json');json_save(path,bundle);exports.append(dict(path=str(path.relative_to(ROOT)),sha256=sha256(path),case_id=case['id'],selection_reason=reason))
        ambiguity=directory/dataset/'robustness/ambiguity_example.npz'
        if ambiguity.exists():
            raw=dict(np.load(ambiguity,allow_pickle=False));channels=raw['input'].shape[0];raw['truth']=np.zeros(channels,bool)
            eligible=np.zeros(channels,bool);eligible[raw['query']]=True;ess=np.zeros(channels);ess[raw['query']]=1/np.square(raw['posterior_weights']).sum(1)
            evidence_arrays=dict(score_flow_ratio=raw['full_candidate_score'],eligible=eligible,ess=ess,numerical_adequate=ess>=16)
            case=dict(id='physical_common_mode_0',block='paired_latent_ambiguity_0',timestamp=63,start=0,stop=64,values=raw['input'],reference=raw['reference'],
                      truth=raw['truth'],track='ambiguity',fault=dict(family='physical change or coordinated measurement fault'),target_times=raw['target_times'].tolist())
            record=dict(seed=int(raw['seed']),input_sha256=hashlib.sha256(raw['input'].tobytes()).hexdigest())
            bundle=make_bundle(dataset,case,evidence_arrays,raw,record,selection,lock_hash,'first observationally identical physical/common-mode pair',status_override='ambiguous')
            path=output/(dataset+'_ambiguity.json');json_save(path,bundle);exports.append(dict(path=str(path.relative_to(ROOT)),sha256=sha256(path),case_id=case['id'],selection_reason='first ambiguity pair'))
        stress_cases=json.loads((directory/dataset/'robustness/cases.json').read_text())
        assessed=next(row for row in stress_cases if row['condition']=='graph_error_0.25')
        stress_arrays=np.load(directory/dataset/'robustness/predictions.npz',allow_pickle=False)
        observed=stress_arrays['graph_error_0.25__input'][0];case=dict(actual[[c['id'] for c in actual].index(assessed['case_id'])])
        case.update(id=case['id']+'_association_review',values=observed,reference=observed,truth=np.zeros(len(observed),bool),track='association')
        graph=graph_for(ROOT,dataset)
        for change in assessed['changed_associations']:graph['edges'][change['index']]=change['edge']
        graph['version']=graph['version']+':stress:'+hashlib.sha256(json.dumps(graph,sort_keys=True).encode()).hexdigest()[:12]
        if models is None:models=[load_flow(ROOT,r) for r in selection['members']['members']]
        result=infer_case(models,observed,graph,selection['models']['selected']['specification']['context_length'],selection['scoring']['sample_count'],selection['scoring']['scale'],
                          seed=assessed['seed'],times=case['target_times'])
        np.testing.assert_allclose(result['scores']['flow_ratio'],stress_arrays['graph_error_0.25__flow_ratio'][0],atol=1e-5,rtol=1e-5)
        raw=result['raw'];raw.update(reference=observed,truth=case['truth'])
        evidence_arrays=dict(score_flow_ratio=result['scores']['flow_ratio'],eligible=result['eligible'],ess=result['ess'],numerical_adequate=result['numerical_adequate'])
        record=dict(seed=assessed['seed'],input_sha256=hashlib.sha256(observed.tobytes()).hexdigest())
        bundle=make_bundle(dataset,case,evidence_arrays,raw,record,selection,lock_hash,'first case in the predeclared 25 percent association-error stratum',graph_override=graph)
        bundle['hypothesis']['meaning']='A disputed predictive association changes the conditioning context. The reading score alone does not identify a false edge.'
        edge=next((v['edge'] for v in assessed['changed_associations'] if v['edge']['target']==bundle['hypothesis']['target']),assessed['changed_associations'][0]['edge'])
        names=sensor_names(dataset,metadata(ROOT,dataset));bundle['view']=layout(graph,names,bundle['hypothesis']['target'],bundle['hypothesis']['context_channels']+[edge['source'],edge['target']])
        if edge['id'] not in [e['id'] for e in bundle['view']['edges']]:
            positions={n['index']:n for n in bundle['view']['nodes']};a=positions[edge['source']];b=positions[edge['target']]
            bundle['view']['edges'].append(dict(edge,label_x=(a['x']+b['x'])/2,label_y=(a['y']+b['y'])/2-20))
        bundle['disputed_associations']=[edge['id']]
        bundle['association_hypotheses']=[dict(id=bundle['window_id']+':relation:'+edge['id'],edge_id=edge['id'],source=edge['source'],target=edge['target'],
            direct_window_residual=assessed['association_maximum'],window_p=assessed['association_window_p'],
            meaning='Direct prediction residual for a separately assessed association condition. No causal claim or reading-to-edge inference.')]
        path=output/(dataset+'_association_review.json');json_save(path,bundle);exports.append(dict(path=str(path.relative_to(ROOT)),sha256=sha256(path),case_id=case['id'],selection_reason='first predeclared association error'))
        if models is not None:del models;torch.cuda.empty_cache()
    if args.persist_only:exports=json.loads((directory/'graph/export_manifest.json').read_text())
    if args.persist or args.persist_only:
        for item in exports:item['persistence']=persist_export(json.loads((ROOT/item['path']).read_text()))
        first=transaction([statement('MATCH (n) WHERE n.namespace=$namespace RETURN labels(n)[0],count(*)',namespace='graph_flow_v1')])
        for item in exports:persist_export(json.loads((ROOT/item['path']).read_text()))
        second=transaction([statement('MATCH (n) WHERE n.namespace=$namespace RETURN labels(n)[0],count(*)',namespace='graph_flow_v1')])
        assert first==second,'Repeated export changed entity counts'
        json_save(directory/'graph/persistence_audit.json',dict(exports=exports,counts=second,idempotent=True))
    json_save(directory/'graph/export_manifest.json',exports)

if __name__=='__main__':export()

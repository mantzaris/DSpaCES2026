"""Versioned graph-flow evidence with immutable observations and separate decisions."""
import datetime
import json
from pathlib import Path
import uuid

from .persistence import transaction,statement,DEFAULT_URL

LABELS=('Sensor','PhysicalSource','ObservationWindow','AssociationVersion','ModelRun',
        'FaultHypothesis','GenerationBundle','ScoreEvidence','RepairProposal','ReviewDecision')


def persist_flow_bundle(bundle,url=DEFAULT_URL):
    queries=[statement(f'CREATE CONSTRAINT flow_{label.lower()}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE') for label in LABELS]
    namespace=bundle['namespace'];run=bundle['run_id'];window=bundle['window_id'];dataset=bundle['dataset']
    def node(label,identity,**properties):
        properties.update(namespace=namespace)
        queries.append(statement(f'MERGE (n:{label} {{id:$id}}) ON CREATE SET n += $properties',id=identity,properties=properties))
    def link(left,identity,relationship,right,other):
        queries.append(statement(f'MATCH (a:{left} {{id:$a}}),(b:{right} {{id:$b}}) MERGE (a)-[:{relationship}]->(b)',a=identity,b=other))
    node('ModelRun',run,protocol_sha256=bundle['protocol_sha256'],model_hashes=bundle['model_hashes'],dataset=dataset)
    node('ObservationWindow',window,case_id=bundle['case']['id'],block=bundle['case']['block'],timestamp=bundle['case']['timestamp'],
         input_sha256=bundle['input_sha256'],artifact=bundle['artifact']['path'],artifact_sha256=bundle['artifact']['sha256'],measurements_immutable=True)
    link('ObservationWindow',window,'SCORED_BY','ModelRun',run)
    for sensor in bundle['sensors']:
        source=namespace+':'+dataset+':source:'+sensor['source'];identity=namespace+':'+dataset+':sensor:'+str(sensor['index'])
        node('PhysicalSource',source,name=sensor['source'],dataset=dataset)
        node('Sensor',identity,name=sensor['name'],unit=sensor['unit'],index=sensor['index'],dataset=dataset)
        link('Sensor',identity,'HAS_SOURCE','PhysicalSource',source)
    for edge in bundle['associations']:
        identity=run+':association:'+edge['id']
        properties={k:v for k,v in edge.items() if k!='id' and v is not None}
        properties.update(meaning='predictive association, not causal',lag_units='recording observation steps',version=bundle['graph_version'])
        node('AssociationVersion',identity,**properties)
        source=namespace+':'+dataset+':sensor:'+str(edge['source']);target=namespace+':'+dataset+':sensor:'+str(edge['target'])
        link('Sensor',source,'SOURCE_OF','AssociationVersion',identity);link('AssociationVersion',identity,'PREDICTS','Sensor',target)
        link('ObservationWindow',window,'USES_ASSOCIATION','AssociationVersion',identity)
    hypothesis=bundle['hypothesis'];identity=hypothesis['id'];target=namespace+':'+dataset+':sensor:'+str(hypothesis['target'])
    node('FaultHypothesis',identity,kind='measurement',interval_start=bundle['case']['stop']-8,interval_stop=bundle['case']['stop'],
         meaning=hypothesis['meaning'],status=hypothesis['status'])
    link('FaultHypothesis',identity,'TARGETS','Sensor',target);link('ObservationWindow',window,'HAS_HYPOTHESIS','FaultHypothesis',identity)
    generation=identity+':generation';evidence=identity+':score';proposal=identity+':repair'
    node('GenerationBundle',generation,artifact=bundle['artifact']['path'],sha256=bundle['artifact']['sha256'],draws_per_member=hypothesis['draws_per_member'],
         ensemble_members=3,seed=bundle['seed'],prior_excludes_target=True)
    link('GenerationBundle',generation,'GENERATED_BY','ModelRun',run);link('FaultHypothesis',identity,'USES_GENERATIONS','GenerationBundle',generation)
    node('ScoreEvidence',evidence,log_normal=hypothesis['log_normal'],log_fault=hypothesis['log_fault'],log_ratio=hypothesis['score'],ess=hypothesis['ess'],
         calibrated_probability=hypothesis.get('probability'),calibration_prevalence=hypothesis.get('calibration_prevalence'),
         adequate=hypothesis['numerical_adequate'],artifact=bundle['artifact']['path'],sha256=bundle['artifact']['sha256'])
    link('ScoreEvidence',evidence,'SCORES','FaultHypothesis',identity);link('ScoreEvidence',evidence,'SCORED_BY','ModelRun',run)
    node('RepairProposal',proposal,artifact=bundle['artifact']['path'],sha256=bundle['artifact']['sha256'],summary='weighted conditional mean and 90 percent marginal interval',
         requires_review=True,applied=False,status=hypothesis['status'])
    link('FaultHypothesis',identity,'PROPOSES_REPAIR','RepairProposal',proposal);link('RepairProposal',proposal,'GENERATED_FROM','GenerationBundle',generation)
    transaction(queries,url);return dict(window=window,hypothesis=identity,statements=len(queries))


def flow_review(root,hypothesis_id,action,note='',purpose='operator_review',url=DEFAULT_URL):
    if action not in ('accept','reject','defer'):raise ValueError('Unknown review action')
    if purpose not in ('operator_review','automated_ui_test'):raise ValueError('Unknown review purpose')
    if not hypothesis_id.startswith('graph_flow_v1:'):raise ValueError('Incorrect study namespace')
    record=dict(id='graph_flow_v1:decision:'+str(uuid.uuid4()),namespace='graph_flow_v1',hypothesis_id=hypothesis_id,
                action=action,note=str(note)[:2000],purpose=purpose,time=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                observation_changed=False,repair_applied=False)
    result=transaction([statement('MATCH (h:FaultHypothesis {id:$hypothesis}) CREATE (d:ReviewDecision) SET d=$properties CREATE (d)-[:REVIEWS]->(h) RETURN d.id',
                                  hypothesis=hypothesis_id,properties=record)],url)
    if not result[0]['data']:raise ValueError('Unknown graph-flow hypothesis')
    path=Path(root)/'results/graph_flow_v1/graph/review_decisions.jsonl';path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as stream:stream.write(json.dumps(record)+'\n')
    return record

"""Versioned Neo4j evidence. No write path changes a measurement or actuator."""
from __future__ import annotations
import datetime,json,urllib.request,uuid
from pathlib import Path

DEFAULT_URL='http://127.0.0.1:17474/db/neo4j/tx/commit'
LABELS=['Sensor','Channel','ObservationWindow','AssociationVersion','Disagreement','RepairHypothesis','EvidenceGroup','ModelRun','OperatorDecision']


def transaction(statements,url=DEFAULT_URL):
    # Neo4j forbids schema changes and data writes in one transaction. Keep the
    # response order while committing schema setup before the evidence batch.
    schema=[s for s in statements if s['statement'].lstrip().upper().startswith(('CREATE CONSTRAINT','CREATE INDEX'))]
    if schema and len(schema)!=len(statements):
        schema_result=transaction(schema,url)
        data=[s for s in statements if s not in schema]
        data_result=transaction(data,url)
        ordered=[];si=di=0
        for item in statements:
            if item in schema:ordered.append(schema_result[si]);si+=1
            else:ordered.append(data_result[di]);di+=1
        return ordered
    request=urllib.request.Request(url,data=json.dumps({'statements':statements}).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=30) as response:result=json.load(response)
    if result.get('errors'):raise RuntimeError(json.dumps(result['errors']))
    return result['results']


def statement(query,**parameters):return dict(statement=query,parameters=parameters)


def initialize(url=DEFAULT_URL):
    return transaction([statement(f'CREATE CONSTRAINT iot_{label.lower()}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE') for label in LABELS],url)


def persist_bundle(bundle,url=DEFAULT_URL):
    statements=[];dataset=bundle['dataset'];run=bundle['run'];case=bundle['case'];window_id=bundle.get('window_id',dataset+':'+case['id'])
    def node(label,identity,properties):
        statements.append(statement(f'MERGE (n:{label} {{id:$id}}) ON CREATE SET n += $properties',id=identity,properties=properties))
    def link(a,identity,rel,b,other):
        statements.append(statement(f'MATCH (a:{a} {{id:$a}}),(b:{b} {{id:$b}}) MERGE (a)-[:{rel}]->(b)',a=identity,b=other))
    node('ModelRun',run['id'],run)
    node('ObservationWindow',window_id,dict(source_block=case['block'],start=case['start'],stop=case['stop'],timestamp=case['timestamp'],
        raw_artifact=bundle['artifact'],sha256=case['raw_sha256'],native_process_label=case['native_process_label'],
        label_provenance=case['fault']['label_provenance'] if 'label_provenance' in case['fault'] else 'unmodified reference',
        measurements_immutable=True))
    node('Disagreement',window_id+':review',dict(status='unreviewed',process_alert=bundle.get('process_alert',False)))
    link('Disagreement',window_id+':review','CONCERNS','ObservationWindow',window_id)
    link('ModelRun',run['id'],'EVALUATED','ObservationWindow',window_id)
    for ch,source in enumerate(case['graph']['groups']):
        sensor=dataset+':source:'+source;channel=dataset+':channel:'+str(ch)
        node('Sensor',sensor,dict(source_group=source,dataset=dataset))
        node('Channel',channel,dict(channel=ch,unit=bundle['units'][ch],training_median=bundle['median'][ch],training_scale=bundle['scale'][ch]))
        link('Sensor',sensor,'HAS_CHANNEL','Channel',channel)
    for edge in case['graph']['edges']:
        identity=dataset+':'+case['graph']['version']+':'+edge['id']
        properties={k:v for k,v in edge.items() if v is not None and k!='id'}
        properties.update(graph_version=case['graph']['version'],source_unit=bundle['units'][edge['source']],target_unit=bundle['units'][edge['target']],
            predictor_units='training median/IQR normalized',provenance='training discovery and development validation',confidence_status='stored predictive relation, not causal proof')
        node('AssociationVersion',identity,properties)
        if 'association_context' in bundle:
            # Enrich missing provenance once. Existing predictor attributes and
            # version identities remain immutable across repeated exports.
            statements.append(statement('MATCH (a:AssociationVersion {id:$id}) SET a.discovery_context=coalesce(a.discovery_context,$context), a.discovery_interval=coalesce(a.discovery_interval,$discovery), a.validation_interval=coalesce(a.validation_interval,$validation)',
                id=identity,context=json.dumps(bundle['association_context']),
                discovery=json.dumps(bundle['association_context']['train']),validation=json.dumps(bundle['association_context']['development'])))
        link('Channel',dataset+':channel:'+str(edge['source']),'SOURCE_OF','AssociationVersion',identity)
        link('AssociationVersion',identity,'PREDICTS','Channel',dataset+':channel:'+str(edge['target']))
        link('ObservationWindow',window_id,'USES_VERSION','AssociationVersion',identity)
    for row in bundle['hypotheses']:
        identity=row.get('id',window_id+':'+row['kind']+':'+str(row['index']))
        properties={key:value for key,value in row.items() if isinstance(value,(str,int,float,bool))}
        properties.update(witness_sources=json.dumps(row['witness_groups']),evidence_ref=bundle['artifact'],
            generated_alternatives=json.dumps(row.get('generated_interval_quantiles')),observed_values=json.dumps(row.get('observed_interval')))
        node('RepairHypothesis',identity,properties)
        link('ObservationWindow',window_id,'HAS_HYPOTHESIS','RepairHypothesis',identity)
        link('Disagreement',window_id+':review','COMPARES','RepairHypothesis',identity)
        link('ModelRun',run['id'],'SCORED','RepairHypothesis',identity)
        if row['kind']=='observation':link('RepairHypothesis',identity,'PROPOSES_READING_REVIEW','Channel',dataset+':channel:'+str(row['index']))
        else:link('RepairHypothesis',identity,'PROPOSES_MASK','AssociationVersion',dataset+':'+case['graph']['version']+':'+case['graph']['edges'][row['index']]['id'])
        for group in row['witness_groups']:
            group_id=identity+':evidence:'+group
            node('EvidenceGroup',group_id,dict(source_group=group,witness_hash=row['witness_hash_before'],target_ref=bundle['artifact'],unchanged=True))
            link('EvidenceGroup',group_id,'SUPPORTS','RepairHypothesis',identity)
    transaction(statements,url)
    return dict(statements=len(statements),window=window_id)


def log_decision(root,hypothesis_id,action,note='',url=DEFAULT_URL):
    if action not in ('confirm','reject','defer'):raise ValueError('Unknown review action')
    record=dict(id=str(uuid.uuid4()),hypothesis_id=hypothesis_id,action=action,note=str(note)[:2000],
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='operator hypothesis review; no actuation')
    # Commit to Neo4j first. Failure is visible and does not claim persistence.
    result=transaction([statement('MATCH (h:RepairHypothesis {id:$hypothesis}) CREATE (d:OperatorDecision) SET d=$properties CREATE (d)-[:REVIEWS]->(h) RETURN d.id',
                                 hypothesis=hypothesis_id,properties=record)],url)
    if not result[0]['data']:raise ValueError('Unknown hypothesis')
    path=Path(root)/'results/operator_decisions.jsonl';path.parent.mkdir(exist_ok=True)
    with path.open('a') as stream:stream.write(json.dumps(record)+'\n')
    return record

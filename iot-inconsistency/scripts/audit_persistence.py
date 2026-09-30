"""Verify idempotent evidence import and links for the actual review bundles."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.persistence import persist_bundle,transaction,statement,LABELS
from iot_repair.experiment import json_save

def counts():
    result=transaction([statement('MATCH (n) WHERE any(label IN labels(n) WHERE label IN $labels) RETURN labels(n)[0] AS entity,count(*) AS count ORDER BY entity',labels=LABELS)])
    return dict(r['row'] for r in result[0]['data'])

before=counts();checks=[]
for path in sorted((ROOT/'results/graph').glob('*.json')):
    bundle=json.loads(path.read_text())
    if 'hypotheses' not in bundle:continue
    assert hashlib.sha256((ROOT/bundle['artifact']).read_bytes()).hexdigest()==bundle['case']['raw_sha256']
    persist_bundle(bundle)
    for hypothesis in bundle['hypotheses']:
        rows=transaction([statement('MATCH (m:ModelRun {id:$run})-[:SCORED]->(h:RepairHypothesis {id:$hypothesis})<-[:HAS_HYPOTHESIS]-(w:ObservationWindow {id:$window}) OPTIONAL MATCH (e:EvidenceGroup)-[:SUPPORTS]->(h) RETURN h.score,w.sha256,count(e),h.witness_hash_before',
            run=bundle['run']['id'],hypothesis=hypothesis['id'],window=bundle['window_id'])])[0]['data']
        assert len(rows)==1
        assert rows[0]['row']==[hypothesis['score'],bundle['case']['raw_sha256'],hypothesis['support_count'],hypothesis['witness_hash_before']]
    checks.append(dict(bundle=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),hypotheses=len(bundle['hypotheses'])))
after=counts();assert before==after,'Idempotent import changed entity counts'
decisions=transaction([statement('MATCH (d:OperatorDecision)-[:REVIEWS]->(h:RepairHypothesis) RETURN d.id,d.action,d.note,h.id')])[0]['data']
local=[json.loads(line) for line in (ROOT/'results/operator_decisions.jsonl').read_text().splitlines() if line]
stored={r['row'][0]:r['row'][1:] for r in decisions}
for row in local:assert stored[row['id']]==[row['action'],row['note'],row['hypothesis_id']]
json_save(ROOT/'results/audits/persistence.json',dict(status='passed',idempotent_counts=after,bundles=checks,decisions_verified=len(local),
    scope='Current bundle links, values, immutable file hashes, repeated import and saved automated operator decisions. Historical versions remain in the database.'))
print('Verified',len(checks),'bundles and',len(local),'operator decisions; repeated import changed no counts')

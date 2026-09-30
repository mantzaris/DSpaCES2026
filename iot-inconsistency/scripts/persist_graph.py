"""Restore the review graph from committed evidence bundles, without raw data."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.persistence import initialize,persist_bundle,transaction,statement,LABELS
from iot_repair.experiment import json_save
initialize();reports=[]
for path in sorted((ROOT/'results/graph').glob('*.json')):
    bundle=json.loads(path.read_text())
    if 'case' in bundle and 'hypotheses' in bundle:reports.append(persist_bundle(bundle))
counts=transaction([statement('MATCH (n) WHERE any(label IN labels(n) WHERE label IN $labels) RETURN labels(n)[0] AS entity, count(*) AS count',labels=LABELS)])
json_save(ROOT/'results/graph/persistence_audit.json',dict(exports=reports,counts=counts))
print('Persisted',len(reports),'saved evidence bundles')

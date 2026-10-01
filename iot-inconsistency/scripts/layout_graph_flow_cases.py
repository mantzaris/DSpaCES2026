"""Regenerate presentation coordinates without touching any scientific evidence."""
from pathlib import Path
import json
from export_graph_flow import layout,sha256,ROOT

directory=ROOT/'results/graph_flow_v1/graph'
manifest=json.loads((directory/'export_manifest.json').read_text())
for item in manifest:
    path=ROOT/item['path'];bundle=json.loads(path.read_text());context=list(bundle['hypothesis']['context_channels'])
    for edge in bundle.get('association_hypotheses',[]):context.extend([edge['source'],edge['target']])
    graph=dict(edges=bundle['associations']);names=[s['name'] for s in bundle['sensors']]
    bundle['view']=layout(graph,names,bundle['hypothesis']['target'],context)
    present={edge['id'] for edge in bundle['view']['edges']}
    positions={n['index']:n for n in bundle['view']['nodes']}
    for edge in graph['edges']:
        if edge['id'] in bundle.get('disputed_associations',[]) and edge['id'] not in present:
            a,b=positions[edge['source']],positions[edge['target']]
            bundle['view']['edges'].append(dict(edge,label_x=(a['x']+b['x'])/2,label_y=(a['y']+b['y'])/2-20))
    path.write_text(json.dumps(bundle,indent=2)+'\n');item['sha256']=sha256(path)
(directory/'export_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

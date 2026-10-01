"""Report fault-family and legacy-screen behavior without changing any detector."""
from pathlib import Path
import json
import sys

import numpy as np
from sklearn.metrics import average_precision_score
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.flow_data import sha256


def main():
    directory=ROOT/'results/graph_flow_v1';config=json.loads((directory/'protocol_lock.json').read_text())['configuration'];out={}
    for dataset in config['datasets']:
        path=directory/dataset/'test/manifest.json';cases=json.loads(path.read_text())['cases'];arrays=[]
        for case in cases:
            original=directory/dataset/'test'/(case['id']+'.npz')
            source=original if original.exists() else directory/'compact'/dataset/'test'/(case['id']+'.npz')
            arrays.append(dict(np.load(source,allow_pickle=False)))
        truth=np.stack([a['truth'] for a in arrays]);screen=np.stack([a['legacy_screen'] for a in arrays]);eligible=np.stack([a['eligible'] for a in arrays])
        scores={key[6:]:np.stack([a[key] for a in arrays]) for key in arrays[0] if key.startswith('score_')};strata={}
        for family in config['faults_development']+config['faults_heldout']:
            mask=np.array([c['track']=='clean' or c['fault']['family']==family for c in cases])
            strata[family]=dict(cases=int(mask.sum()),positive_candidates=int(truth[mask].sum()),
                ap={m:float(average_precision_score(truth[mask].ravel(),scores[m][mask].ravel())) for m in ('flow_ratio','flow_nll','pca','ppca','supervised')})
        out[dataset]=dict(test_manifest_sha256=sha256(path),candidates=int(truth.size),faults=int(truth.sum()),
            legacy_screened_candidates=int(screen.sum()),legacy_population_screen_fraction=float(screen.mean()),
            legacy_screen_fault_recall=float((screen&truth).sum()/truth.sum()),
            legacy_scorable_fault_recall=float(((scores['legacy_witness']>-1e11)&truth).sum()/truth.sum()),
            availability_fraction=float(eligible.mean()),fault_families=strata)
    (directory/'screening_and_fault_families.json').write_text(json.dumps(out,indent=2)+'\n')


if __name__=='__main__':main()

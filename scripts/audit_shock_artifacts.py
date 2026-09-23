"""Hash completed local artifacts and check seals without opening held-out values."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import yaml


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda:source.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    frozen=json.loads(Path('results/shock/frozen_manifest.json').read_text())
    prep=json.loads(Path('results/shock/preparation.json').read_text())
    assert digest('configs/regional_shock.json')==frozen['config_sha256']
    assert digest('results/shock/calibration.json')==frozen['calibration_sha256']
    assert digest('data/regional/refinement/model.npz')==frozen['model_sha256']
    for record in prep['backgrounds']:
        assert digest(record['path'])==record['sha256']
        with np.load(record['path']) as a:
            dates=a['timestamps']
            assert dates.min()>='2013-01-01' and dates.max()<'2013-04-01'
    assert not yaml.safe_load(Path('configs/main_study.yaml').read_text()).get('authorized',False)
    checks=pd.read_csv('results/shock/run/checks.csv.gz')
    assert checks.same_information_max_abs.max()<=1e-7
    cost=pd.read_csv('results/shock/run/costs.csv.gz')
    assert cost[cost.method.isin(['M1','M2','M3','M3_fixed'])].fine_attempts.max()<=209
    assert (cost[cost.method.isin(['M2','M3','M3_fixed'])].fine_attempts==209).all()
    roots=['data/regional/shock','results/shock','reports/figures/shock']
    files=[dict(path=str(p),bytes=p.stat().st_size,sha256=digest(p))
        for root in roots for p in sorted(Path(root).rglob('*')) if p.is_file() and p.name!='.ledger.lock']
    data_bytes=sum(p.stat().st_size for p in Path('data').rglob('*') if p.is_file())
    assert data_bytes<30_000_000_000
    report=dict(files=files,combined_local_data_bytes=data_bytes,
        new_ignored_background_bytes=sum(r['bytes'] for r in files if r['path'].startswith('data/')),
        durable_location='Existing local project disk; original raw archive and previous snapshots preserved',
        irreplaceable_completed_pod_only_artifacts=[],
        frozen_GPU_source_sha=frozen.get('source_sha',frozen.get('source_sha256',frozen.get('source_commit'))),
        original_main_authorized=False,london_holdout_opened=False,bdg2_outcomes_opened=False,
        copy_verification='Transport archive SHA-256 verified separately; source NPZ/model/config/calibration hashes verified here')
    Path('manifests/regional_shock_durable.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))


if __name__=='__main__':main()

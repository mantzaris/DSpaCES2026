"""Audit durable pilot artifacts and seals without opening sealed outcomes."""
import json
import hashlib
from pathlib import Path
import subprocess
import numpy as np
import pandas as pd


def immutable_digest(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    root = Path('data/regional/refinement')
    frozen = json.loads(Path('results/refinement/frozen_manifest.json').read_text())
    files = [dict(path=str(p), bytes=p.stat().st_size, sha256=immutable_digest(p))
             for p in sorted(root.rglob('*')) if p.is_file()]
    masks = []
    for oi in range(len(frozen['origins'])):
        with np.load(root/('origin_%03d' % oi)/'query_support.npz') as query:
            masks.append(query['mask'])
    masks = np.concatenate(masks)
    import yaml
    old = yaml.safe_load(Path('configs/main_study.yaml').read_text())
    if old.get('authorized', False):
        raise RuntimeError('Original main study unexpectedly enabled')
    checks = pd.read_csv('results/refinement/replay/checks.csv')
    legal = checks[checks.policy.isin(['fixed','random','uncertainty'])]
    columns = ['representation_error','cycle_error','factor_error','separator_mean_error',
               'separator_covariance_error','aggregation_mean_error']
    if legal[columns].max().max() > 1e-7:
        raise RuntimeError('Numerical consistency failure')
    footprint = sum(p.stat().st_size for p in Path('data').rglob('*') if p.is_file())
    if footprint > 30_000_000_000:
        raise RuntimeError('Combined data/cache cap exceeded')
    summary = dict(files=files, refinement_artifact_bytes=sum(p['bytes'] for p in files),
        combined_existing_data_bytes=footprint,
        unique_target_intervals=len(masks), unique_observed_household_targets=int(masks.sum()),
        households=masks.shape[1], complete_population_target_intervals=int(masks.all(1).sum()),
        observed_households_min=int(masks.sum(1).min()), observed_households_max=int(masks.sum(1).max()),
        training_model_sha256=immutable_digest(root/'model.npz'),
        london_sealed_directory_opened=False, bdg2_outcomes_opened=False,
        original_main_authorized=False,
        durable_location='local project ignored data/regional/refinement',
        irreplaceable_pod_only_artifacts=[],
        GPU_tested_source_sha='4f3d09e',
        current_git_sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    Path('manifests/regional_refinement_durable.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='files'}, indent=2))


if __name__ == '__main__':
    main()

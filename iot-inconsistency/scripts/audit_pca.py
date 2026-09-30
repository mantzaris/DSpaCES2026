"""Verify B1--B3 and portable PCA projection against every saved test residual."""
from pathlib import Path
import json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.baselines import PCADetector
from iot_repair.experiment import json_save
from iot_repair.artifacts import load_case_arrays
reports=[]
for name in json.loads((ROOT/'configs/study.json').read_text())['datasets']:
    directory=ROOT/'results/study'/name/'test';manifest=json.loads((directory/'case_manifest.json').read_text())['cases']
    values=np.stack([load_case_arrays(directory/(case['id']+'.npz'))['input'] for case in manifest]);saved=np.load(directory/'baselines_raw.npz')
    for key in saved.files:
        if not key.startswith('pca_'):continue
        lag=int(key.split('_')[1][3:]);model=PCADetector.load(ROOT/'results/models'/name/(key+'.npz'),lag)
        actual=model.score(values);expected=saved[key]
        np.testing.assert_allclose(actual,expected,atol=2e-6,rtol=2e-5,equal_nan=True)
        # Independent double-precision projection and coordinate attribution.
        vectors=model.vectors(values).astype('float64');observed=np.isfinite(vectors)
        fill=np.where(observed,vectors,model.fill);centered=fill-model.portable_mean
        projection=model.portable_components.astype('float64').T@model.portable_components.astype('float64')
        squared=(centered-centered@projection)**2;squared[~observed]=np.nan
        scores=np.nanmean(squared.reshape(len(values),values.shape[-1]-lag+1,values.shape[1],lag)[:,-8:,:,-1],axis=1)
        np.testing.assert_allclose(scores,expected,atol=2e-6,rtol=2e-5,equal_nan=True)
        reports.append(dict(dataset=name,method=key,windows=len(values),rank=model.rank,
            portable_max_absolute_error=float(np.nanmax(np.abs(actual-expected))),
            double_projection_max_absolute_error=float(np.nanmax(np.abs(scores-expected))),absolute_tolerance=2e-6,relative_tolerance=2e-5))
json_save(ROOT/'results/audits/pca_scores.json',dict(checks=reports,scope='Every primary test window, all saved PCA rank/lag settings. No fitting or test-based selection.'))
print('Audited',len(reports),'PCA rank/lag/configuration combinations')

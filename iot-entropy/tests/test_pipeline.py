from pathlib import Path
import json

import numpy as np
import torch

from iot_entropy.data import SensorData
from iot_entropy.features import Scan, score_features, summarize_reference
from iot_entropy.reference import issue_reference
from iot_entropy.synthetic import inject
from iot_entropy.psd_sensitivity import covariance_em


def fixture_data():
    rng=np.random.default_rng(9)
    return SensorData('fixture',rng.normal(size=(1200,12,1)).astype(np.float32),
        np.arange(1200,dtype=np.int64)*300*10**9,rng.uniform(size=(12,2)),
        np.ones((12,12),np.float32)-np.eye(12,dtype=np.float32),np.arange(12),
        np.zeros((12,1)),np.ones((12,1)),np.array([0,600,800,1000,1200]),
        np.array([[0,600,0],[600,800,1],[800,1000,2],[1000,1200,3]]),['x'],['unit'],300)


def test_boundaries_and_future_leakage():
    data=fixture_data()
    for split in range(4):
        indices=data.issuance_indices(split,48,120,168)
        assert np.all(indices-48>=data.bounds[split])
        assert np.all(indices+120<=data.bounds[split+1])
        np.testing.assert_array_equal(indices,data.issuance_indices(split,48,120,168))
    class Recorder:
        def sample(self,context,calendar,samples,steps,chunk):return context.clone()
    config={'context':48,'generated_samples':8,'sampling_steps':10,'sample_chunk':4}
    x=data.standardized.copy()
    first=issue_reference(Recorder(),data,x,700,80,config,'cpu','diffusion',None,17)
    x[700:]=99999
    second=issue_reference(Recorder(),data,x,700,80,config,'cpu','diffusion',None,17)
    torch.testing.assert_close(first,second)


def test_shared_reference_features_and_quality():
    torch.manual_seed(3)
    data=fixture_data()
    config={'shrinkage':.05,'group_sizes':[6,12],'windows':[24,48,96],'maximum_group_centers':4}
    scan=Scan(data.adjacency,data.coordinates,data.channels,config,'cpu')
    reference=scan.extract(torch.randn(8,120,12,1))
    observed=scan.extract(torch.randn(120,12,1))
    floor=torch.full_like(observed.values[0],.001)
    a,_=score_features(observed,reference,floor)
    b,_=score_features(observed,reference,floor,summarize_reference(reference,floor))
    for name in a:torch.testing.assert_close(a[name],b[name])
    assert len(a['entropy'])==len(scan.records)
    constants=scan.extract(torch.ones(120,12,1))
    scored,_=score_features(constants,reference,floor)
    assert torch.isnan(scored['entropy']).all()
    assert (scored['quality_hybrid']==1e6).all()


def test_matched_mean_covariance_fault():
    rng=np.random.default_rng(491)
    x=rng.normal(size=(192,6,1))
    x[:,1,0]=.8*x[:,0,0]+.6*x[:,1,0]
    modified=inject(x,list(range(6)),96,96,'matched_covariance',1.,12)
    a,b=x[96:,:,0],modified[96:,:,0]
    np.testing.assert_allclose(a.mean(0),b.mean(0),atol=1e-12)
    np.testing.assert_allclose(a.std(0),b.std(0),atol=1e-12)
    ra,rb=np.corrcoef(a.T),np.corrcoef(b.T)
    np.testing.assert_allclose(ra.sum(),rb.sum(),atol=1e-10)
    assert np.linalg.norm(ra-rb)>.1


def test_missing_covariance_em_psd():
    rng=np.random.default_rng(42)
    x=rng.normal(size=(96,6));x[rng.uniform(size=x.shape)<.15]=np.nan
    r=covariance_em(x)
    assert r is not None and np.linalg.eigvalsh(r).min()>0
    np.testing.assert_allclose(np.diag(r),1,atol=1e-12)

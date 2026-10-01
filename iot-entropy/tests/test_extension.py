import json
from pathlib import Path

import numpy as np
import torch

from iot_entropy.extension_scoring import extract, summaries, score, summarize_scores
from iot_entropy.features import Scan
from iot_entropy.extension import floor_from_development
from iot_entropy.extension_data import verify_target
from test_pipeline import fixture_data


def test_extension_endpoints_common_support_and_families():
    root=Path(__file__).resolve().parents[1]
    config=json.loads((root/'configs/full.json').read_text())
    config.update(json.loads((root/'configs/extension-v2.json').read_text()))
    config.update(maximum_group_centers=2,sample_delta=.3)
    data=fixture_data()
    scan=Scan(data.adjacency,data.coordinates,data.channels,config,'cpu')
    torch.manual_seed(751)
    samples=torch.randn(8,120,12,1)*.2
    observed=samples[:1].clone()
    # Current W=96 has 96 observations; its preceding endpoint has only 24.
    observed[:,:24]=float('nan')
    generated=extract(samples,scan,config); actual=extract(observed,scan,config)
    floors={'spatial':floor_from_development(generated['spatial'].values),
        'temporal':{w:floor_from_development(generated['temporal'][w]['u']) for w in config['windows']}}
    summary=summaries(generated,floors,config)
    scored=score(actual,generated,summary,scan,floors,config,.25)
    names,maxima,available,rank=summarize_scores(scored,scan,12,12)
    assert len(names)==25 and rank.shape==(25,3,12)
    from iot_entropy.localization import participation
    group_scores=scored['groups']['T'].numpy()
    old=participation(group_scores,scan.groups,12)
    valid=np.isfinite(group_scores)
    weights=scan._participation_weights
    denominator=valid@weights
    new=np.divide(np.where(valid,group_scores,0)@weights,denominator,
                  out=np.zeros(12),where=denominator>0)
    np.testing.assert_allclose(new,old,atol=1e-12)
    for a,b in [('S','ST'),('T','ST'),('B','BST')]:
        finite=torch.isfinite(scored['groups'][a])
        assert torch.all(scored['groups'][b][finite]>=scored['groups'][a][finite])
    for key in ['S','PE','SE','B','BST']:
        restricted=scored['groups']['common/'+key]
        assert torch.isnan(restricted[~scored['common']]).all()
    verify_target(data,700,48,80,1)
    try:
        verify_target(data,790,48,80,1)
        assert False,'cross-partition target accepted'
    except ValueError:
        pass


def test_constant_channels_keep_conventional_variance_but_abstain_entropy():
    from iot_entropy.temporal import window
    root=Path(__file__).resolve().parents[1]
    config=json.loads((root/'configs/extension-v2.json').read_text())
    out=window(torch.zeros(2,96),config)
    assert out['flat'].all()
    assert torch.isnan(out['values'][:,:2]).all()
    assert (out['values'][:,6]==0).all()

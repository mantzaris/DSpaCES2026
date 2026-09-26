import numpy as np
import pandas as pd
import pytest
from evidence_fusion.chronological_splits import pilot_roles, sealed_read, causal_target_mask
from evidence_fusion.provider_models import allocate_days
from evidence_fusion.record_identity import evidence_digest, record_id


def test_sealed_test_reader(tmp_path):
    path=tmp_path/'bad.csv'
    path.write_text('timestamp,b\n2017-01-01 00:00:00,123\n')
    with pytest.raises(ValueError):sealed_read(path)


def test_chronological_roles_and_dst():
    t=pd.date_range('2016-10-01',periods=744,freq='h')
    roles=pilot_roles(t)
    assert roles['covariance'].sum()==240 and roles['calibration'].sum()==240 and roles['score'].sum()==264
    assert np.all(sum(roles.values())==1)
    dst=pd.date_range('2016-03-13',periods=6,freq='h')
    mask=causal_target_mask(dst,'America/New_York')
    assert not mask[2] and not mask[3]


def test_overlap_fixed_counts_and_record_identity():
    days=pd.date_range('2016-01-01','2016-09-30',freq='D')
    for shared in (0,21,38):
        pools=allocate_days(days,shared)
        assert all(len(x)==42 for x in pools)
        assert len(set(pools[0])&set(pools[1]))==shared
        assert len(set().union(*map(set,pools)))==shared+4*(42-shared)
    identifier=record_id('building','2016-01-01T00:00:00',0)
    with pytest.raises(ValueError):evidence_digest([identifier,identifier])
    assert identifier!=record_id('building','2016-01-01T00:00:00',0,revision=1)


def test_later_outcomes_do_not_change_fitted_weights_or_calibration():
    from evidence_fusion.fusion_baselines import learned_covariance
    from evidence_fusion.calibration import fit_correction
    rng=np.random.default_rng(571)
    means=rng.normal(size=(90,4));outcomes=rng.normal(size=90)
    history=np.arange(90)<30;cal=(np.arange(90)>=30)&(np.arange(90)<60)
    first,info=learned_covariance(means,outcomes,history)
    changed=outcomes.copy();changed[~history]+=10000
    second,info2=learned_covariance(means,changed,history)
    assert info==info2
    np.testing.assert_array_equal(first['mean'],second['mean'])
    correction=fit_correction(first['mean'],first['variance'],outcomes,cal)
    changed=outcomes.copy();changed[60:]-=9999
    assert correction==fit_correction(first['mean'],first['variance'],changed,cal)

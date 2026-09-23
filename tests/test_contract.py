from dataclasses import replace, fields
import inspect
import numpy as np
import pytest
from evidence_fusion.message_contracts import Message, ActiveMessages
from evidence_fusion.provenance_sketches import Epoch
from evidence_fusion import conservative_fusion


def epoch(cap=10):
    return Epoch('test',5,512,cap,4,.01)


def message(provider='p0'):
    return Message('weighted-provenance/1',provider,'building','2016-10-22T01:00:00',
        '2016-10-22T02:00:00','kWh','2016-09-30T23:00:00','2016-10-22T00:59:00',
        '2016-10-22T01:00:00','calendar-v1',provider+'model',provider+'support',0,'',
        'noise-v1',3.,'test',5,512,12.,1.,0.,tuple([0.]*512)).signed()


def test_duplicate_reordering_and_revision_chain():
    m=message(); newer=replace(m,revision=1,supersedes=m.message_id,mean=13.).signed()
    other=message('p1')
    results=[]
    for stream in ([m,newer,other,m], [other,newer,m,newer], [newer,other,m]*10):
        state=ActiveMessages(epoch())
        for packet in stream: state.accept(packet)
        results.append([x.message_id for x in state.finalize()])
    assert results[0] == results[1] == results[2]


@pytest.mark.parametrize('changes', [{'unit':'MW'}, {'seed':6}, {'epoch':'different'},
    {'target_end':'2016-10-22T03:00:00'}, {'norm':-1}, {'cutoff':'2017-01-01T00:00:00'}])
def test_reject_invalid_contract(changes):
    with pytest.raises(ValueError): ActiveMessages(epoch()).accept(replace(message(),**changes).signed())


def test_conflicting_and_missing_revisions_rejected():
    state=ActiveMessages(epoch());m=message();state.accept(m)
    with pytest.raises(ValueError):state.accept(replace(m,mean=9).signed())
    state=ActiveMessages(epoch());state.accept(replace(m,revision=2,supersedes='unknown').signed())
    with pytest.raises(ValueError):state.finalize()


def test_exact_derived_duplicate_collapses():
    m=message();copy=replace(m,provider='other').signed()
    state=ActiveMessages(epoch());state.accept(m);state.accept(copy)
    assert len(state.finalize()) == 1


def test_epoch_exhaustion():
    ep=epoch(cap=1)
    ep.consume('q0',4);ep.consume('q0',4)
    with pytest.raises(ValueError):ep.consume('q1',4)
    with pytest.raises(ValueError):ep.consume('q0',5)


def test_binary_round_trip_and_tamper():
    m=message();assert Message.from_wire(m.to_wire())==m
    with pytest.raises(ValueError):Message.from_wire(m.to_wire()[:-8])
    with pytest.raises(ValueError):ActiveMessages(epoch()).accept(replace(m,mean=55))


def test_consumer_has_no_evaluator_imports_or_raw_fields():
    prohibited={'outcomes','observations','influences','raw_records','support','operator'}
    assert not prohibited.intersection({f.name for f in fields(Message)})
    assert not prohibited.intersection(inspect.signature(conservative_fusion.fuse_arrays).parameters)
    source=inspect.getsource(conservative_fusion)
    assert 'import pandas' not in source and 'data_access' not in source and 'influence_operators' not in source

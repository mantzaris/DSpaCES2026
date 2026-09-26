"""Richer public-calendar contract: lossless support transfer and exact recovery.

No training outcomes are exchanged. The consumer gets explicit support identities,
public feature recipe, retained columns, and each provider's plug-in noise scale.
"""
import json
import struct
import zlib
from dataclasses import dataclass
import numpy as np
import pandas as pd
from .provider_models import calendar_features, qr_operator
from .record_identity import support_encodings


def encode(models, building, universe_size):
    entries=[];payload=[]
    for model in models:
        candidates=support_encodings(model.support,universe_size)
        name=min(candidates,key=lambda key:(len(candidates[key]),key))
        body=candidates[name]
        entries.append(dict(encoding=name,bytes=len(body),sigma=model.sigma,active_columns=model.active_columns))
        payload.append(body)
    header=json.dumps(dict(protocol='exact-public-calendar/1',dataset='BDG2-v1.0',
        building=building,meter='electricity',unit='kWh',start='2016-01-01',
        hours=universe_size,record_revision=0,feature_recipe='calendar-19-v1',entries=entries),
        sort_keys=True,separators=(',',':')).encode()
    return struct.pack('<I',len(header))+header+b''.join(payload)


@dataclass
class RecoveredOperator:
    support: np.ndarray
    operator: np.ndarray


def decode(blob):
    size=struct.unpack('<I',blob[:4])[0]
    header=json.loads(blob[4:4+size]);offset=4+size
    if header['protocol']!='exact-public-calendar/1' or header['feature_recipe']!='calendar-19-v1':
        raise ValueError('Unsupported exact recipe')
    times=pd.date_range(header['start'],periods=header['hours'],freq='h')
    x,_=calendar_features(times);models=[]
    for entry in header['entries']:
        body=blob[offset:offset+entry['bytes']];offset+=entry['bytes']
        encoding=entry['encoding']
        if encoding.startswith('zlib_'):body=zlib.decompress(body);encoding=encoding[5:]
        if encoding=='bitmap':
            support=np.flatnonzero(np.unpackbits(np.frombuffer(body,dtype=np.uint8))[:header['hours']])
        elif encoding=='intervals':
            pairs=np.frombuffer(body,dtype='<u4').reshape(-1,2)
            support=np.concatenate([np.arange(int(a),int(a+b)) for a,b in pairs])
        elif encoding=='uint32':support=np.frombuffer(body,dtype='<u4').astype(int)
        else:raise ValueError('Unknown support encoding')
        active=entry['active_columns']
        op,_=qr_operator(x[support][:,active])
        full=np.zeros((x.shape[1],len(support)));full[active]=entry['sigma']*op
        models.append(RecoveredOperator(support,full))
    if offset!=len(blob):raise ValueError('Unexpected trailing payload')
    return models

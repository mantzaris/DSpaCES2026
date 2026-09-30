"""Isolated 10% training-window contamination, with the original normalizer fixed."""
from pathlib import Path
import hashlib,json,shutil,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.faults import inject_observation
from iot_repair.experiment import json_save
source=ROOT/'data/processed/synthetic_32_nonlinear';target=ROOT/'data/processed/synthetic_32_nonlinear_contaminated';target.mkdir(exist_ok=True)
for name in ['development.npz','calibration.npz','test.npz','metadata.json']:shutil.copyfile(source/name,target/name)
arrays=dict(np.load(source/'train.npz'));x=arrays['x'].copy();rng=np.random.default_rng(93401);chosen=rng.choice(len(x),int(np.ceil(.1*len(x))),replace=False);faults=[]
for index in chosen:
    x[index],truth,fault=inject_observation(x[index],93401+int(index),'offset',strength=4.,duration=16);faults.append(dict(training_index=int(index),**fault))
arrays['x']=x;np.savez_compressed(target/'train.npz',**arrays)
json_save(ROOT/'data/manifests/training_contamination.json',dict(dataset='synthetic_32_nonlinear_contaminated',parent='synthetic_32_nonlinear',fraction=len(chosen)/len(x),
    scope='post-normalization contamination isolates training and association discovery; original training normalizer held fixed',faults=faults,
    training_sha256=hashlib.sha256(x.tobytes()).hexdigest()))

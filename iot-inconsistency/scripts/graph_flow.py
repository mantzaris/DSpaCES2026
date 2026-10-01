"""Stage dispatcher for the finite graph-flow study. Final scoring needs a lock."""
from pathlib import Path
import argparse
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['prepare','develop_models','neural','baselines','sampling','freeze','calibration','calibrate','test','legacy_calibration','legacy_test','analyze','audit','smoke'])
    args=parser.parse_args()
    import torch
    torch.set_num_threads(4)
    import fcntl
    lock_path=ROOT/'results/graph_flow_v1'/('.'+args.stage+'.lock')
    lock_path.parent.mkdir(parents=True,exist_ok=True)
    lock=lock_path.open('w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if args.stage in ('sampling','audit'):
        from iot_repair.flow_audit import sampling_development,audit_production
        (sampling_development if args.stage=='sampling' else audit_production)(ROOT)
    elif args.stage=='freeze':
        from iot_repair.flow_execution import freeze
        freeze(ROOT)
    elif args.stage in ('calibration','test'):
        from iot_repair.flow_execution import run_split
        run_split(ROOT,args.stage)
    elif args.stage=='calibrate':
        from iot_repair.flow_confidence import calibrate
        calibrate(ROOT)
    elif args.stage.startswith('legacy_'):
        from iot_repair.flow_legacy import run_legacy
        run_legacy(ROOT,(args.stage[7:],))
    elif args.stage=='analyze':
        from iot_repair.flow_analysis import analyze
        analyze(ROOT)
    elif args.stage=='smoke':
        from iot_repair.flow_execution import development_selection,load_suite,score_case
        from iot_repair.flow_data import build_cases,configuration
        from iot_repair.experiment import json_save
        results={}
        for dataset in configuration(ROOT)['datasets']:
            suite=load_suite(ROOT,dataset,development_selection(ROOT,dataset))
            arrays,evidence,timing=score_case(suite,build_cases(ROOT,dataset,'development')[1],123,primary_samples=32,full_evidence=True)
            results[dataset]=dict(timing=timing,methods=[k for k in arrays if k.startswith('score_')])
            del suite
            torch.cuda.empty_cache()
        json_save(ROOT/'results/graph_flow_v1/smoke.json',results)
    elif args.stage=='prepare':
        from iot_repair.flow_data import prepare
        prepare(ROOT)
    elif args.stage=='develop_models':
        import torch
        torch.set_num_threads(4)
        from iot_repair.flow_training import develop_models
        develop_models(ROOT)
    elif args.stage=='baselines':
        from iot_repair.flow_baselines import develop_baselines
        develop_baselines(ROOT)
    elif args.stage=='neural':
        import torch
        torch.set_num_threads(4)
        from iot_repair.flow_development import finish_neural_development
        finish_neural_development(ROOT)


if __name__=='__main__':main()

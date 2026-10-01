"""Stage dispatcher for the finite graph-flow study. Final scoring needs a lock."""
from pathlib import Path
import argparse
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['prepare','develop_models'])
    args=parser.parse_args()
    if args.stage=='prepare':
        from iot_repair.flow_data import prepare
        prepare(ROOT)
    elif args.stage=='develop_models':
        import torch
        torch.set_num_threads(4)
        from iot_repair.flow_training import develop_models
        develop_models(ROOT)


if __name__=='__main__':main()

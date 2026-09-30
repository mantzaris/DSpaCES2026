from pathlib import Path
import argparse,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from iot_repair.data import prepare_dataset
p=argparse.ArgumentParser();p.add_argument('--datasets',nargs='+',default=['synthetic_32_linear','synthetic_32_nonlinear','synthetic_64_nonlinear','intel','skab'])
args=p.parse_args()
for name in args.datasets:
    path=prepare_dataset(ROOT,name,{'train':1000,'development':160,'calibration':192,'test':224})
    print(name,path,flush=True)

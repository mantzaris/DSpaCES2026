"""Two pilot figures generated only from saved measured results."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'pdf.fonttype':42,'ps.fonttype':42,
                     'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
out=Path('reports/figures');out.mkdir(parents=True,exist_ok=True)
data=Path('results/figure_data');data.mkdir(exist_ok=True)
m=pd.read_csv('results/pilot_metrics.csv')
methods={'naive_independence':('Naive independent','#999999'),
         'common_corrected':('Common-noise corrected','#E69F00'),
         'ci':('Scalar CI','#009E73'),
         'shrinkage':('Historical shrinkage','#CC79A7'),
         'exact_lineage':('Exact lineage','#0072B2'),
         'sketch_2048':('Sketch k=2048','#D55E00')}
agg=m[m.method.isin(methods)].groupby(['method','overlap','calibrated'])[['coverage90','normalized_is90']].mean().reset_index()
agg.to_csv(data/'pilot_quality.csv',index=False)
fig,axes=plt.subplots(2,2,figsize=(10,6),constrained_layout=True)
for col,calibrated in enumerate((False,True)):
    for method,(label,color) in methods.items():
        a=agg[(agg.method==method)&(agg.calibrated==calibrated)].sort_values('overlap')
        axes[0,col].plot(a.overlap,a.coverage90*100,'o-',color=color,label=label,markersize=4)
        axes[1,col].plot(a.overlap,a.normalized_is90,'o-',color=color,markersize=4)
    axes[0,col].axhline(90,color='black',linestyle=':',linewidth=1)
    axes[0,col].set_title('Empirically calibrated' if calibrated else 'Raw working-model intervals')
    axes[0,col].set_ylabel('90% interval coverage (%)');axes[0,col].set_ylim(45,100)
    axes[1,col].set_ylabel('Normalized 90% interval score')
    for ax in axes[:,col]:
        ax.set_xticks([0,.5,38/42]);ax.set_xticklabels(['0%','50%','90.5%']);ax.set_xlabel('Shared provider records')
        ax.grid(axis='y',alpha=.15)
axes[0,0].legend(fontsize=7,ncol=2,loc='lower left')
fig.suptitle('Validation-only pilot: 16 buildings / 16 sites, October 21–31, 2016\nOne allocation seed; descriptive averages, no test-year claim',fontsize=11)
for extension in ('pdf','svg','png'):fig.savefig(out/f'pilot_quality.{extension}',dpi=180)
plt.close(fig)

c=pd.read_csv('results/pilot_costs.csv');e=pd.read_json('results/exact_exchange.json')
quality=m[m.calibrated].groupby('method').normalized_is90.mean()
bench=json.loads(Path('results/benchmarks.json').read_text())
costrows=[]
header=float(c[c.k==2048].common_header_bytes_per_query.mean())
costrows.append(dict(method='Exact public-calendar support',contract='cached',bytes_per_query=header+e.once_bytes.mean()/256,
                     score=quality['exact_lineage']))
for k in (512,2048):
    chunk=c[c.k==k]
    for contract,field in [('per query','sketch_bytes_per_query'),('cached','sketch_amortized_bytes_per_query')]:
        costrows.append(dict(method=f'Sketch k={k}',contract=contract,bytes_per_query=chunk[field].mean(),score=quality[f'sketch_{k}']))
pd.DataFrame(costrows).to_csv(data/'pilot_bytes_quality.csv',index=False)
pd.DataFrame(bench['summary']).to_csv(data/'pilot_throughput.csv',index=False)
fig,axes=plt.subplots(1,2,figsize=(10,4.5),constrained_layout=True)
for row in costrows:
    color='#0072B2' if row['method'].startswith('Exact') else ('#D55E00' if '2048' in row['method'] else '#E69F00')
    axes[0].scatter(row['bytes_per_query'],row['score'],color=color,marker='s' if row['contract']=='cached' else '^',s=55,
        label=row['method']+' / '+row['contract'])
axes[0].set_xscale('log');axes[0].set_xlabel('Bytes / completed four-provider query')
axes[0].set_ylabel('Calibrated normalized interval score')
axes[0].set_title('Wire bytes and cache estimates; 256 targets');axes[0].legend(fontsize=7,loc='best')
labels=[];throughput=[];colors=[]
for backend in ('cpu','gpu'):
    for batch in (1,256):
        row=next(r for r in bench['summary'] if r['backend']==backend and r['batch']==batch)
        labels.append(f'{backend.upper()}\nbatch {batch}');throughput.append(row['queries_per_second'])
        colors.append('#0072B2' if backend=='cpu' else '#D55E00')
bars=axes[1].bar(labels,throughput,color=colors)
for bar,value in zip(bars,throughput):axes[1].text(bar.get_x()+bar.get_width()/2,value+1,f'{value:.1f}',ha='center',fontsize=8)
axes[1].set_ylabel('Completed queries / second');axes[1].set_title('Complete warm pipeline, FP64, 5 repeats')
axes[1].set_ylim(0,max(throughput)*1.25)
fig.suptitle('Pilot cost: exact supports use fewer bytes; serialization dominates runtime\nAMD EPYC 7443P, 4 threads; RTX PRO 4500 Blackwell',fontsize=10)
for extension in ('pdf','svg','png'):fig.savefig(out/f'pilot_cost.{extension}',dpi=180)
plt.close(fig)
print('Wrote two measured pilot figures as PDF, SVG and PNG')

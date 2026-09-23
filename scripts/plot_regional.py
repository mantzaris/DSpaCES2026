"""Four substantive figures from saved measurements; no generated data."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    out=Path('reports/figures/regional'); out.mkdir(parents=True,exist_ok=True)
    root=Path('results/regional/replay')
    forecast=pd.read_csv(root/'forecasts.csv'); numerical=pd.read_csv(root/'numerical.csv')
    costs=pd.read_csv(root/'costs.csv'); cert=pd.read_csv(root/'certificates.csv')
    ingest=json.loads(Path('results/regional/ingestion.json').read_text())
    summary=json.loads((root/'summary.json').read_text())
    plt.rcParams.update({'font.size':9,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
    colors=['#0072B2','#D55E00','#009E73','#CC79A7']
    def save(fig,name):
        fig.tight_layout(); fig.savefig(out/(name+'.pdf')); fig.savefig(out/(name+'.svg')); plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(9,6),sharex=True)
    for ax,horizon in zip(axes,[2,12]):
        panel=forecast[(forecast.profile==0)&(forecast.horizon==horizon)]
        real=panel[panel.method=='exact_twin']
        x=np.arange(len(real))
        ax.plot(x,real.observed_sum_kwh,'ko-',lw=1,ms=3,label='Observed target support')
        for color,method in zip(colors,['exact_twin','seasonal','no_new_observation']):
            sub=panel[panel.method==method]
            ax.plot(x,sub.prediction_observed_support_kwh,color=color,label=method.replace('_',' '))
        ax.set_ylabel('%d-hour horizon\nkWh / half hour'%(horizon//2)); ax.legend(ncol=2,fontsize=8)
        ax.set_title('All-provider profile; %d households, observed target support %d–%d'%(summary['households'],real.observed_households.min(),real.observed_households.max()))
    axes[-1].set_xlabel('Frozen origin index across four development weeks (gaps are not continuous time)')
    save(fig,'regional_predictions')
    fig,axes=plt.subplots(1,3,figsize=(12,3.8))
    methods=list(numerical.method.unique())
    axes[0].boxplot([np.maximum(numerical[numerical.method==m].relative_residual,1e-17) for m in methods],labels=methods)
    axes[0].set_yscale('log'); axes[0].axhline(1e-5,color='black',ls='--'); axes[0].set_ylabel('Relative residual'); axes[0].tick_params(axis='x',rotation=90,labelsize=7)
    for color,name in zip(colors,['identity','reference_eigen','rjd']):
        s=cert[cert.basis==name]
        axes[1].plot(np.sort(s.delta),label=name,color=color)
    axes[1].axhline(1,color='black',ls='--'); axes[1].set_yscale('log'); axes[1].set_ylabel('Best family bound delta'); axes[1].set_xlabel('Sorted queries'); axes[1].legend(fontsize=8)
    for color,name in zip(colors,['identity','reference_eigen','rjd']):
        s=cert[(cert.basis==name)&np.isfinite(cert.output_bound_kwh)]
        if len(s): axes[2].scatter(s.polynomial_output_error_kwh,s.output_bound_kwh,s=8,label=name,color=color)
    axes[2].axhline(summary['output_tolerance_kwh'],color='black',ls='--',label='Frozen output tolerance')
    if not np.isfinite(cert.output_bound_kwh).any():
        axes[2].text(.5,.5,'No finite family-certified\npolynomial output bound',ha='center',va='center',transform=axes[2].transAxes)
    else:
        axes[2].set_xscale('symlog',linthresh=1e-10); axes[2].set_yscale('log')
    axes[2].set_xlabel('Actual polynomial output error (kWh)'); axes[2].set_ylabel('Exact-arithmetic bound (kWh)'); axes[2].legend(fontsize=7)
    save(fig,'numerical_accuracy_bounds')
    selected=['cpu_banded','cpu_cholesky','gpu_cholesky','cpu_pcg','gpu_pcg','cpu_rjd_corrected','gpu_rjd_corrected']
    fig,axes=plt.subplots(1,2,figsize=(10,4.5))
    selected=[m for m in selected if m in set(costs.method)]
    med=[]; p05=[]; p95=[]
    for m in selected:
        x=costs[costs.method==m].complete_seconds/costs[costs.method==m].queries
        med.append(x.median()); p05.append(x.quantile(.05)); p95.append(x.quantile(.95))
    axes[0].bar(np.arange(len(selected)),np.asarray(med)*1000,color=colors[0])
    axes[0].errorbar(np.arange(len(selected)),np.asarray(med)*1000,yerr=[(np.array(med)-p05)*1000,(np.array(p95)-med)*1000],fmt='none',ecolor='black')
    axes[0].set_xticks(np.arange(len(selected))); axes[0].set_xticklabels(selected,rotation=60,ha='right',fontsize=8)
    axes[0].set_yscale('log'); axes[0].set_ylabel('Measured complete ms / query\nmedian and 5–95% across origins')
    repeats=np.array([1,2,4,8,16,32,64,128,256])
    for color,m in zip(colors,['cpu_banded','cpu_cholesky','gpu_cholesky','gpu_rjd_corrected']):
        if m not in selected: continue
        frame=costs[costs.method==m]; each=float((frame.complete_seconds/frame.queries).median())
        setup=summary['parsing_seconds']+(summary['basis_setup_seconds']['rjd'] if 'rjd' in m else 0)+(summary['cuda_initialization_seconds'] if m.startswith('gpu') else 0)
        axes[1].plot(repeats,each+setup/(repeats*summary['queries']),label=m,color=color)
    axes[1].set_xscale('log',base=2); axes[1].set_yscale('log'); axes[1].set_xlabel('Hypothetical reuse of measured query package'); axes[1].set_ylabel('Projected amortized seconds / query'); axes[1].legend(fontsize=7)
    axes[1].set_title('Projection from measured setup and replay; not new runs')
    save(fig,'speed_amortization')
    stages=pd.DataFrame(ingest['stages']); parse=stages[stages.stage=='stream_parse']
    fig,axes=plt.subplots(1,2,figsize=(9,3.7))
    axes[0].plot(parse.elapsed_seconds,parse.cumulative_rows/1e6,color=colors[0]); axes[0].set_xlabel('Successful ingestion elapsed seconds'); axes[0].set_ylabel('Parsed source rows (million)')
    axes[1].plot(np.arange(len(stages)),stages.peak_rss_bytes/1e9,color=colors[2]); axes[1].axhline(8,color='black',ls='--',label='Host working target'); axes[1].set_xlabel('Parse/deduplication stage index'); axes[1].set_ylabel('Peak process resident memory (GB)'); axes[1].legend()
    fig.suptitle('%s source rows; %.2f GB ZIP → %.2f GB Parquet'%(format(ingest['source_rows'],','),ingest['archive_bytes']/1e9,ingest['parquet_bytes']/1e9))
    save(fig,'pipeline_scale')


if __name__=='__main__': main()

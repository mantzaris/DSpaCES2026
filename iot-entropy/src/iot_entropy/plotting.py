"""Publication figures and tables regenerated from immutable saved measurements."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch,FancyBboxPatch
import numpy as np
import pandas as pd

from .data import load_data
from .utils import write_json

COLORS={'synthetic':'#326b99','intel':'#92539d','pems':'#c76527',
        'diffusion':'#7057a0','bootstrap':'#247e87'}
NAMES={'synthetic':'Synthetic (64/128/256)','intel':'Intel Lab','pems':'PEMS-BAY'}


def style() -> None:
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':9,
                         'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,
                         'legend.fontsize':7,'pdf.fonttype':42,'ps.fonttype':42,
                         'axes.spines.top':False,'axes.spines.right':False,
                         'savefig.dpi':220,'lines.linewidth':1.3})


def save(fig,root: Path,name: str) -> None:
    directory=root/'manuscript/figures';directory.mkdir(parents=True,exist_ok=True)
    for extension in ['pdf','svg','png']:
        fig.savefig(directory/f'{name}.{extension}',bbox_inches='tight',pad_inches=.035)
    plt.close(fig)


def architecture(root: Path) -> None:
    fig,ax=plt.subplots(figsize=(7.15,1.9));ax.set_xlim(0,13);ax.set_ylim(0,3.2);ax.axis('off')
    def box(x,y,w,h,text,gpu=False):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.05,rounding_size=.07',
                                  linewidth=.8,edgecolor='#52718a',facecolor='#e5edf8' if gpu else '#f6f7f7'))
        ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=7.2)
    def arrow(a,b):ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=9,color='#476278',linewidth=.9))
    box(.05,1.95,2.15,.85,'History + masks\nGraph + calendar')
    box(2.7,1.95,2.3,.85,'Joint diffusion\n64 future blocks',True)
    box(5.55,1.95,2.4,.85,'Reference statistics\nSame measurement rule',True)
    box(.05,.3,2.15,.85,'Observed target\nAvailable at t')
    box(2.7,.3,2.3,.85,'Common-row PSD\nH, ΔH; C, D, P; R',True)
    box(5.55,.3,2.4,.85,'Quality / eligibility\nRobust discrepancy',True)
    box(8.45,1.1,1.8,1.1,'Scan maxima\nHeld-out ranks\nParticipation')
    box(10.8,1.1,2.1,1.1,'Evidence replay\nLinked traces\nCause kept distinct')
    for a,b in [((2.2,2.37),(2.7,2.37)),((5,2.37),(5.55,2.37)),((2.2,.72),(2.7,.72)),
                ((5,.72),(5.55,.72)),((6.75,1.95),(6.75,1.2)),((7.95,.72),(8.45,1.3)),
                ((10.25,1.65),(10.8,1.65))]:arrow(a,b)
    ax.text(0,3.02,'Historically issued forecast: context ends before the entire observed target',fontsize=8.5,weight='bold')
    ax.text(8.5,.3,'Blue fill: GPU tensors\nGray fill: CPU / storage',fontsize=7,color='#425c71')
    save(fig,root,'architecture')


def theory(root: Path) -> None:
    fig=plt.figure(figsize=(3.48,3.05));grid=fig.add_gridspec(2,3,height_ratios=[1.3,1],hspace=.72,wspace=.38)
    ax=fig.add_subplot(grid[0,:]);rho=np.linspace(0,.9999,350)
    for m,color in [(4,'#326b99'),(12,'#92539d'),(24,'#c76527')]:
        for shrinkage,ls in [(0,'-'),(.05,'--')]:
            r=rho*(1-shrinkage);p=(1+(m-1)*r)/m;q=(1-r)/m
            h=-(p*np.log(p)+(m-1)*q*np.log(q))/np.log(m)
            ax.plot(rho,h,ls,color=color,label=f'm={m}' if shrinkage==0 else None)
    ax.set(xlabel='Equicorrelation ρ',ylabel='Normalized H',ylim=(0,1.04));ax.legend(ncol=3,loc='lower left',frameon=False)
    ax.set_title('Solid λ=0; dashed λ=.05',fontsize=8)
    first=np.full((4,4),.2);np.fill_diagonal(first,1)
    second=np.eye(4);second[0,1]=second[1,0]=second[2,3]=second[3,2]=.6
    for i,(matrix,title) in enumerate([(first,'A: equicorrelated'),(second,'B: two pairs')]):
        ax=fig.add_subplot(grid[1,i]);ax.imshow(matrix,vmin=0,vmax=1,cmap='Blues')
        ax.set_xticks([]);ax.set_yticks([]);ax.set_title(title,fontsize=7)
        p=np.linalg.eigvalsh(matrix)/4;h=-(p*np.log(p)).sum()/np.log(4)
        ax.set_xlabel(f'H={h:.3f}',fontsize=7)
    ax=fig.add_subplot(grid[1,2]);x=np.arange(4)
    ax.bar(x-.16,np.linalg.eigvalsh(first)[::-1],.31,color='#326b99',label='A')
    ax.bar(x+.16,np.linalg.eigvalsh(second)[::-1],.31,color='#c76527',label='B')
    ax.set_xticks(x);ax.set_xticklabels(['1','2','3','4']);ax.set_xlabel('Eigenvalue index',fontsize=7)
    ax.set_title('Same C=.2, P=.4',fontsize=7);ax.legend(frameon=False,fontsize=6)
    save(fig,root,'theory')


def replay(root: Path,event_index: int) -> tuple[dict,list[dict],list[dict]]:
    directory=root/'experiments/full/score-synthetic64-physical-17'
    frames=[json.loads(p.read_text()) for p in sorted((directory/'replay').glob(f'{event_index}-*.json'),key=lambda p:int(p.stem.split('-')[1]))]
    groups=json.loads((directory/'groups.json').read_text())
    return json.loads((directory/'events.json').read_text())[event_index],frames,groups


def choose_case_group(event: dict,frames: list[dict],groups: list[dict],sign: int) -> int:
    overlap=np.array([len(set(g['nodes'])&set(event['nodes']))/len(set(g['nodes'])|set(event['nodes'])) for g in groups])
    during=[f for f in frames if event['onset']<=f['end']<event['onset']+event['duration']]
    change=np.array([[np.nan if row[1] is None else row[1] for row in f['observed']] for f in during])
    score=np.nanmean(change,axis=0)*sign
    score[(overlap<.25)|~np.isfinite(score)]=-np.inf
    return int(np.argmax(score))


def cases(root: Path) -> list[dict]:
    fig,axes=plt.subplots(5,2,figsize=(7.15,5.2),sharex='col',gridspec_kw={'hspace':.16,'wspace':.28})
    records=[];data=load_data(root,'synthetic64')
    directory=root/'experiments/full/score-synthetic64-physical-17'
    cal=np.load(directory/'calibration.npz');column=cal['methods'].tolist().index('diffusion/entropy')
    maxima=cal['maxima'][:,column];critical=np.sort(maxima)[len(maxima)-int(np.floor(.1*(len(maxima)+1)))]
    for col,(index,sign,title) in enumerate([(0,-1,'Copy injection: measured decrease'),(18,1,'Independent noise: measured increase')]):
        event,frames,groups=replay(root,index);group=choose_case_group(event,frames,groups,sign);g=groups[group]
        time=np.array([f['end'] for f in frames]);relative=time-event['onset'];channel=g['channel']
        # Reconstruct the observed suffix from overlapping saved raw frames.
        raw={}
        for frame in frames:
            for t,row in zip(range(frame['end']-119,frame['end']+1),frame['raw']):raw[t]=row
        raw_times=np.array(sorted(raw));values=np.array([raw[t] for t in raw_times],dtype=float)
        for node in g['nodes'][:4]:
            axes[0,col].plot(raw_times-event['onset'],values[:,node,channel],alpha=.7,lw=.7)
        axes[0,col].set_title(title,fontsize=8.5);axes[0,col].set_ylabel('Raw (scaled)')
        for row,feature,label in [(1,0,'H'),(2,1,'ΔH'),(3,2,'Signed C')]:
            observed=np.array([f['observed'][group][feature] for f in frames],dtype=float)
            center=np.array([f['reference_center'][group][feature] for f in frames],dtype=float)
            low=np.array([f['reference_low'][group][feature] for f in frames],dtype=float)
            high=np.array([f['reference_high'][group][feature] for f in frames],dtype=float)
            ax=axes[row,col];ax.fill_between(relative,low,high,color='#b5cbdc',alpha=.55)
            ax.plot(relative,center,'--',color='#6e8ba1',lw=.8)
            color='#66509d' if sign<0 else '#c76527'
            if feature==0:
                # Show the actually measured lagged level as well as issuance
                # levels; lag W/4 need not equal the 12-row alert stride.
                past=observed-np.array([f['observed'][group][1] for f in frames],dtype=float)
                points=sorted(zip(np.r_[relative,relative-g['lag']],np.r_[observed,past]))
                ax.plot([p[0] for p in points],[p[1] for p in points],color=color,lw=1)
                ax.scatter(relative-g['lag'],past,s=9,facecolor='white',edgecolor=color,linewidth=.7)
                ax.scatter(relative,observed,s=11,color=color)
            else:ax.plot(relative,observed,'o-',markersize=2.5,color=color)
            ax.set_ylabel(label)
        ax=axes[4,col];scores=np.array([f['scores']['diffusion/entropy'][group] for f in frames],dtype=float)
        ax.plot(relative,scores,'o-',markersize=2.5,color='#283f57');ax.axhline(critical,ls='--',color='#788594',lw=.9)
        ax.set_ylabel('Group Aᴴ');ax.set_xlabel('Samples relative to true onset')
        for ax in axes[:,col]:
            ax.axvline(0,color='#b34e32',lw=.8);ax.axvspan(0,event['duration']-1,color='#b34e32',alpha=.08)
            ax.set_xlim(-25,120);ax.grid(axis='y',alpha=.14)
        during=[f for f in frames if event['onset']<=f['end']<event['onset']+event['duration']]
        records.append({'event':event['id'],'group':group,'window':g['window'],'size':g['size'],
                        'actual_mean_delta_h_during_event':float(np.mean([f['observed'][group][1] for f in during])),
                        'selection':'Fixed saved copy/noise cases; choose largest signed mean change among groups with truth IoU >= .25, for illustration only'})
    save(fig,root,'cases');write_json(root/'results/case-selection.json',records)
    return records


def spatial(root: Path,cases: list[dict]) -> None:
    fig=plt.figure(figsize=(7.15,2.6));grid=fig.add_gridspec(1,3,width_ratios=[1,1,1.5],wspace=.32)
    data=load_data(root,'synthetic64');xy=data.coordinates
    for col,(index,selected) in enumerate(zip([0,18],cases)):
        event,frames,groups=replay(root,index);group=selected['group'];frame=min(frames,key=lambda f:abs(f['end']-203));g=groups[group]
        ax=fig.add_subplot(grid[0,col]);edges=np.argwhere(np.triu(data.adjacency>0,1))
        for a,b in edges:ax.plot(xy[[a,b],0],xy[[a,b],1],color='#d4dce3',lw=.5,zorder=0)
        ax.scatter(*xy.T,s=8,color='#aebdcc');nodes=g['nodes'];ax.scatter(xy[nodes,0],xy[nodes,1],s=27,
                     color='#66509d' if col==0 else '#c76527',marker='v' if col==0 else '^',label='Selected group')
        truth=event['nodes'];ax.scatter(xy[truth,0],xy[truth,1],s=54,facecolor='none',edgecolor='#182d42',lw=.8,label='Injected nodes')
        ax.set(xlim=(-.05,1.05),ylim=(-.05,1.05),aspect='equal');ax.set_xticks([]);ax.set_yticks([])
        ax.set_title(f"{event['kind']}: g{group}, W={g['window']}",fontsize=8)
        if col==0:ax.legend(loc='upper center',bbox_to_anchor=(.5,-.02),fontsize=6,frameon=False)
    event,frames,groups=replay(root,18);group=cases[1]['group']
    selected=sorted(range(len(groups)),key=lambda i:len(set(groups[i]['nodes'])&set(event['nodes'])),reverse=True)[:15]
    matrix=np.array([[np.nan if f['observed'][g][0] is None or f['reference_center'][g][0] is None else f['observed'][g][0]-f['reference_center'][g][0] for f in frames] for g in selected])
    ax=fig.add_subplot(grid[0,2]);limit=max(.05,np.nanmax(np.abs(matrix)))
    im=ax.imshow(matrix,aspect='auto',cmap='PuOr_r',vmin=-limit,vmax=limit,interpolation='none')
    ax.set_yticks(range(0,15,3));ax.set_yticklabels([f'g{selected[i]}' for i in range(0,15,3)])
    ticks=np.arange(0,len(frames),3);ax.set_xticks(ticks);ax.set_xticklabels([frames[i]['end']-192 for i in ticks])
    ax.set_xlabel('Samples relative to onset');ax.set_title('Noise case: signed H residual',fontsize=8)
    fig.colorbar(im,ax=ax,fraction=.045,pad=.035).set_label('H − expected H',fontsize=7)
    save(fig,root,'spatial')


def performance(root: Path) -> None:
    summaries=json.loads((root/'results/summary.json').read_text());paired=json.loads((root/'results/paired_comparisons.json').read_text())
    frame=pd.read_csv(root/'results/event_metrics.csv.gz');frame=frame[(frame.alpha==.1)&(frame.graph=='physical')&frame.is_fault]
    fig,axes=plt.subplots(2,3,figsize=(7.15,3.6),gridspec_kw={'hspace':.8,'wspace':.38})
    methods=[f'{reference}/{feature}' for reference in ['bootstrap','diffusion'] for feature in ['entropy','synchronization','combined']]
    for col,dataset in enumerate(['synthetic','intel','pems']):
        ax=axes[0,col]
        for i,method in enumerate(methods):
            entry=next(s for s in summaries if s['dataset']==dataset and s['method']==method)
            result=entry['event_recall'];mean=result['mean'];low=result['low'];high=result['high']
            color=COLORS[method.split('/')[0]]
            ax.errorbar(i,mean,yerr=[[mean-low],[high-mean]],color=color,fmt='o',capsize=2,ms=4)
            for direction,marker,offset in [('increase','^',-.15),('decrease','v',.15)]:
                subset=frame[(frame.primary_dataset==dataset)&(frame.method==method)&(frame.actual_entropy_direction==direction)]
                ax.scatter(i+offset,subset.tp.mean(),marker=marker,s=13,facecolor='none',edgecolor=color)
        ax.set_title(NAMES[dataset],fontsize=8);ax.set_xticks(range(6));ax.set_xticklabels(['B:H','B:S','B:H+S','D:H','D:S','D:H+S'],rotation=45,ha='right')
        ax.set_ylim(-.03,1.03);ax.grid(axis='y',alpha=.15)
        if col==0:ax.set_ylabel('Event recall (95% CI)')
        ax=axes[1,col]
        contrasts=[('diffusion/entropy','diffusion/synchronization','H − S'),
                   ('diffusion/combined','diffusion/synchronization','H+S − S'),
                   ('diffusion/entropy','diffusion/matrix','H − full R')]
        for i,(left,right,label) in enumerate(contrasts):
            result=next(p for p in paired if p['dataset']==dataset and p['left']==left and p['right']==right and p['metric']=='localization_iou')
            mean=result['mean'];ax.errorbar(mean,i,xerr=[[mean-result['low']],[result['high']-mean]],color='#4a6280',fmt='s',capsize=2,ms=3)
        ax.axvline(0,color='#8795a3',ls='--',lw=.7);ax.set_yticks(range(3));ax.set_yticklabels([x[2] for x in contrasts],fontsize=7)
        ax.set_xlabel('Paired difference in IoU');ax.invert_yaxis();ax.grid(axis='x',alpha=.15)
    save(fig,root,'performance')


def calibration_cost(root: Path) -> None:
    frame=pd.read_csv(root/'results/event_metrics.csv.gz')
    benchmarks=json.loads((root/'experiments/benchmark.json').read_text())
    fig,axes=plt.subplots(2,2,figsize=(7.15,3.65),gridspec_kw={'wspace':.35,'hspace':.52})
    ax=axes[0,0]
    subset=frame[(frame.graph=='physical')&(frame.kind=='untouched')&(frame.method=='diffusion/entropy')]
    for dataset,group in subset.groupby('primary_dataset'):
        rates=group.groupby('alpha')[['flagged_issuances','issuances']].sum();rate=rates.flagged_issuances/rates.issuances
        ax.plot(rate.index,rate.values,'o-',color=COLORS[dataset],label=NAMES[dataset],ms=3)
    ax.plot([0,.22],[0,.22],'--',color='#8c9aa5',lw=.8);ax.set(xlabel='Nominal per-issuance α',ylabel='Untouched exceedance',xlim=(0,.22));ax.legend(frameon=False,fontsize=6)
    ax=axes[0,1];records=benchmarks['detector'];x=np.arange(len(records));labels=['64','128','256','Intel','PEMS']
    model=np.array([r['model_only']['p50_seconds'] for r in records]);pipeline=np.array([r['complete_detector']['p50_seconds'] for r in records])
    ax.bar(x-.17,model,.32,color='#849bb0',label='Generation only');ax.bar(x+.17,pipeline,.32,color='#66509d',label='Complete H detector')
    ax.set_xticks(x);ax.set_xticklabels(labels);ax.set_ylabel('p50 seconds / issuance');ax.legend(frameon=False,fontsize=6)
    ax=axes[1,0]
    subset=frame[(frame.alpha==.1)&(frame.graph=='physical')&frame.is_fault&(frame.method=='diffusion/entropy')]
    vals=[subset[subset.primary_dataset==d].delay_seconds.dropna().values/60 for d in ['synthetic','intel','pems']]
    ax.boxplot(vals,labels=['Synthetic','Intel','PEMS'],showfliers=False,widths=.45)
    ax.set_ylabel('Detected-event delay (min)');ax.text(.03,.96,'Missed events excluded; counts in table',transform=ax.transAxes,va='top',fontsize=6)
    ax=axes[1,1]
    for name in ['synthetic64','pems']:
        values=[]
        for b in [32,64,128]:
            path=root/f'experiments/sensitivity/B{b}/score-{name}-physical-17/runtime.json'
            runtime=json.loads(path.read_text())
            values.append(np.median([t['seconds'] for t in runtime['timings'] if t['stage']=='calibration']))
        ax.plot([32,64,128],values,'o-',ms=3,color=COLORS['synthetic' if name.startswith('synthetic') else 'pems'],label='64 nodes' if name.startswith('synthetic') else 'PEMS')
    ax.set(xlabel='Joint generated samples B',ylabel='Full comparison pipeline (s)',xticks=[32,64,128]);ax.legend(frameon=False,fontsize=6)
    save(fig,root,'calibration-cost')


def latex_escape(value: str) -> str:
    return value.replace('_',r'\_').replace('%',r'\%').replace('&',r'\&')


def tables(root: Path) -> None:
    directory=root/'manuscript/generated';directory.mkdir(exist_ok=True)
    config=json.loads((root/'configs/full.json').read_text());summary=json.loads((root/'results/summary.json').read_text())
    lines=[r'\begin{table*}[t]',r'\centering\caption{Primary datasets and frozen splits. Counts are time rows; independent synthetic episodes define the partitions. Intel and PEMS faults are controlled injections, not confirmed field failures.}',
           r'\label{tab:data}\small',r'\begin{tabular}{lrrrrll}',r'\toprule Dataset & Nodes & Train & Dev. & Cal. / test & Interval; primary channels & Source span used\\\midrule']
    dataset_rows=[]
    for name in config['datasets']:
        data=load_data(root,name);manifest=json.loads((root/'data/manifests'/f'{name}.json').read_text())
        counts=[int(sum(stop-start for start,stop,split in data.episode_bounds if split==i)) for i in range(4)]
        label='Synthetic '+name.replace('synthetic','') if name.startswith('synthetic') else NAMES[name]
        channels='signal' if name.startswith('synthetic') else 'temp., humidity' if name=='intel' else 'speed (mph)'
        span='independent simulations' if name.startswith('synthetic') else '28 Feb.--23 Mar. 2004' if name=='intel' else '1 Jan.--30 June 2017'
        lines.append(f"{label} & {len(data.node_ids)} & {counts[0]:,} & {counts[1]:,} & {counts[2]:,} / {counts[3]:,} & {manifest['interval_seconds']//60} min; {channels} & {span}" + r" \\")
        dataset_rows.append({'dataset':name,'counts':counts,'nodes':len(data.node_ids),'interval_seconds':manifest['interval_seconds']})
    lines += [r'\bottomrule\end{tabular}',r'\end{table*}']
    (directory/'datasets.tex').write_text('\n'.join(lines)+'\n')
    write_json(root/'results/dataset-table.json',dataset_rows)
    methods=[('bootstrap/entropy','Bootstrap H'),('bootstrap/synchronization','Bootstrap S'),('bootstrap/combined','Bootstrap H+S'),
             ('diffusion/entropy','Diffusion H'),('diffusion/synchronization','Diffusion S'),('diffusion/combined','Diffusion H+S'),
             ('diffusion/matrix','Diffusion full R'),('diffusion/raw','Diffusion raw'),('diffusion/entropy_raw','Diffusion H+raw'),
             ('diffusion/quality_hybrid','Diffusion quality hybrid'),('cusum','CUSUM'),('gdn','GDN adaptation')]
    lines=[r'\begin{table*}[t]',r'\centering\caption{Main results at nominal $\alpha=.10$. Each cell is event recall / localization IoU / event-PR area. Localization counts missed events as zero. Values are averages over three training seeds; synthetic configurations form one dataset. Equal nominal calibration budgets do not imply equal realized background rates.}',
           r'\label{tab:main}\small',r'\begin{tabular}{lccc}',r'\toprule Method & Synthetic & Intel Lab & PEMS-BAY\\\midrule']
    for method,label in methods:
        entries=[]
        for dataset in ['synthetic','intel','pems']:
            s=next(s for s in summary if s['dataset']==dataset and s['method']==method)
            entries.append(f"{s['event_recall']['mean']:.3f} / {s['localization_iou']['mean']:.3f} / {s['mean_event_auprc_envelope']:.3f}")
        lines.append(label+' & '+' & '.join(entries)+r' \\')
    lines.extend([r'\bottomrule\end{tabular}',r'\end{table*}'])
    (directory/'main-table.tex').write_text('\n'.join(lines)+'\n')


def build(root: Path) -> None:
    style();architecture(root);theory(root)
    records=cases(root);spatial(root,records)
    performance(root);calibration_cost(root);tables(root)

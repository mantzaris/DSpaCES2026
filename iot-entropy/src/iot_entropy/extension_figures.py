"""Publication figures and numeric TeX generated exclusively from saved outputs."""
from __future__ import annotations

import json
import subprocess
import shutil
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd

from .extension_reporting import read_json
from .utils import write_json

COLORS={'bootstrap':'#197ba7','diffusion':'#cc6138'}
LABELS={'synthetic':'Synthetic','intel':'Intel Lab','pems':'PEMS-BAY'}


def save(fig, destination: Path, name: str):
    path=destination/(name+'.pdf')
    fig.savefig(path,bbox_inches='tight',pad_inches=.03)
    fig.savefig(destination/(name+'.png'),dpi=160,bbox_inches='tight',pad_inches=.03)
    plt.close(fig)
    # Older Matplotlib embeds whole fonts. Subset them without rasterizing
    # plots or changing numeric data; retain the original local PDF.
    backup=destination.parents[1]/'.local/figure-font-originals';backup.mkdir(parents=True,exist_ok=True)
    original=backup/path.name;shutil.copy2(path,original)
    subprocess.run(['gs','-q','-dBATCH','-dNOPAUSE','-sDEVICE=pdfwrite',
        '-dCompatibilityLevel=1.5','-dEmbedAllFonts=true','-dSubsetFonts=true',
        '-dCompressFonts=true','-sOutputFile='+str(path),str(original)],check=True)


def build_figures(root: Path):
    out=root/'results/extension-v2';dest=root/'manuscript/figures-v2';dest.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':9,
        'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,
        'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(3.4,2.65));ax.set_position([.01,.05,.98,.94]);ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    def box(x,y,w,h,label,color='#e9f3f8'):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.012',facecolor=color,edgecolor='#6b8798',linewidth=.7))
        ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=7.2)
    def arrow(x1,y1,x2,y2):ax.annotate('',(x2,y2),(x1,y1),arrowprops={'arrowstyle':'->','lw':.8,'color':'#405d70'})
    box(.02,.84,.96,.14,'Historical context + masks\nFixed graph + known calendar')
    box(.02,.62,.46,.15,'Joint block bootstrap\nIntact training blocks')
    box(.52,.62,.46,.15,'Graph-conditioned diffusion\n64 joint forecast draws')
    arrow(.25,.83,.25,.78);arrow(.75,.83,.75,.78)
    box(.02,.43,.96,.13,'Saved forecasts + observed target\nTarget arrives only at decision','#f5f3ea')
    arrow(.25,.61,.25,.57);arrow(.75,.61,.75,.57)
    box(.02,.21,.46,.15,'Spatial spectrum entropy\nCorrelation / matrix statistics')
    box(.52,.21,.46,.15,'Per-sensor PE / sample entropy\nACF, variance, trend, CUSUM')
    arrow(.25,.42,.25,.37);arrow(.75,.42,.75,.37)
    box(.02,.04,.96,.10,'Group scores → calibrated S / T / ST / B / BST','#eaf1eb')
    arrow(.25,.20,.25,.15);arrow(.75,.20,.75,.15)
    ax.text(.5,-.025,'CUDA: references / measures / scores · CPU: reports / replay',ha='center',fontsize=6.8)
    save(fig,dest,'architecture')
    theory=read_json(out/'theory-checks.json');diag=pd.read_csv(out/'diagnostics.csv.gz')
    fig,axes=plt.subplots(2,1,figsize=(3.4,2.9),gridspec_kw={'height_ratios':[1,1.15]})
    positions=np.arange(4)
    for i,(matrix,h) in enumerate(zip(theory['matched_summary_matrices'],theory['matched_H_unshrunk'])):
        spectrum=np.linalg.eigvalsh(matrix)[::-1]/4
        axes[0].bar(positions+(i-.5)*.28,spectrum,width=.27,color=list(COLORS.values())[i],label=f'$H_S$={h:.3f}')
    axes[0].set(xticks=positions,xticklabels=['1','2','3','4'],ylabel='Spectral mass',title='(a) Matched C = 0.2 and leading mass = 0.4')
    axes[0].legend(ncol=2,frameon=False,loc='upper right',fontsize=6.8)
    axes[0].set_ylim(0,.55)
    for i,case in enumerate(['normal','joint_time_shuffle']):
        v=diag[(diag.scale==1)&(diag.scenario==case)][['spatial_H','permutation','sample','acf1']].mean()
        axes[1].bar(positions+(i-.5)*.28,v,width=.27,color=list(COLORS.values())[i],label=['Original','Joint row shuffle'][i])
    axes[1].set(xticks=positions,xticklabels=['$H_S$','PE','SE','ACF1'],ylabel='Measurement',title='(b) Aligned 96-row diagnostics (64 simulations)')
    axes[1].legend(ncol=2,frameon=False,fontsize=6.8)
    axes[1].set_ylim(-.08,1.45)
    fig.tight_layout(pad=.35,h_pad=.65);save(fig,dest,'theory')
    replay_path=out/'replays/synthetic64.json'
    if replay_path.exists() or Path(str(replay_path)+'.gz').exists():
        replay=read_json(replay_path);frames=replay['frames'];truth=set(replay['event']['nodes'])
        candidates=[g for g in replay['groups'] if g['window']==96 and g['channel']==0]
        group=max(candidates,key=lambda g:len(truth&set(g['nodes']))/len(truth|set(g['nodes'])))
        gi=group['index'];node=replay['event']['nodes'][0];times=np.asarray(replay['times'])
        selection={'event':replay['event'],'group_index':gi,'sensor_index':node,
                   'rule':'First prespecified copy event, first affected sensor; best-overlap group uses injection labels for illustration only.'}
        write_json(out/'figure-case-selection.json',selection)
        fig,axes=plt.subplots(2,3,figsize=(7.05,2.85),sharex=True)
        plots=[('spatial',0,'Spatial entropy'),('temporal',0,'Permutation entropy'),('temporal',1,'Sample entropy'),
               ('spatial',2,'Signed correlation'),('temporal',2,'ACF at lag 1'),('temporal',6,'Local variance')]
        for ax,(kind,f,title) in zip(axes.flat,plots):
            if kind=='spatial':
                values=[fr['spatial'][gi][f] for fr in frames];low=[fr['spatial_low'][gi][f] for fr in frames];high=[fr['spatial_high'][gi][f] for fr in frames]
            else:
                f=replay.get('feature_indices',list(range(10))).index(f)
                values=[fr['temporal']['96']['values'][node][0][f][0] for fr in frames]
                low=[fr['temporal']['96']['low'][node][0][f][0] for fr in frames]
                high=[fr['temporal']['96']['high'][node][0][f][0] for fr in frames]
            values,low,high=[np.asarray(v,dtype=float) for v in [values,low,high]]
            ax.fill_between(times,low,high,color='#b7d6e6',alpha=.75,label='90% model interval')
            ax.plot(times,values,color='#173e54',lw=1.4,label='Observed')
            ax.axvspan(192,203,color='#f2bc9a',alpha=.5)
            ax.set_title(title);ax.grid(axis='y',alpha=.15)
        for ax in axes[1]:ax.set_xlabel('Decision sample (event 192–203)')
        axes[0,0].legend(fontsize=6,frameon=False)
        fig.tight_layout(pad=.4,w_pad=.8,h_pad=.6);save(fig,dest,'traces')
    summary=read_json(out/'summary.json');lookup={(r['dataset'],r['method']):r for r in summary}
    if not all((d,'diffusion/BST') in lookup for d in LABELS):return
    paired=read_json(out/'paired.json');families=['S','T','ST','B','BST']
    fig,axes=plt.subplots(3,3,figsize=(7.05,4.9))
    for col,dataset in enumerate(LABELS):
        for row,metric in enumerate(['recall','iou']):
            ax=axes[row,col]
            for i,ref in enumerate(COLORS):
                stats=[lookup[dataset,ref+'/'+f][metric] for f in families]
                mean=np.asarray([s['mean'] for s in stats]);lower=np.asarray([s['low'] for s in stats]);upper=np.asarray([s['high'] for s in stats])
                ax.errorbar(np.arange(5)+(i-.5)*.13,mean,yerr=[mean-lower,upper-mean],fmt='o-',color=COLORS[ref],lw=1,ms=3,capsize=2,label=ref)
            ax.set(xticks=np.arange(5),xticklabels=families,ylim=(-.015,1 if row==0 else .65))
            ax.grid(axis='y',alpha=.18)
            if row==0:ax.set_title(LABELS[dataset])
            if col==0:ax.set_ylabel('Event recall' if row==0 else 'Unconditional IoU')
        ax=axes[2,col]
        contrasts=[('S','SB'),('T','TB'),('BST','B')]
        for i,ref in enumerate(COLORS):
            stats=[next(r for r in paired if r['dataset']==dataset and r['a']==ref+'/'+a and r['b']==ref+'/'+b and r['metric']=='tp') for a,b in contrasts]
            mean=np.asarray([s['mean'] for s in stats]);lower=np.asarray([s['low'] for s in stats]);upper=np.asarray([s['high'] for s in stats])
            ax.errorbar(mean,np.arange(3)+(i-.5)*.15,xerr=[mean-lower,upper-mean],fmt='o',ms=3,capsize=2,color=COLORS[ref])
        ax.axvline(0,color='#738391',lw=.7);ax.set(yticks=np.arange(3),yticklabels=['S − SB','T − TB','BST − B'],xlabel='Paired recall difference',xlim=(-.8,.8));ax.grid(axis='x',alpha=.18)
    axes[0,0].legend(frameon=False,fontsize=6.7)
    fig.tight_layout(pad=.4,h_pad=.75,w_pad=.8);save(fig,dest,'performance')
    missing=read_json(out/'missingness-development.json')
    missing=pd.DataFrame(missing)
    missing['dataset']=missing.dataset.map(lambda x:'synthetic' if x.startswith('synthetic') else x)
    fig,axes=plt.subplots(3,3,figsize=(7.05,4.3))
    for col,dataset in enumerate(LABELS):
        for i,ref in enumerate(COLORS):
            fs=['S','PE','SE','B','BST'];x=np.arange(len(fs))+(i-.5)*.15
            axes[0,col].plot(x,[lookup[dataset,ref+'/'+f]['availability']['mean'] for f in fs],'o-',color=COLORS[ref],lw=1,ms=3,label=ref)
            axes[1,col].plot(x,[lookup[dataset,ref+'/'+f]['background_exceedance'] for f in fs],'o-',color=COLORS[ref],lw=1,ms=3)
        axes[0,col].set(xticks=np.arange(5),xticklabels=fs,ylim=(-.02,1.04),title=LABELS[dataset])
        axes[1,col].set(xticks=np.arange(5),xticklabels=fs,ylim=(-.02,1.04))
        axes[1,col].axhline(.1,color='#748795',ls='--',lw=.9)
        m=missing[(missing.dataset==dataset)&(missing.window==96)].groupby('extra_missing_rate').mean(numeric_only=True)
        for key,label,color in [('spatial_available','Spatial','#715596'),('permutation_available','PE','#197ba7'),('sample_available','SE','#cc6138')]:
            axes[2,col].plot(m.index,m[key],'o-',ms=3,lw=1,label=label,color=color)
        axes[2,col].set(ylim=(-.02,1.04),xlabel='Additional missingness (development)')
        for ax in axes[:,col]:ax.grid(axis='y',alpha=.2)
    axes[0,0].set_ylabel('Eligible group fraction');axes[1,0].set_ylabel('Background\nexceedance');axes[0,0].legend(frameon=False,fontsize=6.8)
    axes[2,0].set_ylabel('W96 support');axes[2,0].legend(frameon=False,fontsize=6.5,ncol=3)
    fig.tight_layout(pad=.4,h_pad=.65,w_pad=.7);save(fig,dest,'availability')
    path=out/'replays/intel.json'
    if path.exists() or Path(str(path)+'.gz').exists():
        replay=read_json(path);fr=replay['frames'][3];coordinates=np.asarray(replay['coordinates']);adj=np.asarray(replay['adjacency'])
        fig,axes=plt.subplots(1,2,figsize=(7.05,2.35),gridspec_kw={'width_ratios':[1,1.1]})
        ax=axes[0]
        for a,b in zip(*np.where(np.triu((adj+adj.T)>0,1))):ax.plot(coordinates[[a,b],0],coordinates[[a,b],1],color='#d2dde5',lw=.5,zorder=0)
        scores=np.asarray(fr['sensor']['BST'],dtype=float)
        image=ax.scatter(coordinates[:,0],coordinates[:,1],c=scores,cmap='viridis',s=17,vmin=0,vmax=np.nanquantile(scores,.95))
        affected=np.asarray(replay['event']['nodes']);ax.scatter(coordinates[affected,0],coordinates[affected,1],facecolors='none',edgecolors='#ce6546',s=52,lw=1)
        ax.set_title('Intel replay · first copy event, decision 203');ax.set_aspect('equal');ax.set_xlabel('Coordinate (m)');ax.set_ylabel('Coordinate (m)')
        fig.colorbar(image,ax=ax,fraction=.045,pad=.03,label='BST sensor score')
        costs=pd.DataFrame(read_json(out/'isolated-benchmark.json'))
        labels=['synthetic64','intel','pems'];yy=np.arange(3)
        for offset,ref in [(-.16,'bootstrap'),(.16,'diffusion')]:
            values=costs[costs.reference==ref].set_index('dataset')
            axes[1].barh(yy+offset,[values.loc[n,'pipeline_total_seconds'] for n in labels],height=.29,label=ref,color=COLORS[ref])
        axes[1].set(yticks=yy,yticklabels=['Syn.64','Intel','PEMS'],xlabel='Seconds per single-episode pipeline',title='A6000 · isolated median after warmup')
        axes[1].legend(frameon=False,fontsize=6.2);axes[1].grid(axis='x',alpha=.18)
        fig.tight_layout(pad=.4,w_pad=1);save(fig,dest,'dashboard_cost')


def numeric_tables(root: Path):
    out=root/'results/extension-v2';dest=root/'manuscript/generated-v2';dest.mkdir(parents=True,exist_ok=True)
    summary=read_json(out/'summary.json');lookup={(r['dataset'],r['method']):r for r in summary}
    def n(x):return '--' if x is None or not np.isfinite(x) else f'{x:.3f}'
    lines=[r'\begin{table*}[t]\centering\small',
        r'\caption{Operational extension results at nominal $\alpha=.10$. P/R: event precision/recall; AP: event-PR envelope area; IoU includes missed events as zero. These are not matched achieved background rates. PE/SE, all comparators and common-support results are retained in the artifact.}\label{tab:main}',
        r'\begin{tabular}{llrrrrrrrrrrrr}\toprule',
        r'&&\multicolumn{4}{c}{Synthetic (three sizes)}&\multicolumn{4}{c}{Intel Lab}&\multicolumn{4}{c}{PEMS-BAY}\\',
        r'Reference&Family&P&R&AP&IoU&P&R&AP&IoU&P&R&AP&IoU\\\midrule']
    for ref in COLORS:
        for family in ['S','T','ST','B','BST']:
            values=[]
            for dataset in LABELS:
                r=lookup[dataset,ref+'/'+family];values.extend([r['event_precision'],r['recall']['mean'],r['event_auprc'],r['iou']['mean']])
            lines.append(('Block' if ref=='bootstrap' else 'Diffusion')+' & '+family+' & '+' & '.join(n(v) for v in values)+r' \\')
        lines.append(r'\midrule')
    lines.extend([r'\bottomrule\end{tabular}\end{table*}'])
    (dest/'main-table.tex').write_text('\n'.join(lines)+'\n')
    test=pd.DataFrame(read_json(out/'paired-reference-fidelity.json'))
    test['dataset']=test.dataset.map(lambda x:'synthetic' if x.startswith('synthetic') else x)
    table=[r'\begin{table*}[t]\centering\small',
        r'\caption{Paired fidelity on unchanged backgrounds: seed 17, first two blocks, decisions 167/263. References share evaluated raw coordinates or eligible feature units; donor masks can still change per-draw support. Raw, H, PE, SE: 90\% coverage; TV: ordinal-pattern total variation; ES: normalized energy score (lower is better). Temporal entries use W=96. Means omit undefined units; counts and widths are saved.}\label{tab:fidelity}',
        r'\begin{tabular}{llrrrrrrrr}\toprule Dataset&Reference&Raw&H&PE&SE&ACF1 MAE&Ordinal TV&R RMSE&ES\\\midrule']
    for dataset in LABELS:
        for ref in COLORS:
            values=test[(test.dataset==dataset)&(test.reference==ref)].mean(numeric_only=True)
            keys=['coverage90','spatial_entropy_coverage90','permutation_96_coverage90','sample_96_coverage90','acf1_96_mae','ordinal_tv_96','correlation_rmse','energy_score']
            table.append(LABELS[dataset]+' & '+('Block' if ref=='bootstrap' else 'Diffusion')+' & '+' & '.join(n(values[k]) for k in keys)+r' \\')
    table.append(r'\bottomrule\end{tabular}\end{table*}')
    (dest/'fidelity-table.tex').write_text('\n'.join(table)+'\n')

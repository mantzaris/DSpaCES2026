"""Exact vector research figures from immutable graph-flow result records."""
from pathlib import Path
import hashlib
import json

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Circle
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / 'results/graph_flow_v1'
OUT = ROOT / 'paper/figures/graph_flow'
OUT.mkdir(parents=True, exist_ok=True)
SOURCES = {}
FIGURES = {}
ORDER = ['synthetic_32_linear', 'synthetic_32_nonlinear', 'synthetic_64_nonlinear', 'intel', 'skab']
LABELS = dict(zip(ORDER, ['S32L', 'S32N', 'S64N', 'Intel', 'SKAB']))
COLORS = {'flow_ratio': '#0072b2', 'pca': '#d55e00', 'flow_nll': '#009e73', 'ppca': '#9b59a0'}
METHODS = {'flow_ratio': 'Flow + corruption', 'pca': 'PCA', 'flow_nll': 'Same-flow NLL', 'ppca': 'PPCA + corruption'}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8, 'axes.titlesize': 9,
    'axes.labelsize': 8, 'legend.fontsize': 7, 'xtick.labelsize': 7, 'ytick.labelsize': 7,
    'pdf.fonttype': 42, 'svg.fonttype': 'none', 'axes.spines.top': False, 'axes.spines.right': False})


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    path = Path(path)
    if not path.is_absolute():
        path = RESULT / path
    SOURCES[str(path.relative_to(ROOT))] = digest(path)
    return json.loads(path.read_text())


def arrays(path):
    path = Path(path)
    if not path.is_absolute():
        path = RESULT / path
    SOURCES[str(path.relative_to(ROOT))] = digest(path)
    return dict(np.load(path, allow_pickle=False))


def save(fig, name, details=None):
    outputs = {}
    for suffix in ('pdf', 'svg', 'png'):
        path = OUT / (name + '.' + suffix)
        fig.savefig(path, bbox_inches='tight', bbox_extra_artists=list(fig.legends)+[a.get_legend() for a in fig.axes if a.get_legend() is not None], pad_inches=.05, dpi=180)
        if suffix == 'svg':
            path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')
        outputs[str(path.relative_to(ROOT))] = digest(path)
    FIGURES[name] = dict(inputs=dict(SOURCES), outputs=outputs, details=details)
    plt.close(fig)


def architecture(lock):
    fig, ax = plt.subplots(figsize=(7.16, 2.45))
    ax.set(xlim=(0, 10), ylim=(0, 3.7)); ax.axis('off')
    def box(x, y, w, h, text, color='#edf3f7'):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=.035',
            edgecolor='#697b89', facecolor=color, linewidth=.7))
        ax.text(x+w/2, y+h/2, text, ha='center', va='center', fontsize=8)
    def arrow(a, b):
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle='-|>', mutation_scale=9,
                                    linewidth=.8, color='#526879'))
    box(.1, 2.75, 2.35, .65, 'History + sources\nTarget block masked')
    box(3.25, 2.75, 2.25, .65, 'Graph + temporal\nFrozen associations')
    box(6.45, 2.75, 3.35, .65, 'Neural inverse flow\n3 models + normal latent draws')
    box(6.45, 1.5, 3.35, .65, 'Generated reference intervals\nM = 32, 128 or 2048 per model')
    box(.1, 1.5, 2.35, .65, 'Recorded interval\n8 completed values', '#fff0df')
    box(3.25, 1.5, 2.25, .65, 'Corruption channel q\nBias/drift/noise/stuck')
    box(.1, .15, 2.35, .7, 'Normal flow density\npθ(y | context)')
    box(3.25, .15, 2.25, .7, 'Fault density\nMean q over draws')
    box(6.45, .15, 3.35, .7, 'Log ratio + weighted repair\nCalibration → Neo4j → operator')
    for a, b in [((2.45,3.075),(3.25,3.075)),((5.5,3.075),(6.45,3.075)),
                 ((8.1,2.75),(8.1,2.15)),((6.45,1.825),(5.5,1.825)),
                 ((2.45,1.825),(3.25,1.825)),((1.275,1.5),(1.275,.85)),
                 ((4.375,1.5),(4.375,.85)),((5.5,.5),(6.45,.5))]:
        arrow(a,b)
    ax.plot([1.275,1.275,7.0],[.15,.015,.015],color='#526879',lw=.8)
    arrow((7.0,.015),(7.0,.15))
    save(fig,'architecture',dict(protocol_sha256=digest(RESULT/'protocol_lock.json')))


def performance(report):
    fig, axes = plt.subplots(2,3,figsize=(7.16,4.15))
    for ax, dataset in zip(axes[0], ['synthetic_32_nonlinear','intel','skab']):
        curve=arrays(Path(dataset)/'precision_recall.npz')
        for method,color in COLORS.items():
            ax.plot(curve[method+'_recall'],curve[method+'_precision'],color=color,lw=1,label=METHODS[method])
        row=report['datasets'][dataset]
        ax.set(xlim=(0,1),ylim=(0,1.02),xlabel='Recall',ylabel='Precision',
               title=LABELS[dataset]+f"  n = {row['candidates']:,}")
        ax.axhline(row['prevalence'],ls=':',color='#888888',lw=.7)
    for ax, method in zip(axes[1],['pca','flow_nll','ppca']):
        for index,dataset in enumerate(ORDER):
            item=report['datasets'][dataset]['paired_differences'][method]
            ax.plot(item['interval_95'],[index,index],color='#708798',lw=1.1)
            ax.plot(item['estimate'],index,'o',color='#0072b2',ms=3)
        item=report['paired_macro_comparisons'][method]
        ax.plot(item['interval'],[5.3,5.3],color='#222222',lw=1.7)
        ax.plot(item['macro_ap_difference'],5.3,'D',color='#222222',ms=4)
        ax.axvline(0,color='#888888',ls=':',lw=.8);ax.axvline(.02,color='#dddddd',lw=.7)
        ax.set_yticks(list(range(5))+[5.3]);ax.set_yticklabels([LABELS[d] for d in ORDER]+['Macro'])
        ax.invert_yaxis();ax.set(xlabel='Flow ratio AP minus comparator AP',title=METHODS[method])
    for ax in axes.ravel():ax.grid(alpha=.12)
    handles=[Line2D([0],[0],color=c,label=METHODS[m]) for m,c in COLORS.items()]
    fig.legend(handles=handles,loc='lower center',ncol=4,frameon=False)
    fig.tight_layout(rect=(0,.065,1,1));save(fig,'performance')


def confidence(report):
    fig,axes=plt.subplots(3,3,figsize=(7.16,5.15))
    details={}
    for column,dataset in enumerate(['synthetic_32_nonlinear','intel','skab']):
        row=report['datasets'][dataset];ax=axes[0,column]
        reliability=row['methods']['flow_ratio']['confidence']['bins']
        bins=[b for b in reliability if b['count']]
        # Field names are from the saved calibration report, never refitted here.
        x=[b['predicted'] for b in bins];y=[b['observed'] for b in bins]
        ax.plot([0,1],[0,1],':',color='#888888',lw=.7);ax.plot(x,y,'o-',color=COLORS['flow_ratio'],ms=3,lw=.9)
        counts=[str(b['count']) for b in reliability]
        ax.text(.03,.97,'Counts in successive 0.1 bins\n'+', '.join(counts[:5])+'\n'+', '.join(counts[5:]),
            transform=ax.transAxes,va='top',fontsize=6,
            bbox=dict(facecolor='white',edgecolor='none',alpha=.8,pad=1))
        ax.set(xlim=(-.03,1.03),ylim=(-.06,1.06),xlabel='Fitted fault probability',ylabel='Fault frequency',title=LABELS[dataset]+' reliability')
        for method,color in COLORS.items():
            curve=row['methods'][method]['review'];ax=axes[1,column]
            ax.plot([r['coverage'] for r in curve],[r['precision'] for r in curve],color=color,lw=1)
        axes[1,column].set(xlim=(0,1),ylim=(0,1.02),xlabel='Candidate review coverage',ylabel='Review precision',
                          title=f"{row['candidates']:,} candidates")
        maximum_counts=[]
        for method in ['flow_ratio','pca','ppca']:
            curve=[r for r in row['methods'][method]['repair']['curve'] if r['accepted']]
            curve=sorted(curve,key=lambda r:r['coverage'])
            ax=axes[2,column]
            ax.plot([r['coverage'] for r in curve],[r['risk'] for r in curve],color=COLORS[method],lw=1,marker='.',ms=2)
            maximum_counts.append(curve[-1]['accepted'] if curve else 0)
        ax.set(xlim=(0,1),ylim=(0,1.03),xlabel='All-case repair coverage',ylabel='Repair failure rate',title=f"{row['cases']} evaluation cases")
        ax.axhline(.1,ls=':',lw=.7,color='#888888')
        ax.text(.97,.77 if dataset=='intel' else .97,
                'Max actions\nFlow '+str(maximum_counts[0])+'  PCA '+str(maximum_counts[1])+'\nPPCA '+str(maximum_counts[2]),
                transform=ax.transAxes,ha='right',va='top',fontsize=6,
                bbox=dict(facecolor='white',edgecolor='none',alpha=.8,pad=1))
        details[dataset]=dict(reliability_bins=reliability,repair_policies={m:row['methods'][m]['repair']['policy'] for m in ['flow_ratio','pca','ppca']})
    for ax in axes.ravel():ax.grid(alpha=.12)
    fig.legend(handles=[Line2D([0],[0],color=c,label=METHODS[m]) for m,c in COLORS.items()],loc='lower center',ncol=4,frameon=False)
    fig.tight_layout(rect=(0,.045,1,1));save(fig,'confidence',details)


def network(bundle):
    # Fixed incoming-context layout for a legible single-column research panel.
    # The operator retains the larger saved neighborhood.
    fig,ax=plt.subplots(figsize=(3.5,2.8));ax.set(xlim=(0,750),ylim=(-60,450));ax.set_aspect('equal');ax.axis('off')
    h=bundle['hypothesis'];target=h['target'];support=list(h['context_channels'])
    positions={target:np.array([505.,240.])}
    for query,y in zip(support,np.linspace(370,100,len(support))):positions[query]=np.array([75.,y])
    candidates=sorted(bundle['associations'],key=lambda e:(-e['validation_gain'],e['id']))
    edges=[e for e in candidates if e['target']==target and e['source'] in support]
    outgoing=next((e for e in candidates if e['source']==target and e['target'] not in positions),None)
    if outgoing:
        positions[outgoing['target']]=np.array([660.,65.]);edges.append(outgoing)
    for edge in edges:
        a,b=positions[edge['source']],positions[edge['target']];u=(b-a)/np.linalg.norm(b-a)
        ax.add_patch(FancyArrowPatch(a+27*u,b-32*u,arrowstyle='-|>',mutation_scale=7,color='#9aa6af',linewidth=.8))
        if edge['target']==target:
            i=support.index(edge['source']);position=[278.,(a[1]+b[1])/2+22]
        else:position=[533.,92.]
        text=f"lag {edge['lag']} samples\n|r train| {edge['training_abs_correlation']:.2f}"
        ax.text(*position,text,ha='center',va='center',fontsize=6.5,bbox=dict(facecolor='white',edgecolor='none',alpha=.95,pad=1))
    for index,point in positions.items():
        color='#b82232' if index==target else '#176faa' if index in support else '#758798'
        ax.add_patch(Circle(point,27,facecolor='white',edgecolor=color,lw=1.3))
        if index==target:ax.add_patch(Circle(point,33,fill=False,edgecolor=color,lw=1.1))
        ax.text(*point,'C'+str(index),ha='center',va='center',fontsize=7)
        ax.text(point[0],point[1]-48,bundle['sensors'][index]['name'],ha='center',va='center',fontsize=6.5)
    ax.text(375,-31,f"Disputed C{target}   S {h['score']:.1f}   ESS {h['ess']:.1f}",ha='center',fontsize=7)
    handles=[Line2D([0],[0],marker='o',color='white',markeredgecolor='#b82232',label='Disputed reading'),
      Line2D([0],[0],marker='o',color='white',markeredgecolor='#176faa',label='Allowed context'),
      Line2D([0],[0],color='#9aa6af',label='Predictive edge')]
    ax.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,-.02),ncol=2,frameon=False,fontsize=6.5)
    fig.tight_layout();save(fig,'network',dict(case_id=bundle['case']['id'],dataset=bundle['dataset'],selection_reason=bundle['selection_reason'],
                                           rendered_nodes=list(positions),rendered_edges=[e['id'] for e in edges]))


def repairs(bundles):
    fig,axes=plt.subplots(1,3,figsize=(7.16,2.25))
    for ax,bundle in zip(axes,bundles):
        t=bundle['trajectories'];x=np.asarray(t['times'])-t['times'][0]
        for prior in t['prior']:ax.plot(x,prior,color='#a3abb3',alpha=.55,lw=.6)
        ax.fill_between(x,t['lower'],t['upper'],color='#79bce1',alpha=.45)
        ax.plot(x,t['mean'],color='#0072b2',lw=1.5)
        ax.plot(x,t['observed'],color='#b82232',lw=1.2)
        ax.plot(x,t['reference'],'--',color='#218551',lw=1.2)
        h=bundle['hypothesis'];name=bundle['selection_reason'].replace('_',' ')
        if name=='numerical abstention':name='Low sampling resolution'
        ax.set(xlabel='Elapsed time (s)',ylabel=t['unit'],title=name.capitalize())
        ax.text(.02,.02,f"S {h['score']:.1f}, ESS {h['ess']:.1f}",transform=ax.transAxes,fontsize=7,
                bbox=dict(facecolor='white',edgecolor='none',alpha=.8))
        ax.grid(alpha=.12)
    handles=[Line2D([0],[0],color=c,linestyle=ls,label=label) for c,ls,label in
      [('#b82232','-','Recorded'),('#218551','--','Offline reference'),('#a3abb3','-','Prior draws'),('#0072b2','-','Weighted mean and 90% band')]]
    fig.legend(handles=handles,loc='lower center',ncol=4,frameon=False)
    fig.tight_layout(rect=(0,.1,1,1));save(fig,'repair',dict(cases=[dict(dataset=b['dataset'],case=b['case']['id'],reason=b['selection_reason']) for b in bundles]))


def equations(report,lock,runtime):
    fig,axes=plt.subplots(2,2,figsize=(7.16,3.9))
    comparisons=report['paired_macro_comparisons'];keys=['flow_nll','ppca','flow_plugin','own_history']
    for i,key in enumerate(keys):
        row=comparisons[key];axes[0,0].plot(row['interval'],[i,i],color='#0072b2',lw=1.5);axes[0,0].plot(row['macro_ap_difference'],i,'o',color='#0072b2',ms=4)
    axes[0,0].set_yticks(range(4));axes[0,0].set_yticklabels(['Same-flow NLL','PPCA + same q','Deterministic plug-in','Own history'])
    axes[0,0].invert_yaxis();axes[0,0].axvline(0,color='#888888',ls=':',lw=.8)
    axes[0,0].set(xlabel='Family-macro AP difference',title='(a) Contribution of each component')
    colors=['#0072b2','#e69f00','#009e73','#cc79a7','#666666']
    for dataset,color in zip(ORDER,colors):
        sampling=read(Path('development')/(dataset+'_sampling.json'))
        axes[0,1].plot([r['samples'] for r in sampling['repeatability']],
                       [r['repeat_absolute_difference_p95'] for r in sampling['repeatability']],'.-',color=color,label=LABELS[dataset])
        axes[1,0].plot([r['samples'] for r in sampling['profiles']],
                      [np.median([v['seconds'] for v in r['repetitions']])*1000 for r in sampling['profiles']],'.-',color=color)
    axes[0,1].set(xscale='log',yscale='log',xlabel='Prior draws per model',ylabel='95th percentile score change',title='(b) Repeated sampling seeds')
    axes[0,1].legend(frameon=False,ncol=2)
    axes[1,0].set(xscale='log',yscale='log',xlabel='Prior draws per model',ylabel='GPU scorer time (ms)',title='(c) Development scoring cost')
    x=np.arange(len(ORDER));width=.25
    for offset,method,color in [(-width,'flow_ratio_and_repair','#0072b2'),(0,'same_flow_nll','#009e73'),(width,'pca','#d55e00')]:
        axes[1,1].bar(x+offset,[runtime[d]['methods'][method]['median_seconds']*1000 for d in ORDER],width,color=color,label={'flow_ratio_and_repair':'Ratio + repair','same_flow_nll':'NLL','pca':'PCA'}[method])
    axes[1,1].set_xticks(x);axes[1,1].set_xticklabels([LABELS[d] for d in ORDER]);axes[1,1].set(yscale='log',ylabel='Wall time per window (ms)',title='(d) Operational inference cost')
    axes[1,1].legend(frameon=False)
    for ax in axes.ravel():ax.grid(alpha=.12)
    fig.tight_layout();save(fig,'equations',dict(development_cost_scope='Includes optional offline distribution metrics. Runtime panel excludes all reference-truth metrics.'))


def main():
    lock=read('protocol_lock.json');report=read('analysis.json');runtime=read('runtime.json')
    architecture(lock);performance(report);confidence(report)
    manifest=read('graph/export_manifest.json')
    available={Path(item['path']).stem:item for item in manifest}
    def case(dataset,reason):
        return read(ROOT/available[dataset+'_'+reason]['path'])
    network(case('synthetic_32_nonlinear','correct_attribution'))
    selected=[case('synthetic_32_nonlinear','correct_attribution'),case('synthetic_32_nonlinear','incorrect_attribution')]
    third='skab_numerical_abstention'
    if third not in available:third='skab_lowest_ess_diagnostic'
    selected.append(read(ROOT/available[third]['path']));repairs(selected)
    equations(report,lock,runtime)
    (RESULT/'figure_provenance.json').write_text(json.dumps(FIGURES,indent=2)+'\n')


if __name__=='__main__':main()

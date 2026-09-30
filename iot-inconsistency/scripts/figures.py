"""Scientific vector figures from executed configuration and saved experiment outputs."""
from pathlib import Path
import argparse,json,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch,FancyBboxPatch,Circle
from matplotlib.lines import Line2D
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.experiment import json_save
out=ROOT/'paper/figures';out.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':9,'axes.labelsize':8,'legend.fontsize':8,
                     'xtick.labelsize':8,'ytick.labelsize':8,'svg.fonttype':'none','pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
labels={'synthetic_32_linear':'Synthetic 32 linear','synthetic_32_nonlinear':'Synthetic 32 nonlinear','synthetic_64_nonlinear':'Synthetic 64 nonlinear','intel':'Intel','skab':'SKAB'}
colors=['#0072b2','#d55e00','#009e73','#cc79a7','#6c5b24']
provenance={}
def save(fig,name,sources):
    for suffix in ('pdf','svg','png'):fig.savefig(out/(name+'.'+suffix),dpi=200,bbox_inches='tight',pad_inches=.04)
    plt.close(fig);provenance[name]=sources

# Architecture labels are taken from the actual recorded study configuration.
config=json.loads((ROOT/'configs/study.json').read_text())
fig,ax=plt.subplots(figsize=(7.16,2.5));ax.set_xlim(0,10);ax.set_ylim(0,4);ax.axis('off')
def box(x,y,w,h,text,color='#e9f2f7'):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.04',facecolor=color,edgecolor='#617384',linewidth=.8));ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=8)
def arrow(a,b,color='#52667b',style='-'):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=9,linewidth=.9,color=color,linestyle=style,connectionstyle='arc3,rad=0'))
box(.1,2.45,1.4,.8,'Measured window\nand source identities')
box(1.95,2.45,1.45,.8,'Canonical inputs\nFrozen hypotheses')
box(3.85,2.45,1.5,.8,'Proposal context\nWitness targets hidden')
box(5.85,2.45,1.55,.8,f'{config["ensemble_seeds"].__len__()} fitted models\n{config["replicates"]} proposals each')
box(8.,2.45,1.7,.8,'Before and after\nwitness predictions')
for left,right in [((1.5,2.85),(1.95,2.85)),((3.4,2.85),(3.85,2.85)),((5.35,2.85),(5.85,2.85)),((7.4,2.85),(8,2.85))]:arrow(left,right)
box(1.95,1.12,1.45,.75,'Unchanged witness\ntargets and masks','#fff1d7')
box(5.85,1.12,1.55,.75,'CRPS change\nGain R and spread U')
arrow((2.65,2.45),(2.65,1.87));arrow((3.4,1.5),(5.85,1.5),color='#a56b00');arrow((8.85,2.45),(7.4,1.62))
box(8,1.12,1.7,.75,'S = R − κU − λΩ\nType-specific calibration')
arrow((7.4,1.5),(8,1.5));box(8,.05,1.7,.68,'Neo4j evidence writes\nOperator review')
arrow((8.85,1.12),(8.85,.73))
box(.1,.05,2.5,.65,'Training artifacts\nNormalization, relations and models','#edf1ed');arrow((1.35,.7),(4.4,2.42),style='--')
box(3.05,.05,2.25,.65,'Separate calibration blocks\nNull tails and probabilities','#edf1ed');arrow((5.3,.37),(8,1.22),style='--')
ax.text(4.55,1.18,'Targets reach\nscoring only',ha='center',va='top',color='#855900',fontsize=8)
save(fig,'architecture',['configs/study.json','src/iot_repair/pipeline.py','src/iot_repair/calibration.py'])

analysis_path=ROOT/'results/analysis.json'
if not analysis_path.exists():raise SystemExit('Architecture saved; complete result analysis is required for measured figures')
reports=json.loads(analysis_path.read_text());names=[name for name in ['synthetic_32_nonlinear','intel','skab'] if name in reports]
fig,axes=plt.subplots(2,2,figsize=(7.16,5.15));axes=axes.ravel()
for color,name in zip(colors,names):
    report=reports[name]
    for panel,kind in enumerate(['observation','association']):
        track=report['tracks'][kind]
        for method,style in [('proposed','-'),(track['primary_comparator'],'--')]:
            curve=track['methods'][method]['pr_curve'];axes[panel].plot(curve['recall'],curve['precision'],style,color=color,lw=1.1)
    track=report['tracks']['observation']
    for method,style in [('proposed','-'),(track['primary_comparator'],'--')]:
        metric=track['methods'][method]
        if method=='proposed' and 'probability_evaluation' in metric:
            bins=[r for r in metric['probability_evaluation']['reliability'] if r['count']]
            axes[2].plot([r['mean_probability'] for r in bins],[r['fault_frequency'] for r in bins],'-o',color=color,lw=1,ms=3)
            for r in bins:axes[2].annotate(str(r['count']),(r['mean_probability'],r['fault_frequency']),xytext=(3,3),textcoords='offset points',fontsize=8,color=color)
        curve=metric['candidate_risk_coverage'];axes[3].plot([r['coverage'] for r in curve],[r['risk'] for r in curve],style,color=color,lw=1.1)
for i in (0,1):axes[i].set(xlim=(0,1),ylim=(0,1.02),xlabel='Recall',ylabel='Precision')
axes[0].set_title('(a) Added observation faults',loc='left');axes[1].set_title('(b) Added association faults',loc='left')
axes[2].plot([0,1],[0,1],':',color='black',lw=.8);axes[2].set(xlabel='Mean fitted fault probability',ylabel='Observed injected-fault frequency',xlim=(0,1),ylim=(0,1));axes[2].set_title('(c) Reliability with bin counts',loc='left')
axes[3].set(xlabel='Fraction of screened candidates accepted',ylabel='Incorrect attribution fraction',xlim=(0,1),ylim=(0,1.02));axes[3].set_title('(d) Observation review risk',loc='left')
for ax in axes:ax.grid(alpha=.15)
handles=[Line2D([0],[0],color=c,label=labels[n]) for c,n in zip(colors,names)]+[Line2D([0],[0],color='black',label='Witness repair'),Line2D([0],[0],color='black',linestyle='--',label='Stated comparator')]
fig.legend(handles=handles,loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.5,-.01));fig.tight_layout(rect=[0,.13,1,1]);save(fig,'confidence',['results/analysis.json'])

# Fixed-coordinate operator panels use one selected saved case and its paired reference.
bundle_path=ROOT/'results/graph/synthetic_32_nonlinear_illustration.json'
if bundle_path.exists():
    bundle=json.loads(bundle_path.read_text());case=bundle['case'];graph=case['graph'];view=bundle['view'];positions={n['index']:np.array([n['x'],470-n['y']]) for n in view['nodes']}
    obs=next(h for h in bundle['hypotheses'] if h['kind']=='observation');edge=next(h for h in bundle['hypotheses'] if h['kind']=='association')
    fig,axes=plt.subplots(1,3,figsize=(7.16,2.6))
    for panel,(ax,hypothesis,title) in enumerate(zip(axes,[None,obs,edge],['(a) Disagreement before attribution','(b) Reading hypothesis','(c) Alternative relation mask'])):
        ax.set_title(title,loc='left',fontsize=8.5);ax.set_xlim(35,685);ax.set_ylim(-22,475);ax.set_aspect('equal');ax.axis('off')
        witness=set(hypothesis['witness_channels']) if hypothesis else set()
        for e in view['edges']:
            a,b=positions[e['source']],positions[e['target']];direction=b-a;norm=np.linalg.norm(direction);unit=direction/norm
            flagged=hypothesis is not None and hypothesis['kind']=='association' and hypothesis['index']==e['index']
            ax.add_patch(FancyArrowPatch(a+24*unit,b-28*unit,arrowstyle='-|>',mutation_scale=7,linewidth=1.4 if flagged else .6,
                color='#a95300' if flagged else '#8293a0',linestyle='--' if flagged else '-',connectionstyle='arc3,rad=0.05'))
            midpoint=(a+b)/2+np.array([-unit[1],unit[0]])*12
            ax.text(*midpoint,f"lag {e['lag']}",fontsize=8,ha='center',va='center',bbox=dict(facecolor='white',edgecolor='none',alpha=.86,pad=.1))
        for i,position in positions.items():
            suspect=hypothesis is not None and hypothesis['kind']=='observation' and hypothesis['index']==i
            color='#b91c1c' if suspect else '#1769aa' if i in witness else '#52667b'
            ax.add_patch(Circle(position,24,facecolor='white',edgecolor=color,lw=1.4 if suspect or i in witness else .8))
            if suspect:ax.add_patch(Circle(position,30,fill=False,edgecolor=color,lw=1.1))
            ax.text(*position,f'{i:02d}',ha='center',va='center',fontsize=8.2)
            if i in witness:ax.text(position[0],position[1]-39,'witness',fontsize=8,ha='center',color='#1769aa')
        if hypothesis:
            r=hypothesis;text=f"R {r['mean_gain']:.3f}   U {r['model_instability']:.3f}\nS {r['selected_score']:.3f}   p {r['candidate_null_tail']:.3f}"
            ax.text(360,-10,text,ha='center',va='top',fontsize=8)
            target=r['index'] if r['kind']=='observation' else graph['edges'][r['index']]['source']
            ax.plot([360,positions[target][0]],[0,positions[target][1]-30],':',color='#333',lw=.7)
        else:
            position=positions[obs['index']];ax.plot([360,position[0]],[0,position[1]-30],':',color='#333',lw=.7)
            observed=np.asarray(obs['observed_interval'],float);median=bundle['median'][obs['index']];scale=bundle['scale'][obs['index']]
            value=float(np.nanmean(observed)*scale+median)
            ax.text(360,-10,f"C{obs['index']:02d} mean {value:.2f} {bundle['units'][obs['index']]}\nReading and relation reviewed",ha='center',va='top',fontsize=8)
    fig.subplots_adjust(wspace=.08,bottom=.18);save(fig,'network',[str(bundle_path.relative_to(ROOT)),bundle['artifact']])

# Four empirical equation panels. The focal nonlinear configuration was fixed in the protocol.
name='synthetic_32_nonlinear';report=reports.get(name);abl_path=ROOT/'results/ablations'/name/'analysis.json'
if report and abl_path.exists():
    ablations=json.loads(abl_path.read_text());fig,axes=plt.subplots(2,2,figsize=(7.16,5.0));axes=axes.ravel();main=report['tracks']['observation']['methods']['proposed']['window_ap']
    rows=[]
    for key,title in [('fixed_penalties','Fixed positive penalties'),('R_only','Gain only'),('no_uncertainty','No spread penalty'),('no_cost','No edit penalty')]:
        rows.append((title,main-report['tracks']['observation']['methods'][key]['window_ap'],None,False))
    for key,title in [('deterministic','Deterministic'),('no_graph','No graph'),('no_witness_separation','Visible witnesses'),('no_provenance_deduplication','Count known copies')]:
        if key not in ablations:continue
        result=ablations[key]['metrics']['observation']['paired_main_minus_ablation'];rows.append((title,result['difference'],result['interval'],ablations[key]['scope']=='unsafe diagnostic'))
    for y,(title,difference,interval,unsafe) in enumerate(rows):
        axes[0].plot(difference,y,'s' if unsafe else 'o',color='#a95300' if unsafe else '#0072b2',ms=4)
        if interval:axes[0].plot(interval,[y,y],color='#a95300' if unsafe else '#0072b2',lw=1.2)
    axes[0].set_yticks(range(len(rows)));axes[0].set_yticklabels([r[0] for r in rows]);axes[0].axvline(0,color='#888',lw=.7);axes[0].invert_yaxis();axes[0].set_xlabel('Main AP minus ablation AP');axes[0].set_title('(a) Paired equation ablations',loc='left')
    sensitivity=[]
    for path in (ROOT/'results/sensitivity'/name).glob('case*_E3_M*_L8_amp1.json'):
        row=json.loads(path.read_text());sensitivity.append(row)
    for case_id in sorted({r['case'] for r in sensitivity}):
        points=sorted([r for r in sensitivity if r['case']==case_id],key=lambda r:r['M']);axes[1].plot([r['M'] for r in points],[np.median([v['monte_carlo_standard_error'] for v in r['records']]) for r in points],'-o',ms=3,label=f'Development case {case_id+1}')
    axes[1].set(xlabel='Paired proposals M',ylabel='Median Monte Carlo standard error');axes[1].set_xticks([2,4,8,16]);axes[1].set_title('(b) Sampling diagnostic',loc='left');axes[1].legend(frameon=False,fontsize=8)
    stress=[]
    for path in (ROOT/'results/robustness'/name).glob('conditioning_*.json'):stress.append(json.loads(path.read_text()))
    fractions=sorted({r['details']['fraction'] for r in stress})
    if fractions:
        rates=[np.mean([r['primary_target_top1'] for r in stress if r['details']['fraction']==f]) for f in fractions]
        axes[2].plot(fractions,rates,'o-',color='#0072b2');axes[2].set_ylim(0,1.02)
    axes[2].set(xlabel='Fraction of conditioning channels corrupted',ylabel='Primary target ranked first');axes[2].set_title('(c) Contaminated source evidence',loc='left')
    costs=report['costs'];timings=costs['baseline_timing'];points=[('Witness repair',np.median(costs['inference_seconds_per_window']),main)]
    for method,title in [('gdn','GDN'),('backbone','Diffusion residual'),('diffad','DiffAD adaptation')]:points.append((title,timings[method],report['tracks']['observation']['methods'][method]['window_ap']))
    for method in report['selection']['pca'].values():points.append(('PCA lag '+method.split('_')[1][3:],timings[method]['inference_seconds_per_window'],report['tracks']['observation']['methods'][method]['window_ap']))
    for i,(title,seconds,accuracy) in enumerate(points):
        axes[3].scatter(seconds,accuracy,s=18,color=colors[i%len(colors)]);axes[3].annotate(title,(seconds,accuracy),xytext=(3,3 if i%2 else -11),textcoords='offset points',fontsize=8)
    axes[3].set_xscale('log');axes[3].set(xlabel='Seconds per window',ylabel='Observation average precision',ylim=(0,1.05));axes[3].set_title('(d) Detection and inference cost',loc='left')
    for ax in axes:ax.grid(alpha=.15)
    fig.tight_layout();save(fig,'equations',['results/analysis.json',str(abl_path.relative_to(ROOT)),'results/sensitivity/'+name,'results/robustness/'+name])

# Term distributions remain separate by hypothesis type and truth.
if report:
    rows=[]
    for path in (ROOT/'results/study'/name/'test').glob('test_*.json'):rows+=json.loads(path.read_text())['records']
    fig,axes=plt.subplots(2,3,figsize=(7.16,3.9))
    for row,kind in enumerate(['observation','association']):
        for column,key in enumerate(['mean_gain','model_instability','edit_cost']):
            for label,color in [(False,'#808b95'),(True,'#0072b2')]:
                values=[r[key] for r in rows if r['kind']==kind and r['truth']==label]
                if values:axes[row,column].hist(values,bins=22,density=True,histtype='step',linewidth=1.2,color=color,label='Injected target' if label else 'Other candidate')
            axes[row,column].set_title(kind.capitalize()+' · '+{'mean_gain':'R','model_instability':'U','edit_cost':'Ω'}[key],loc='left');axes[row,column].set_ylabel('Density')
    axes[0,0].legend(frameon=False);fig.tight_layout();save(fig,'score_terms',['results/study/'+name+'/test'])
json_save(out/'provenance.json',provenance)
print('Saved figures',list(provenance))

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
fig,ax=plt.subplots(figsize=(7.16,3.05));ax.set_xlim(0,10);ax.set_ylim(0,4.9);ax.axis('off')
def box(x,y,w,h,text,color='#e9f2f7'):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.04',facecolor=color,edgecolor='#617384',linewidth=.8));ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=8)
def arrow(a,b,color='#52667b',style='-'):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=9,linewidth=.9,color=color,linestyle=style,connectionstyle='arc3,rad=0'))
box(.1,4.,2.6,.65,'Frozen training artifacts\nScales, relations and models','#edf1ed')
box(3.7,4.,2.6,.65,'Measured window and identities\nCanonical inputs and hypotheses')
box(2.9,2.85,2.3,.7,'Proposal context\nWitness targets hidden')
box(7.1,2.85,2.7,.7,'Unchanged witness targets\nFixed cell IDs and masks','#fff1d7')
box(.2,1.65,2.2,.7,f"{len(config['ensemble_seeds'])} fitted models\n{config['replicates']} proposals per model")
box(3.15,1.65,2.55,.7,f"Before and after predictions\n{config['predictive_samples']} draws per witness target")
box(7.1,1.65,2.7,.7,'CRPS on identical targets\nMean gain R and spread U')
box(.2,.25,2.2,.7,'Separate calibration blocks\nNull and probability references','#edf1ed')
box(3.15,.25,2.55,.7,'S = R − κU − λΩ\nCalibrated review quantities')
box(7.1,.25,2.7,.7,'Neo4j evidence writes\nOperator review')
for left,right in [((5,4),(4,3.55)),((6.3,4.2),(8.45,3.55)),((4,2.85),(1.3,2.35)),((4.7,2.85),(4.7,2.35)),((2.4,2),(3.15,2)),((5.7,2),(7.1,2)),((8.45,1.65),(5.7,.95)),((1.3,1.65),(3.15,.95)),((2.4,.6),(3.15,.6)),((5.7,.6),(7.1,.6))]:arrow(left,right)
arrow((8.45,2.85),(8.45,2.35),color='#a56b00');arrow((1.3,4),(.8,2.35),style='--')
ax.text(8.6,2.6,'Scoring only',va='center',color='#855900',fontsize=8)
ax.text(1.45,1.25,'Edit cost Ω',fontsize=8)
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
    fig,axes=plt.subplots(1,3,figsize=(7.16,3.1))
    for panel,(ax,hypothesis,title) in enumerate(zip(axes,[None,obs,edge],['(a) Disagreement','(b) Reading hypothesis','(c) Relation mask'])):
        ax.set_title(title,loc='left',fontsize=8.5);ax.set_xlim(35,685);ax.set_ylim(-22,475);ax.set_aspect('equal');ax.axis('off')
        witness=set(hypothesis['witness_channels']) if hypothesis else set()
        occupied=[(p[0]-32,p[0]+32,p[1]-32,p[1]+32) for p in positions.values()]
        occupied += [(positions[i][0]-65,positions[i][0]+65,positions[i][1]-53,positions[i][1]-25) for i in witness]
        for e in view['edges']:
            a,b=positions[e['source']],positions[e['target']];direction=b-a;norm=np.linalg.norm(direction);unit=direction/norm
            flagged=hypothesis is not None and hypothesis['kind']=='association' and hypothesis['index']==e['index']
            ax.add_patch(FancyArrowPatch(a+24*unit,b-28*unit,arrowstyle='-|>',mutation_scale=7,linewidth=1.4 if flagged else .6,
                color='#a95300' if flagged else '#8293a0',linestyle='--' if flagged else '-',connectionstyle='arc3,rad=0.05'))
            options=[]
            for fraction in [.5,.3,.7]:
                for offset in [17,-17,35,-35,52,-52,80,-80]:
                    point=a+fraction*(b-a)+np.array([-unit[1],unit[0]])*offset
                    point=np.clip(point,[105,80],[610,405])
                    bounds=(point[0]-65,point[0]+65,point[1]-16,point[1]+16)
                    collisions=sum(bounds[0]<r[1] and bounds[1]>r[0] and bounds[2]<r[3] and bounds[3]>r[2] for r in occupied)
                    options.append((collisions,abs(offset),abs(fraction-.5),point,bounds))
            _,_,_,midpoint,bounds=min(options,key=lambda item:item[:3]);occupied.append(bounds)
            ax.text(*midpoint,f"→{e['target']:02d} {e['lag']}s",fontsize=8,ha='center',va='center',bbox=dict(facecolor='white',edgecolor='none',alpha=.90,pad=.1))
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
            ax.plot([360,positions[target][0]],[0,positions[target][1]-30],':',color='#333333',lw=.7)
        else:
            position=positions[obs['index']];ax.plot([360,position[0]],[0,position[1]-30],':',color='#333333',lw=.7)
            observed=np.asarray(obs['observed_interval'],float);median=bundle['median'][obs['index']];scale=bundle['scale'][obs['index']]
            quantiles=np.asarray(obs['generated_interval_quantiles'])*scale+median;step=int(np.nanargmax(np.abs(observed*scale+median-quantiles[1])))
            value=float(observed[step]*scale+median);lower,mid,upper=quantiles[:,step]
            ax.text(360,-10,f"C{obs['index']:02d} = {value:.1f} {bundle['units'][obs['index']]} at t{case['stop']-8+step}\nGenerated {mid:.1f} [{lower:.1f}, {upper:.1f}]",ha='center',va='top',fontsize=8)
    fig.subplots_adjust(wspace=.13,bottom=.18,left=.025,right=.99);save(fig,'network',[str(bundle_path.relative_to(ROOT)),bundle['artifact']])

# Four empirical equation panels. The focal nonlinear configuration was fixed in the protocol.
name='synthetic_32_nonlinear';report=reports.get(name);abl_path=ROOT/'results/ablations'/name/'analysis.json'
if report and abl_path.exists():
    ablations=json.loads(abl_path.read_text());fig,axes=plt.subplots(2,2,figsize=(7.16,5.0));axes=axes.ravel();main=report['tracks']['observation']['methods']['proposed']['window_ap']
    rows=[]
    for key,title in [('fixed_penalties','Fixed positive penalties'),('R_only','Gain only'),('no_uncertainty','No spread penalty'),('no_cost','No edit penalty')]:
        rows.append((title,main-report['tracks']['observation']['methods'][key]['window_ap'],report['tracks']['observation']['methods'][key]['paired_main_minus_variant']['interval'],False))
    for key,title in [('deterministic','Deterministic'),('no_graph','No graph'),('no_witness_separation','Visible witnesses'),('no_provenance_deduplication','Count known copies')]:
        if key not in ablations:continue
        result=ablations[key]['metrics']['observation']['paired_main_minus_ablation'];rows.append((title,result['difference'],result['interval'],ablations[key]['scope']=='unsafe diagnostic'))
    for y,(title,difference,interval,unsafe) in enumerate(rows):
        axes[0].plot(difference,y,'s' if unsafe else 'o',color='#a95300' if unsafe else '#0072b2',ms=4)
        if interval:axes[0].plot(interval,[y,y],color='#a95300' if unsafe else '#0072b2',lw=1.2)
    axes[0].set_yticks(range(len(rows)));axes[0].set_yticklabels([r[0] for r in rows]);axes[0].axvline(0,color='#888888',lw=.7);axes[0].invert_yaxis();axes[0].set_xlabel('Main AP minus ablation AP');axes[0].set_title('(a) Paired equation ablations',loc='left')
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
    latency_path=ROOT/'results/latency_scaling.json'
    if latency_path.exists():
        timings=json.loads(latency_path.read_text())['runs']
        for color,dataset in zip(colors,['synthetic_32_nonlinear','synthetic_64_nonlinear']):
            selected=[r for r in timings if r['dataset']==dataset];counts=sorted({r['tested_candidates'] for r in selected})
            medians=[np.median([r['elapsed_seconds'] for r in selected if r['tested_candidates']==count]) for count in counts]
            axes[3].plot(counts,medians,'o-',color=color,ms=3,label=labels[dataset])
        axes[3].legend(frameon=False,fontsize=8)
    axes[3].set(xlabel='Tested hypotheses per window',ylabel='Median seconds per window');axes[3].set_title('(d) Inference cost and candidate count',loc='left')
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

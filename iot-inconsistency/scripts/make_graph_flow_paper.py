"""Generate manuscript tables and a hash-linked numerical claim ledger."""
from pathlib import Path
import hashlib
import json

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
RESULT=ROOT/'results/graph_flow_v1'
OUT=ROOT/'paper/generated/graph_flow'
ORDER=['synthetic_32_linear','synthetic_32_nonlinear','synthetic_64_nonlinear','intel','skab']
LABELS=dict(zip(ORDER,['S32L','S32N','S64N','Intel','SKAB']))
SOURCES={};OUTPUTS={};CLAIMS={}


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def read(relative):
    path=RESULT/relative;SOURCES[str(path.relative_to(ROOT))]=digest(path)
    return json.loads(path.read_text())


def write(name,text):
    path=OUT/name;path.write_text(text+'\n');OUTPUTS[str(path.relative_to(ROOT))]=digest(path)


def number(value,places=3):return '--' if value is None else f'{value:.{places}f}'


def scientific(value):
    if value==0:return '0'
    mantissa,exponent=f'{value:.2e}'.split('e')
    return r'$'+mantissa+r'\times10^{'+str(int(exponent))+'}$'


def interval(item):return f"{item['macro_ap_difference']:+.3f} [{item['interval'][0]:+.3f}, {item['interval'][1]:+.3f}]"


def table(name,caption,label,columns,head,rows,wide=False):
    env='table*' if wide else 'table'
    text='\\begin{'+env+'}[t]\n\\centering\n\\caption{'+caption+'}\n\\label{'+label+'}\n\\small\n'
    text+='\\begin{tabular}{'+columns+'}\n\\toprule\n'+' & '.join(head)+r' \\'+'\n\\midrule\n'
    text+='\n'.join(' & '.join(map(str,row))+r' \\' for row in rows)
    text+='\n\\bottomrule\n\\end{tabular}\n\\end{'+env+'}'
    write(name,text)


def macro(report,method):
    values=[report['datasets'][d]['methods'][method]['average_precision'] for d in ORDER]
    return float(np.mean([np.mean(values[:3]),values[3],values[4]]))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report=read('analysis.json');lock=read('protocol_lock.json');audit=read('production_equation_audit.json')
    runtime=read('runtime.json');robust=read('robustness.json');pilot=read('pilot.json');data=read('data_manifest.json')
    compared=report['paired_macro_comparisons'];datasets=report['datasets']
    methods=[('flow_ratio','Flow + corruption'),('pca','PCA residual'),('flow_nll','Same-flow NLL'),
             ('ppca','Graph PPCA + corruption'),('mixture_ppca','Mixture PPCA + corruption'),('all_ppca','All-channel PPCA + corruption'),
             ('ganf','Official GANF'),('supervised','Supervised trees'),('legacy_witness','Legacy diffusion witness'),
             ('legacy_gdn','GDN residual'),('legacy_backbone','Diffusion residual'),('legacy_diffad','DiffAD adaptation')]
    rows=[]
    for method,label in methods:
        if method not in datasets['skab']['methods']:continue
        rows.append([label]+[number(datasets[d]['methods'][method]['average_precision']) for d in ORDER]+[number(macro(report,method))])
    table('ap_table.tex','Sensor-interval average precision over the full candidate population. The synthetic configurations form one family in the macro-average. All methods use identical cases and complete-target eligibility.','tab:ap','lrrrrrr',['Method']+[LABELS[d] for d in ORDER]+['Macro'],rows,True)
    rows=[]
    for d in ORDER:
        r=datasets[d];v=lock['choices'][d]['models']['selected']['training_volume']
        rows.append([LABELS[d],str(data['datasets'][d]['splits']['test']['channels']),str(v['source_blocks'])+'/'+str(r['source_blocks']),
                     f"{r['cases']}",f"{r['candidates']:,}",str(r['fault_candidates']),f"{100*r['eligible_fraction']:.1f}\\%"])
    table('data_table.tex','Evaluated populations. Blocks show training and final source blocks. Eligibility is complete availability of the eight target observations. Missing targets remain in the primary population.','tab:data','lrrrrrr',['Config.','$C$','Blocks','Cases','Candidates','Faults','Eligible'],rows,True)
    table('contrasts.tex','Paired family-macro AP differences. Primary contrasts use 97.5\% individual block-bootstrap intervals for simultaneous 95\% coverage. Other intervals are descriptive 95\% intervals.','tab:contrasts','lr',['Comparator','Ratio minus comparator [interval]'],
          [[label,interval(compared[key])] for key,label in [('pca','PCA'),('flow_nll','Same-flow NLL'),('ppca','PPCA + same corruption'),('mixture_ppca','Mixture PPCA'),('flow_plugin','Deterministic plug-in'),('own_history','Own history')]])
    rows=[]
    for d in ORDER:
        r=datasets[d]['methods']['flow_ratio'];policy=r['repair']['policy'];alarm=r['window_alarms']['0.1']
        rows.append([LABELS[d],number(r['confidence']['brier']),number(r['confidence']['log_loss']),number(r['minimum_window_p']),
          f"{alarm['false_alarms']}/{alarm['normal_windows']}",number(alarm['recall']),str(policy['accepted']),
          '--' if policy['risk'] is None else f"{policy['failures']}/{policy['accepted']}",str(policy['harmful'])])
    table('confidence_table.tex','Flow ratio confidence and selected repair policy on final cases. Alarms use the separately calibrated window maximum at level 0.10. Repair counts cover all evaluation cases. A dash denotes undefined risk because no action was accepted.','tab:confidence','lrrrrrrrr',
          ['Config.','Brier','Log loss','Min. $p$','False alarms','Recall','Repairs','Failed','Harmful'],rows,True)
    rows=[]
    for d in ORDER:
        for method,label in [('flow','Flow'),('ppca','PPCA')]:
            r=datasets[d]['repair_distributions'][method]
            rows.append([LABELS[d],label,number(r['crps']),number(r['interval_coverage']),number(r['interval_width']),number(r['energy_score'])])
    table('repair_table.tex','Oracle-target repair distributions on eligible injected faults. Width and scores use training-normalized measurement units. Interval coverage is measured for nominal 90\% marginal intervals. Lower CRPS and energy score are better.','tab:repair','llrrrr',
          ['Config.','Prior','CRPS','Coverage','Width','Energy'],rows)
    rows=[]
    for d in ORDER:
        r=lock['choices'][d];fits=r['members']['members'];t=runtime[d]
        rows.append([LABELS[d],number(fits[0]['parameters']/1000,1),str(fits[0]['training_volume']['candidates']),str(t['draws']),
          number(t['methods']['flow_ratio_and_repair']['median_seconds']*1000,1)])
    table('runtime_table.tex','Selected model size, training intervals and operational latency on the RTX PRO 4500. Times are medians of seven warm full-window calls including repair summaries. Loading and offline truth metrics are excluded.','tab:runtime','lrrrr',
          ['Config.','Params (k)','Train $N$','$M$','Ratio (ms)'],rows)
    rows=[]
    for d in ORDER:
        r=datasets[d]['methods'];rows.append([LABELS[d]]+[number(r[m]['localization']['top1']) for m in ('flow_ratio','pca','flow_nll','ppca')]+[str(r['flow_ratio']['localization']['unscorable_fault_windows'])])
    table('localization.tex','Top-one localization among windows with a changed observed target. Unscorable faults remain misses.','tab:localization','lrrrrr',['Config.','Ratio','PCA','NLL','PPCA','Misses'],rows)
    rows=[]
    for d in ORDER:
        r=datasets[d]['methods'];rows.append([LABELS[d]]+[number(r['flow_ratio']['strata'][s]['average_precision'])+'/'+number(r['pca']['strata'][s]['average_precision']) for s in ('known','heldout')])
    table('strata.tex','Known and held-out fault families, each pooled with clean windows. Entries give flow-ratio AP / PCA AP. Held-out mechanisms were absent from channel modeling and classifier development.','tab:strata','lrr',['Config.','Known','Held out'],rows)
    rows=[]
    for d in ORDER:
        r=robust[d]
        rows.append([LABELS[d]]+[number(r[k]['methods']['flow_ratio']['primary_top1']) for k in ('single_source','missing_context_0.5','multiple_sources_0.5')]+
                    [number(r['graph_error_0.5']['methods']['flow_ratio']['window_alarm_fraction_at_010'])])
    table('stress_table.tex','Registered stress diagnostics on twelve source windows per configuration. First three columns give primary-target top-one rates. The last gives measurement alarms under a graph-only error affecting half the stored associations. This is cross-type confusion, not association diagnosis.','tab:stress','lrrrr',
          ['Config.','Single','Half missing','Half faulty','Graph alarm'],rows)
    rows=[]
    for key,label in [('flow_ratio','Integrated ratio'),('flow_nll','Ordinary NLL'),('flow_plugin','Mean plug-in'),('flow_single','Single trained model'),
                       ('mean_member_ratios','Mean member log ratios'),('without_bias','Without bias channel'),('without_drift','Without drift channel'),
                       ('without_noise','Without noise channel'),('without_stuck','Without stuck channel'),('own_history','Own history')]:
        rows.append([label]+[number(datasets[d]['methods'][key]['average_precision']) for d in ORDER]+[number(macro(report,key))])
    table('ablations.tex','Predeclared equation ablations. Every variant retains the same candidate population. Single-model performance is one member, not an independent ensemble repetition.','tab:ablations','lrrrrrr',
          ['Variant']+[LABELS[d] for d in ORDER]+['Macro'],rows,True)
    scalar={
      'MacroRatioAP':number(macro(report,'flow_ratio')),'MacroPCAAP':number(macro(report,'pca')),'MacroNLLAP':number(macro(report,'flow_nll')),
      'PCADifference':number(compared['pca']['macro_ap_difference']),'NLLDifference':number(compared['flow_nll']['macro_ap_difference']),
      'PPCADifference':number(compared['ppca']['macro_ap_difference']),
      'TotalCases':f"{sum(d['cases'] for d in datasets.values()):,}",'TotalCandidates':f"{sum(d['candidates'] for d in datasets.values()):,}",
      'AuditCandidates':f"{audit['compact_candidate_scores_recomputed']:,}",'AuditMaximum':scientific(audit['compact_max_error']),
      'PilotTime':number(pilot['training_seconds'],2),'PilotInitial':number(pilot['initial_validation_nll'],3),
      'PilotFinal':number(pilot['final_validation_nll'],3),'PilotInverse':scientific(pilot['inverse_max_absolute_error']),
      'IntelEligibility':number(100*datasets['intel']['eligible_fraction'],1),'IntelMisses':str(datasets['intel']['unscorable_fault_candidates'])}
    replay=[r for r in audit['full_generation_and_density_replays'] if r.get('candidates',0)>0]
    for key,field in [('ReplayDensity','normal_density_max_error'),('ReplayGeneration','generated_max_error'),('ReplayCorruption','corruption_density_max_error'),
                      ('ReplayRatio','ratio_max_error'),('ReplayPosterior','repair_mean_max_error'),('ReplayJacobian','autograd_logdet_error')]:
        scalar[key]=scientific(max(r[field] for r in replay))
    scalar['ReplayBundles']=str(len(replay))
    write('numbers.tex','\n'.join('\\newcommand{\\'+k+'}{'+v+'}' for k,v in scalar.items()))
    # This prose is tied to the locked result, and checks its qualitative premises.
    assert report['h1_supported'] and not report['h2_supported']
    assert compared['flow_nll']['macro_ap_difference']<.02
    assert all(datasets[d]['methods']['supervised']['average_precision']>datasets[d]['methods']['flow_ratio']['average_precision'] for d in ORDER)
    write('abstract_results.tex',
      f"The ratio improves the three-family mean AP by {compared['pca']['macro_ap_difference']:.3f} over PCA and {compared['flow_nll']['macro_ap_difference']:.3f} over same-flow likelihood, with both paired primary intervals above zero. "
      "The latter misses the declared 0.02 usefulness margin. Neural benefit over matched PPCA and benefit from integration over a mean replacement remain inconclusive. Supervised trees perform better, and real-data alarm and repair failures limit operational claims.")
    write('primary_results.tex',
      f"The locked evaluation contains {scalar['TotalCases']} cases and {scalar['TotalCandidates']} candidate intervals. Family-macro AP is {scalar['MacroRatioAP']} for the ratio, {scalar['MacroPCAAP']} for PCA and {scalar['MacroNLLAP']} for same-flow NLL. "
      f"The paired differences are {interval(compared['pca'])} against PCA and {interval(compared['flow_nll'])} against NLL. Both simultaneous primary intervals are positive, supporting the directional H1 for this defined protocol. The NLL contrast is smaller than the chosen 0.02 practical margin.\n\n"
      "This aggregate does not imply improvement in every environment. PCA is stronger on both 32-channel synthetic settings, with negative paired intervals for the ratio. The ratio improves on PCA in S64N and the two real families. SKAB contributes most of the macro difference. Intel remains weak in absolute terms despite its positive comparison. "
      f"Only {scalar['IntelEligibility']}\\% of Intel target blocks are eligible, and {scalar['IntelMisses']} changed targets remain unscorable misses.\n\n"
      f"The matched PPCA comparison is {interval(compared['ppca'])}. Its interval spans zero, so H2 is inconclusive. The mixture-PPCA interval also spans zero. The conditional Gaussian control is particularly strong in the linear configuration. "
      f"Supervised trees exceed the ratio in every configuration. Their macro advantage is {-compared['supervised']['macro_ap_difference']:.3f}, and the paired ratio-minus-tree interval is [{compared['supervised']['interval'][0]:+.3f}, {compared['supervised']['interval'][1]:+.3f}]. Thus the results do not establish the ratio as the strongest available detector when labeled injection mechanisms can be exploited. "
      "The author GANF and rerun legacy methods provide additional comparisons in Table~\\ref{tab:ap}. "
      f"Top-one ratio attribution is {datasets['synthetic_32_nonlinear']['methods']['flow_ratio']['localization']['top1']:.3f} on S32N, {datasets['intel']['methods']['flow_ratio']['localization']['top1']:.3f} on Intel and {datasets['skab']['methods']['flow_ratio']['localization']['top1']:.3f} on SKAB. "
      "Held-out mechanisms substantially reduce AP (Table~\\ref{tab:strata}).")
    skab=datasets['skab']['methods']['flow_ratio'];intel=datasets['intel']['methods']['flow_ratio']
    risk=skab['repair']['policy'];ci=skab['repair']['repair_risk_interval_95'];s64=datasets['synthetic_64_nonlinear']['methods']
    write('confidence_results.tex',
      "Confidence is not uniformly reliable. The ratio has lower Brier score than PCA in all synthetic configurations and SKAB, but a much worse Intel Brier score. "
      f"Intel gives {intel['confidence']['brier']:.3f} with block interval [{intel['confidence']['brier_interval_95'][0]:.3f}, {intel['confidence']['brier_interval_95'][1]:.3f}], compared with PCA's {datasets['intel']['methods']['pca']['confidence']['brier']:.3f}. "
      f"Its smallest attainable window p-value is {intel['minimum_window_p']:.3f}, so neither a 1\\% nor a 5\\% alarm level is representable. At level 0.10, {intel['window_alarms']['0.1']['false_alarms']} of {intel['window_alarms']['0.1']['normal_windows']} unchanged Intel cases alarm. The ratio's relative AP gain therefore does not establish a usable Intel alarm system. Normal cases include injection attempts that changed no observed coordinate.\n\n"
      "The flow policy accepts useful synthetic repairs with no observed failures, but generally has lower coverage than PPCA. In S64N it accepts "
      f"{s64['flow_ratio']['repair']['policy']['accepted']} of {datasets['synthetic_64_nonlinear']['cases']} cases, versus no PCA recommendation and {s64['ppca']['repair']['policy']['accepted']} PPCA recommendations. "
      "Zero observed failures do not imply zero population risk, especially with dependent blocks. Intel accepts no repair and has undefined recommendation risk.\n\n"
      f"On SKAB the ratio accepts {risk['accepted']} repairs and makes {risk['failures']} failed recommendations, all harmful. Actual risk is {risk['risk']:.3f}, with a wide block interval [{ci[0]:.3f}, {ci[1]:.3f}], exceeding the calibration target in point estimate. "
      f"PCA and PPCA risks are {datasets['skab']['methods']['pca']['repair']['policy']['risk']:.3f} and {datasets['skab']['methods']['ppca']['repair']['policy']['risk']:.3f}. "
      "H3 is not established as a general controlled-risk coverage advantage. Table~\\ref{tab:repair} further shows that matched PPCA has lower repair CRPS and energy score in every configuration. Flow interval widths do not buy reliable real-data coverage. Figure~\\ref{fig:repair} retains both successful and failed cases. Probability calibration concerns the designed injection prevalence, not operational physical-failure probabilities.")
    native=read('skab/robustness/native_process.json')
    sampling={d:read('development/'+d+'_sampling.json') for d in ORDER}
    rows=read('synthetic_32_nonlinear/robustness/cases.json')
    graph_rows=[r for r in rows if r['condition']=='graph_error_0.5']
    ambiguity=read('synthetic_32_nonlinear/robustness/ambiguity.json')
    write('ablation_results.tex',
      f"Integrated generation improves macro AP over the prior-mean plug-in by {compared['flow_plugin']['macro_ap_difference']:.3f}, with interval [{compared['flow_plugin']['interval'][0]:+.3f}, {compared['flow_plugin']['interval'][1]:+.3f}]. This does not demonstrate that integration is needed for the measured detection gain. "
      f"Graph context improves over own history by {compared['own_history']['macro_ap_difference']:.3f} [{compared['own_history']['interval'][0]:+.3f}, {compared['own_history']['interval'][1]:+.3f}]. "
      f"Family-macro AP is {macro(report,'flow_single'):.3f} for a single member and {macro(report,'mean_member_ratios'):.3f} when member log ratios are averaged instead of mixing densities. "
      "All leave-one-corruption-channel-out results remain saved without selecting a new fault prior after testing. Scale sensitivity is retained from development.\n\n"
      f"Sampling error remains visible. At 2048 draws per member, the SKAB 95th percentile repeated-seed score change is {sampling['skab']['repeatability'][-1]['repeat_absolute_difference_p95']:.3f}. The maximum tested budget is a finite reference, not exact integration. "
      "Low-ESS cases remain detection outcomes and become recommendation abstentions. Missing support changes attribution in Table~\\ref{tab:stress}. With multiple true faults, a lower original-target top-one rate alone does not mean an incorrect fault was chosen. "
      f"For S32N with half the other sources corrupted, pooled AP over all true targets is {robust['synthetic_32_nonlinear']['multiple_sources_0.5']['methods']['flow_ratio']['candidate_ap']:.3f}, at the changed fault prevalence. "
      "Known-copy canonicalization gives exactly unchanged scores on every registered copy case.\n\n"
      f"The separate association diagnostic uses direct residuals. On the twelve S32N cases with half the graph associations changed, mean edge-localization AP is {np.mean([r['association_localization_ap'] for r in graph_rows]):.3f}. "
      "Reading and association alarms can both fire or both remain silent. Their full cross-type counts are saved, and a reading ratio is never treated as proof that an edge is false. "
      f"The synthetic physical-change counterexample produces identical observations for both explanations; {sum(r['flow_window_p']<=.1 for r in ambiguity)} of {len(ambiguity)} S32N physical-change cases trigger the reading alarm at 0.10. "
      f"The separate native SKAB task contains {native['cases']} windows, including {native['native_event_windows']} process-event windows. Window AP is {native['methods']['flow_ratio']['window_ap']:.3f} for the ratio, {native['methods']['flow_nll']['window_ap']:.3f} for NLL and {native['methods']['pca']['window_ap']:.3f} for PCA. These are process detections and do not validate sensor-fault diagnoses.")
    fits={}
    def collect(obj):
        if isinstance(obj,dict):
            if str(obj.get('path','')).endswith('.pt') and 'training_seconds' in obj:fits[obj['path']]=obj
            for value in obj.values():collect(value)
        elif isinstance(obj,list):
            for value in obj:collect(value)
    for p in sorted((RESULT/'development').glob('*.json')):collect(read('development/'+p.name))
    all_seconds=sum(v['training_seconds'] for v in fits.values())+pilot['training_seconds']
    gpu_peaks=[v['peak_gpu_bytes'] for v in fits.values()]+[pilot['peak_gpu_bytes']]
    selected=[c['models']['selected']['parameters'] for c in lock['choices'].values()]
    ganf_residuals=[r['history'][r['selected_outer']-1]['acyclicity'] for c in lock['choices'].values() for r in c['ganf']['members']]
    write('runtime_results.tex',
      f"The bounded study completed {len(fits)+1} distinct neural fits including the Gaussian pilot. Their recorded fitting time sums to {all_seconds/60:.1f} minutes, excluding data preparation, Gaussian fitting, scoring and evaluation. "
      f"The selected flows have {min(selected):,} to {max(selected):,} parameters per member. Peak allocation over the registered neural fits is {max(gpu_peaks)/1024**3:.2f} GiB. "
      f"Selected GANF acyclicity residuals range from {min(ganf_residuals):.3g} to {max(ganf_residuals):.3g}, documenting incomplete graph convergence within the finite budget. "
      f"Training the selected three flow members takes {min(sum(f['training_seconds'] for f in c['members']['members']) for c in lock['choices'].values()):.1f} to {max(sum(f['training_seconds'] for f in c['members']['members']) for c in lock['choices'].values()):.1f} seconds per configuration. "
      f"Same-flow NLL takes {min(runtime[d]['methods']['same_flow_nll']['median_seconds']*1000 for d in ORDER):.1f} to {max(runtime[d]['methods']['same_flow_nll']['median_seconds']*1000 for d in ORDER):.1f} milliseconds per window, compared with {min(runtime[d]['methods']['pca']['median_seconds']*1000 for d in ORDER):.2f} to {max(runtime[d]['methods']['pca']['median_seconds']*1000 for d in ORDER):.2f} for PCA. "
      "Table~\\ref{tab:runtime} reports isolated operational wall times, including conditional repair summaries and returned evidence transfer. PCA and PPCA execute on the CPU. Float32 neural computation and float64 score arithmetic are used without mixed precision. The initial independent replay mistakenly retained float32 in a SciPy ensemble reduction. Explicit promotion corrected that audit without changing predictions, models or the protocol lock. The failed audit and correction are preserved.")
    interface=read('graph/interface/browser_verification.json');persistence=read('graph/persistence_audit.json')
    assert persistence['idempotent']
    write('interface_results.tex',
      f"The saved interface collection contains {interface['case_count']} cases, including first correct and incorrect attributions, inadequate sampling, constructed ambiguity and separate association review. "
      "Repeated Neo4j export leaves entity counts unchanged. Automated browser checks exercise evidence loading, node and edge selection, actual generated curves, hidden-by-default evaluation truth, artifact download, accept/reject/defer persistence and preservation of the observation. These checks are interface verification, not a human operator experiment.")
    write('discussion_results.tex',
      "The positive primary contrast, driven mainly by SKAB, is narrower than a general neural-generation claim. The same-flow gain is small, and the PPCA and mean-plug-in controls leave its mechanism unresolved. Stronger supervised performance shows the value of explicit fault information outside a generative model. Repair and calibration are stricter tests than ranking alone. Intel abstention does not convert missed faults into successful detections, and SKAB repair risk exceeds the target in point estimate. The evidence supports further testing of operator review under declared assumptions.")
    write('conclusion_results.tex',
      "GPU-generated reference trajectories support an executable chain from normalized fault comparison to weighted repair and graph evidence. The frozen study supports directional H1 with a small score-specific gain. Neural necessity, integration benefit and controlled repair risk remain unestablished. Supervised performance, poor Intel confidence, held-out faults and context ambiguity define the next questions rather than being excluded from the evidence.")
    CLAIMS['reported_macros']=scalar
    CLAIMS['primary_hypotheses']={k:compared[k] for k in ('pca','flow_nll','ppca')}
    CLAIMS['scope']=dict(primary='All declared sensor intervals',three_families=True,real_recordings_previously_examined=True,
                        empirical_inputs='analysis.json, protocol_lock.json, runtime.json, production_equation_audit.json and robustness.json')
    CLAIMS['resource_totals']=dict(distinct_neural_fits=len(fits)+1,neural_training_seconds=all_seconds,peak_training_gpu_bytes=max(gpu_peaks))
    (RESULT/'paper_claims.json').write_text(json.dumps(dict(inputs=SOURCES,outputs=OUTPUTS,claims=CLAIMS,
        interpretation='Generated values trace to complete immutable source records. Tables use their named dataset/method keys; no value is invented or manually rounded from a chart.'),indent=2)+'\n')
    print(json.dumps(dict(macros=scalar,h1_supported=report['h1_supported'],h2_supported=report['h2_supported']),indent=2))


if __name__=='__main__':main()

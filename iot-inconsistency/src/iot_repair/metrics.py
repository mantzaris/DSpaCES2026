"""Metrics preserve window, candidate, source-block and label distinctions."""
from __future__ import annotations
import numpy as np
from sklearn.metrics import average_precision_score,roc_auc_score,brier_score_loss,log_loss
FLOOR=-1e12


def ap(y,s):
    y=np.asarray(y);s=np.asarray(s)
    return float(average_precision_score(y,s)) if y.any() else None


def candidate_score(record,method,kappa=1.,edit_weight=.2):
    r,u,c=record['mean_gain'],record['model_instability'],record['edit_cost']
    if method=='fixed_penalties':return r-u-.2*c
    if method=='R_only':return r
    if method=='no_uncertainty':return r-edit_weight*c
    if method=='no_cost':return r-kappa*u
    return r-kappa*u-edit_weight*c


def scores_for(case,method,kind,parameters):
    count=len(case[kind+'_truth']);scores=np.full(count,FLOOR);support=np.zeros(count,dtype=int)
    if method in ('proposed','fixed_penalties','R_only','no_uncertainty','no_cost','supervised_terms'):
        for row in case['records']:
            if row['kind']!=kind:continue
            support[row['index']]=row['support_count']
            if row['support_count']<2:continue
            if method=='supervised_terms':
                p=parameters['supervised_terms'][kind];f=(np.array([row['mean_gain'],row['model_instability'],row['edit_cost']])-p['mean'])/p['scale']
                score=float(f@np.array(p['coefficient'])+p['intercept'])
            else:score=candidate_score(row,method,parameters['kappa'],parameters['lambda'])
            scores[row['index']]=score
    elif method=='edge_residual':scores=np.nan_to_num(np.asarray(case['edge_residuals'],dtype=float),nan=FLOOR)
    elif kind=='observation':
        scores=np.nan_to_num(np.asarray(case['baseline_sensor_scores'][method],dtype=float),nan=FLOOR);support[:]=2
    else:raise ValueError('Unsupported association output')
    return scores,support


def task_cases(cases,kind):
    return [case for case in cases if case['track'] in ('clean',kind) and
            (case['track']=='clean' or case['fault']['status']=='injected')]


def selected_pool(case,kind,count):
    mask=np.zeros(count,dtype=bool)
    for candidate_kind,index in case['candidates']:
        if candidate_kind==kind:mask[index]=True
    return mask


def paired_ap_interval(y,a,b,blocks,repetitions=1000,seed=9026):
    y=np.array(y);a=np.array(a);b=np.array(b);blocks=np.array(blocks);units=np.unique(blocks)
    if len(units)<2:return dict(difference=ap(y,a)-ap(y,b),interval=None,blocks=len(units))
    rng=np.random.default_rng(seed);values=[]
    for _ in range(repetitions):
        index=np.concatenate([np.flatnonzero(blocks==unit) for unit in rng.choice(units,len(units),replace=True)])
        if len(np.unique(y[index]))<2:continue
        values.append(ap(y[index],a[index])-ap(y[index],b[index]))
    return dict(difference=ap(y,a)-ap(y,b),interval=np.quantile(values,[.025,.975]).tolist(),blocks=len(units),replicates=len(values))


def summarize(cases,method,kind,parameters,reference=None,alphas=(.01,.05,.1)):
    from .calibration import null_tail_value
    selected=task_cases(cases,kind);ys=[];zs=[];cy=[];cs=[];top1=[];top3=[];rr=[];covered=[];screen=[];groups=[]
    records=[];review_scores=[];review_truth=[];review_pool_count=0
    for case in selected:
        truth=np.array(case[kind+'_truth'],bool);scores,support=scores_for(case,method,kind,parameters)
        eligible=scores>FLOOR;best=int(np.argmax(scores)) if len(scores) else -1;z=float(scores.max()) if len(scores) else FLOOR
        y=int(truth.any());ys.append(y);zs.append(z);groups.append(case['block']);cy.extend(truth.tolist());cs.extend(scores.tolist())
        covered.append(bool(eligible.any()))
        pool=selected_pool(case,kind,len(scores)) if 'candidates' in case else np.ones(len(scores),bool)
        review_pool_count+=int(pool.sum())
        review_scores.extend(scores[eligible&pool]);review_truth.extend(truth[eligible&pool])
        if y:
            order=np.argsort(-scores,kind='stable');hits=truth[order]&eligible[order]
            top1.append(bool(hits[:1].any()));top3.append(bool(hits[:3].any()));rr.append(1/(int(np.flatnonzero(hits)[0])+1) if hits.any() else 0.)
            screen.append(bool(np.any(truth&eligible)))
        records.append(dict(id=case['id'],block=case['block'],y=y,score=z,best_index=best,
            attribution_correct=bool(truth[best]) if best>=0 and eligible[best] else False,eligible=bool(eligible.any()),
            fault_family=case['fault']['family'],duration=case['fault'].get('duration'),strength=case['fault'].get('strength')))
    y=np.array(ys);z=np.array(zs)
    report=dict(window_ap=ap(y,z),candidate_ap=ap(cy,cs),prevalence=float(y.mean()),windows=len(y),source_blocks=len(set(groups)),
        top1=float(np.mean(top1)) if top1 else None,top3=float(np.mean(top3)) if top3 else None,mrr=float(np.mean(rr)) if rr else None,
        screening_recall=float(np.mean(screen)) if screen else None,coverage=float(np.mean(covered)),decisions=records)
    if reference is not None:
        p=null_tail_value(reference,z)
        report['null_reference_units']=len(reference);report['null_resolution']=1/(len(reference)+1)
        report['operating_points']=[dict(alpha=alpha,fpr=float((p[y==0]<=alpha).mean()),recall=float((p[y==1]<=alpha).mean()),
            precision=float(y[p<=alpha].mean()) if (p<=alpha).any() else None,
            f1=float(2*((p<=alpha)&(y==1)).sum()/max(1,(p<=alpha).sum()+(y==1).sum()))) for alpha in alphas]
        for row,tail in zip(records,p):row['window_null_tail']=float(tail)
    # Risk is wrong attribution among all reviewed windows, including clean ones.
    order=np.argsort(-z,kind='stable');curve=[]
    for coverage in (.1,.25,.5,1.):
        k=max(1,int(np.ceil(len(order)*coverage)));ix=order[:k]
        precision=np.mean([records[i]['attribution_correct'] for i in ix])
        curve.append(dict(coverage=k/len(order),precision=float(precision),risk=float(1-precision),reviewed=k))
    report['risk_coverage']=curve
    order=np.argsort(-np.asarray(review_scores),kind='stable');candidate_curve=[]
    for coverage in (.1,.25,.5,1.):
        k=min(len(order),max(1,int(np.ceil(review_pool_count*coverage))))
        if not k:continue
        precision=float(np.mean(np.asarray(review_truth)[order[:k]]))
        candidate_curve.append(dict(coverage=k/max(1,review_pool_count),precision=precision,risk=1-precision,accepted=k,pool=review_pool_count))
    report['candidate_risk_coverage']=candidate_curve
    return report

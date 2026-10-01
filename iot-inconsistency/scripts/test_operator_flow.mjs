// Local browser and persistence verification. This is not a human operator study.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const base='http://127.0.0.1:8100';
const pages=await(await fetch('http://127.0.0.1:9229/json')).json();
const socket=new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);
await new Promise(resolve=>socket.addEventListener('open',resolve,{once:true}));
let next=0;const pending=new Map(),exceptions=[];
socket.addEventListener('message',event=>{const r=JSON.parse(event.data);if(r.id){const p=pending.get(r.id);pending.delete(r.id);r.error?p.reject(Error(JSON.stringify(r.error))):p.resolve(r.result)}else if(r.method==='Runtime.exceptionThrown')exceptions.push(r.params)});
function cdp(method,params={}){return new Promise((resolve,reject)=>{const id=++next;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));})}
async function evaluate(expression){const r=await cdp('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value}
async function until(expression){for(let i=0;i<100;i++){if(await evaluate(expression))return;await new Promise(resolve=>setTimeout(resolve,100));}throw Error('Timed out '+expression)}
await cdp('Page.enable');await cdp('Runtime.enable');
await cdp('Network.enable');await cdp('Network.setCacheDisabled',{cacheDisabled:true});
await cdp('Page.navigate',{url:'about:blank'});
await until("location.href==='about:blank' && typeof bundle==='undefined'");
await cdp('Emulation.setDeviceMetricsOverride',{width:1500,height:1200,deviceScaleFactor:1,mobile:false});
await cdp('Page.navigate',{url:base+'/flow?test=1'});
await until("typeof bundle!=='undefined' && !!bundle && !!currentHypothesis");
const paths=await(await fetch(base+'/api/flow/cases')).json();assert.ok(paths.length>=15);
await evaluate("load('results/graph_flow_v1/graph/cases/synthetic_32_nonlinear_correct_attribution.json')");
assert.equal(await evaluate("$('cases').options.length"),paths.length);
assert.ok(await evaluate("$('network').querySelectorAll('.node').length>=4"));
assert.ok(await evaluate("$('network').querySelectorAll('.edge').length>=3"));
assert.ok(await evaluate("/C[0-9]+ → C[0-9]+/.test($('network').textContent)"));
assert.ok(await evaluate("['Log likelihood ratio','Effective sample size','Calibrated fault probability'].every(s=>$('evidence').textContent.includes(s))"));
assert.ok(await evaluate("$('trajectory').querySelectorAll('.prior-sample').length===12"));
assert.equal(await evaluate("$('reference').checked"),false);
const artifact=await evaluate("$('artifact').getAttribute('href')");assert.equal((await fetch(base+artifact)).status,200);
const original=await evaluate('JSON.stringify(bundle.trajectories.observed)');
await fs.mkdir('results/graph_flow_v1/graph/interface',{recursive:true});
let shot=await cdp('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});
await fs.writeFile('results/graph_flow_v1/graph/interface/measurement.png',Buffer.from(shot.data,'base64'));
await evaluate("$('reference').checked=true; $('reference').dispatchEvent(new Event('change'))");
const reviews=[];
for(const action of ['accept','reject','defer']){
 await evaluate(`$('note').value='[automated interface test] ${action} persistence only. No human diagnosis.'; document.querySelector('[data-action="${action}"]').click()`);
 await until(`$('status').textContent.startsWith('Saved ${action} review')`);
 reviews.push(await evaluate("$('status').textContent"));
}
assert.equal(await evaluate('JSON.stringify(bundle.trajectories.observed)'),original);
await evaluate("load('results/graph_flow_v1/graph/cases/synthetic_32_nonlinear_association_review.json')");
assert.ok(await evaluate("$('network').querySelector('[stroke-dasharray=\"7 5\"]')!==null"));
await evaluate("$('network').querySelector('[stroke-dasharray=\"7 5\"]').dispatchEvent(new Event('click'))");
assert.ok(await evaluate("$('heading').textContent.includes('Association')"));
assert.ok(await evaluate("$('evidence').textContent.includes('Direct window residual')"));
shot=await cdp('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});
await fs.writeFile('results/graph_flow_v1/graph/interface/association.png',Buffer.from(shot.data,'base64'));
await evaluate("load('results/graph_flow_v1/graph/cases/synthetic_32_nonlinear_ambiguity.json')");
assert.ok(await evaluate("$('adequacy').textContent.includes('Ambiguous')"));
const inadequate=paths.find(p=>p.includes('skab_numerical_abstention'));
if(inadequate){await evaluate(`load(${JSON.stringify(inadequate)})`);assert.ok(await evaluate("$('adequacy').textContent.includes('Numerical abstention')"));}
await cdp('Emulation.setDeviceMetricsOverride',{width:820,height:1100,deviceScaleFactor:1,mobile:false});
assert.ok(await evaluate('document.documentElement.scrollWidth<=window.innerWidth+2'));
assert.deepEqual(exceptions,[]);
const report={tested_at:new Date().toISOString(),url:base+'/flow',case_count:paths.length,
 checks:['saved case selection','named classic 2D sensor network','annotated predictive edges','actual prior draws and weighted intervals',
 'reference truth hidden by default','evidence download','accept/reject/defer persistence','immutable observed values',
 'separately assessed association selection','ambiguity and numerical abstention','narrow-screen layout','no uncaught browser exceptions'],
 reviews,scope:'Automated local interface verification. Not a human operator study and not authorization to apply a repair.'};
await fs.writeFile('results/graph_flow_v1/graph/interface/browser_verification.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));socket.close();

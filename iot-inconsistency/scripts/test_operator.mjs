// Browser verification against the local, saved-evidence operator application.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const base='http://127.0.0.1:8099';
const pages=await (await fetch('http://127.0.0.1:9229/json')).json();
const socket=new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);
await new Promise(resolve=>socket.addEventListener('open',resolve,{once:true}));
let next=0;const pending=new Map();const exceptions=[];
socket.addEventListener('message',event=>{const r=JSON.parse(event.data);if(r.id){const p=pending.get(r.id);pending.delete(r.id);r.error?p.reject(Error(JSON.stringify(r.error))):p.resolve(r.result)}else if(r.method==='Runtime.exceptionThrown')exceptions.push(r.params)});
function cdp(method,params={}){return new Promise((resolve,reject)=>{const id=++next;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));})}
async function evaluate(expression){const r=await cdp('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value}
async function until(expression){for(let i=0;i<100;i++){if(await evaluate(expression))return;await new Promise(resolve=>setTimeout(resolve,100));}throw Error('Timed out '+expression)}
await cdp('Page.enable');await cdp('Runtime.enable');
await cdp('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false});
await cdp('Page.navigate',{url:base});
await until("typeof bundle!=='undefined' && !!bundle && !!current");
assert.equal(await evaluate("$('caseSelect').options.length"),10);
await evaluate("load('results/graph/synthetic_32_nonlinear_illustration.json')");
assert.ok(await evaluate("['Mean gain R','Selected score S','Candidate null-tail value','Saved evidence'].every(x=>$('evidence').textContent.includes(x))"));
assert.ok(await evaluate("$('network').querySelectorAll('.node').length>=8"));
assert.ok(await evaluate("$('network').querySelectorAll('.edge').length>=7"));
assert.ok(await evaluate("$('values').textContent.includes('Unchanged witness predictions')"));
const rawLink=await evaluate("$('evidence').querySelector('a').getAttribute('href')");assert.equal((await fetch(base+rawLink)).status,200);
await fs.mkdir('results/interface',{recursive:true});
let shot=await cdp('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});await fs.writeFile('results/interface/operator_observation.png',Buffer.from(shot.data,'base64'));
await evaluate("selectHypothesis(bundle.hypotheses.find(h=>h.kind==='association'))");
assert.ok(await evaluate("$('network').querySelector('.edge[stroke-dasharray=\"8 5\"]')!==null"));
assert.ok(await evaluate("$('values').querySelectorAll('table').length>=2"));
const before=await evaluate("$('network').querySelectorAll('.node').length");
await evaluate("$('focus').value='local'; $('focus').dispatchEvent(new Event('change'))");
assert.ok(await evaluate("$('network').querySelectorAll('.node').length")<=before);
await evaluate("$('focus').value='all'; draw(); $('values').querySelector('details').open=true");
shot=await cdp('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});await fs.writeFile('results/interface/operator_association.png',Buffer.from(shot.data,'base64'));
const reviews=[];
for(const action of ['confirm','reject','defer']){
 await evaluate(`$('decisionNote').value='[automated verification] ${action} control test. This is not a human diagnosis.'; document.querySelector('[data-action="${action}"]').click()`);
 await until(`$('status').textContent.startsWith('Saved ${action} review')`);
 reviews.push(await evaluate("$('status').textContent"));
}
assert.deepEqual(exceptions,[]);
const report={tested_at:new Date().toISOString(),url:base,case_count:10,run_id:await evaluate('bundle.run.id'),case_id:await evaluate('bundle.case.id'),graph_version:await evaluate('bundle.case.graph.version'),checks:['saved case and time selection','classic SVG node-link network','observation and association selection','unchanged witness values and before/after intervals','evidence artifact download','neighborhood focus','confirm/reject/defer persistence','no uncaught browser exceptions'],reviews,scope:'automated local interface verification, not a human evaluation'};
await fs.writeFile('results/interface/browser_verification.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));socket.close();

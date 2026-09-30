// Exercise the actual exported replay in a local Chrome DevTools session.
import fs from 'node:fs/promises';
const tabs=await(await fetch('http://127.0.0.1:9226/json/list')).json();
const tab=tabs.find(t=>t.type==='page'&&t.url.includes('8766'));
if(!tab)throw Error('Open the dashboard on local port 8766 with Chrome debugging port 9226');
const socket=new WebSocket(tab.webSocketDebuggerUrl);
await new Promise(resolve=>socket.addEventListener('open',resolve,{once:true}));
let id=0;const pending=new Map(),errors=[];
socket.addEventListener('message',event=>{
  const message=JSON.parse(event.data);
  if(message.method==='Runtime.exceptionThrown')errors.push(message.params.exceptionDetails);
  if(pending.has(message.id)){
    const [resolve,reject]=pending.get(message.id);pending.delete(message.id);
    message.error?reject(Error(JSON.stringify(message.error))):resolve(message.result);
  }
});
const send=(method,params={})=>new Promise((resolve,reject)=>{
  pending.set(++id,[resolve,reject]);socket.send(JSON.stringify({id,method,params}));
});
const evaluate=async expression=>{
  const result=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});
  if(result.exceptionDetails)throw Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
};
await send('Runtime.enable');await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false});
await send('Page.reload',{ignoreCache:true});
await evaluate("new Promise(resolve=>{const timer=setInterval(()=>{if(typeof data!=='undefined'&&data?.frames?.length){clearInterval(timer);resolve(true)}},100)})");
const first=await evaluate("({status:$('status').textContent,groups:ranked.length,frames:data.frames.length,caseCount:catalog.length,selected:gi})");
await evaluate("$('time').value=9;$('time').dispatchEvent(new Event('input'));document.querySelectorAll('.row')[2].click();true");
const selected=await evaluate("({time:ti,group:gi,evidence:$('evidence').textContent,merged:data.frames[ti].merged_alert_groups.length})");
if(selected.time!==9||!selected.evidence.includes('Forecast issued:'))throw Error('Linked selection failed');
const edge=await evaluate("(()=>{const edge=edgeRecords[0],a=positions[edge.a],b=positions[edge.b],rect=$('network').getBoundingClientRect();$('network').dispatchEvent(new MouseEvent('mousemove',{clientX:rect.left+(a[0]+b[0])/2,clientY:rect.top+(a[1]+b[1])/2}));return $('edgeinfo').textContent})()");
if(!edge.includes('observed r=')||!edge.includes('Δreference='))throw Error('Edge evidence inspection failed');
const checks=[];
for(let index=0;index<first.caseCount;index++){
  await evaluate(`$('case').value=${index};load()`);
  checks.push(await evaluate("({dataset:data.dataset,kind:data.event.kind,group:gi,frames:data.frames.length,hasThreshold:finite(data.strict_score_threshold)})"));
}
await evaluate("$('case').value=0;load()");
await evaluate("ti=3;gi=11;rawNode=data.groups[gi].nodes[0];$('time').value=ti;update();true");
const layout=await send('Page.getLayoutMetrics');
const screenshot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,
  clip:{x:0,y:0,width:1440,height:Math.ceil(layout.cssContentSize.height),scale:1}});
await fs.mkdir('dashboard/validation',{recursive:true});
await fs.writeFile('dashboard/validation/replay.png',Buffer.from(screenshot.data,'base64'));
await fs.writeFile('dashboard/validation/check.json',JSON.stringify({first,selected,edge,checks,errors},null,2)+'\n');
console.log(JSON.stringify({cases:checks.length,interactionPassed:true,javascriptExceptions:errors.length}));
socket.close();if(errors.length)process.exitCode=1;

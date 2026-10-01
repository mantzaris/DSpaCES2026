// Validate the actual saved extension replays in an isolated local Chrome.
import fs from 'node:fs/promises';
const tabs=await(await fetch('http://127.0.0.1:9226/json/list')).json();
const tab=tabs.find(t=>t.type==='page'&&t.url.includes('8766'));
if(!tab)throw Error('Dashboard must be served on 8766 with Chrome debugging on 9226');
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
await evaluate("new Promise((resolve,reject)=>{let count=0;const timer=setInterval(()=>{if(typeof data!=='undefined'&&data?.frames?.length){clearInterval(timer);resolve(true)}else if(count++>100){clearInterval(timer);reject(Error('replay timeout'))}},100)})");
const checks=[];
for(const name of ['synthetic64','intel','pems']){
  await evaluate(`$('dataset').value='${name}';load()`);
  const before=await evaluate('JSON.stringify(positions)');
  await evaluate("$('time').value=9;$('time').dispatchEvent(new Event('input'));document.querySelectorAll('.choice')[2].click();$('family').value='T';$('family').dispatchEvent(new Event('change'));true");
  const row=await evaluate("({dataset:data.dataset,time:ti,group:gi,frames:data.frames.length,channels:data.channels.length,quality:$('quality').textContent,provenance:$('provenance').textContent,p:+$('scanP').textContent,rawRows:data.frames[ti].raw.length,positions:JSON.stringify(positions)})");
  if(row.time!==9||row.frames!==13||row.rawRows!==48||row.positions!==before)throw Error('Time selection or stable layout failed');
  if(!row.quality.includes('Actual change')||!row.quality.includes('Valid templates')||!row.provenance.includes('Forecast issued:')||!Number.isFinite(row.p))throw Error('Evidence fields missing');
  const selectedNode=await evaluate("(()=>{const p=positions[1],r=$('network').getBoundingClientRect();$('network').dispatchEvent(new MouseEvent('click',{clientX:r.left+p[0],clientY:r.top+p[1]}));return node})()");
  if(selectedNode!==1)throw Error('Node inspection failed');
  if(row.channels>1){await evaluate("$('channel').value=1;$('channel').dispatchEvent(new Event('change'));true");if(await evaluate('data.groups[gi].channel')!==1)throw Error('Channel selection failed');}
  const edge=await evaluate("(()=>{if(!edges.length)return 'no overlay above display threshold';const e=edges[0],a=positions[e.a],b=positions[e.b],r=$('network').getBoundingClientRect();$('network').dispatchEvent(new MouseEvent('mousemove',{clientX:r.left+(a[0]+b[0])/2,clientY:r.top+(a[1]+b[1])/2}));return $('edgeInfo').textContent})()");
  if(!edge.includes('observed r=')&&!edge.includes('no overlay'))throw Error('Edge inspection failed');
  delete row.positions;checks.push({...row,selectedNode,edge});
}
await evaluate("$('dataset').value='synthetic64';load()");
await evaluate("$('truth').checked=true;document.querySelectorAll('.choice')[0].click();true");
const layout=await send('Page.getLayoutMetrics');
const screenshot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,
  clip:{x:0,y:0,width:1440,height:Math.ceil(layout.cssContentSize.height),scale:1}});
await fs.mkdir('dashboard/validation',{recursive:true});
await fs.writeFile('dashboard/validation/extension.png',Buffer.from(screenshot.data,'base64'));
await fs.writeFile('dashboard/validation/extension-check.json',JSON.stringify({checks,errors},null,2)+'\n');
console.log(JSON.stringify({cases:checks.length,interactionPassed:true,javascriptExceptions:errors.length}));
socket.close();if(errors.length)process.exitCode=1;

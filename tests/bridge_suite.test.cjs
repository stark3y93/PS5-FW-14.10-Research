const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict'), path = require('node:path');
const code = fs.readFileSync(path.join(__dirname, '../diagnostics/bridge/suite.js'), 'utf8');
function environment(overrides = {}) {
  const data = new Map([['personal', 'do not touch']]);
  const storage = {getItem:k=>data.has(k)?data.get(k):null,setItem:(k,v)=>data.set(k,String(v)),removeItem:k=>data.delete(k)};
  const window = {Promise,Map,Set,Symbol,BigInt,ArrayBuffer,Uint8Array,TextEncoder,WebAssembly:undefined,
    location:{origin:'http://127.0.0.1:9999',protocol:'http:'},isSecureContext:false,navigator:{},
    localStorage:storage,sessionStorage:storage,performance:{now:()=>0},document:{fonts:{check(){}},createElement:()=>({})},
    ...overrides};
  const context = vm.createContext({window,Promise,Date,Math,JSON,Error,Uint8Array,ArrayBuffer,setTimeout,clearTimeout});
  vm.runInContext(code,context); return {suite:window.PS5Suite,window,data};
}
(async()=>{
 let n=0;
 async function check(name, fn){await fn();n++;console.log('PASS '+name);}
 await check('HTTP WASM absence remains context observation',async()=>{
  const {suite}=environment();const rows=await suite.run('surface',{});
  const row=rows.find(x=>x.test_id==='surface.WebAssembly');
  assert.equal(row.gate,'CONFIRMED BLOCKED OR UNAVAILABLE');assert.ok(row.scope.includes('http:'));
  assert.equal(rows.find(x=>x.test_id==='surface.Promise').gate,'CONFIRMED AVAILABLE');
 });
 await check('restricted getter does not abort remaining results',async()=>{
  const e=environment();Object.defineProperty(e.window,'FontFace',{get(){throw Error('restricted');}});
  const rows=await e.suite.run('surface',{});
  assert.equal(rows.find(x=>x.test_id==='surface.FontFace').gate,'INCONCLUSIVE');
  assert.ok(rows.some(x=>x.test_id==='surface.TransformStream'));
 });
 await check('storage touches only owned keys and requires actual new page for persistence',async()=>{
  const e=environment();let rows=await e.suite.run('storage',{});
  assert.equal(e.data.get('personal'),'do not touch');
  rows=await e.suite.run('storage',{});
  assert.equal(rows.find(x=>x.test_id==='storage.reload').gate,'REQUIRES USER INTERACTION');
 });
 await check('small buffer allocation remains capped',async()=>{
  let largest=0;const e=environment({ArrayBuffer:function(n){largest=Math.max(largest,n);return new ArrayBuffer(n);}});
  const rows=await e.suite.run('rendering',{});
  assert.equal(rows.find(x=>x.test_id==='rendering.buffer').gate,'CONFIRMED AVAILABLE');
  assert.ok(largest<=262144);
 });
 await check('secure APIs absent over HTTP request HTTPS retest',async()=>{
  const e=environment();const rows=await e.suite.run('security',{});
  assert.equal(rows.find(x=>x.test_id==='security.serviceWorker').gate,'REQUIRES HTTPS');
  assert.equal(rows.find(x=>x.test_id==='security.wasm').gate,'CONFIRMED BLOCKED OR UNAVAILABLE');
 });
 await check('unknown task is never executable',async()=>{
  await assert.rejects(()=>environment().suite.run('eval',{}));
 });
 await check('negative aggregate probes never become available',async()=>{
  const e=environment({WebAssembly:{validate:()=>false}});
  let rows=await e.suite.run('surface',{});
  assert.equal(rows.find(x=>x.test_id==='surface.devices').gate,'CONFIRMED BLOCKED OR UNAVAILABLE');
  rows=await e.suite.run('security',{});
  assert.equal(rows.find(x=>x.test_id==='security.wasm').gate,'INCONCLUSIVE');
 });
 await check('cleanup preserves storage ownership collisions',async()=>{
  const e=environment();e.data.set('ps5bridge-v1.local','not suite data');
  const result=await e.suite.cleanup();
  assert.equal(e.data.get('ps5bridge-v1.local'),'not suite data');
  assert.ok(result.preserved_collisions>=1);
 });
 await check('failed XHR control cannot prove controlled timeout or failure',async()=>{
  function BrokenXHR(){this.open=()=>{};this.send=()=>queueMicrotask(()=>this.onerror());}
  const rows=await environment({XMLHttpRequest:BrokenXHR}).suite.run('network',{});
  for(const name of ['timeout','failure']) assert.equal(rows.find(x=>x.test_id==='network.'+name).gate,'INCONCLUSIVE');
 });
 await check('mixed language operations remain inconclusive',async()=>{
  const rows=await environment({BigInt:undefined}).suite.run('rendering',{});
  assert.equal(rows.find(x=>x.test_id==='rendering.language').gate,'INCONCLUSIVE');
 });
 await check('synthetic FileReader verifies exact memory-only content',async()=>{
  class MemoryFile extends Blob {constructor(parts,name,options){super(parts,options);this.name=name;}}
  function Reader(){this.readAsText=f=>f.text().then(x=>{this.result=x;this.onload();});this.abort=()=>{};}
  const rows=await environment({File:MemoryFile,FileReader:Reader}).suite.run('files',{});
  const r=rows.find(r=>r.test_id==='files.fileReader');assert.equal(r.gate,'CONFIRMED AVAILABLE');assert.equal(r.observed.exact_match,true);assert.equal(r.observed.bytes,47);
 });
 await check('filesystem types do not trigger picker or enumerate directories',async()=>{
  let calls=0;const fail=()=>{calls++;throw Error('must not call picker');};
  const rows=await environment({showOpenFilePicker:fail,showDirectoryPicker:fail,showSaveFilePicker:fail}).suite.run('files',{});
  assert.equal(calls,0);assert.equal(rows.find(r=>r.test_id==='files.showDirectoryPicker').observed.type,'function');
  assert.equal(rows.find(r=>r.test_id==='files.getDirectory').gate,'REQUIRES HTTPS');
 });
 await check('FileReader mismatch and restricted getter retain exact errors',async()=>{
  function File(){this.size=47;}function Reader(){this.readAsText=()=>{this.result='wrong';this.onload();};this.abort=()=>{};}
  const e=environment({File,FileReader:Reader});Object.defineProperty(e.window,'showOpenFilePicker',{get(){throw Object.assign(Error('policy denied'),{name:'SecurityError'});}});
  const rows=await e.suite.run('files',{});
  assert.equal(rows.find(r=>r.test_id==='files.fileReader').gate,'INCONCLUSIVE');
  assert.equal(rows.find(r=>r.test_id==='files.showOpenFilePicker').error,'SecurityError: policy denied');
 });
 console.log(n+' bridge JavaScript tests passed');
})().catch(e=>{console.error(e);process.exitCode=1;});

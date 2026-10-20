const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),assert=require('node:assert/strict');
const code=fs.readFileSync(path.join(__dirname,'../diagnostics/bridge/client.js'),'utf8');
async function fixture(){
 const nodes={},calls=[];let reads=0;
 const node=()=>({value:'',textContent:'',files:[],appendChild(){},focus(){},select(){}});
 ['status','raw','summary','connect','pair','firmware','identity','tasks','cleanup','selectRaw','openTxt','downloadTxt','attributeTxt','navigation','blob','blobLink','file','popup','manualTest','manualOutcome','confirmManual'].forEach(k=>nodes[k]=node());
 nodes.pair.value='localtest';nodes.firmware.value='14.10';
 function XHR(){this.open=(m,p)=>{this.path=p;};this.setRequestHeader=()=>{};this.send=()=>{this.status=200;this.responseText=JSON.stringify(this.path==='/config'?{tasks:[],text:'PS5 capability suite: harmless synthetic text.\n'}:this.path==='/api/register'?{token:'private-test-session',client_id:'fixture'}:{ok:true});Promise.resolve().then(()=>this.onload());};}
 const w={XMLHttpRequest:XHR,navigator:{userAgent:'fixture'},location:{protocol:'http:',origin:'http://fixture'},isSecureContext:false,PS5Suite:{cleanup(){}},FileReader:function(){reads++;this.readAsText=()=>{};}};
 const d={getElementById:id=>nodes[id],createElement:node};
 vm.runInNewContext(code,{window:w,document:d,Promise,JSON,String,setInterval(){},setTimeout(){},clearTimeout(){}});
 nodes.connect.onclick();for(let i=0;i<10;i++)await Promise.resolve();
 return {nodes,reads:()=>reads};
}
(async()=>{
 let n=0;
 const a=await fixture();a.nodes.file.onchange({target:{files:[{name:'personal.txt',size:20}],value:'chosen'}});
 assert.equal(a.reads(),0,'personal filename must be rejected before FileReader');n++;console.log('PASS non-fixture file is never read');
 const b=await fixture();b.nodes.downloadTxt.onclick();const rows=JSON.parse(b.nodes.raw.value);
 assert.equal(rows[0].gate,'REQUIRES USER INTERACTION');assert.ok(!b.nodes.raw.value.includes('private-test-session'));n++;console.log('PASS link request is not download success and contains no token');
 const c=await fixture();c.nodes.popup.onclick();
 assert.equal(JSON.parse(c.nodes.raw.value)[0].gate,'INCONCLUSIVE');n++;console.log('PASS missing popup handle does not prove blocking');
 console.log(n+' bridge client tests passed');
})().catch(e=>{console.error(e);process.exitCode=1;});

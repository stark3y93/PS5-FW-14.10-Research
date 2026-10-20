(function(w,d){'use strict';
 var token='',clientId='',config=null,busy=false,paired=false;
 var status=d.getElementById('status'),raw=d.getElementById('raw'),summary=d.getElementById('summary');
 function show(text){status.textContent=text;}
 function request(method,path,data,auth){return new Promise(function(resolve,reject){
  if(w.XMLHttpRequest){var x=new w.XMLHttpRequest();x.open(method,path,true);x.timeout=4000;
   if(data!==undefined)x.setRequestHeader('Content-Type','application/json');if(auth)x.setRequestHeader('Authorization','Bearer '+auth);
   x.onload=function(){try{var j=JSON.parse(x.responseText);if(x.status!==200)throw new Error(j.error||'HTTP '+x.status);resolve(j);}catch(e){reject(e);}};
   x.onerror=function(){reject(new Error('LAN request failed'));};x.ontimeout=function(){reject(new Error('Bridge request timeout'));};x.send(data===undefined?null:JSON.stringify(data));
  }else{reject(new Error('Control transport XMLHttpRequest unavailable; preserve on-screen evidence. No bridge task was executed.'));}
 });}
 function localRow(id,gate,observed,confidence){return {test_id:'manual.'+id,gate:gate,observed:observed,error:'',scope:w.location.protocol+' current page; isSecureContext='+(w.isSecureContext===true),confidence:confidence||'AUTOMATED OBSERVATION'};}
 function retain(rows){raw.value=JSON.stringify(rows,null,2);summary.textContent=rows.map(function(r){return r.test_id+': '+r.gate+' — '+JSON.stringify(r.observed);}).join('\n');}
 function manual(rows){retain(rows);if(!paired){show('Pair before uploading. These local observations remain below.');return;}
  request('POST','/api/manual',{results:rows},token).then(function(){show('Manual/action observation retained on PC.');},function(e){show('Upload failed: '+e.message+' — keep the raw text below.');});}
 function poll(){if(!paired||busy)return;request('GET','/api/poll',undefined,token).then(function(j){if(!j.job)return;busy=true;show('Running '+j.job.task+' (bounded)...');
  var timed=false,timer=setTimeout(function(){timed=true;show('Task exceeded 30 seconds; result remains inconclusive. Reload to recover if needed.');},30000);
  w.PS5Suite.run(j.job.task,{secondary_origin:config.secondary_origin,token:token}).then(function(rows){clearTimeout(timer);retain(rows);return request('POST','/api/results',{job_id:j.job.id,results:rows},token);}).then(function(){busy=false;show(timed?'Late task results uploaded; inspect job status.':'Task complete and uploaded.');},function(e){clearTimeout(timer);busy=false;show('Task/upload failed: '+e.message+' — preserve raw text.');});
 },function(e){show('Polling failed: '+e.message);});}
 d.getElementById('connect').onclick=function(){if(paired){show('Already paired. Reload only for a new page context.');return;}
  var key=d.getElementById('pair').value,firmware=d.getElementById('firmware').value;if(!/^\d{1,2}\.\d{2}$/.test(firmware)){show('Use firmware label such as 14.10.');return;}
  request('GET','/config').then(function(c){config=c;return request('POST','/api/register',{pair_key:key,info:{firmware:firmware,user_agent:String(w.navigator.userAgent).slice(0,1024),secure_context:w.isSecureContext===true}});}).then(function(j){
   token=j.token;clientId=j.client_id;paired=true;d.getElementById('pair').value='';d.getElementById('identity').textContent='Client '+clientId+' · '+w.navigator.userAgent+' · '+w.location.origin;
   var tasks=d.getElementById('tasks');config.tasks.forEach(function(name){var b=d.createElement('button');b.textContent='Run '+name;b.onclick=function(){if(busy){show('Wait for current task.');return;}request('POST','/api/start',{task:name},token).then(poll,function(e){show(e.message);});};tasks.appendChild(b);});
   show('Paired. Choose a test or schedule one from the PC. Manual actions never run remotely.');
   var initial=['downloadLink','txtDownload','attribute','blobDownload','fileUpload','popup','navigation'].map(function(id){return localRow(id,'REQUIRES USER INTERACTION','Use the named local control; no successful outcome inferred');});
   initial.push(localRow('fileOpen','NOT TESTABLE FROM A NORMAL WEBPAGE','A webpage cannot inspect the download directory; only normal browser UI/user observation can supply evidence'));
   request('POST','/api/manual',{results:initial},token).catch(function(e){show('Initial gate upload failed: '+e.message);});
   setInterval(function(){request('POST','/api/heartbeat',{},token).catch(function(e){show('Heartbeat failed: '+e.message);});},10000);setInterval(poll,2000);
  },function(e){show('Pairing failed: '+e.message);});
 };
 d.getElementById('cleanup').onclick=function(){w.PS5Suite.cleanup().then(function(result){manual([localRow('storageCleanup',result.errors.length||result.preserved_collisions?'INCONCLUSIVE':'CONFIRMED AVAILABLE',result)]);});};
 d.getElementById('selectRaw').onclick=function(){raw.focus();raw.select();};
 ['openTxt','downloadTxt','attributeTxt','navigation'].forEach(function(id){d.getElementById(id).onclick=function(){manual([localRow({openTxt:'downloadLink',downloadTxt:'txtDownload',attributeTxt:'attribute',navigation:'navigation'}[id],'REQUIRES USER INTERACTION','Link clicked/requested; saved/opened outcome is NOT established')]);};});
 d.getElementById('blob').onclick=function(){try{var url=w.URL.createObjectURL(new w.Blob([config?config.text:'PS5 capability suite: harmless synthetic text.\n'],{type:'text/plain'})),a=d.createElement('a');a.href=url;a.download='ps5-blob.txt';a.textContent='Click to download synthetic Blob';a.onclick=function(){manual([localRow('blobDownload','REQUIRES USER INTERACTION','Blob URL created and link clicked; confirm actual outcome below')]);};var holder=d.getElementById('blobLink');holder.textContent='';holder.appendChild(a);setTimeout(function(){w.URL.revokeObjectURL(url);holder.textContent='Blob link expired; create another if needed.';},30000);manual([localRow('blobDownload','REQUIRES USER INTERACTION','Blob URL created; click its link, then report observed outcome')]);}catch(e){manual([localRow('blobDownload','INCONCLUSIVE',String(e.name)+': '+String(e.message).slice(0,150))]);}};
 d.getElementById('file').onchange=function(e){var f=e.target.files&&e.target.files[0];if(!f)return;if(!config||['ps5-synthetic.txt','ps5-attribute.txt','ps5-blob.txt'].indexOf(f.name)<0||f.size!==config.text.length){manual([localRow('fileUpload','INCONCLUSIVE','Selection rejected before reading: filename/size must match the generated synthetic fixture')]);e.target.value='';return;}
  var reader=new w.FileReader();reader.onload=function(){if(reader.result!==config.text){manual([localRow('fileUpload','INCONCLUSIVE','Content did not match synthetic fixture; no contents or filename uploaded')]);}else{manual([localRow('fileUpload','CONFIRMED AVAILABLE','Exact synthetic fixture selected/read; only this confirmation was uploaded','USER OBSERVATION')]);}e.target.value='';};reader.onerror=function(){manual([localRow('fileUpload','INCONCLUSIVE','Synthetic file read failed')]);e.target.value='';};reader.readAsText(f);
 };
 d.getElementById('pickerTest').onclick=function(){
  d.getElementById('pickerInstruction').textContent='Observe whether a file-selection window appears. Select only the generated TXT or cancel. Then choose File-picker UI and your actual observation below.';
  manual([localRow('pickerUI','REQUIRES USER INTERACTION','Picker gesture requested; no visible outcome inferred')]);
  try{var input=d.getElementById('file');if(typeof input.showPicker==='function')input.showPicker();else input.click();}catch(e){var r=localRow('pickerUI','INCONCLUSIVE','Picker API threw');r.error=String(e.name)+': '+String(e.message).slice(0,350);manual([r]);}
 };
 var blobNonce='',blobControlUrl='',blobObserved=false;
 if(w.addEventListener)w.addEventListener('message',function(e){if(!blobNonce||e.origin!==w.location.origin||!e.source||!e.data||e.data.bridge!=='ps5-blob-navigation-v1'||e.data.nonce!==blobNonce||e.data.protocol!=='blob:')return;
  blobObserved=true;manual([localRow('blobNavigation','CONFIRMED AVAILABLE',{controlled_document_ran:true,url_scheme:'blob:',navigation_confirmed:true,saved_file_not_inferred:true})]);
 });
 d.getElementById('blobControl').onclick=function(){try{
  if(blobControlUrl)w.URL.revokeObjectURL(blobControlUrl);blobNonce=String(Date.now())+Math.random().toString(16).slice(2);blobObserved=false;
  var nonce=blobNonce,html='<!doctype html><meta charset="utf-8"><h1>PS5 synthetic Blob navigation control</h1><p>This content is in browser memory; it is not proof of a saved file.</p><span hidden id="bridgeNonce">'+nonce+'</span><script src="'+w.location.origin+'/bridge/blob_observer.js"></script>';
  var url=w.URL.createObjectURL(new w.Blob([html],{type:'text/html'}));blobControlUrl=url;
  var a=d.createElement('a');a.href=url;a.target='_blank';a.rel='opener';a.download='ps5-navigation-control.html';a.textContent='Click instrumented Blob download/navigation link';
  a.onclick=function(){manual([localRow('blobNavigation','REQUIRES USER INTERACTION','Control link clicked; waiting for a validated Blob-page message')]);};var holder=d.getElementById('blobControlLink');holder.textContent='';holder.appendChild(a);
  setTimeout(function(){w.URL.revokeObjectURL(url);if(blobNonce===nonce){holder.textContent='Control expired.';if(!blobObserved)manual([localRow('blobNavigation','INCONCLUSIVE','No validated page message in 45 seconds; this does not prove save, block or navigation')]);blobNonce='';}},45000);
  manual([localRow('blobNavigation','REQUIRES USER INTERACTION','Instrumented HTML Blob created; click its link and report visible outcome')]);
 }catch(e){var r=localRow('blobNavigation','INCONCLUSIVE','Control creation failed');r.error=String(e.name)+': '+String(e.message).slice(0,350);manual([r]);}};
 d.getElementById('popup').onclick=function(){var x=null;try{x=w.open('/manual/popup','ps5bridgeSynthetic','width=400,height=250');}catch(ignore){}manual([localRow('popup',x?'REQUIRES USER INTERACTION':'INCONCLUSIVE',x?'Window handle returned; confirm visible page yourself':'No window handle returned for this gesture')]);};
 d.getElementById('confirmManual').onclick=function(){var name=d.getElementById('manualTest').value,value=d.getElementById('manualOutcome').value;
  var success=name==='pickerUI'?value==='pickerOpened':value==='saved'||value==='opened';var gate=success?'CONFIRMED AVAILABLE':value==='blocked'?'CONFIRMED BLOCKED OR UNAVAILABLE':'INCONCLUSIVE';
  manual([localRow(name,gate,{user_reported:value,not_independently_authenticated:true},'USER OBSERVATION')]);};
}(window,document));

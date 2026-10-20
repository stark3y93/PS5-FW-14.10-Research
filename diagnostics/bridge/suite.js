/* Bounded ordinary-webpage tests. No native interfaces, external URLs or exploits. */
(function (w) {
    'use strict';
    var A = 'CONFIRMED AVAILABLE', B = 'CONFIRMED BLOCKED OR UNAVAILABLE', I = 'INCONCLUSIVE';
    var H = 'REQUIRES HTTPS', U = 'REQUIRES USER INTERACTION';
    var page = 'bridge:' + Date.now() + ':' + Math.random().toString(16).slice(2);
    var scope = function () { return w.location.protocol + ' page; isSecureContext=' + (w.isSecureContext === true); };
    function row(id, gate, observed, error) {
        return {test_id:id, gate:gate, observed:observed, error:error ? String(error.name || 'Error') + ': ' + String(error.message || error).slice(0,350) : '', scope:scope(), confidence:'AUTOMATED OBSERVATION'};
    }
    function exists(obj, key) { return typeof obj[key] !== 'undefined' && obj[key] !== null; }
    function absence(secureOnly) { return secureOnly && w.isSecureContext !== true ? H : B; }
    function bounded(fn, ms) {
        return new Promise(function (resolve, reject) {
            var timer = setTimeout(function () { reject(new Error('bounded test timeout; cause unknown')); }, ms || 2200);
            Promise.resolve().then(fn).then(function(x){clearTimeout(timer);resolve(x);},function(e){clearTimeout(timer);reject(e);});
        });
    }
    function evaluate(id, fn, absentGate) {
        return bounded(fn).then(function(value){
            if (value && value.bridgeGate) return row(id,value.bridgeGate,value.observed);
            return row(id,value === false ? (absentGate || B) : A,value);
        },function(e){return row(id,I,'Operation did not complete as expected',e);});
    }
    function unavailable(gate, observation) { return {bridgeGate:gate, observed:observation}; }
    function request(method, url, body, timeout) {
        return new Promise(function(resolve,reject){
            if (!w.XMLHttpRequest) {reject(new Error('XMLHttpRequest unavailable'));return;}
            var x = new w.XMLHttpRequest(); x.open(method,url,true); x.timeout=timeout || 1600;
            if(body) x.setRequestHeader('Content-Type','application/json');
            x.onload=function(){if(x.status===200)resolve(x.responseText);else reject(new Error('HTTP '+x.status));};
            x.onerror=function(){reject(new Error('XHR network error'));};
            x.ontimeout=function(){var e=new Error('Expected controlled XHR timeout');e.controlledTimeout=true;reject(e);};
            x.send(body || null);
        });
    }
    function sentinel(storage, key) {
        var previous = storage.getItem(key), fromPriorPage = typeof previous==='string' && previous.indexOf('bridge:')===0 && previous!==page;
        if(previous!==null && previous.indexOf('bridge:')!==0) throw new Error('Owned-key collision; left unchanged');
        storage.setItem(key,page);
        if(storage.getItem(key)!==page) throw new Error('Synthetic readback mismatch');
        return {readback:true, prior_page_sentinel:fromPriorPage};
    }
    function database() {
        return new Promise(function(resolve,reject){
            if (!w.indexedDB) {resolve(false);return;}
            var db, done=false, timer=setTimeout(function(){finish(new Error('IndexedDB timeout'));},1800);
            function finish(error,value){if(done)return;done=true;clearTimeout(timer);if(db)db.close();if(error)reject(error);else resolve(value);}
            var open=w.indexedDB.open('ps5bridge-capability-v1',1);
            open.onupgradeneeded=function(){open.result.createObjectStore('synthetic');};
            open.onerror=function(){finish(open.error || new Error('IDB open failed'));};
            open.onblocked=function(){finish(new Error('IDB upgrade blocked; close other suite tabs'));};
            open.onsuccess=function(){
                db=open.result;if(done){db.close();return;}
                var tx=db.transaction('synthetic','readwrite'), store=tx.objectStore('synthetic'), old=store.get('sentinel'), prior=false;
                old.onsuccess=function(){
                    var value=old.result;
                    if(value!==undefined && (typeof value!=='string' || value.indexOf('bridge:')!==0)){tx.abort();return;}
                    prior=!!value && value!==page;store.put(page,'sentinel');
                    var read=store.get('sentinel');read.onsuccess=function(){if(read.result!==page)tx.abort();};
                };
                tx.oncomplete=function(){finish(null,{readback:true,prior_page_sentinel:prior});};
                tx.onabort=tx.onerror=function(){finish(tx.error || new Error('IDB transaction failed or owned-key collision'));};
            };
        });
    }
    function frame(kind) {
        if(!w.addEventListener || !w.removeEventListener || !w.document.body)return false;
        return new Promise(function(resolve,reject){
            var f=w.document.createElement('iframe'), done=false;
            var timer=setTimeout(function(){finish(new Error('iframe control timeout'));},1700);
            function finish(error,value){if(done)return;done=true;clearTimeout(timer);w.removeEventListener('message',message);if(f.parentNode)f.parentNode.removeChild(f);if(error)reject(error);else resolve(value);}
            function message(e){if(kind==='sandbox' && e.source===f.contentWindow && e.data && e.data.bridge==='sandbox-child'){
                var denied=false;try {denied=!f.contentDocument || !f.contentDocument.body;}catch(ignore){denied=true;}
                finish(null,e.origin==='null' && denied ? {opaque_origin:true,parent_dom_blocked:true} : unavailable(I,'Sandbox control did not match expected restrictions'));
            }}
            w.addEventListener('message',message);
            f.title='Temporary controlled policy test';f.hidden=true;
            if(kind==='sandbox')f.setAttribute('sandbox','allow-scripts');
            if(kind==='csp')f.onload=function(){setTimeout(function(){
                try {var control=f.contentDocument.getElementById('control');finish(null,control && !f.contentWindow.bridgeExecuted ? {control_loaded:true,inline_script_blocked:true} : unavailable(I,'CSP control mismatch'));}catch(e){finish(e);}
            },150);};
            f.src='/frames/'+kind;w.document.body.appendChild(f);
        });
    }
    function worker() {
        if(!w.Worker || !w.Blob || !w.URL || !w.URL.createObjectURL)return false;
        return new Promise(function(resolve,reject){
            var url=w.URL.createObjectURL(new w.Blob(['postMessage("PS5-BRIDGE-SYNTHETIC");'],{type:'text/javascript'})), x;
            var timer=setTimeout(function(){finish(new Error('worker timeout'));},1200);
            function finish(e,value){clearTimeout(timer);if(x)x.terminate();w.URL.revokeObjectURL(url);if(e)reject(e);else resolve(value);}
            try{x=new w.Worker(url);x.onmessage=function(e){finish(null,e.data==='PS5-BRIDGE-SYNTHETIC');};x.onerror=function(){finish(new Error('worker error'));};}catch(e){finish(e);}
        });
    }
    function definitions(task, options) {
        var tests=[], n=w.navigator || {}, d=w.document;
        function add(name,fn,absent){tests.push({id:task+'.'+name,fn:fn,absent:absent});}
        if(task==='surface') {
            ['Promise','Map','Set','Symbol','BigInt','ArrayBuffer','Uint8Array','TextEncoder','FontFace','TransformStream','WebAssembly'].forEach(function(name){add(name,function(){return exists(w,name);});});
            add('fontSet',function(){return !!d.fonts && typeof d.fonts.check==='function';});
            add('cssGrid',function(){return !!w.CSS && w.CSS.supports('display','grid');});
            add('cssFontFamily',function(){return !!w.CSS && w.CSS.supports('font-family','sans-serif');});
            add('clipboard',function(){return !!n.clipboard ? unavailable(U,'Clipboard object present; no personal clipboard read or write attempted') : false;},absence(true));
            add('fileInput',function(){var e=d.createElement('input');e.type='file';return e.type==='file';});
            add('fileSystem',function(){return !!w.showOpenFilePicker ? unavailable(U,'Picker API present; no picker invoked') : false;},absence(true));
            add('fileAPIs',function(){var out={};['File','FileReader','Blob','FileList'].forEach(function(k){out[k]=exists(w,k);});out.blobURL=!!w.URL&&typeof w.URL.createObjectURL==='function';return unavailable(Object.keys(out).every(function(k){return out[k];})?A:I,out);});
            add('devices',function(){var out={},count=0;['bluetooth','usb','serial','hid','mediaDevices','geolocation'].forEach(function(k){out[k]=exists(n,k);if(out[k])count+=1;});return unavailable(count===0?B:count===6?A:I,out);});
            add('isolation',function(){var out={crossOriginIsolated:w.crossOriginIsolated===true,SharedArrayBuffer:exists(w,'SharedArrayBuffer'),policy:'This page does not request COOP/COEP isolation'};return unavailable(out.crossOriginIsolated&&out.SharedArrayBuffer?A:B,out);});
            add('permissions',function(){return !!n.permissions && typeof n.permissions.query==='function';});
        } else if(task==='files') {
            var fixture='PS5 capability suite: harmless synthetic text.\n';
            function exposure(obj,key,secure){var value=obj?obj[key]:undefined;return unavailable(typeof value==='function'?A:secure&&w.isSecureContext!==true?H:B,{type:typeof value,is_null:value===null,secure_context:w.isSecureContext===true,secure_context_prerequisite:!!secure,cause_of_absence_not_established:true,invoked:false});}
            ['showOpenFilePicker','showDirectoryPicker','showSaveFilePicker','webkitRequestFileSystem','requestFileSystem','FileSystemHandle','FileSystemFileHandle','FileSystemDirectoryHandle'].forEach(function(key){add(key,function(){return exposure(w,key,key.indexOf('Picker')>=0||key.indexOf('Handle')>=0);});});
            add('getDirectory',function(){return exposure(n.storage,'getDirectory',true);});
            add('fileReader',function(){
                if(typeof w.File!=='function'||typeof w.FileReader!=='function')return unavailable(B,{File:typeof w.File,FileReader:typeof w.FileReader,invoked:false});
                return new Promise(function(resolve,reject){var file=new w.File([fixture],'ps5-memory-only.txt',{type:'text/plain',lastModified:0}),reader=new w.FileReader(),done=false;
                    var timer=setTimeout(function(){finish(new Error('Synthetic FileReader exceeded 1500ms'));try{reader.abort();}catch(ignore){}},1500);
                    function finish(error,value){if(done)return;done=true;clearTimeout(timer);if(error)reject(error);else resolve(value);}
                    reader.onload=function(){var exact=reader.result===fixture;finish(null,unavailable(exact?A:I,{exact_match:exact,bytes:file.size,expected_bytes:47,in_memory_only:true,no_user_file_selected:true}));};
                    reader.onerror=function(){finish(reader.error||new Error('FileReader error without details'));};reader.onabort=function(){finish(new Error('Synthetic FileReader aborted'));};
                    try{reader.readAsText(file,'utf-8');}catch(e){finish(e);}
                });
            });
            add('originPrivate',function(){
                if(!n.storage||typeof n.storage.getDirectory!=='function')return unavailable(w.isSecureContext===true?B:H,{invoked:false,reason:'not exposed here; insecure context may be a prerequisite, not proven cause'});
                return n.storage.getDirectory().then(function(handle){return unavailable(handle&&handle.kind==='directory'?A:I,{returned_kind:handle&&handle.kind,scope:'origin storage bucket only',entries_enumerated:false,files_created:false,os_paths_collected:false});});
            });
            add('legacyTemporary',function(){var fn=w.webkitRequestFileSystem||w.requestFileSystem;if(typeof fn!=='function')return unavailable(B,{invoked:false,reason:'legacy temporary filesystem API not exposed'});
                return new Promise(function(resolve,reject){var done=false,timer=setTimeout(function(){finish(new Error('Temporary filesystem callback exceeded 1500ms'));},1500);
                    function finish(e,v){if(done)return;done=true;clearTimeout(timer);if(e)reject(e);else resolve(v);}
                    try{fn.call(w,0,0,function(fs){finish(null,unavailable(fs&&fs.root&&fs.root.isDirectory?A:I,{temporary_namespace:true,root_is_directory:!!(fs&&fs.root&&fs.root.isDirectory),requested_bytes:0,entries_enumerated:false,files_created:false,paths_collected:false}));},function(e){finish(e||new Error('Temporary filesystem error without details'));});}catch(e){finish(e);}
                });
            });
            add('blobReadback',function(){if(!w.Blob||!w.URL||typeof w.URL.createObjectURL!=='function'||!w.XMLHttpRequest)return false;var url=w.URL.createObjectURL(new w.Blob([fixture],{type:'text/plain'}));
                return request('GET',url).then(function(text){w.URL.revokeObjectURL(url);return unavailable(text===fixture?A:I,{url_scheme:'blob:',exact_match:text===fixture,expected_characters:47,saved_file_not_inferred:true});},function(e){w.URL.revokeObjectURL(url);throw e;});
            });
        } else if(task==='storage') {
            var prior=[];
            add('local',function(){var result=sentinel(w.localStorage,'ps5bridge-v1.local');prior.push(result.prior_page_sentinel);return result;});
            add('session',function(){var result=sentinel(w.sessionStorage,'ps5bridge-v1.session');prior.push(result.prior_page_sentinel);return result;});
            add('indexedDB',function(){return database().then(function(value){if(value)prior.push(value.prior_page_sentinel);return value;});});
            add('estimate',function(){
                var s=w.localStorage,key='ps5bridge-v1.quota',old=s.getItem(key),value=new Array(2049).join('s');
                if(old!==null) return unavailable(I,'Owned quota key already present; not overwritten');
                try{s.setItem(key,value);if(s.getItem(key)!==value)throw new Error('Synthetic storage readback failed');}finally{s.removeItem(key);}
                if(n.storage && n.storage.estimate)return n.storage.estimate().then(function(q){return {synthetic_characters:2048,max_utf16_payload_bytes:4096,origin_usage_estimate:q.usage,origin_quota_estimate:q.quota,not_a_quota_exhaustion_test:true};});
                return {synthetic_characters:2048,max_utf16_payload_bytes:4096,estimate_available:false};
            });
            add('reload',function(){return prior.indexOf(true)>=0 ? {prior_page_sentinel_seen:true,stores_with_prior_marker:prior.filter(function(x){return x;}).length} : unavailable(U,'Use normal Reload, re-pair, then run storage again; same-page reruns are not persistence proof');});
            add('cleanup',function(){return unavailable(U,'Sentinels retained for reload testing; use the explicit cleanup button when finished');});
        } else if(task==='network') {
            var xhrControl=false;
            function fetchMarker(method,url){if(!w.fetch)return Promise.resolve(false);return w.fetch(url,{method:method,headers:method==='POST'?{'Content-Type':'application/json'}:{},body:method==='POST'?JSON.stringify({marker:'PS5-BRIDGE-SYNTHETIC'}):undefined,cache:'no-store'}).then(function(r){if(!r.ok)throw new Error('HTTP '+r.status);return r.json();}).then(function(j){if(j.marker!=='PS5-BRIDGE-SYNTHETIC')throw new Error('marker mismatch');return true;});}
            add('fetchGET',function(){return fetchMarker('GET','/net/echo');});
            add('fetchPOST',function(){return fetchMarker('POST','/net/echo');});
            add('xhrGET',function(){if(!w.XMLHttpRequest)return false;return request('GET','/net/echo').then(function(raw){xhrControl=JSON.parse(raw).marker==='PS5-BRIDGE-SYNTHETIC';return xhrControl;});});
            add('xhrPOST',function(){if(!w.XMLHttpRequest)return false;return request('POST','/net/echo',JSON.stringify({marker:'PS5-BRIDGE-SYNTHETIC'})).then(function(raw){return JSON.parse(raw).method==='POST';});});
            add('cors',function(){
                if(!w.fetch)return false;
                return fetchMarker('GET',options.secondary_origin+'/net/cors-allow').then(function(control){
                    if(!control) return unavailable(I,'Allowed-origin control failed');
                    return w.fetch(options.secondary_origin+'/net/cors-deny',{mode:'cors'}).then(function(){return unavailable(I,'No-CORS-header response unexpectedly readable; inspect raw context');},function(){return unavailable(B,'Allowed-origin control passed; no-header cross-origin response was unreadable as expected');});
                });
            });
            add('websocket',function(){
                if(!w.WebSocket)return false;
                return new Promise(function(resolve,reject){var x=new w.WebSocket(w.location.origin.replace(/^http/,'ws')+'/net/ws'),done=false;
                    var timer=setTimeout(function(){finish(new Error('WebSocket timeout'));},1600);
                    function finish(e,value){if(done)return;done=true;clearTimeout(timer);x.close();if(e)reject(e);else resolve(value);}
                    x.onopen=function(){x.send(JSON.stringify({token:options.token,marker:'PS5-BRIDGE-SYNTHETIC'}));};
                    x.onmessage=function(e){try{finish(null,JSON.parse(e.data).marker==='PS5-BRIDGE-SYNTHETIC');}catch(err){finish(err);}};
                    x.onerror=function(){finish(new Error('WebSocket connection failed'));};
                });
            });
            add('eventSource',function(){if(!w.EventSource)return false;return new Promise(function(resolve,reject){var x=new w.EventSource('/net/events'),timer=setTimeout(function(){finish(new Error('EventSource timeout'));},1500),done=false;
                function finish(e,v){if(done)return;done=true;clearTimeout(timer);x.close();if(e)reject(e);else resolve(v);}
                x.onmessage=function(e){finish(null,e.data==='PS5-BRIDGE-SYNTHETIC');};x.onerror=function(){finish(new Error('EventSource failed before event'));};});});
            add('streaming',function(){if(!w.fetch)return false;return w.fetch('/net/stream').then(function(r){if(!r.body || !r.body.getReader)return unavailable(B,'ReadableStream reader unavailable in this response');var reader=r.body.getReader();return reader.read().then(function(part){var count=part.value?part.value.byteLength:0;reader.cancel();return unavailable(count>0?A:I,{first_chunk_bytes:count,bounded_synthetic_response:true});});});});
            add('timeout',function(){if(!w.XMLHttpRequest)return false;if(!xhrControl)return unavailable(I,'Same-origin XHR control failed; timeout cause cannot be established');return request('GET','/net/slow',null,100).then(function(){return unavailable(I,'Controlled delay did not produce timeout');},function(e){return e.controlledTimeout ? {controlled_timeout_observed:true} : Promise.reject(e);});});
            add('failure',function(){if(!w.XMLHttpRequest)return false;if(!xhrControl)return unavailable(I,'Same-origin XHR control failed; connection-failure cause cannot be established');return request('GET','/net/closed').then(function(){return unavailable(I,'Controlled close unexpectedly returned data');},function(e){return {controlled_connection_failure_reported:true,error:String(e.message).slice(0,120)};});});
        } else if(task==='security') {
            add('context',function(){return unavailable(w.isSecureContext===true?A:H,{isSecureContext:w.isSecureContext===true,protocol:w.location.protocol,crossOriginIsolated:w.crossOriginIsolated===true});});
            add('permissions',function(){if(!n.permissions || !n.permissions.query)return false;return n.permissions.query({name:'geolocation'}).then(function(p){return {state:p.state,permission_was_not_requested:true};});});
            add('wasm',function(){if(!w.WebAssembly)return false;var bytes=new w.Uint8Array([0,97,115,109,1,0,0,0]),ok=w.WebAssembly.validate(bytes);return unavailable(ok?A:I,{minimal_module_valid:ok,bytes:8,permanent_disablement_not_inferred:true});});
            add('worker',worker);
            add('serviceWorker',function(){
                if(!n.serviceWorker)return false;
                return n.serviceWorker.register('/bridge/sw.js',{scope:'/bridge/sw-check/'}).then(function(r){return r.unregister().then(function(ok){return unavailable(ok?A:I,{registered:true,unregistered:ok,scope:'/bridge/sw-check/',no_fetch_handler:true});});});
            },absence(true));
            add('crypto',function(){if(!w.crypto || !w.crypto.subtle)return false;return w.crypto.subtle.digest('SHA-256',new w.Uint8Array([1,2,3])).then(function(x){return unavailable(x.byteLength===32?A:I,{digest_bytes:x.byteLength,synthetic_input_bytes:3});});},absence(true));
            add('sandbox',function(){return frame('sandbox');});
            add('csp',function(){return frame('csp');});
        } else if(task==='rendering') {
            add('language',function(){var m=new w.Map(),s=new w.Set();m.set('synthetic',1);s.add('synthetic');var out={map:m.get('synthetic')===1,set:s.has('synthetic'),symbol:typeof w.Symbol('synthetic')==='symbol',bigint:typeof w.BigInt==='function'?String(w.BigInt('7')+w.BigInt('1')):'absent',promise:typeof w.Promise==='function'};return unavailable(out.map&&out.set&&out.symbol&&out.bigint==='8'&&out.promise?A:I,out);});
            add('buffer',function(){var b=new w.ArrayBuffer(262144),v=new w.Uint8Array(b);v[0]=17;v[v.length-1]=23;var ok=v[0]===17 && v[v.length-1]===23;b=null;v=null;return ok;});
            add('canvas',function(){var c=d.createElement('canvas');c.width=c.height=16;var x=c.getContext('2d');if(!x)return false;x.fillStyle='#ff0000';x.fillRect(0,0,1,1);var pixel=x.getImageData(0,0,1,1).data;return pixel[0]===255 && pixel[3]===255;});
            add('webgl',function(){var c=d.createElement('canvas');c.width=c.height=16;var gl=c.getContext('webgl');if(!gl)return false;gl.clearColor(0,0,0,1);gl.clear(gl.COLOR_BUFFER_BIT);var ext=gl.getExtension('WEBGL_lose_context');if(ext)ext.loseContext();return {context_created:true,surface:'16x16',no_device_identifiers_queried:true};});
            add('timing',function(){var start=w.performance && w.performance.now?w.performance.now():Date.now(),sum=0;for(var i=0;i<10000;i+=1)sum+=i;var end=w.performance && w.performance.now?w.performance.now():Date.now();return {iterations:10000,elapsed_ms:end-start,checksum:sum,not_a_stress_or_version_test:true};});
            add('errors',function(){try{throw new Error('PS5 bridge synthetic handled error');}catch(e){return {name:e.name,message:e.message,window_error_listener:typeof w.addEventListener==='function'};}});
        } else throw new Error('Task not in fixed allowlist');
        return tests;
    }
    w.PS5Suite={run:function(task,options){
        return Promise.resolve().then(function(){var tests=definitions(task,options || {}),results=[],chain=Promise.resolve();
            tests.forEach(function(test){chain=chain.then(function(){return evaluate(test.id,test.fn,test.absent);}).then(function(value){results.push(value);});});
            return chain.then(function(){return results;});
        });
    },cleanup:function(){
        var report={removed:0,preserved_collisions:0,errors:[]};
        function clean(storage,key){try{var value=storage.getItem(key);if(value===null)return;if(typeof value==='string'&&value.indexOf('bridge:')===0){storage.removeItem(key);report.removed+=1;}else report.preserved_collisions+=1;}catch(e){report.errors.push(String(e.name));}}
        try{clean(w.localStorage,'ps5bridge-v1.local');clean(w.localStorage,'ps5bridge-v1.quota');}catch(e){report.errors.push(String(e.name));}
        try{clean(w.sessionStorage,'ps5bridge-v1.session');}catch(e){report.errors.push(String(e.name));}
        if(!w.indexedDB)return Promise.resolve(report);
        return new Promise(function(resolve){var db,done=false,created=false,timer=setTimeout(function(){report.errors.push('IndexedDB cleanup timeout');finish();},1800);
            function finish(){if(done)return;done=true;clearTimeout(timer);if(db)db.close();resolve(report);}
            function remove(){db.close();var del=w.indexedDB.deleteDatabase('ps5bridge-capability-v1');del.onsuccess=function(){report.removed+=1;finish();};del.onerror=del.onblocked=function(){report.errors.push('Owned database deletion failed/blocked');finish();};}
            var open=w.indexedDB.open('ps5bridge-capability-v1',1);open.onupgradeneeded=function(){created=true;};open.onerror=open.onblocked=function(){report.errors.push('Owned database open failed/blocked');finish();};
            open.onsuccess=function(){db=open.result;if(done){db.close();return;}if(created){remove();return;}if(!db.objectStoreNames.contains('synthetic')){report.preserved_collisions+=1;finish();return;}
                var tx=db.transaction('synthetic','readonly'),get=tx.objectStore('synthetic').get('sentinel'),owned=false;
                get.onsuccess=function(){owned=typeof get.result==='string'&&get.result.indexOf('bridge:')===0;};
                tx.oncomplete=function(){if(owned)remove();else{report.preserved_collisions+=1;finish();}};
                tx.onabort=tx.onerror=function(){report.errors.push('Owned database validation failed');finish();};
            };
        });
    }};
}(window));

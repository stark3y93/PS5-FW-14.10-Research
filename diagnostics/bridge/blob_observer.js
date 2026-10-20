/* Runs only in our synthetic Blob navigation control. No files or credentials. */
(function(w,d){'use strict';
 if(w.location.protocol!=='blob:')return;
 var marker=d.getElementById('bridgeNonce');
 if(!marker||!w.opener)return;
 w.opener.postMessage({bridge:'ps5-blob-navigation-v1',nonce:marker.textContent,protocol:w.location.protocol},w.location.origin);
}(window,document));

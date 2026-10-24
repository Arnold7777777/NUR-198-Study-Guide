/* Open the folds that hold a deep-linked figure or topic, then scroll to it. */
(function(){function go(){var h=decodeURIComponent(location.hash.slice(1));if(!h)return;var t=document.getElementById(h);if(!t)return;
for(var e=t;e;e=e.parentElement){if(e.tagName==='DETAILS')e.open=true;}
if(t.tagName==='DETAILS')t.open=true;setTimeout(function(){t.scrollIntoView({block:'start'});},60);}
window.addEventListener('hashchange',go);if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',go);else go();})();

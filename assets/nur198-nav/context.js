/* Remember the module she is studying so a shared page (Mega Quiz, Medications ...) can send her back to it. */
(function(){
  var bar=document.querySelector('.n198ctx[data-module],.n198ctx[data-shared]'); if(!bar)return;
  var K='nur198-last-module', m=+bar.getAttribute('data-module');
  try{ if(m) sessionStorage.setItem(K,String(m)); else if(bar.hasAttribute('data-shared')) m=+sessionStorage.getItem(K); }catch(e){}
  if(!m)return;
  var here=bar.querySelector('.n198-mods a[href$="#m'+m+'"]'); if(here){here.classList.add('here');here.setAttribute('aria-current','true');}
  if(bar.hasAttribute('data-shared')){var b=bar.querySelector('.n198-back'); if(b){b.href=b.href.replace(/#.*$/,'#m'+m); b.textContent='← Back to Module '+m; b.hidden=false;}}
})();

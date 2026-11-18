/* Keep the reading toolbar available without covering the study notes. */
(()=>{'use strict';
 function init(){
  const bar=document.querySelector('.bar');if(!bar||bar.dataset.collapsible)return;
  bar.dataset.collapsible='true';bar.classList.add('collapsible-study-menu');
  const controls=document.createElement('div');controls.id='study-menu-controls';
  while(bar.firstChild)controls.append(bar.firstChild);
  const row=document.createElement('div');row.className='study-menu-heading wrap';
  const button=document.createElement('button');button.type='button';button.id='study-menu-toggle';button.setAttribute('aria-controls',controls.id);
  const hint=document.createElement('span');hint.className='study-menu-hint';hint.textContent='Filters & study tools';
  row.append(button,hint);bar.append(row,controls);
  const nav=document.getElementById('navBtns');if(nav){controls.append(nav);nav.classList.add('study-menu-links');}
  const key='nur198-study-menu-hidden';let saved=false;try{saved=localStorage.getItem(key)==='true';}catch{}
  function setHidden(hidden,focus){
   controls.hidden=hidden;button.setAttribute('aria-expanded',String(!hidden));button.textContent=hidden?'☰ Show menu':'− Hide menu';bar.classList.toggle('menu-closed',hidden);
   try{localStorage.setItem(key,String(hidden));}catch{}
   if(focus)button.focus();
  }
  button.addEventListener('click',()=>setHidden(!controls.hidden,false));
  bar.addEventListener('keydown',e=>{if(e.key==='Escape'&&!controls.hidden){e.preventDefault();setHidden(true,true);}});
  setHidden(saved,false);
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();

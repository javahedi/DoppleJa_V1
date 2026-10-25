/* DoppleJa: decorate an existing confirmed mutual-match modal; never invent matches. */
(() => {
 'use strict';
 const colors=['#FFD23B','#FFFFFF','#F8A5E2','#A999FF','#78E4CB','#FF9C66'];
 const decorate=panel=>{
   const overlay=panel.closest('.dj2-celebration');
   if(!overlay || overlay.classList.contains('dj-party-v1')) return;
   overlay.classList.add('dj-party-v1');
   const burst=document.createElement('div');
   burst.className='dj-party-confetti'; burst.setAttribute('aria-hidden','true');
   if(!window.matchMedia('(prefers-reduced-motion: reduce)').matches){
     const frag=document.createDocumentFragment();
     for(let i=0;i<38;i++){
       const piece=document.createElement('i');piece.className='dj-party-piece';
       const x=(i*73+17)%101, drift=((i*37)%141)-70;
       piece.style.setProperty('--x',x+'%');
       piece.style.setProperty('--w',(5+i%4)+'px');
       piece.style.setProperty('--h',(7+i%5)+'px');
       piece.style.setProperty('--c',colors[i%colors.length]);
       piece.style.setProperty('--r',((i*41)%360)+'deg');
       piece.style.setProperty('--drift',drift+'px');
       piece.style.setProperty('--delay',((i%9)*.075)+'s');
       piece.style.setProperty('--dur',(1.65+(i%7)*.14)+'s');
       frag.appendChild(piece);
     }
     burst.appendChild(frag);
   }
   panel.insertBefore(burst,panel.firstChild);
   // Escape closes the dialog; button click handles cleanup of its own listener.
   const close=overlay.querySelector('.dj2-celebration-close');
   const onKey=e=>{if(e.key==='Escape'){e.preventDefault();close?.click();}};
   document.addEventListener('keydown',onKey);
   const removalObserver=new MutationObserver(()=>{
     if(!overlay.isConnected){document.removeEventListener('keydown',onKey);removalObserver.disconnect();}
   });
   removalObserver.observe(document.body,{childList:true});
 };
 const check=node=>{
   if(!(node instanceof Element))return;
   if(node.matches('.dj2-celebration-panel'))decorate(node);
   node.querySelectorAll('.dj2-celebration-panel').forEach(decorate);
 };
 const observe=()=>{
   check(document.body);
   new MutationObserver(records=>records.forEach(r=>r.addedNodes.forEach(check)))
     .observe(document.body,{childList:true,subtree:true});
 };
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',observe,{once:true});
 else observe();
})();

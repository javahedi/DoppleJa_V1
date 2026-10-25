/* DoppleJa shared main-screen masthead and bottom nav. Presentation only. */
(() => {
  'use strict';
  const root = document.getElementById('app');
  if (!root) return;
  const brand = '/app-assets/assets/brand/doppleja-logo.svg';
  const icons = {
    discover:'<circle cx="10.5" cy="10.5" r="7"/><path d="m16 16 5 5"/>',
    matches:'<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z"/>',
    chats:'<path d="M21 11.5c0 5-4.1 9-9.3 9a10 10 0 0 1-4.3-1L3 21l1.4-4.3A8.8 8.8 0 0 1 3 12C3 7 7 3 12 3s9 3.6 9 8.5Z"/>',
    profile:'<circle cx="12" cy="8" r="4"/><path d="M4.5 21c.3-4.2 3.1-6.4 7.5-6.4s7.2 2.2 7.5 6.4"/>'
  };
  const labelByRoute = {discover:'Entdecken',matches:'Matches',likes:'Matches','my-jobs':'Matches',chats:'Chats',profile:'Profil'};
  function renderIcon(kind) { return `<span class="dj-nav-icon" aria-hidden="true"><svg viewBox="0 0 24 24">${icons[kind]}</svg></span>`; }
  function normalizeNav() {
    const nav = root.querySelector('.bottom-nav');
    if (!nav || nav.closest('.dj-chat3-conversation')) return;
    for (const button of nav.querySelectorAll('button[data-go]')) {
      const route = button.dataset.go;
      const kind = route==='discover'?'discover':(['matches','likes','my-jobs'].includes(route)?'matches':route==='chats'?'chats':route==='profile'?'profile':null);
      if (!kind) continue;
      // In older layouts, the old label may still say "Personal" or "Meine Likes".
      // Use the unified label while retaining the original route and click listener.
      if (button.dataset.djNavIcon==='v1') continue;
      button.dataset.djNavIcon='v1';
      button.innerHTML = `${renderIcon(kind)}<span class="dj-nav-label">${labelByRoute[route]}</span>`;
      button.setAttribute('aria-label',labelByRoute[route]);
    }
  }
  function normalizeHeaders(){
    // The page modules still create their own header markup; CSS handles final alignment.
    const chatHeader=root.querySelector('.dj-chat3-list > .header');
    if (chatHeader && !chatHeader.querySelector(':scope > img.dj-chat3-brand')) {
      const old=chatHeader.querySelector('.logo');
      if (old) {
        const img=document.createElement('img');
        img.src=brand; img.alt='DoppleJa';img.className='dj-chat3-brand';old.replaceWith(img);
      }
    }
  }
  let pending=false;
  function schedule(){
    if (pending) return;
    pending=true;
    queueMicrotask(()=>{pending=false;normalizeHeaders();normalizeNav();});
  }
  new MutationObserver(schedule).observe(root,{childList:true,subtree:false});
  if (document.readyState==='loading') document.addEventListener('DOMContentLoaded',schedule,{once:true});
  else schedule();
})();

/* DoppleJa Chats V3: scoped, presentation-only enhancements.
   The existing app continues to own navigation, form submission, WebSocket and review APIs. */
(() => {
  'use strict';
  const root = document.getElementById('app');
  if (!root) return;
  const icon = (kind) => {
    const shapes = {
      search:'<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
      sliders:'<path d="M4 7h9m4 0h3M4 17h3m4 0h9"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="17" r="2"/>',
      send:'<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
      briefcase:'<rect x="3" y="7" width="18" height="14" rx="2"/><path d="M8 7V5a2 2 0 012-2h4a2 2 0 012 2v2"/>',
      chevron:'<path d="m9 18 6-6-6-6"/>'
    };
    return `<svg aria-hidden="true" viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">${shapes[kind]}</svg>`;
  };
  const initials = name => (name || 'DJ').trim().split(/\s+/).slice(0,2).map(s=>s[0]||'').join('').toLocaleUpperCase('de-DE');
  const briefDate = value => {
    if (!value) return '';
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return '';
    const now=new Date();
    if(d.toDateString()===now.toDateString()) return d.toLocaleTimeString('de-DE',{hour:'2-digit',minute:'2-digit'});
    return d.toLocaleDateString('de-DE',{day:'2-digit',month:'2-digit'});
  };
  function setBrand(screen){
    const old = screen.querySelector(':scope > .header .logo');
    if (old) {
      const img=document.createElement('img');
      img.src='/app-assets/assets/brand/doppleja-logo.svg';img.alt='DoppleJa';img.className='dj-chat3-brand';old.replaceWith(img);
    }
  }
  function list(screen){
    if(screen.dataset.chat3==='list')return;
    if(screen.querySelector('h1.title')?.textContent.trim()!=='Nachrichten')return;
    screen.dataset.chat3='list';screen.classList.add('dj-chat3-list');setBrand(screen);
    const header=screen.querySelector('h1.title');
    const sub=screen.querySelector('p.subtitle');
    if(sub)sub.textContent='Deine Gespräche mit deinen Matches.';
    const oldLabel=screen.querySelector('.dj2-page-label');if(oldLabel)oldLabel.remove();
    const items=screen.querySelector('.dj2-match-list');if(!items)return;
    const cards=[...items.querySelectorAll('.dj2-match')];
    if(cards.length){
      const tools=document.createElement('div');tools.className='dj-chat3-tools';
      tools.innerHTML=`<label class="dj-chat3-search">${icon('search')}<input type="search" autocomplete="off" placeholder="Gespräche suchen …" aria-label="Gespräche suchen"></label><button type="button" class="dj-chat3-sort" aria-label="Neueste Gespräche zuerst" title="Nach neuester Aktivität sortiert">${icon('sliders')}</button>`;
      header?.parentNode.insertBefore(tools,items);
      const search=tools.querySelector('input');
      const sorted=[...cards];
      for(const card of cards){
        const name=card.querySelector('.dj2-match-person')?.textContent.trim()||'Dein Match';
        const work=card.querySelector('.dj2-match-job')?.textContent.trim()||'';
        const date=card.querySelector('.dj2-match-meta time')?.getAttribute('datetime')||'';
        const fullDateText=card.querySelector('.dj2-match-meta time')?.textContent.trim()||'';
        const preview=card.querySelector('.dj2-match-preview')?.textContent.trim()||'';
        const oldButton=card.querySelector('[data-open-match]');
        if(!oldButton)continue;
        const matchId=oldButton.getAttribute('data-open-match');
        const avatar=card.querySelector('.dj2-match-icon');
        if(avatar)avatar.textContent=initials(name);
        card.classList.add('dj-chat3-card');
        const info=card.querySelector('.dj2-match-content');
        if(info){
          const meta=info.querySelector('.dj2-match-meta');
          if(meta){
            const label=meta.querySelector('.dj2-match-status');
            const time=meta.querySelector('time');
            if(label)label.remove();
            if(time){time.classList.add('dj-chat3-timestamp');time.textContent=fullDateText;}
          }
          const jobEl=info.querySelector('.dj2-match-job');if(jobEl)jobEl.classList.add('dj-chat3-job');
        }
        oldButton.classList.add('dj-chat3-open');oldButton.textContent='';oldButton.setAttribute('aria-label',`Unterhaltung mit ${name} öffnen`);
        card.setAttribute('data-chat3-search',`${name} ${work} ${preview}`.toLocaleLowerCase('de-DE'));
        card.setAttribute('data-chat3-match',matchId||'');
      }
      search.addEventListener('input',()=>{
        const q=search.value.trim().toLocaleLowerCase('de-DE');
        cards.forEach(card=>{card.hidden=!card.getAttribute('data-chat3-search')?.includes(q);});
      });
      const sortButton=tools.querySelector('.dj-chat3-sort');
      sortButton.addEventListener('click',()=>{
        search.focus();
      });
    }
    const blank=items.querySelector('.dj2-blank');if(blank)blank.classList.add('dj-chat3-blank');
  }
  function conversation(screen){
    if(screen.dataset.chat3==='conversation')return;
    const box=screen.querySelector('.dj2-conversation');if(!box)return;
    screen.dataset.chat3='conversation';screen.classList.add('dj-chat3-conversation');
    const header=screen.querySelector(':scope > .header');if(header)header.classList.add('dj-chat3-hidden-header');
    const nav=screen.nextElementSibling?.matches('.bottom-nav')?screen.nextElementSibling:root.querySelector('.bottom-nav');
    if(nav)nav.classList.add('dj-chat3-hidden-nav');
    const identity=box.querySelector('.dj2-chat-identity');
    const name=identity?.querySelector('strong')?.textContent.trim()||'Dein Match';
    const job=identity?.querySelector('.dj2-chat-job')?.textContent.trim()||'';
    const avatar=box.querySelector('.dj2-chat-avatar');if(avatar)avatar.textContent=initials(name);
    const heading=box.querySelector('.dj2-chat-header');if(heading)heading.classList.add('dj-chat3-heading');
    const jobBanner=document.createElement('div');jobBanner.className='dj-chat3-job-banner';
    jobBanner.innerHTML=`<span class="dj-chat3-job-icon">${icon('briefcase')}</span><span class="dj-chat3-job-label"></span><span class="dj-chat3-job-arrow">${icon('chevron')}</span>`;
    jobBanner.querySelector('.dj-chat3-job-label').textContent=job||'Gemeinsames Match';
    heading?.insertAdjacentElement('afterend',jobBanner);
    const panel=box.querySelector('#dj54-review-panel');
    if(panel){
      const existing=panel.closest('details.dj-chat-v2-details');
      if(existing){existing.classList.add('dj-chat3-review-details');existing.querySelector('summary').textContent='Auftrag & Bewertung';}
      else{
        const d=document.createElement('details');d.className='dj-chat3-review-details';
        const sum=document.createElement('summary');sum.textContent='Auftrag & Bewertung';d.appendChild(sum);
        panel.before(d);d.appendChild(panel);
      }
    }
    jobBanner.addEventListener('click',()=>{
      const details=box.querySelector('.dj-chat3-review-details');if(details)details.open=!details.open;
    });
    jobBanner.setAttribute('role','button');jobBanner.tabIndex=0;jobBanner.setAttribute('aria-label','Auftrag und Bewertung anzeigen');
    jobBanner.addEventListener('keydown', e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();jobBanner.click();}});
    const tip=box.querySelector('.dj2-chat-tip');if(tip)tip.classList.add('dj-chat3-tip');
    const compose=box.querySelector('#chat-form');
    if(compose){compose.classList.add('dj-chat3-compose');const button=compose.querySelector('button[type=submit]');if(button)button.innerHTML=icon('send');}
    const area=box.querySelector('#messages');
    if(area)area.classList.add('dj-chat3-messages');
  }
  function enhance(){
    const screen=root.querySelector(':scope > section.screen');if(!screen)return;
    if(screen.querySelector('.dj2-conversation'))conversation(screen);
    else if(screen.querySelector('.dj2-match-list')&&screen.querySelector('h1.title')?.textContent.trim()==='Nachrichten')list(screen);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',enhance);else enhance();
  new MutationObserver(enhance).observe(root,{childList:true});
})();

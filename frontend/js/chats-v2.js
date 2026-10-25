/* DoppleJa Chats V2 – presentation-only enhancement of existing chat screens. */
(() => {
  'use strict';
  const root = document.getElementById('app');
  if (!root) return;
  const initials = name => (name || 'DJ').trim().split(/\s+/).slice(0,2).map(s=>s[0]||'').join('').toLocaleUpperCase('de-DE');
  function brandHeader(screen) {
    const header = screen.querySelector(':scope > .header');
    const logo = header?.querySelector('.logo');
    if (logo) {
      const img = document.createElement('img');
      img.src='/app-assets/assets/brand/doppleja-logo.svg';
      img.alt='DoppleJa';
      img.className='dj-chat-v2-brand';
      logo.replaceWith(img);
    }
  }
  function decorateList(screen) {
    if (screen.dataset.chatsV2) return;
    const heading=screen.querySelector('h1.title');
    if (!heading || heading.textContent.trim() !== 'Nachrichten') return;
    screen.dataset.chatsV2='true';
    screen.classList.add('dj-chats-v2');
    brandHeader(screen);
    const label=screen.querySelector('.dj2-page-label');
    if (label) label.textContent='DEINE VERBINDUNGEN';
    const sub=screen.querySelector('p.subtitle');
    if (sub) sub.textContent='Schreibe mit deinen gegenseitigen Matches.';
    const list=screen.querySelector('.dj2-match-list');
    if (!list) return;
    const cards=[...list.querySelectorAll('.dj2-match')];
    if (!cards.length) return;
    const tools=document.createElement('div');tools.className='dj-chat-v2-list-tools';
    const search=document.createElement('input');search.type='search';search.placeholder='Chats durchsuchen …';
    search.setAttribute('aria-label','Chats durchsuchen');
    tools.appendChild(search);
    const count=document.createElement('span');count.className='dj-chat-v2-total';count.textContent=`${cards.length} ${cards.length===1?'Chat':'Chats'}`;
    tools.appendChild(count);list.before(tools);
    cards.forEach(card=>{
      const icon=card.querySelector('.dj2-match-icon');
      const person=card.querySelector('.dj2-match-person')?.textContent||'DoppleJa';
      if(icon){icon.textContent=initials(person);icon.setAttribute('aria-hidden','true');}
      const button=card.querySelector('.dj2-match-open');
      if(button){button.textContent='Nachrichten öffnen →';}
    });
    search.addEventListener('input',()=>{
      const term=search.value.toLocaleLowerCase('de-DE').trim();
      let visible=0;
      cards.forEach(card=>{const show=card.textContent.toLocaleLowerCase('de-DE').includes(term);card.hidden=!show;if(show)visible++;});
      count.textContent=`${visible} ${visible===1?'Chat':'Chats'}`;
    });
  }
  function decorateConversation(screen) {
    if (screen.dataset.conversationV2) return;
    const conversation=screen.querySelector('.dj2-conversation');
    if(!conversation)return;
    screen.dataset.conversationV2='true';
    screen.classList.add('dj-conversation-v2');
    brandHeader(screen);
    const name=conversation.querySelector('.dj2-chat-identity strong')?.textContent||'Dein Match';
    const avatar=conversation.querySelector('.dj2-chat-avatar');
    if(avatar){avatar.textContent=initials(name);avatar.setAttribute('aria-hidden','true');}
    const header=conversation.querySelector('.dj2-chat-header');
    if(header)header.setAttribute('aria-label',`Chat mit ${name}`);
    const panel=conversation.querySelector('#dj54-review-panel');
    if(panel){
      const details=document.createElement('details');details.className='dj-chat-v2-details';
      const summary=document.createElement('summary');summary.textContent='Auftrag & Bewertung';
      details.appendChild(summary);panel.before(details);details.appendChild(panel);
    }
    const tip=conversation.querySelector('.dj2-chat-tip');
    if(tip)tip.textContent='Ihr habt euch gegenseitig geliked. Viel Erfolg beim Kennenlernen!';
    const send=conversation.querySelector('.dj2-compose button[type="submit"]');
    if(send)send.textContent='➤';
  }
  function update(){
    const screen=root.querySelector(':scope > section.screen');
    if(!screen)return;
    if(screen.querySelector('.dj2-conversation')) decorateConversation(screen);
    else if(screen.querySelector('.dj2-match-list')) decorateList(screen);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',update);
  else update();
  new MutationObserver(update).observe(root,{childList:true});
})();

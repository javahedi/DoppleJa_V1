/* PHASE_52B2_PREMIUM_DASHBOARDS */
/* PHASE_52A_START: premium onboarding; existing application modules remain intact */
/* DoppleJa V1: plain JavaScript SPA; all API calls stay same-origin. */
(() => {
  'use strict';
  const root = document.getElementById('app');
  const state = { registrationRole:'worker', user:null, profile:null, page:'home', categories:[], jobs:[],
    candidates:[], mine:[], matches:[], chats:[], selectedJob:null, editingJob:null,
    currentMatch:null, socket:null, filterCity:'', filterCategory:'', filterWorkType:'', busy:false, chatPoll:null };
  const esc = v => String(v ?? '').replace(/[&<>"']/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[s]));
  const money = v => v == null ? '' : `${Number(v).toLocaleString('de-DE',{maximumFractionDigits:2})} €`;
  const date = v => v ? new Date(v).toLocaleTimeString('de-DE',{hour:'2-digit',minute:'2-digit'}) : '';
  const $ = selector => root.querySelector(selector);
  const api = async (url, opts={}) => {
    const response = await fetch(url,{credentials:'same-origin',headers:{'Content-Type':'application/json',...(opts.headers || {})},...opts});
    const raw = await response.text(); let data; try{data = raw ? JSON.parse(raw) : null;}catch{data = raw;}
    if(!response.ok){let detail = data?.detail || `HTTP ${response.status}`;
    if(Array.isArray(detail)) detail = detail.map(x=>x.msg).join(', ');
    throw new Error(detail);}
    return data;
  };
  let toastTimer;
  const toast = message => { const t=document.getElementById('toast');
    t.textContent=message; t.classList.add('show');
    clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.classList.remove('show'),3600); };
  const run = async (fn) => {try{await fn();}catch(e){toast(e.message || 'Etwas ist schiefgelaufen.'); console.error(e);}};
  const field = (label,name,value='',extra='')=>`<label class="field">${esc(label)}<input name="${esc(name)}" value="${esc(value)}" ${extra}></label>`;
  const textarea = (label,name,value='')=>`<label class="field">${esc(label)}<textarea name="${esc(name)}" maxlength="1500">${esc(value)}</textarea></label>`;
  const options = (values,selected)=> values.map(([value,label])=>`<option value="${esc(value)}"
  ${String(selected??'')===String(value)?'selected':''}>${esc(label)}</option>`).join('');
  const select = (label,name,values,selected)=>`<label class="field">${esc(label)}<select name="${esc(name)}">${options(values,selected)}</select></label>`;
  const values = form => Object.fromEntries(new FormData(form).entries());
  const shell = (content, active='discover') =>
    `<section class="screen"><header class="header"><span class="logo">DoppleJa<span style="color:#ffd900">●</span></span><button class="back" data-go="settings" aria-label="Einstellungen">⚙</button></header>${content}</section><nav class="bottom-nav" aria-label="Hauptnavigation">${(state.user?.role==='employer'?[['discover','⌕','Entdecken'],['matches','♡','Matches'],['chats','☏','Chats'],['profile','♙','Profil']]:[['discover','⌕','Entdecken'],['matches','♡','Matches'],['chats','☏','Chats'],['profile','♙','Profil']]).map(([id,ic,label])=>`<button data-go="${id}" class="${active===id?'active':''}"><span>${ic}</span>${label}</button>`).join('')}</nav>`;
  const render = html => { root.innerHTML=html; root.scrollTop=0; window.scrollTo(0,0); };
  function closeChat(){if(state.socket){state.socket.onclose=null;state.socket.close();
    state.socket=null;}if(state.chatPoll){clearInterval(state.chatPoll);state.chatPoll=null;}}
  async function navigate(page){ if(state.page==='conversation'&&page!=='conversation')closeChat();state.page=page;
    render('<div class="loading">Lädt …</div>'); await run(async()=>{switch(page){case 'home':return home();
      case 'login':return loginView();case 'register':return registerChoiceView();case 'register-details':return registerView();case 'verification':return verifyView();case 'profile':return profileView();
      case 'discover':return discoveryView();case 'matches':return matchesView();case 'likes':return likesView();case 'chats':return chatsView();
      case 'conversation':return conversationView();case 'job-create':return jobFormView();
      case 'my-jobs':djMatchTab='jobs';return matchesView();case 'settings':return settingsView();default: return home();}});}

  function home(){render(`<section class="splash dj-welcome-v2" aria-label="DoppleJa Willkommen">
    <header class="dj-welcome-header"><img src="/app-assets/assets/brand/doppleja-logo.svg" alt="DoppleJa" class="dj-welcome-logo"></header>
    <div class="dj-welcome-body"><img class="dj-welcome-hero" src="/app-assets/assets/images/onboarding/hero-professions.webp" alt="Menschen aus Gastronomie, Pflege, Handwerk, Transport und Reinigung finden zueinander" width="887" height="990" fetchpriority="high">
      <div class="dj-welcome-copy"><h1>Viele Berufe.<br><span>Ein Match.</span></h1><p>Jobs finden. Mitarbeiter finden.<br>Einfach matchen.</p></div>
    </div>
    <div class="dj-welcome-actions"><button type="button" class="dj-welcome-button dj-welcome-primary" data-go="register">Registrieren <span aria-hidden="true">›</span></button>
    <button type="button" class="dj-welcome-button dj-welcome-secondary" data-go="login">Einloggen <span aria-hidden="true">›</span></button></div>
  </section>`);}
  function loginView(){render(`<section class="screen premium-auth"><button class="back" data-go="home">← Zurück</button>
    <div class="pa-kicker">DOPPLEJA · WILLKOMMEN ZURÜCK</div><h1 class="title topspace">Schön, dass du da bist! <span class="pa-yellow">✦</span></h1>
    <p class="subtitle">Einloggen und dort weitermachen, wo dein Match wartet.</p><div class="pa-login-decoration" aria-hidden="true">🤝</div>
    <form class="form" id="login-form">${field('E-Mail','email','','type="email" required autocomplete="email"')}${field('Passwort','password','',
      'type="password" required autocomplete="current-password"')}<button class="btn pa-primary" type="submit">Einloggen →</button></form>
      <p class="center"><button class="link-btn" data-go="register">Neu hier? Jetzt registrieren</button></p>
      <p class="pa-legal">Einfach anmelden. Kein Lebenslauf, keine Bewerbung.</p></section>`);}
  function registerChoiceView(){
    render(`<section class="dj-register-choice" aria-label="Registrierung: Rolle auswählen">
      <header class="dj-register-header">
        <button type="button" class="dj-register-back" data-go="home" aria-label="Zurück zur Startseite">‹</button>
        <img class="dj-register-logo" src="/app-assets/assets/brand/doppleja-logo.svg" alt="DoppleJa">
      </header>
      <div class="dj-register-heading"><h1>Willkommen bei <span>DoppleJa</span></h1>
        <h2>Wie möchtest du starten?</h2><p>Wähle aus, wie du DoppleJa nutzen möchtest.</p></div>
      <div class="dj-register-grid">
        <article class="dj-register-card dj-register-worker">
          <div class="dj-register-card-art"><img src="/app-assets/assets/images/registration/worker.webp" alt="Illustration einer Mitarbeiterin aus dem Handwerk"></div>
          <div class="dj-register-card-copy">
            <div class="dj-register-card-symbol" aria-hidden="true">♙</div><h3>Arbeit finden</h3>
            <p>Entdecke Jobs, die zu dir passen – ganz ohne Lebenslauf.</p>
            <ul><li>Passende Jobs entdecken</li><li>Einfach liken statt bewerben</li><li>Bei einem Match direkt chatten</li></ul>
            <button type="button" class="dj-register-cta dj-register-cta-purple" data-register-role="worker">Als Arbeitnehmer starten <span aria-hidden="true">→</span></button>
          </div>
        </article>
        <article class="dj-register-card dj-register-employer">
          <div class="dj-register-card-art"><img src="/app-assets/assets/images/registration/employer.webp" alt="Illustration eines Arbeitgebers mit Tablet"></div>
          <div class="dj-register-card-copy">
            <div class="dj-register-card-symbol" aria-hidden="true">♙</div><h3>Mitarbeiter finden</h3>
            <p>Finde passende Menschen für dein Unternehmen oder deinen privaten Bedarf.</p>
            <ul><li>Geeignete Menschen entdecken</li><li>Profile kennenlernen</li><li>Bei einem Match direkt chatten</li></ul>
            <button type="button" class="dj-register-cta dj-register-cta-yellow" data-register-role="employer">Als Arbeitgeber starten <span aria-hidden="true">→</span></button>
          </div>
        </article>
      </div><footer class="dj-register-footer">Bereits registriert? <button type="button" data-go="login">Einloggen →</button></footer>
    </section>`);
  }
  function registerView(){
    const worker=state.registrationRole==='worker';
    const role=worker?'worker':'employer';
    const heading=worker?'Arbeit finden':'Mitarbeiter finden';
    const hint=worker?'Erstelle dein Konto, um passende Jobs zu entdecken.':'Erstelle dein Konto, um passende Mitarbeiter zu finden.';
    render(`<section class="screen dj-account-create" aria-label="Konto erstellen">
      <header class="dj-account-head">
        <button type="button" class="dj-account-back" data-go="register" aria-label="Zurück zur Auswahl">‹</button>
        <img src="/app-assets/assets/brand/doppleja-logo.svg" alt="DoppleJa" width="190" height="66">
        <span aria-hidden="true"></span>
      </header>
      <div class="dj-account-hero">
        <div class="dj-account-label">${worker?'ARBEITNEHMER':'ARBEITGEBER'} · REGISTRIERUNG</div>
        <h1>Konto erstellen</h1>
        <p>${hint}</p>
        <div class="dj-account-role"><span class="dj-account-role-icon" aria-hidden="true">${worker?'♙':'▣'}</span><strong>${heading}</strong>
          <button type="button" data-go="register">Ändern</button></div>
      </div>
      <form class="dj-account-form" id="register-form">
        <input type="hidden" name="role" value="${role}">
        <label>E-Mail-Adresse
          <input name="email" type="email" autocomplete="email" placeholder="name@beispiel.de" required maxlength="254"></label>
        <label>Passwort <small>(mindestens 10 Zeichen)</small>
          <input name="password" type="password" autocomplete="new-password" placeholder="Dein Passwort" required minlength="10"></label>
        <p class="dj-account-note">Nach der Registrierung bestätigst du deine E-Mail-Adresse. Danach kannst du dein Profil erstellen.</p>
        <button class="dj-account-submit" type="submit">Konto erstellen <span aria-hidden="true">→</span></button>
      </form>
      <div class="dj-account-footer">Schon ein Konto? <button type="button" data-go="login">Einloggen</button></div>
    </section>`);
  }
  function verifyView(){render(`<section class="screen premium-auth pa-verify">
    <div class="pa-verify-icon">✉️</div><h1 class="title">Jetzt E-Mail bestätigen</h1>
    <p class="subtitle">Öffne den Bestätigungslink, um DoppleJa freizuschalten.</p>
    <div class="notice">Im lokalen Entwicklermodus steht der Link in den Docker-Logs:<br><code>docker compose logs --tail=80 api</code></div>
    <button class="btn pa-primary" data-go="login">Zum Login →</button></section>`);}
  async function loadMe(){try{state.user=await api('/api/auth/me');return true;}catch{state.user=null;return false;}}
  // PHASE_54B_PUBLIC_REPUTATION: summary from received reviews only, never made-up scores.
  const readRating=async userId=>{
    if(!userId)return null;
    try{return await api('/api/users/'+encodeURIComponent(userId)+'/rating');}
    catch(e){console.warn('Rating unavailable:',e);return null;}
  };
  const ratingView=(rating,extraClass='')=>{
    if(!rating)return `<div class="dj54b-rating ${extraClass}" aria-label="Bewertungsstatus nicht verfügbar">Bewertungen derzeit nicht verfügbar</div>`;
    if(!rating.count||rating.average==null)return `<div class="dj54b-rating dj54b-unrated ${extraClass}">☆ Noch keine Bewertungen</div>`;
    const avg=Number(rating.average).toLocaleString('de-DE',{minimumFractionDigits:1,maximumFractionDigits:1});
    const total=Number(rating.count);
    return `<div class="dj54b-rating ${extraClass}" aria-label="${esc(avg)} von 5 Sternen aus ${total} Bewertungen"><span aria-hidden="true">★</span> <strong>${esc(avg)} / 5</strong> <span>(${total} ${total===1?'Bewertung':'Bewertungen'})</span></div>`;
  };
  const receivedReviews=async userId=>{
    try{return await api('/api/users/'+encodeURIComponent(userId)+'/reviews?limit=20');}
    catch(e){console.warn('Review history unavailable:',e);return null;}
  };
  const reviewHistory=items=>{
    if(items===null)return '<p class="dj54b-muted">Bewertungen können momentan nicht geladen werden.</p>';
    if(!items.length)return '<p class="dj54b-muted">Noch keine Bewertungen aus abgeschlossenen Aufträgen.</p>';
    return items.map(r=>`<article class="dj54b-review"><div class="dj54b-review-top"><span class="dj54b-review-stars" aria-label="${Number(r.stars)} von 5 Sternen">${'★'.repeat(Number(r.stars))}</span><time>${esc(new Date(r.created_at).toLocaleDateString('de-DE'))}</time></div>${r.comment?`<p>${esc(r.comment)}</p>`:'<p class="dj54b-muted">Ohne Kommentar</p>'}</article>`).join('');
  };
  async function profileView(){
    if(!state.user)return navigate('login');
    let profile;
    try { profile=await api(state.user.role==='worker'?'/api/workers/me':'/api/employers/me'); }
    catch(e){if(!e.message.includes('404')&&!e.message.includes('Complete'))console.warn(e);profile=null;}
    state.profile=profile;
    const [myRating,myReviews]=await Promise.all([readRating(state.user.id),receivedReviews(state.user.id)]);
    const p=profile||{}, worker=state.user.role==='worker';
    const isOwnPhoto=Boolean(p.photo_url);
    const image=isOwnPhoto?esc(p.photo_url):(worker?art(workerArtwork(p.profession)):art(/bau|montage|handwerk|maler/i.test(p.category||'')?'employer-craft.webp':/gesund|pflege|medizin/i.test(p.category||'')?'employer-care.webp':'employer-cafe.webp'));
    const overview=worker?`<div class="dj-detail-grid"><div><span>Beruf</span><strong>${esc(p.profession||'Noch offen')}</strong></div><div><span>Verfügbarkeit</span><strong>${esc(p.availability||'Flexibel')}</strong></div></div>`:
      `<div class="dj-detail-grid"><div><span>Typ</span><strong>${p.employer_type==='business'?'Unternehmen':'Privatperson'}</strong></div><div><span>Bereich</span><strong>${esc(p.category||'Personal gesucht')}</strong></div></div>`;
    render(shell(`<div class="dj-page-eyebrow">MEIN DOPPLEJA</div><h1 class="title">${profile?'Mein Profil':'Profil erstellen'}</h1>
      <p class="subtitle">${worker?'Zeig deine Stärken – ganz ohne Lebenslauf.':'Zeig, wer hinter deinen Stellenanzeigen steht.'}</p>
      <section class="dj-profile-banner"><img src="${image}" alt="" loading="lazy"><div class="dj-photo-label">${isOwnPhoto?'Profilbild':'Symbolbild'}</div><div class="dj-profile-overlay"><span class="dj-profile-chip">${worker?'Jobsuchend':p.employer_type==='business'?'Unternehmen':'Arbeitgeber'}</span><h2>${esc(p.display_name||'Dein DoppleJa Profil')}</h2><p>⌖ ${esc(p.city||'Deutschland')}</p></div></section>
      ${overview}
      <section class="dj54b-profile-panel" aria-label="Öffentliche Bewertungen"><div class="dj54b-profile-heading"><h2>Bewertungen</h2><span>Nach abgeschlossenen Aufträgen</span></div>
      ${ratingView(myRating,'dj54b-rating-large')}
      <details class="dj54b-history"><summary>Bewertungen ansehen <span aria-hidden="true">⌄</span></summary><div>${reviewHistory(myReviews)}</div></details></section>
      <section class="dj-glass-panel"><div class="dj-panel-heading"><h2>Profil bearbeiten</h2><span>Jederzeit änderbar</span></div>
      <form id="profile-form" class="form">${worker?`${field('Name','display_name',p.display_name||'','required minlength="2"')}
      ${field('Beruf / Position','profession',p.profession||'')}${field('Stadt','city',p.city||'')}
      ${select('Verfügbarkeit','availability',[['','Bitte wählen'],['Ab sofort','Ab sofort'],['In 1–2 Wochen','In 1–2 Wochen'],['Flexibel','Flexibel']],p.availability||'')}
      ${textarea('Kurz über mich','bio',p.bio||'')}`:`${select('Wer sucht Personal?','employer_type', [['private','Privatperson'],['business','Unternehmen / Organisation']],p.employer_type||'private')}
      ${field('Name / Betrieb','display_name',p.display_name||'','required minlength="2"')}
      ${field('Bereich (optional)','category',p.category||'')}${field('Stadt','city',p.city||'')}
      ${textarea('Kurzbeschreibung','description',p.description||'')}`}
      ${field('Foto-/Logo-URL (optional)','photo_url',p.photo_url||'','type="url"')}
      <p class="dj-small-note">Ohne eigenes Foto verwenden wir ein deutlich gekennzeichnetes Symbolbild.</p>
      <button class="btn" type="submit">Profil speichern →</button></form></section>`, 'profile'));
  }
    async function loadCategories(){if(!state.categories.length)state.categories=await api('/api/categories');}
  const categoryName=id=>state.categories.find(c=>c.id===id)?.name||'Job';
  // Phase 5.2B: Category artwork is illustrative, never a user's verified photo.
  const jobArtwork = Object.freeze({
    1:'job-cafe.webp', 2:'job-care.webp', 3:'job-logistics.webp',
    4:'job-craft.webp', 5:'job-painting.webp', 6:'job-cleaning.webp',
    7:'job-events.webp', 8:'job-retail.webp', 9:'job-craft.webp'
  });
  const workerArtwork = profession => {
    const text=String(profession||'').toLowerCase();
    if(/pflege|gesund|kranken|medizin|arzt|therap/.test(text)) return 'candidate-care.webp';
    if(/maler|bau|tischler|handwerk|elektr|montage|schrein/.test(text)) return 'candidate-craft.webp';
    return 'candidate-service.webp';
  };
  const art = filename => '/app-assets/assets/dj-people/'+filename;
  const workLabel = type => ({minijob:'Minijob',part_time:'Teilzeit',full_time:'Vollzeit',temporary:'Tagesjob / Kurzfristig'})[type] || type || 'Job';
  // DISCOVER_V2_BEGIN: compact multi-card feed; all records come from existing APIs.
  const djDiscoverMoney = job => job.hourly_pay_min == null && job.hourly_pay_max == null ? '' :
    `${job.hourly_pay_min != null ? money(job.hourly_pay_min) : ''}${job.hourly_pay_max != null ? (job.hourly_pay_min != null ? '–' : '') + money(job.hourly_pay_max) : ''} / Std.`;
  const djDiscoverJob = job => `<article class="djv2-card djv2-job" aria-label="Stellenangebot ${esc(job.title)}">
    <div class="djv2-image"><img src="${art(jobArtwork[job.category_id]||'job-craft.webp')}" alt="Symbolbild ${esc(categoryName(job.category_id))}" loading="lazy"><span class="djv2-image-tag">Symbolbild</span></div>
    <div class="djv2-card-body"><h2>${esc(job.title)}</h2><p class="djv2-quiet">${esc(categoryName(job.category_id))}</p>
      <p class="djv2-fact">⌖ ${esc(job.city||'Ort offen')}</p><p class="djv2-fact">▣ ${esc(workLabel(job.work_type))}</p>
      ${djDiscoverMoney(job)?`<p class="djv2-fact">€ ${esc(djDiscoverMoney(job))}</p>`:''}
      <div class="djv2-tags"><span>${esc(categoryName(job.category_id))}</span><span>${esc(workLabel(job.work_type))}</span></div>
      <details class="djv2-description"><summary>Stellendetails</summary><p>${esc(job.description||'Keine Beschreibung vorhanden.')}</p></details>
      <div class="djv2-actions"><button type="button" class="djv2-skip" data-swipe="pass" data-discover-id="${esc(job.id)}">Überspringen</button>
      <button type="button" class="djv2-like" data-swipe="like" data-discover-id="${esc(job.id)}" aria-label="${esc(job.title)} liken">♡ Interessant</button></div>
    </div></article>`;
  const djDiscoverCandidate = p => `<article class="djv2-card djv2-candidate" aria-label="Kandidat ${esc(p.display_name||'')}">
    <div class="djv2-image"><img src="${p.photo_url?esc(p.photo_url):art(workerArtwork(p.profession))}" alt="${p.photo_url?'Profilfoto':'Symbolbild'}" loading="lazy"><span class="djv2-image-tag">${p.photo_url?'Profilfoto':'Symbolbild'}</span></div>
    <div class="djv2-card-body"><h2>${esc(p.display_name||'Profil')}</h2><p class="djv2-quiet">${esc(p.profession||'Tätigkeit offen')}</p>
      ${p.city?`<p class="djv2-fact">⌖ ${esc(p.city)}</p>`:''}${p.availability?`<p class="djv2-fact">◷ ${esc(p.availability)}</p>`:''}
      <div class="djv2-tags">${p.profession?`<span>${esc(p.profession)}</span>`:''}</div>
      <details class="djv2-description"><summary>Profil ansehen</summary><p>${esc(p.bio||'Noch keine Beschreibung vorhanden.')}</p></details>
      <div class="djv2-actions"><button type="button" class="djv2-skip" data-swipe="pass" data-discover-id="${esc(p.user_id)}">Überspringen</button>
      <button type="button" class="djv2-like" data-swipe="like" data-discover-id="${esc(p.user_id)}" aria-label="${esc(p.display_name||'Profil')} liken">♡ Interessant</button></div>
    </div></article>`;
  function djDiscoverChips(selected=''){
    return `<div class="djv2-chips" aria-label="Bereich wählen"><button type="button" class="${!selected?'on':''}" data-discover-category="">Alle</button>${state.categories.map(c=>`<button type="button" class="${String(selected)===String(c.id)?'on':''}" data-discover-category="${esc(c.id)}">${esc(c.name)}</button>`).join('')}</div>`;
  }
  async function discoveryView(){
    if(!state.user)return navigate('login');await loadCategories();const worker=state.user.role==='worker';
    let items=[];
    if(worker){
      state.jobs=await api('/api/discovery/jobs'+(state.filterCity||state.filterCategory?'?'+new URLSearchParams({...(state.filterCity?{city:state.filterCity}:{}),...(state.filterCategory?{category_id:state.filterCategory}:{})}):''));
      items=state.jobs.filter(j=>!state.filterWorkType||j.work_type===state.filterWorkType);
    }else{
      state.mine=(await api('/api/jobs/mine')).filter(j=>j.is_active&&!j.archived_at);
      if(!state.selectedJob||!state.mine.some(j=>j.id===state.selectedJob))state.selectedJob=state.mine[0]?.id||null;
      state.candidates=state.selectedJob?await api('/api/discovery/workers?job_id='+encodeURIComponent(state.selectedJob)):[];
      items=state.candidates;
    }
    const heading=worker?'Entdecke Jobs':'Entdecke Talente';
    const subtitle=worker?'Finde passende Stellen in deiner Nähe.':'Finde passende Mitarbeiter für dein Team.';
    const controls=worker?`<div class="djv2-filter-row">
       <label class="djv2-search"><span aria-hidden="true">⌕</span><input id="djv2-search" type="search" placeholder="Jobtitel, Stichwort oder Ort" aria-label="Jobs durchsuchen"></label>
       <button type="button" class="djv2-filter-toggle" id="djv2-filter-toggle" aria-expanded="false" aria-controls="djv2-filter-panel">☷ <span class="sr-only">Filter</span></button></div>
       ${djDiscoverChips(state.filterCategory)}
       <section id="djv2-filter-panel" class="djv2-filters" hidden>
         <label>Stadt<input id="filter-city" placeholder="z. B. Berlin" value="${esc(state.filterCity)}"></label>
         <label>Jobmodell<select id="filter-worktype">${options([['','Alle Jobmodelle'],['minijob','Minijob'],['part_time','Teilzeit'],['full_time','Vollzeit'],['temporary','Tagesjob / Kurzfristig']],state.filterWorkType)}</select></label>
         <button type="button" id="filter-apply">Filter anwenden</button><button type="button" id="filter-reset">Zurücksetzen</button></section>`:
      `<div class="djv2-filter-row"><label class="djv2-search"><span aria-hidden="true">⌕</span><input id="djv2-search" type="search" placeholder="Beruf, Stichwort oder Ort" aria-label="Talente durchsuchen"></label></div>
       ${state.mine.length?`<div class="djv2-job-picker">${select('Talente für diese Stelle','job-picker',state.mine.map(j=>[j.id,j.title+' · '+j.city]),state.selectedJob)}</div>`:`<div class="djv2-nojob">Erstelle zuerst eine aktive Stelle. <button type="button" data-go="job-create">Stelle erstellen</button></div>`}`;
    const cards=items.map(i=>worker?djDiscoverJob(i):djDiscoverCandidate(i)).join('');
    const content=`<div class="djv2-discover" data-discover-role="${worker?'worker':'employer'}">
       <header class="djv2-top"><img src="/app-assets/assets/brand/doppleja-logo.svg" alt="DoppleJa"><button type="button" data-go="settings" aria-label="Einstellungen">⚙</button></header>
       <h1>${heading}</h1><p class="djv2-subtitle">${subtitle}</p>${controls}
       <div class="djv2-feed" id="djv2-feed">${cards||`<section class="djv2-empty"><div class="djv2-empty-symbol">♡</div><h2>Im Moment keine neuen ${worker?'Jobs':'Profile'}</h2><p>${worker?'Versuche andere Filter oder schau später wieder vorbei.':state.mine.length?'Für diese Stelle sind derzeit keine weiteren Profile verfügbar.':'Veröffentliche eine Stelle, um Talente zu entdecken.'}</p></section>`}</div>
       <p class="djv2-data-note">${worker?'Berufsbilder sind illustrative Symbolbilder.':'Ohne eigenes Profilfoto zeigen wir ein Symbolbild.'} Es werden nur tatsächlich verfügbare Einträge angezeigt. ${worker&&state.filterWorkType?'Der Jobmodellfilter gilt für die aktuell geladenen Ergebnisse.':''}</p>
       </div>`;
    render(shell(content,'discover'));
    const rootFeed=root.querySelector('#djv2-feed');
    const search=root.querySelector('#djv2-search');
    if(search&&rootFeed)search.addEventListener('input',()=>{
      const q=search.value.trim().toLocaleLowerCase('de');let shown=0;
      rootFeed.querySelectorAll('.djv2-card').forEach((card,i)=>{
        const item=items[i];const searchable=worker?[item.title,item.city,categoryName(item.category_id),item.description]:[item.display_name,item.profession,item.city,item.bio];
        const visible=!q||searchable.some(value=>String(value||'').toLocaleLowerCase('de').includes(q));card.hidden=!visible;if(visible)shown++;
      });
      let empty=rootFeed.querySelector('.djv2-search-empty');
      if(!shown&&items.length){if(!empty){empty=document.createElement('p');empty.className='djv2-search-empty';rootFeed.appendChild(empty);}empty.textContent='Keine Treffer für diese Suche.';}
      else if(empty)empty.remove();
    });
  }
  async function swipe(action,recordId){
    if(state.busy)return;
    const worker=state.user.role==='worker';
    const job_id=worker?(recordId||state.jobs[0]?.id):state.selectedJob;
    const worker_id=worker?null:(recordId||state.candidates[0]?.user_id);
    if(!job_id||(!worker&& !worker_id))return;
    state.busy=true;
    try{const response=await api('/api/swipes',{method:'POST',body:JSON.stringify({job_id,action,...worker_id?{worker_id}:{}})});
      if(!response.is_match)toast(action==='like'?'♥ Interesse gespeichert':'Übersprungen');
      await discoveryView();if(response.is_match)showMatchCelebration();
    }catch(e){toast(e.message);}finally{state.busy=false;}
  }
  // DISCOVER_V2_END

  function showMatchCelebration(){
    const old=document.querySelector('.dj2-celebration');if(old)old.remove();
    const overlay=document.createElement('div');overlay.className='dj2-celebration';
    overlay.innerHTML=`<div class="dj2-celebration-panel" role="dialog" aria-modal="true" aria-label="Neues Match">
      <div class="dj2-celebration-icon">🤝</div><h2>It's a Match!</h2>
      <p>Ihr habt euch beide geliked. Jetzt könnt ihr miteinander chatten.</p>
      <button class="btn dj2-celebration-chats" type="button">Zu den Nachrichten →</button>
      <button class="dj2-celebration-close" type="button">Weiter entdecken</button></div>`;
    overlay.querySelector('.dj2-celebration-close').addEventListener('click',()=>overlay.remove());
    overlay.querySelector('.dj2-celebration-chats').addEventListener('click',()=>{overlay.remove();navigate('chats');});
    document.body.appendChild(overlay);
    overlay.querySelector('.dj2-celebration-chats')?.focus();
  }
  const jobStatus = j=>j.archived_at?'Archiviert':j.is_active?'Aktiv':'Pausiert';
  async function myJobsView(){
    if(state.user?.role!=='employer')return navigate('discover');
    state.mine=await api('/api/jobs/mine');
    const active=state.mine.filter(j=>j.is_active&&!j.archived_at).length;
    const paused=state.mine.filter(j=>!j.is_active&&!j.archived_at).length;
    const archived=state.mine.filter(j=>j.archived_at).length;
    const list=state.mine.map(j=>`<article class="manage-card dj-job-manage" data-job="${esc(j.id)}">
      <div class="dj-manage-heading"><div class="dj-job-thumb"><img src="${art(jobArtwork[j.category_id]||'job-craft.webp')}" alt="" loading="lazy"><span>Symbolbild</span></div>
      <div class="dj-job-main"><strong>${esc(j.title)}</strong><small>⌖ ${esc(j.city)} · ${esc(workLabel(j.work_type))}</small>
      <span class="job-status ${j.archived_at?'archived':j.is_active?'active':'paused'}">${jobStatus(j)}</span></div></div>
      <p class="pay">${money(j.hourly_pay_min)}${j.hourly_pay_max!=null?' – '+money(j.hourly_pay_max):''} <span class="dj-pay-unit">/ Stunde</span></p>
      <p class="desc">${esc(j.description||'Keine Beschreibung')}</p>
      <div class="job-controls">${j.archived_at?'<span class="small-muted">Archivierte Jobs können nicht verändert werden.</span>':
        `<button class="btn small ghost" data-edit-job="${esc(j.id)}">Bearbeiten</button>
        <button class="btn small ghost" data-job-action="${j.is_active?'pause':'reactivate'}" data-job-id="${esc(j.id)}">${j.is_active?'Pausieren':'Reaktivieren'}</button>
        <button class="btn small archive-btn" data-job-action="archive" data-job-id="${esc(j.id)}">Archivieren</button>`}</div>
      </article>`).join('');
    render(shell(`<div class="dj-page-eyebrow">ARBEITGEBER-DASHBOARD</div>
      <div class="row dj-headline-row"><h1 class="title">Meine Jobs</h1><button class="btn small" data-new-job>+ Job</button></div>
      <p class="subtitle">Verwalte deine Anzeigen und finde passendes Personal.</p>
      <div class="dj-stat-grid"><div><strong>${active}</strong><span>Aktiv</span></div><div><strong>${paused}</strong><span>Pausiert</span></div><div><strong>${archived}</strong><span>Archiviert</span></div></div>
      <h2 class="dj-section-title">Deine Stellenanzeigen</h2>
      ${list||`<div class="empty"><div class="emoji">✦</div><h3>Dein erster Job wartet</h3>
      <p>Erstelle eine Anzeige und entdecke passende Menschen.</p><button class="btn" data-new-job>Job erstellen</button></div>`}`,'my-jobs'));
  }
    async function jobFormView(){
    if(state.user?.role!=='employer')return navigate('discover');await loadCategories();
    const editing=state.editingJob ? await api('/api/jobs/'+encodeURIComponent(state.editingJob)) : null;
    const j=editing||{};
    render(shell(`<button class="back" data-go="my-jobs">← Zurück</button>
      <h1 class="title topspace">${editing?'Job bearbeiten':'Job erstellen'}</h1>
      <p class="subtitle">Nur das Wichtigste. Kein langes Bewerbungsverfahren.</p>
      <form id="job-form" class="form">${select('Bereich','category_id',
        state.categories.map(c=>[c.id,c.name]),j.category_id||1)}${field('Position','title',j.title||'',
          'required minlength="3" placeholder="z. B. Servicekraft"')}${field('Stadt','city',j.city||state.profile?.city||'',
            'required')}${select('Arbeitsmodell','work_type',[['minijob','Minijob'],['part_time','Teilzeit'],['full_time',
              'Vollzeit'],['temporary','Tagesjob / Kurzfristig']],j.work_type||'part_time')}${field('Stundenlohn ab (€)',
                'hourly_pay_min',j.hourly_pay_min||'','type="number" min="0" step="0.01"')}${field('Stundenlohn bis (€)',
                  'hourly_pay_max',j.hourly_pay_max||'','type="number" min="0" step="0.01"')}${textarea('Kurzbeschreibung',
                    'description',j.description||'')}<button class="btn" type="submit">${editing?'Änderungen speichern':
                      'Job veröffentlichen'}</button></form>`,'my-jobs'));
  }
  async function likesView(){
    if(state.user?.role!=='worker')return navigate('discover');
    const [items, summaries]=await Promise.all([api('/api/workers/me/likes'),api('/api/match-summaries')]);
    const summariesById=new Map(summaries.map(m=>[m.match_id,m]));
    const counts={matched:0,pending:0,unavailable:0};items.forEach(i=>{if(i.status in counts)counts[i.status]++;});
    const statusInfo={pending:['Warten','pending'],matched:['Match','active'],unavailable:['Nicht mehr verfügbar','archived']};
    const cards=items.map(j=>{
      const [label,cls]=statusInfo[j.status]||statusInfo.pending;
      const details=j.match_id?summariesById.get(j.match_id):null;
      const activity=details?(details.has_messages?`Unterhaltung läuft · ${esc(details.last_message.content)} · ${fullDate(details.last_message.created_at)}`:
        `Neues Match · ${esc(details.other_party_name)} · ${fullDate(details.matched_at)}`):'';
      const category=String(j.category||'').toLowerCase();
      const image=/gastr|café|restaurant/.test(category)?'job-cafe.webp':/reinigung/.test(category)?'job-cleaning.webp':
        /pflege|gesund/.test(category)?'job-care.webp':/logistik|transport/.test(category)?'job-logistics.webp':
        /maler/.test(category+' '+j.title.toLowerCase())?'job-painting.webp':'job-craft.webp';
      return `<article class="manage-card dj-like-card"><div class="dj-manage-heading"><div class="dj-job-thumb"><img src="${art(image)}" alt="" loading="lazy"><span>Symbolbild</span></div>
        <div class="dj-job-main"><strong>${esc(j.title)}</strong><small>${esc(j.city)} · ${esc(j.category)}</small><span class="job-status ${cls}">${j.status==='matched'?'🤝 ':j.status==='pending'?'♥ ':''}${label}</span></div></div>
        <p class="pay">${money(j.hourly_pay_min)}${j.hourly_pay_max!=null?' – '+money(j.hourly_pay_max):''}<span class="dj-pay-unit"> / Std.</span></p>
        <div class="meta"><span class="pill">${esc(workLabel(j.work_type))}</span></div>
        <p class="desc">${esc(j.description||'Keine Beschreibung')}</p>
        ${activity?`<p class="match-activity">${activity}</p>`:''}
        ${j.status==='matched'&&j.match_id?`<div class="job-controls"><button class="btn small" data-open-match="${esc(j.match_id)}">🤝 Match ansehen →</button></div>`:''}
      </article>`;
    }).join('');
    render(shell(`<div class="dj-page-eyebrow">DEINE FAVORITEN</div><h1 class="title">Meine Likes ♥</h1>
      <p class="subtitle">Alles, was dir gefällt – und jedes echte Match.</p>
      <div class="dj-stat-grid"><div><strong>${counts.pending}</strong><span>Warten</span></div><div><strong>${counts.matched}</strong><span>🤝 Matches</span></div><div><strong>${counts.unavailable}</strong><span>Nicht verfügbar</span></div></div>
      <h2 class="dj-section-title">Deine gemerkten Jobs</h2>
      ${cards||`<div class="empty"><div class="emoji">♡</div><h3>Noch keine Likes</h3>
      <p>Tippe auf das Herz eines Jobs, um ihn hier wiederzufinden.</p><button class="btn" data-go="discover">Jobs entdecken</button></div>`}`,'likes'));
  }
    const fullDate = v => v ? new Date(v).toLocaleString('de-DE', {day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit'}) : '';
  const summaryHeader = m => `${esc(m.job_title)} · ${esc(m.other_party_name)}`;
  // PHASE_52C_PREMIUM_MATCHES_CHAT: summary data from /api/match-summaries.
  const matchCard = m => {
    const newer = !m.has_messages;
    const stamp = newer ? m.matched_at : m.last_message?.created_at;
    const teaser = newer ? 'Ihr könnt jetzt miteinander schreiben.' : (m.last_message?.content || 'Unterhaltung läuft');
    return `<article class="dj2-match" aria-label="Match mit ${esc(m.other_party_name)}">
      <div class="dj2-match-icon" aria-hidden="true">🤝</div>
      <div class="dj2-match-content">
        <strong class="dj2-match-person">${esc(m.other_party_name)}</strong>
        <div class="dj2-match-job">${esc(m.job_title)} · ${esc(m.city||'')}</div>
        <div class="dj2-match-meta"><span class="dj2-match-status ${newer?'dj2-new':'dj2-active'}">${newer?'Neues Match':'Unterhaltung läuft'}</span><time>${fullDate(stamp)}</time></div>
        <p class="dj2-match-preview">${esc(teaser)}</p>
      </div>
      <button type="button" class="dj2-match-open" data-open-match="${esc(m.match_id)}" aria-label="Chat mit ${esc(m.other_party_name)} öffnen">Chat öffnen <span aria-hidden="true">→</span></button>
    </article>`;
  };
  // MATCHES_V3_BEGIN: shared Matches page, role-specific tabs and real records only.
  let djMatchTab = 'matches';
  const djMatchLogo = `<header class="dj-mv-head"><img src="/app-assets/assets/brand/doppleja-logo.svg" alt="DoppleJa"><button type="button" data-go="settings" aria-label="Einstellungen" class="dj-mv-settings">⚙</button></header>`;
  const djMatchTabs = role => role === 'employer' ? [['matches','Matches'],['likes','Likes'],['jobs','Meine Jobs']] : [['matches','Matches'],['likes','Meine Likes']];
  const djMatchRow = m => `<article class="dj-mv-card">
      <div class="dj-mv-card-top"><span class="dj-mv-avatar" aria-hidden="true">${esc((m.other_party_name||'?').trim().charAt(0).toUpperCase())}</span>
      <div class="dj-mv-card-body"><strong>${esc(m.other_party_name)}</strong><span>${esc(m.job_title)} · ${esc(m.city||'')}</span>
      <small>${m.has_messages?'Unterhaltung läuft':'Neues gegenseitiges Match'} · ${fullDate(m.matched_at)}</small></div>
      <span class="dj-mv-pill dj-mv-pill-match">Match</span></div>
      <div class="dj-mv-card-actions"><button type="button" data-open-match="${esc(m.match_id)}" class="dj-mv-primary">Nachricht schreiben →</button></div>
    </article>`;
  const djWorkerLikeRow = j => `<article class="dj-mv-card"><div class="dj-mv-card-top">
    <div class="dj-mv-avatar dj-mv-job-icon" aria-hidden="true">▣</div>
    <div class="dj-mv-card-body"><strong>${esc(j.title)}</strong><span>${esc(j.city)} · ${esc(j.category)}</span>
    <small>${esc(workLabel(j.work_type))}${j.hourly_pay_min!=null?' · ab '+money(j.hourly_pay_min)+'/Std.':''}</small></div>
    <span class="dj-mv-pill ${j.status==='matched'?'dj-mv-pill-match':j.status==='unavailable'?'dj-mv-pill-muted':'dj-mv-pill-wait'}">${j.status==='matched'?'Match':j.status==='unavailable'?'Nicht verfügbar':'Wartet'}</span></div>
    ${j.match_id?`<div class="dj-mv-card-actions"><button class="dj-mv-primary" data-open-match="${esc(j.match_id)}">Nachricht schreiben →</button></div>`:''}
    </article>`;
  const djEmployerLikeRow = j => `<article class="dj-mv-card"><div class="dj-mv-card-top">
    <span class="dj-mv-avatar" aria-hidden="true">${esc((j.worker_name||'?').trim().charAt(0).toUpperCase())}</span>
    <div class="dj-mv-card-body"><strong>${esc(j.worker_name)}</strong><span>${esc(j.profession||'Jobsuchend')} · ${esc(j.city||'')}</span>
    <small>Für: ${esc(j.job_title)}</small></div><span class="dj-mv-pill ${j.status==='matched'?'dj-mv-pill-match':'dj-mv-pill-wait'}">${j.status==='matched'?'Match':'Wartet'}</span>
    </div>${j.match_id?`<div class="dj-mv-card-actions"><button class="dj-mv-primary" data-open-match="${esc(j.match_id)}">Nachricht schreiben →</button></div>`:''}</article>`;
  const djEmployerJobRow = j => `<article class="dj-mv-card"><div class="dj-mv-card-top"><span class="dj-mv-avatar dj-mv-job-icon" aria-hidden="true">▣</span>
     <div class="dj-mv-card-body"><strong>${esc(j.title)}</strong><span>${esc(j.city)} · ${esc(workLabel(j.work_type))}</span>
     <small>${j.hourly_pay_min!=null?'Ab '+money(j.hourly_pay_min)+'/Std.':'Vergütung nicht angegeben'}</small></div>
     <span class="dj-mv-pill ${j.archived_at?'dj-mv-pill-muted':j.is_active?'dj-mv-pill-match':'dj-mv-pill-wait'}">${esc(jobStatus(j))}</span></div>
     ${j.archived_at?'<p class="dj-mv-muted">Archiviert · Nur noch zur Ansicht</p>':`<div class="dj-mv-card-actions dj-mv-job-actions">
       <button type="button" data-edit-job="${esc(j.id)}">Bearbeiten</button>
       <button type="button" data-job-action="${j.is_active?'pause':'reactivate'}" data-job-id="${esc(j.id)}">${j.is_active?'Pausieren':'Reaktivieren'}</button>
       <button type="button" class="dj-mv-danger" data-job-action="archive" data-job-id="${esc(j.id)}">Archivieren</button>
     </div>`}</article>`;
  async function matchesView(){
    if(!state.user)return navigate('login');
    const role=state.user.role;
    const tabs=djMatchTabs(role);
    if(!tabs.some(([id])=>id===djMatchTab))djMatchTab='matches';
    let rows=[],summary='',action='';
    if(djMatchTab==='matches'){
      state.matches=await api('/api/match-summaries');
      state.matches.sort((a,b)=>new Date(b.last_message?.created_at||b.matched_at)-new Date(a.last_message?.created_at||a.matched_at));
      rows=state.matches.map(djMatchRow);
      summary=state.matches.length+' gegenseitige Matches';
      action=`<div class="dj-mv-empty"><span aria-hidden="true">♡</span><h2>Noch kein Match</h2><p>Wenn beide Seiten auf Interessant tippen, erscheint das Match hier.</p><button type="button" data-go="discover">Jetzt entdecken →</button></div>`;
    }else if(djMatchTab==='likes'&&role==='worker'){
      const items=await api('/api/workers/me/likes');rows=items.map(djWorkerLikeRow);summary=items.length+' Likes';
      action=`<div class="dj-mv-empty"><span aria-hidden="true">♡</span><h2>Noch keine Likes</h2><p>Deine interessanten Stellen erscheinen hier.</p><button data-go="discover">Jobs entdecken →</button></div>`;
    }else if(djMatchTab==='likes'){
      const items=await api('/api/employers/me/likes');rows=items.map(djEmployerLikeRow);summary=items.length+' Likes';
      action=`<div class="dj-mv-empty"><span aria-hidden="true">♡</span><h2>Noch keine Likes</h2><p>Deine interessanten Kandidaten erscheinen hier.</p><button data-go="discover">Talente entdecken →</button></div>`;
    }else if(djMatchTab==='jobs'&&role==='employer'){
      state.mine=await api('/api/jobs/mine');rows=state.mine.map(djEmployerJobRow);summary=state.mine.length+' Stellenanzeigen';
      action=`<div class="dj-mv-empty"><span aria-hidden="true">▣</span><h2>Noch keine Stellen</h2><p>Erstelle deine erste Stellenanzeige.</p><button type="button" data-new-job>Job erstellen →</button></div>`;
    }
    const tabHtml=tabs.map(([id,label])=>`<button type="button" data-dj-match-tab="${id}" role="tab" aria-selected="${djMatchTab===id}" class="${djMatchTab===id?'active':''}">${label}</button>`).join('');
    render(shell(`<div class="dj-matches-v3">${djMatchLogo}
      <h1>Deine Matches</h1><p class="dj-mv-subtitle">${role==='worker'?'Passende Stellen und deine Verbindungen.':'Kandidaten, Likes und Stellen im Überblick.'}</p>
      <div class="dj-mv-tabs" role="tablist" aria-label="Matches verwalten">${tabHtml}</div>
      <div class="dj-mv-list-top"><strong>${esc(summary)}</strong>${role==='employer'&&djMatchTab==='jobs'?'<button type="button" data-new-job>+ Job</button>':''}</div>
      <div class="dj-mv-list">${rows.length?rows.join(''):action}</div>
      </div>`,'matches'));
  }
  // MATCHES_V3_END
  async function chatsView(){
    if(!state.user)return navigate('login');
    state.chats=await api('/api/match-summaries');
    state.chats.sort((a,b)=>new Date(b.last_message?.created_at||b.matched_at)-new Date(a.last_message?.created_at||a.matched_at));
    render(shell(`<div class="dj2-page-label">DOPPLEJA · NACHRICHTEN</div><h1 class="title">Nachrichten</h1>
      <p class="subtitle">Deine Matches und laufenden Unterhaltungen.</p>
      <div class="dj2-match-list">${state.chats.length?state.chats.map(matchCard).join(''):
        `<section class="dj2-blank"><div class="dj2-blank-icon">💬</div><h2>Hier ist es noch ruhig</h2>
        <p>Ein gegenseitiger Like schaltet den Chat frei.</p><button class="btn" data-go="discover">Entdecken →</button></section>`}</div>`,'chats'));
  }
  async function conversationView(){
    if(!state.currentMatch)return navigate('chats');
    const id=state.currentMatch;
    const [messages,summaries]=await Promise.all([
      api(`/api/matches/${encodeURIComponent(id)}/messages?limit=100`),
      api('/api/match-summaries')
    ]);
    const match=summaries.find(m=>m.match_id===id);
    const displayName=match?.other_party_name||'Dein Match';
    const jobTitle=match?.job_title||'DoppleJa Chat';
    const bubbles=messages.map(m=>`<div data-msg-id="${esc(m.id)}" class="bubble ${m.sender_id===state.user.id?'mine':''}">${esc(m.content)}<time>${date(m.created_at)}</time></div>`).join('');
    render(shell(`<section class="dj2-conversation">
      <header class="dj2-chat-header"><button class="back" data-go="chats" aria-label="Zu den Nachrichten">←</button>
        <div class="dj2-chat-avatar" aria-hidden="true">🤝</div><div class="dj2-chat-identity">
          <strong>${esc(displayName)}</strong><div class="dj2-chat-job">${esc(jobTitle)}</div>
          <span class="dj2-chat-status" id="chat-status" role="status">Verbindung wird hergestellt …</span>
        </div></header>
      <section class="dj54-review-panel" id="dj54-review-panel" aria-label="Auftrag abschließen und bewerten"></section>
      <div class="dj2-chat-tip">Ihr habt euch gegenseitig geliked. Jetzt könnt ihr euch direkt austauschen.</div>
      <div class="chat-messages dj2-messages" id="messages" aria-label="Chatverlauf" aria-live="polite">${bubbles||'<div class="dj2-chat-empty">Sag Hallo! 👋</div>'}</div>
      <form id="chat-form" class="chat-compose dj2-compose">
        <input name="content" maxlength="2000" placeholder="Nachricht schreiben …" required autocomplete="off" aria-label="Nachricht schreiben">
        <button type="submit" aria-label="Nachricht senden">➤</button></form></section>`,'chats'));
    const area=$('#messages');if(area)area.scrollTop=area.scrollHeight;
    connectChat(id);
    await loadCompletionPanel(id);
  }
  function appendMessage(message){const area=$('#messages');
    if(!area||!message||area.querySelector(`[data-msg-id="${CSS.escape(message.id)}"]`))return;
    if(area.querySelector('.empty, .dj2-chat-empty'))area.innerHTML='';const div=document.createElement('div');
    div.className='bubble'+(message.sender_id===state.user.id?' mine':'');div.dataset.msgId=message.id;div.textContent=message.content;
    const time=document.createElement('time');time.textContent=date(message.created_at);div.appendChild(time);area.appendChild(div);
    area.scrollTop=area.scrollHeight;}
  function connectChat(id){
    closeChat();
    const protocol=location.protocol==='https:'?'wss:':'ws:';
    const status=$('#chat-status');
    const setStatus=(message,mode)=>{if(status){status.textContent=message;status.dataset.mode=mode;}};
    // Polling is a REST fallback and also refreshes messages when the socket isn't available.
    const refresh=async()=>{
      if(state.page!=='conversation'||state.currentMatch!==id)return;
      try{const items=await api(`/api/matches/${encodeURIComponent(id)}/messages?limit=100`);items.forEach(appendMessage);}
      catch(e){console.warn('Chat refresh:',e);}
    };
    state.chatPoll=setInterval(refresh,8000);
    let socket;
    try{socket=new WebSocket(`${protocol}//${location.host}/ws/matches/${encodeURIComponent(id)}`);}
    catch(e){setStatus('Live-Chat nicht verfügbar · Senden weiterhin möglich','fallback');return;}
    state.socket=socket;
    socket.onopen=()=>{if(state.socket===socket)setStatus('Live verbunden','online');};
    socket.onmessage=event=>{
      if(state.socket!==socket)return;
      try{const data=JSON.parse(event.data);
        if(data.type==='message')appendMessage(data.message);
        else if(data.type==='error')toast(data.detail||'Nachricht konnte nicht gesendet werden.');
      }catch(e){console.warn('Chat message:',e);}
    };
    socket.onclose=()=>{
      if(state.socket!==socket)return;
      setStatus('Offline · Nachrichten über sichere Verbindung verfügbar','fallback');refresh();
    };
    socket.onerror=()=>{if(state.socket===socket)setStatus('Live-Verbindung gestört · Fallback aktiv','fallback');};
  }
  async function loadCompletionPanel(id){
    const panel=$('#dj54-review-panel');
    if(!panel||state.currentMatch!==id)return;
    try{
      const s=await api(`/api/matches/${encodeURIComponent(id)}/completion`);
      if(!panel.isConnected||state.currentMatch!==id)return;
      const msg=s.completed?'Auftrag von beiden Seiten abgeschlossen':
        s.confirmed_by_me?'Deine Bestätigung gespeichert · Auf die andere Seite warten':
        s.confirmed_by_other?'Die andere Seite hat abgeschlossen · Bitte bestätigen':'Nach dem Auftrag können beide Seiten den Abschluss bestätigen.';
      panel.innerHTML=`<h3>Auftrag & Bewertung ⭐</h3><p>${esc(msg)}</p>
        ${!s.confirmed_by_me?'<button type="button" class="dj54-confirm" data-dj54-confirm>Auftrag abgeschlossen bestätigen</button>':''}
        ${s.completed&&!s.my_review?`<form id="dj54-review-form"><label>Sterne vergeben
          <select name="stars" required><option value="">Bitte bewerten</option>${[1,2,3,4,5].map(n=>`<option value="${n}">${'★'.repeat(n)} (${n}/5)</option>`).join('')}</select></label>
          <label>Kommentar (optional)<textarea name="comment" maxlength="1000" rows="2"></textarea></label>
          <button type="submit" class="dj54-confirm">Bewertung senden</button></form>`:''}
        ${s.my_review?`<p class="dj54-stars">Deine Bewertung: ${'★'.repeat(s.my_review.stars)} (${s.my_review.stars}/5)</p>`:''}
        ${s.completed&&s.their_review?`<p class="dj54-stars">Erhaltene Bewertung: ${'★'.repeat(s.their_review.stars)} (${s.their_review.stars}/5)</p>`:''}`;
    }catch(e){if(panel.isConnected)panel.textContent='Bewertungsstatus momentan nicht verfügbar.';console.warn(e);}
  }
  async function settingsView(){render(shell(`<h1 class="title">Einstellungen</h1>
    <div class="sheet"><div class="card-body"><strong>${esc(state.user?.email)}</strong>
    <p class="subtitle">${state.user?.role==='worker'?'Jobsuchend':'Personal suchend'}</p>
    <button class="btn outline" id="logout">Abmelden</button></div></div>
    <div class="notice topspace">DoppleJa V1 ist derzeit eine lokale Entwicklungsfassung.
    Bitte noch keine echten personenbezogenen Daten oder Bilder hochladen.</div>
    <p class="small-muted">Datenschutz, CSRF-Schutz, Melden/Blockieren und produktiver E-Mail-Versand sind vor einem öffentlichen Launch erforderlich.</p>`,
    'profile'));}
  root.addEventListener('click',event=>run(async()=>{const newJob=event.target.closest('[data-new-job]');
    if(newJob){state.editingJob=null;return navigate('job-create');}
    const edit=event.target.closest('[data-edit-job]');if(edit){state.editingJob=edit.dataset.editJob;return navigate('job-create');}
    const status=event.target.closest('[data-job-action]');
    if(status){const action=status.dataset.jobAction;const ask=action==='archive'?
      'Diesen Job endgültig archivieren? Bestehende Matches und Nachrichten bleiben erhalten.':
      action==='pause'?'Job pausieren?':'Job wieder aktivieren?';
      if(!window.confirm(ask))return;await api('/api/jobs/'+encodeURIComponent(status.dataset.jobId)+
      '/status',{method:'PATCH',body:JSON.stringify({action})});toast(action==='archive'?
        'Job archiviert':action==='pause'?'Job pausiert':'Job reaktiviert');djMatchTab='jobs';return matchesView();}
    if(event.target.closest('[data-dj54-confirm]')){await api(`/api/matches/${encodeURIComponent(state.currentMatch)}/confirm-completion`,{method:'POST'});await loadCompletionPanel(state.currentMatch);return;}
    const roleChoice=event.target.closest('[data-register-role]');if(roleChoice){state.registrationRole=roleChoice.dataset.registerRole;return navigate('register-details');}
    const mvTab=event.target.closest('[data-dj-match-tab]');if(mvTab){djMatchTab=mvTab.dataset.djMatchTab;return matchesView();}
    const go=event.target.closest('[data-go]');if(go)return navigate(go.dataset.go);
    const cat=event.target.closest('[data-discover-category]');
    if(cat){state.filterCategory=cat.dataset.discoverCategory;return discoveryView();}
    const toggle=event.target.closest('#djv2-filter-toggle');
    if(toggle){const panel=root.querySelector('#djv2-filter-panel');if(panel){panel.hidden=!panel.hidden;toggle.setAttribute('aria-expanded',String(!panel.hidden));}return;}
    const s=event.target.closest('[data-swipe]');if(s)return swipe(s.dataset.swipe,s.dataset.discoverId);
    const m=event.target.closest('[data-open-match]');
    if(m){state.currentMatch=m.dataset.openMatch;return navigate('conversation');}
    if(event.target.closest('#filter-reset')){state.filterCity='';state.filterCategory='';state.filterWorkType='';return discoveryView();}
    if(event.target.closest('#filter-apply')){state.filterCity=$('#filter-city').value.trim();
      state.filterWorkType=$('#filter-worktype').value;return discoveryView();}if(event.target.closest('#logout'))
        {await api('/api/auth/logout',{method:'POST'});closeChat();state.user=null;state.profile=null;state.categories=[];
      toast('Abgemeldet');return navigate('login');}}));
  root.addEventListener('change',event=>run(async()=>{if(event.target.name==='job-picker'){state.selectedJob=event.target.value;await discoveryView();}}));
  root.addEventListener('submit',event=>{event.preventDefault();run(async()=>{const form=event.target;const v=values(form);
    const btn=form.querySelector('[type=submit]');if(btn)btn.disabled=true;try{
    if(form.id==='register-form'){delete v.interest;await api('/api/auth/register',{method:'POST',body:JSON.stringify(v)});
    toast('Konto erstellt!');return navigate('verification');}
    if(form.id==='login-form'){state.user=await api('/api/auth/login',{method:'POST',body:JSON.stringify(v)});
    let path;try{state.profile=await api(state.user.role==='worker'?'/api/workers/me':'/api/employers/me');
      path='discover';}catch{path='profile';}toast('Willkommen bei DoppleJa!');return navigate(path);}
    if(form.id==='profile-form'){const endpoint=state.user.role==='worker'?'/api/workers/me':'/api/employers/me';
      state.profile=await api(endpoint,{method:'PUT',body:JSON.stringify(v)});toast('Profil gespeichert!');return navigate('discover');}
    if(form.id==='job-form'){const original=state.editingJob?state.mine.find(j=>j.id===state.editingJob):null;
      const body={...v,category_id:Number(v.category_id),hourly_pay_min:v.hourly_pay_min===''?
        null:Number(v.hourly_pay_min),hourly_pay_max:v.hourly_pay_max===''?null:Number(v.hourly_pay_max),
        is_active:original?original.is_active:true};await api(original?'/api/jobs/'+encodeURIComponent(original.id):
        '/api/jobs',{method:original?'PUT':'POST',body:JSON.stringify(body)});state.editingJob=null;toast(original?
          'Job aktualisiert!':'Job veröffentlicht!');return navigate('my-jobs');}
    if(form.id==='dj54-review-form'){await api(`/api/matches/${encodeURIComponent(state.currentMatch)}/reviews`,{method:'POST',body:JSON.stringify({stars:Number(v.stars),comment:v.comment||null})});toast('Bewertung abgegeben!');await loadCompletionPanel(state.currentMatch);return;}
    if(form.id==='chat-form'){const content=v.content?.trim();if(!content)return;
      const input=form.querySelector('input');input.value='';try{if(state.socket?.readyState===1)
        {state.socket.send(JSON.stringify({type:'message',content}));}
        else{const saved=await api(`/api/matches/${encodeURIComponent(state.currentMatch)}/messages`,{method:'POST',
          body:JSON.stringify({content})});appendMessage(saved);}}catch(e){input.value=content;throw e;}}
  }finally{if(btn?.isConnected)btn.disabled=false;}});});
  (async()=>{if(await loadMe())await navigate('discover');else await navigate('home');})();
})();

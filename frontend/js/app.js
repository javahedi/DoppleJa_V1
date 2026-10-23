/* PHASE_52B2_PREMIUM_DASHBOARDS */
/* PHASE_52A_START: premium onboarding; existing application modules remain intact */
/* DoppleJa V1: plain JavaScript SPA; all API calls stay same-origin. */
(() => {
  'use strict';
  const root = document.getElementById('app');
  const state = { user:null, profile:null, page:'home', categories:[], jobs:[],
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
    `<section class="screen"><header class="header"><span class="logo">DoppleJa<span style="color:#ffd900">●</span></span><button class="back" data-go="settings" aria-label="Einstellungen">⚙</button></header>${content}</section><nav class="bottom-nav" aria-label="Hauptnavigation">${(state.user?.role==='employer'?[['discover','⌂','Personal'],['my-jobs','▣','Meine Jobs'],['chats','☏','Chats'],['profile','♙','Profil']]:[['discover','⌂','Entdecken'],['likes','♡','Meine Likes'],['chats','☏','Chats'],['profile','♙','Profil']]).map(([id,ic,label])=>`<button data-go="${id}" class="${active===id?'active':''}"><span>${ic}</span>${label}</button>`).join('')}</nav>`;
  const render = html => { root.innerHTML=html; root.scrollTop=0; window.scrollTo(0,0); };
  function closeChat(){if(state.socket){state.socket.onclose=null;state.socket.close();
    state.socket=null;}if(state.chatPoll){clearInterval(state.chatPoll);state.chatPoll=null;}}
  async function navigate(page){ if(state.page==='conversation'&&page!=='conversation')closeChat();state.page=page;
    render('<div class="loading">Lädt …</div>'); await run(async()=>{switch(page){case 'home':return home();
      case 'login':return loginView();case 'register':return registerView();case 'verification':return verifyView();case 'profile':return profileView();
      case 'discover':return discoveryView();case 'matches':return matchesView();case 'likes':return likesView();case 'chats':return chatsView();
      case 'conversation':return conversationView();case 'job-create':return jobFormView();
      case 'my-jobs':return myJobsView();case 'settings':return settingsView();default: return home();}});}

  function home(){render(`<section class="splash premium-welcome"><div class="premium-welcome-glow"></div>
    <div class="pw-content"><div class="pw-overline">WILLKOMMEN BEI</div><h1 class="brand">DoppleJa<span class="pw-dot">.
    </span></h1><p class="tagline">Zwei Seiten. Zwei Ja. Ein Match.</p><div class="pw-art" aria-hidden="true">
    <div class="pw-person pw-person-left"><img src="/app-assets/assets/worker-card.jpg" alt=""></div>
    <div class="pw-center"><span>🤝</span></div><div class="pw-person pw-person-right"><img src="/app-assets/assets/employer-card.jpg" alt=""></div>
    <span class="pw-star one">✦</span><span class="pw-star two">♥</span><span class="pw-star three">✦</span></div></div>
    <div class="splash-actions pw-actions"><button class="btn yellow" data-go="register">Los geht’s <span aria-hidden="true">→</span></button>
    <button class="btn outline" data-go="login">Ich habe schon ein Konto</button>
    <p class="center pw-caption">Finde Menschen. Entdecke Arbeit. Einfach matchen.</p></div></section>`);}
  function loginView(){render(`<section class="screen premium-auth"><button class="back" data-go="home">← Zurück</button>
    <div class="pa-kicker">DOPPLEJA · WILLKOMMEN ZURÜCK</div><h1 class="title topspace">Schön, dass du da bist! <span class="pa-yellow">✦</span></h1>
    <p class="subtitle">Einloggen und dort weitermachen, wo dein Match wartet.</p><div class="pa-login-decoration" aria-hidden="true">🤝</div>
    <form class="form" id="login-form">${field('E-Mail','email','','type="email" required autocomplete="email"')}${field('Passwort','password','',
      'type="password" required autocomplete="current-password"')}<button class="btn pa-primary" type="submit">Einloggen →</button></form>
      <p class="center"><button class="link-btn" data-go="register">Neu hier? Jetzt registrieren</button></p>
      <p class="pa-legal">Einfach anmelden. Kein Lebenslauf, keine Bewerbung.</p></section>`);}
  function registerView(){
    const cards=[['restaurant-cafe','Gastronomie','cafe-card.jpg'],['handwerker','Handwerk','craft-card.jpg'],
    ['hospital-care','Gesundheit','hospital-card.jpg'],['cleaning','Reinigung','cleaning-card.jpg'],['drivers-logistics','Logistik','logistics-card.jpg']];
    const interests=cards.map(([key,label,img])=>`<label class="pa-interest"><input type="checkbox" name="interest" value="${key}">
    <img src="/app-assets/assets/${img}" alt=""><span>${label}</span></label>`).join('');
    render(`<section class="screen premium-auth premium-register"><button class="back" data-go="home">← Zurück</button>
      <div class="pa-progress"><span class="pa-progress-on"></span><span></span><span></span></div><div class="pa-kicker">DEIN START IN DOPPLEJA</div>
      <h1 class="title topspace">Wer bist du?</h1><p class="subtitle">Zwei Seiten. Ein Ziel: das passende Match.</p><form class="form" id="register-form">
      <div class="pa-role-cards"><label class="pa-role"><input type="radio" name="role" value="worker" required checked>
      <img src="/app-assets/assets/worker-card.jpg" alt="Servicekraft"><span class="pa-role-copy"><strong>Ich suche einen Job</strong>
      <small>Entdecke Arbeit, die zu dir passt.</small></span><span class="pa-select-arrow">→</span></label><label class="pa-role">
      <input type="radio" name="role" value="employer"><img src="/app-assets/assets/employer-card.jpg" alt="Arbeitgeber">
      <span class="pa-role-copy"><strong>Ich suche Personal</strong><small>Privatperson oder Unternehmen.</small></span>
      <span class="pa-select-arrow">→</span></label></div><div class="pa-interest-section"><div class="pa-section-heading">
      <strong>Was interessiert dich?</strong><small>Optional · bis zu 3 Bereiche</small></div><div class="pa-interests">${interests}</div>
      <p class="pa-tiny">Die Auswahl hilft beim Einstieg. Persönliche Interessen speichern wir erst in einer späteren Profilphase.</p></div>
      <div class="pa-credentials"><div class="pa-section-heading"><strong>Fast geschafft!</strong><small>Konto erstellen</small></div>
      ${field('E-Mail','email','','type="email" required autocomplete="email"')}${field('Passwort (mindestens 10 Zeichen)','password','',
        'type="password" required minlength="10" autocomplete="new-password"')}</div><button class="btn pa-primary" type="submit">Konto erstellen →</button>
        </form><p class="center"><button class="link-btn" data-go="login">Schon dabei? Einloggen</button></p></section>`);

    root.querySelectorAll('.pa-interest input').forEach(input=>input.addEventListener('change',
      ()=>{const selected=root.querySelectorAll('.pa-interest input:checked');if(selected.length>3)
        {input.checked=false;toast('Bitte höchstens 3 Bereiche wählen.');}}));
  }
  function verifyView(){render(`<section class="screen premium-auth pa-verify">
    <div class="pa-verify-icon">✉️</div><h1 class="title">Jetzt E-Mail bestätigen</h1>
    <p class="subtitle">Öffne den Bestätigungslink, um DoppleJa freizuschalten.</p>
    <div class="notice">Im lokalen Entwicklermodus steht der Link in den Docker-Logs:<br><code>docker compose logs --tail=80 api</code></div>
    <button class="btn pa-primary" data-go="login">Zum Login →</button></section>`);}
  async function loadMe(){try{state.user=await api('/api/auth/me');return true;}catch{state.user=null;return false;}}
  async function profileView(){
    if(!state.user)return navigate('login');
    let profile;
    try { profile=await api(state.user.role==='worker'?'/api/workers/me':'/api/employers/me'); }
    catch(e){if(!e.message.includes('404')&&!e.message.includes('Complete'))console.warn(e);profile=null;}
    state.profile=profile;
    const p=profile||{}, worker=state.user.role==='worker';
    const isOwnPhoto=Boolean(p.photo_url);
    const image=isOwnPhoto?esc(p.photo_url):(worker?art(workerArtwork(p.profession)):art(/bau|montage|handwerk|maler/i.test(p.category||'')?'employer-craft.webp':/gesund|pflege|medizin/i.test(p.category||'')?'employer-care.webp':'employer-cafe.webp'));
    const overview=worker?`<div class="dj-detail-grid"><div><span>Beruf</span><strong>${esc(p.profession||'Noch offen')}</strong></div><div><span>Verfügbarkeit</span><strong>${esc(p.availability||'Flexibel')}</strong></div></div>`:
      `<div class="dj-detail-grid"><div><span>Typ</span><strong>${p.employer_type==='business'?'Unternehmen':'Privatperson'}</strong></div><div><span>Bereich</span><strong>${esc(p.category||'Personal gesucht')}</strong></div></div>`;
    render(shell(`<div class="dj-page-eyebrow">MEIN DOPPLEJA</div><h1 class="title">${profile?'Mein Profil':'Profil erstellen'}</h1>
      <p class="subtitle">${worker?'Zeig deine Stärken – ganz ohne Lebenslauf.':'Zeig, wer hinter deinen Stellenanzeigen steht.'}</p>
      <section class="dj-profile-banner"><img src="${image}" alt="" loading="lazy"><div class="dj-photo-label">${isOwnPhoto?'Profilbild':'Symbolbild'}</div><div class="dj-profile-overlay"><span class="dj-profile-chip">${worker?'Jobsuchend':p.employer_type==='business'?'Unternehmen':'Arbeitgeber'}</span><h2>${esc(p.display_name||'Dein DoppleJa Profil')}</h2><p>⌖ ${esc(p.city||'Deutschland')}</p></div></section>
      ${overview}
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
  // PHASE_52B5_WORKER_DISCOVERY: photograph-first card, only real API fields.
  const jobCard=job=>{
    const pay=job.hourly_pay_min!=null||job.hourly_pay_max!=null
      ?`${money(job.hourly_pay_min)}${job.hourly_pay_max!=null?' – '+money(job.hourly_pay_max):''} / Std.`:'Vergütung auf Anfrage';
    const artwork=art(jobArtwork[job.category_id]||'job-craft.webp');
    const description=String(job.description||'Für diese Stelle liegt noch keine ausführliche Beschreibung vor.');
    const posted=job.created_at?new Date(job.created_at).toLocaleDateString('de-DE',{day:'2-digit',month:'short',year:'numeric'}):'';
    return `<article class="dj-b5-card" aria-label="Stellenangebot: ${esc(job.title)}">
      <div class="dj-b5-visual"><img src="${artwork}" alt="Symbolbild für ${esc(categoryName(job.category_id))}" loading="eager">
        <span class="dj-b5-symbol">Symbolbild</span><span class="dj-b5-category">${esc(categoryName(job.category_id))}</span></div>
      <div class="dj-b5-main"><div class="dj-b5-heading"><div><span class="dj-b5-eyebrow">AKTUELLES STELLENANGEBOT</span>
        <h2>${esc(job.title)}</h2></div><span class="dj-b5-type">${esc(workLabel(job.work_type))}</span></div>
        <p class="dj-b5-city">⌖ ${esc(job.city||'Ort nicht angegeben')}${posted?' · '+esc(posted):''}</p>
        <div class="dj-b5-pay">${esc(pay)}</div>
        <details class="dj-b5-details"><summary>Jobdetails anzeigen <span aria-hidden="true">⌄</span></summary>
          <p>${esc(description)}</p><p class="dj-b5-info">Weitere Einzelheiten kannst du nach einem gegenseitigen Match im Chat klären.</p>
        </details>
        <div class="dj-b5-actions"><button type="button" class="dj-b5-pass" data-swipe="pass" aria-label="Job überspringen"><span aria-hidden="true">✕</span><small>Weiter</small></button>
          <button type="button" class="dj-b5-like" data-swipe="like" aria-label="Job liken"><span aria-hidden="true">♥</span><small>Gefällt mir</small></button></div>
      </div></article>`;
  };
  const candidateCard=p=>`<div class="sheet"><div class="hero personal"><img class="dj-photo" src="${p.photo_url?esc(p.photo_url):art(workerArtwork(p.profession))}" alt="" loading="lazy"><span class="dj-photo-tag">${p.photo_url?'Profilfoto':'Symbolbild · Berufsbereich'}</span><h2>${esc(p.display_name)}</h2>
  <p>${esc(p.profession||'Arbeitssuchend')} · ${esc(p.city||'Deutschland')}</p></div><div class="card-body"><div class="meta">
  <span class="pill">${esc(p.availability||'Flexibel')}</span></div><p class="desc">${esc(p.bio||'Offen für neue Möglichkeiten.')}</p>
  <div class="swipe-actions"><button class="round" data-swipe="pass" aria-label="Weiter">✕</button>
  <button class="round like" data-swipe="like" aria-label="Gefällt mir">♥</button></div></div></div>`;
  async function discoveryView(){if(!state.user)return navigate('login');await loadCategories();let content='';if(state.user.role==='worker'){
    state.jobs=await api('/api/discovery/jobs'+(state.filterCity||state.filterCategory?'?'
      +new URLSearchParams({...state.filterCity?{city:state.filterCity}:{},...state.filterCategory?{category_id:state.filterCategory}:{}}):''));
      // PHASE_52B5_WORKER_DISCOVERY: server-filter city/category; client-filter job type over returned feed.
      // Work-type filtering only applies to the first server-returned batch; not advertised as exhaustive.
      const visibleJobs=state.filterWorkType
        ?state.jobs.filter(j=>j.work_type===state.filterWorkType):state.jobs;
      const job=visibleJobs[0];
      const filtered=Boolean(state.filterCity||state.filterCategory||state.filterWorkType);
      const count=visibleJobs.length;
      content=`<section class="dj-b5-intro"><div class="dj-b5-overline">DOPPLEJA · ENTDECKEN</div>
          <h1>Finde deinen nächsten Job</h1><p>Ganz ohne Lebenslauf. Entdecke passende Stellen und zeig mit ♥ Interesse.</p>
          <span class="dj-b5-count">${count} ${count===1?'Job':'Jobs'} in deiner Auswahl</span></section>
        <section class="dj-b5-filter-panel" aria-label="Jobs filtern"><div class="dj-b5-filter-title"><strong>Deine Suche</strong>
          <span>Stadt, Bereich &amp; Jobmodell</span></div>
          <div class="dj-b5-fields"><label class="field">Stadt<input id="filter-city" placeholder="z. B. Berlin" value="${esc(state.filterCity)}"></label>
          <label class="field">Bereich<select id="filter-category">${options([['','Alle Bereiche'],...state.categories.map(c=>[c.id,c.name])],state.filterCategory)}</select></label>
          <label class="field dj-b5-worktype">Jobmodell<select id="filter-worktype">${options([['','Alle Jobmodelle'],['minijob','Minijob'],['part_time','Teilzeit'],['full_time','Vollzeit'],['temporary','Tagesjob / Kurzfristig']],state.filterWorkType)}</select></label></div>
          <div class="dj-b5-filter-buttons"><button type="button" class="btn" id="filter-apply">Jobs anzeigen →</button>
          <button type="button" class="dj-b5-reset" id="filter-reset">Zurücksetzen</button></div></section>
        ${job?`<div class="dj-b5-stack-label"><strong>Für dich entdecken</strong><span>${count} in dieser Auswahl</span></div>${jobCard(job)}`:
        `<section class="dj-b5-empty"><div class="dj-b5-empty-icon">${filtered?'⌕':'🤝'}</div>
          <h2>${filtered?'Keine Jobs mit diesen Filtern':'Du bist auf dem neuesten Stand!'}</h2>
          <p>${filtered?'Versuche andere Suchkriterien. Die Auswahl beim Jobmodell wird auf die aktuell geladenen Stellen angewendet.':'Du hast die derzeit verfügbaren Jobs für deinen Account angesehen. Neue Jobs können später hinzukommen.'}</p>
          <div class="dj-b5-empty-links"><button type="button" data-go="likes">♥ Meine Likes</button>
          <button type="button" data-go="chats">🤝 Chats öffnen</button></div></section>`}
        <p class="dj-b5-note">Jobfotos sind Symbolbilder. Likes und Matches basieren auf echten Einträgen in deiner aktuellen Datenbank.</p>`;

  }else{
    state.mine=(await api('/api/jobs/mine')).filter(j=>j.is_active && !j.archived_at);if(!state.selectedJob||!state.mine.some(j=>j.id===state.selectedJob))
      state.selectedJob=state.mine[0]?.id||null;
    if(state.selectedJob)state.candidates=await api('/api/discovery/workers?job_id='+encodeURIComponent(state.selectedJob));else state.candidates=[];
    const employerName=state.profile?.display_name||'Dein Unternehmen';
    const dashboard=`<section class="dj-employer-intro"><div class="dj-page-eyebrow">PERSONAL FINDEN</div>
      <h2>Hallo, ${esc(employerName)} 👋</h2><p>Dein nächstes 🤝 Match ist vielleicht nur ein Like entfernt.</p>
      <div class="dj-employer-stats"><span><strong>${state.mine.length}</strong> aktive Jobs</span><span><strong>${state.candidates.length}</strong> neue Profile</span></div></section>`;
    content=`${dashboard}<div class="row"><h1 class="title">Personal entdecken</h1><button class="btn small" data-go="my-jobs">Meine Jobs</button>
    <button class="btn small" data-go="job-create">+ Job</button></div><p class="subtitle">Finde Menschen für deinen Job – ohne Bewerbung.
    </p>${state.mine.length?`${select('Für welchen Job?','job-picker',
      state.mine.map(j=>[j.id,j.title]),state.selectedJob)}`:`<div class="notice">Erstelle zuerst einen Job, damit du Kandidaten entdecken kannst.</div>
      <button class="btn" data-go="job-create">Job erstellen</button>`}
      ${state.candidates.length?candidateCard(state.candidates[0]):state.mine.length?`<div class="empty"><div class="emoji">👥</div>
        <h3>Keine weiteren Profile</h3><p>Neue Kandidaten erscheinen hier.</p></div>`:''}`;
  }render(shell(content,'discover'));}
  async function swipe(action){if(state.busy)return;let job_id,worker_id;if(state.user.role==='worker'){job_id=state.jobs[0]?.id;}
  else{job_id=state.selectedJob;worker_id=state.candidates[0]?.user_id;}if(!job_id)return;state.busy=true;
  try{const response=await api('/api/swipes',{method:'POST',body:JSON.stringify({job_id,action,...worker_id?{worker_id}:{}})});
  toast(response.is_match?'🎉 It’s a Match!':action==='like'?'♥ Gefällt dir!':'Weiter geht’s');
  await discoveryView();}catch(e){toast(e.message);}finally{state.busy=false;}}
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
  const matchCard = m => `<article class="list-card match-summary-card">
    <div class="avatar">🤝</div>
    <div class="grow"><strong>${summaryHeader(m)}</strong>
      <small>${esc(m.city)} · ${m.has_messages?'Unterhaltung läuft':'Neues Match'}</small>
      <small>${m.has_messages ? `${esc(m.last_message.content)} · ${fullDate(m.last_message.created_at)}` : `Match am ${fullDate(m.matched_at)}`}</small>
    </div><button data-open-match="${esc(m.match_id)}">${m.has_messages?'Chat öffnen':'Nachricht senden'} →</button>
  </article>`;
  async function matchesView(){
    if(!state.user)return navigate('login');
    state.matches=await api('/api/match-summaries');
    render(shell(`<h1 class="title">Deine Matches 🤝</h1><p class="subtitle">Neue Matches und laufende Unterhaltungen.</p>
      ${state.matches.length?state.matches.map(matchCard).join(''):`<div class="empty"><div class="emoji">🤝</div><h3>Noch kein Match</h3>
        <p>Wenn ihr euch beide liked, erscheint euer Match hier.</p><button class="btn" data-go="discover">Entdecken</button></div>`}`,'matches'));
  }
  async function chatsView(){
    if(!state.user)return navigate('login');
    const summaries=await api('/api/match-summaries');
    state.chats=summaries.sort((a,b)=>new Date(b.last_message?.created_at||b.matched_at)-new Date(a.last_message?.created_at||a.matched_at));
    render(shell(`<h1 class="title">Nachrichten</h1><p class="subtitle">Deine Matches und Unterhaltungen.</p>
      ${state.chats.length?state.chats.map(matchCard).join(''):`<div class="empty"><div class="emoji">💬</div><h3>Hier ist es noch ruhig</h3>
        <p>Deine Matches erscheinen hier, damit ihr ein Gespräch beginnen könnt.</p><button class="btn" data-go="likes">Meine Likes</button></div>`}`,'chats'));
  }
  async function conversationView(){if(!state.currentMatch)return navigate('chats');const id=state.currentMatch;const messages=await
    api(`/api/matches/${encodeURIComponent(id)}/messages?limit=100`);const bubbles=messages.map(m=>`<div data-msg-id="${esc(m.id)}
    " class="bubble ${m.sender_id===state.user.id?'mine':''}">${esc(m.content)}<time>${date(m.created_at)}</time></div>`).join('');
    render(shell(`<div class="row"><button class="back" data-go="chats">←</button><div class="grow"><strong>Dein Match 🤝</strong>
      <div class="small-muted" id="chat-status">Verbinde …</div></div></div><div class="chat-messages" id="messages">
      ${bubbles||'<div class="empty">Sag Hallo! 👋</div>'}</div><form id="chat-form" class="chat-compose">
      <input name="content" maxlength="2000" placeholder="Nachricht schreiben …" required autocomplete="off">
      <button type="submit" aria-label="Nachricht senden">➤</button></form>`,'chats'));const area=$('#messages');
      area.scrollTop=area.scrollHeight;connectChat(id);}
  function appendMessage(message){const area=$('#messages');
    if(!area||!message||area.querySelector(`[data-msg-id="${CSS.escape(message.id)}"]`))return;
    if(area.querySelector('.empty'))area.innerHTML='';const div=document.createElement('div');
    div.className='bubble'+(message.sender_id===state.user.id?' mine':'');div.dataset.msgId=message.id;div.textContent=message.content;
    const time=document.createElement('time');time.textContent=date(message.created_at);div.appendChild(time);area.appendChild(div);
    area.scrollTop=area.scrollHeight;}
  function connectChat(id){closeChat();const protocol=location.protocol==='https:'?'wss:':'ws:';
    const socket=new WebSocket(`${protocol}//${location.host}/ws/matches/${encodeURIComponent(id)}`);
    state.socket=socket;const status=$('#chat-status');socket.onopen=()=>{if(status)status.textContent='Live verbunden';};
    socket.onmessage=event=>{try{const data=JSON.parse(event.data);if(data.type==='message')appendMessage(data.message);
      else if(data.type==='error')toast(data.detail);}catch(e){console.warn(e);}};
      socket.onclose=()=>{if(status)status.textContent='Offline · Nachrichten werden geladen';};
      socket.onerror=()=>{if(status)status.textContent='Verbindungsproblem';};
      state.chatPoll=setInterval(async()=>{if(state.page!=='conversation')return;
        try{const items=await api(`/api/matches/${encodeURIComponent(id)}/messages?limit=100`);
        items.forEach(appendMessage);}catch(e){console.warn(e);}},8000);}
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
        'Job archiviert':action==='pause'?'Job pausiert':'Job reaktiviert');return myJobsView();}
    const go=event.target.closest('[data-go]');if(go)return navigate(go.dataset.go);
    const s=event.target.closest('[data-swipe]');if(s)return swipe(s.dataset.swipe);
    const m=event.target.closest('[data-open-match]');
    if(m){state.currentMatch=m.dataset.openMatch;return navigate('conversation');}
    if(event.target.closest('#filter-reset')){state.filterCity='';state.filterCategory='';state.filterWorkType='';return discoveryView();}
    if(event.target.closest('#filter-apply')){state.filterCity=$('#filter-city').value.trim();
      state.filterCategory=$('#filter-category').value;state.filterWorkType=$('#filter-worktype').value;return discoveryView();}if(event.target.closest('#logout'))
        {await api('/api/auth/logout',{method:'POST'});closeChat();state.user=null;state.profile=null;state.categories=[];
      toast('Abgemeldet');return navigate('home');}}));
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
    if(form.id==='chat-form'){const content=v.content?.trim();if(!content)return;
      const input=form.querySelector('input');input.value='';try{if(state.socket?.readyState===1)
        {state.socket.send(JSON.stringify({type:'message',content}));}
        else{const saved=await api(`/api/matches/${encodeURIComponent(state.currentMatch)}/messages`,{method:'POST',
          body:JSON.stringify({content})});appendMessage(saved);}}catch(e){input.value=content;throw e;}}
  }finally{if(btn?.isConnected)btn.disabled=false;}});});
  (async()=>{if(await loadMe())await navigate('discover');else await navigate('home');})();
})();

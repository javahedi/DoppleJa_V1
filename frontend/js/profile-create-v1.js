/* DoppleJa: creation-only profile presentation, preserves the existing profile-form submit API. */
(() => {
  'use strict';
  const root = document.getElementById('app');
  if (!root) return;
  const safe = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const options = (entries, selected='') => entries.map(([v,l])=>`<option value="${safe(v)}" ${String(v)===String(selected)?'selected':''}>${safe(l)}</option>`).join('');
  const input = (title,name,placeholder,value='',required=false,type='text')=>`<label class="dj-pc-field"><span>${title}</span><input type="${type}" name="${name}" placeholder="${safe(placeholder)}" value="${safe(value)}" ${required?'required':''} maxlength="100"></label>`;
  const select = (title,name,entries,selected='')=>`<label class="dj-pc-field"><span>${title}</span><select name="${name}">${options(entries,selected)}</select></label>`;
  function build(form) {
    const original = Object.fromEntries(new FormData(form).entries());
    const worker = !!form.querySelector('[name="profession"]');
    const container = form.closest('section.screen');
    if (!container || container.classList.contains('dj-pc-page')) return;
    const name = original.display_name || '';
    const person = name.trim().split(/\s+/);
    const first = worker ? person.shift() || '' : '';
    const last = worker ? person.join(' ') : '';
    const fields = worker ? `
      <div class="dj-pc-columns">
        <label class="dj-pc-field"><span>Vorname</span><input data-pc-first placeholder="Vorname" value="${safe(first)}" required maxlength="50"></label>
        <label class="dj-pc-field"><span>Nachname</span><input data-pc-last placeholder="Nachname" value="${safe(last)}" maxlength="50"></label>
      </div>
      <input type="hidden" name="display_name" value="${safe(name)}">
      ${input('Beruf / Tätigkeit','profession','z. B. Fahrerin, Pflegekraft, Reinigung',original.profession||'')}
      ${input('Standort','city','PLZ oder Stadt',original.city||'')}
      ${select('Verfügbarkeit','availability',[['','Bitte auswählen'],['Ab sofort','Ab sofort'],['In 1–2 Wochen','In 1–2 Wochen'],['Flexibel','Flexibel']],original.availability||'')}
      <label class="dj-pc-field"><span>Über mich <em>(optional)</em></span><textarea name="bio" maxlength="500" placeholder="Erzähl kurz von dir oder was du suchst …">${safe(original.bio||'')}</textarea><small class="dj-pc-count">0/500</small></label>` : `
      ${select('Wer sucht Mitarbeiter?','employer_type',[['private','Privatperson / Haushalt'],['business','Unternehmen / Betrieb']],original.employer_type||'private')}
      ${input('Name / Betrieb','display_name','Dein Name oder Unternehmensname',name,true)}
      ${input('Ich suche Mitarbeiter für','category','z. B. Haushalt, Pflege, Garten, Transport',original.category||'')}
      ${input('Standort','city','PLZ oder Stadt',original.city||'')}
      <label class="dj-pc-field"><span>Über uns / Gesuchte Hilfe <em>(optional)</em></span><textarea name="description" maxlength="500" placeholder="Beschreibe kurz, wen du suchst …">${safe(original.description||'')}</textarea><small class="dj-pc-count">0/500</small></label>`;
    const src = worker ? 'worker-delivery.webp' : 'employer-home.webp';
    container.className = 'screen dj-pc-page';
    container.innerHTML = `
      <header class="dj-pc-header"><button type="button" data-go="discover" aria-label="Zurück">‹</button><img src="/app-assets/assets/brand/doppleja-logo.svg" alt="DoppleJa"></header>
      <div class="dj-pc-progress"><span class="dj-pc-active">1</span><i></i><span>Profil</span></div>
      <section class="dj-pc-hero"><div><h1>${worker?'Erzähl uns etwas über dich':'Stell dich kurz vor'}</h1><p>${worker?'So können Arbeitgeber dich besser kennenlernen.':'So können passende Mitarbeiter dich und deinen Bedarf kennenlernen.'}</p></div><img src="/app-assets/assets/profile/${src}" alt="${worker?'Illustration eines Lieferfahrers':'Illustration eines privaten Arbeitgebers'}"></section>
      <div class="dj-pc-panel">
        <div class="dj-pc-photo"><div class="dj-pc-avatar" aria-hidden="true">◉</div><div><strong>Profilbild <span>(optional)</span></strong><small>Wähle ein Foto für die Vorschau. Dauerhaftes Speichern aktivieren wir mit dem Upload-Service.</small></div></div>
        <form id="profile-form" class="dj-pc-form">
          ${fields}
          <button class="dj-pc-submit" type="submit">Profil speichern <span aria-hidden="true">→</span></button>
        </form>
      </div>`;
    const current = container.querySelector('#profile-form');
    const firstInput = current.querySelector('[data-pc-first]');
    if (firstInput) {
      current.addEventListener('submit', event => {
        const fullName = [firstInput.value.trim(),current.querySelector('[data-pc-last]').value.trim()].filter(Boolean).join(' ');
        current.querySelector('[name="display_name"]').value=fullName;
        if (fullName.length < 2) { event.preventDefault(); event.stopImmediatePropagation(); firstInput.setCustomValidity('Bitte mindestens zwei Zeichen eingeben.'); firstInput.reportValidity(); }
      },true);
      firstInput.addEventListener('input',()=>firstInput.setCustomValidity(''));
    }
    current.querySelectorAll('textarea[maxlength]').forEach(el => {
      const counter = el.parentElement.querySelector('.dj-pc-count');
      const update=()=>counter.textContent=`${el.value.length}/${el.maxLength}`;
      el.addEventListener('input',update);update();
    });
  }
  function update() {
    const form = root.querySelector('#profile-form');
    if (!form || form.closest('.dj-pc-page')) return;
    const title = root.querySelector('h1.title');
    if (!title || !/profil erstellen/i.test(title.textContent)) return;
    build(form);
  }
  if (document.readyState==='loading') document.addEventListener('DOMContentLoaded', update);
  else update();
  new MutationObserver(update).observe(root,{childList:true,subtree:false});
})();

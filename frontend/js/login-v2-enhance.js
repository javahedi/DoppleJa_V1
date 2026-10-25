(() => {
  'use strict';
  let hintTimer;
  function showHint(message){
    const toast = document.getElementById('toast');
    if(!toast){ window.alert(message); return; }
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(hintTimer);
    hintTimer = setTimeout(() => toast.classList.remove('show'), 2800);
  }
  function iconMail(){return `<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"></rect><path d="M4 7l8 6 8-6"></path></svg>`;}
  function iconLock(){return `<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="11" width="16" height="10" rx="2"></rect><path d="M8 11V8a4 4 0 118 0v3"></path></svg>`;}
  function iconEye(){return `<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6Z"></path><circle cx="12" cy="12" r="2.8"></circle></svg>`;}
  const esc = value => String(value || '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  function buildLoginSection(section){
    const email = section.querySelector('input[name="email"]')?.value || '';
    const password = section.querySelector('input[name="password"]')?.value || '';
    section.className = 'screen dj-login-v2';
    section.innerHTML = `
      <div class="dj-login-top">
        <button class="dj-auth-back" type="button" data-go="home" aria-label="Zurück">‹</button>
        <div class="dj-auth-brand"><img src="/app-assets/assets/brand/doppleja-logo.svg" alt="DoppleJa" class="dj-auth-logo"></div>
        <div aria-hidden="true"></div>
      </div>
      <div class="dj-login-hero"><img src="/app-assets/assets/auth/login-hero.webp" alt="Arbeitnehmerin und Arbeitgeber finden sich über DoppleJa"></div>
      <div class="dj-login-copy"><h1>Willkommen zurück!</h1><p>Melde dich an und mach dort weiter,<br>wo du aufgehört hast.</p></div>
      <form class="form dj-auth-form" id="login-form" novalidate>
        <div class="dj-auth-stack">
          <label class="dj-auth-field"><span class="dj-auth-icon">${iconMail()}</span><input name="email" type="email" autocomplete="email" required placeholder="E-Mail-Adresse" value="${esc(email)}"><span aria-hidden="true"></span></label>
          <label class="dj-auth-field"><span class="dj-auth-icon">${iconLock()}</span><input name="password" type="password" autocomplete="current-password" required placeholder="Passwort" value="${esc(password)}"><button class="dj-auth-toggle" type="button" aria-label="Passwort anzeigen">${iconEye()}</button></label>
        </div>
        <div class="dj-auth-meta"><button type="button" class="dj-auth-text-link" data-auth-soon="Passwort zurücksetzen kommt bald.">Passwort vergessen?</button></div>
        <button class="dj-auth-submit" type="submit"><span>Einloggen</span><span class="dj-auth-submit-arrow" aria-hidden="true">→</span></button>
        <div class="dj-auth-divider"><span>Oder</span></div>
        <div class="dj-auth-alt-actions">
          <button type="button" class="dj-auth-alt-btn" data-auth-soon="Google-Login ist in DoppleJa V1 noch nicht aktiviert."><span class="dj-auth-google">G</span><span>Mit Google einloggen</span></button>
          <button type="button" class="dj-auth-alt-btn" data-auth-soon="Apple-Login ist in DoppleJa V1 noch nicht aktiviert."><span class="dj-auth-apple"></span><span>Mit Apple einloggen</span></button>
        </div>
      </form>
      <div class="dj-auth-footer">Noch kein Konto?<br><button type="button" class="dj-auth-register" data-go="register">Jetzt registrieren →</button></div>`;

    const toggle = section.querySelector('.dj-auth-toggle');
    const passwordInput = section.querySelector('input[name="password"]');
    if(toggle && passwordInput){
      toggle.addEventListener('click', () => {
        const visible = passwordInput.type === 'text';
        passwordInput.type = visible ? 'password' : 'text';
        toggle.setAttribute('aria-label', visible ? 'Passwort anzeigen' : 'Passwort verbergen');
      });
    }
    section.querySelectorAll('[data-auth-soon]').forEach(btn => btn.addEventListener('click', e => {
      e.preventDefault();
      showHint(btn.getAttribute('data-auth-soon') || 'Bald verfügbar.');
    }));
  }
  function maybeEnhance(){
    const root = document.getElementById('app');
    if(!root) return;
    const loginForm = root.querySelector('section.premium-auth #login-form');
    if(!loginForm) return;
    const section = loginForm.closest('section.premium-auth');
    if(!section || section.classList.contains('dj-login-v2')) return;
    buildLoginSection(section);
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', maybeEnhance);
  else maybeEnhance();
  const app = document.getElementById('app');
  if(app){
    const observer = new MutationObserver(() => maybeEnhance());
    observer.observe(app, {childList:true, subtree:true});
  }
})();

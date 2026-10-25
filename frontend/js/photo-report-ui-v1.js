/* DoppleJa photo report UI V1: safe progressive enhancement for employer discover cards. */
(() => {
  'use strict';
  const PHOTO_PATH = /^\/api\/media\/profile-photos\/[0-9a-f]{32}\.webp$/;
  const REASONS = [
    ['sexual_content', 'Sexuelle / unangemessene Inhalte'],
    ['violence', 'Gewalt / verstörende Inhalte'],
    ['hate', 'Hass / Diskriminierung'],
    ['impersonation', 'Identitätsmissbrauch'],
    ['privacy', 'Verletzung der Privatsphäre'],
    ['other', 'Anderer Grund']
  ];
  let activeDialog = null;
  const onEscape = (event) => { if (event.key === 'Escape' && activeDialog) closeDialog(); };

  function closeDialog() {
    if (!activeDialog) return;
    const {overlay, opener} = activeDialog;
    document.removeEventListener('keydown', onEscape);
    overlay.remove();
    activeDialog = null;
    if (opener?.isConnected) opener.focus();
  }

  function identifyPhoto(card) {
    const photo = card.querySelector('.dj-b6-photo img');
    if (!photo) return null;
    try {
      const url = new URL(photo.getAttribute('src'), window.location.href);
      if (url.origin !== window.location.origin || !PHOTO_PATH.test(url.pathname)) return null;
      return url.pathname;
    } catch { return null; }
  }

  function make(tag, className, text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text) el.textContent = text;
    return el;
  }

  function openDialog(photoUrl, opener) {
    if (activeDialog) closeDialog();
    const overlay = make('div', 'dj-report-overlay');
    const panel = make('section', 'dj-report-panel');
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-modal', 'true');
    panel.setAttribute('aria-labelledby', 'dj-report-title');
    const title = make('h2', '', 'Profilfoto melden');
    title.id = 'dj-report-title';
    panel.append(title, make('p', 'dj-report-note', 'Melde nur Inhalte, die gegen die DoppleJa-Regeln verstoßen. Ein Tierbild oder Logo ist allein kein Verstoß.'));
    const form = make('form', 'dj-report-form');
    const reasonLabel = make('label', '', 'Grund der Meldung');
    reasonLabel.htmlFor = 'dj-report-reason';
    const reason = make('select');
    reason.id = 'dj-report-reason';
    reason.required = true;
    reason.append(new Option('Bitte auswählen', ''));
    REASONS.forEach(([value, label]) => reason.append(new Option(label, value)));
    const explanationLabel = make('label', '', 'Beschreibung (optional, maximal 500 Zeichen)');
    explanationLabel.htmlFor = 'dj-report-explanation';
    const explanation = make('textarea');
    explanation.id = 'dj-report-explanation';
    explanation.maxLength = 500;
    explanation.rows = 3;
    const status = make('p', 'dj-report-status');
    status.setAttribute('role', 'status');
    const actions = make('div', 'dj-report-actions');
    const cancel = make('button', 'dj-report-cancel', 'Abbrechen');
    cancel.type = 'button';
    cancel.onclick = closeDialog;
    const submit = make('button', 'dj-report-submit', 'Meldung senden');
    submit.type = 'submit';
    actions.append(cancel, submit);
    form.append(reasonLabel, reason, explanationLabel, explanation, status, actions);
    panel.append(form);
    overlay.append(panel);
    document.body.append(overlay);
    activeDialog = {overlay, opener};
    document.addEventListener('keydown', onEscape);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) closeDialog(); });
    reason.focus();
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (!reason.value) { reason.focus(); return; }
      submit.disabled = true;
      status.textContent = 'Meldung wird gesendet …';
      try {
        const response = await fetch('/api/moderation/photo-reports', {
          method: 'POST',
          credentials: 'same-origin',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({photo_url: photoUrl, reason: reason.value, explanation: explanation.value.trim() || null})
        });
        if (response.status === 201 || response.status === 200) {
          status.textContent = 'Danke! Deine Meldung wurde zur Prüfung erfasst.';
          form.querySelectorAll('select,textarea').forEach(el => el.disabled = true);
          cancel.textContent = 'Schließen';
          submit.remove();
        } else if (response.status === 401 || response.status === 403) {
          status.textContent = 'Bitte melde dich erneut an und versuche es noch einmal.';
          submit.disabled = false;
        } else if (response.status === 429) {
          status.textContent = 'Du hast das Meldelimit erreicht. Bitte versuche es später erneut.';
          submit.disabled = false;
        } else if (response.status === 404) {
          status.textContent = 'Das Profilfoto ist nicht mehr verfügbar.';
          submit.disabled = false;
        } else {
          status.textContent = `Meldung fehlgeschlagen (HTTP ${response.status}).`;
          submit.disabled = false;
        }
      } catch {
        status.textContent = 'Verbindung fehlgeschlagen. Bitte versuche es erneut.';
        submit.disabled = false;
      }
    });
  }

  function enhanceCards() {
    document.querySelectorAll('.dj-b6-card').forEach(card => {
      const photoUrl = identifyPhoto(card);
      const existing = card.querySelector('[data-dj-report-photo]');
      if (!photoUrl) { if (existing) existing.remove(); return; }
      if (existing?.dataset.djReportPhoto === photoUrl) return;
      if (existing) existing.remove();
      const target = card.querySelector('.dj-b6-body');
      if (!target) return;
      const button = make('button', 'dj-report-link', '⚑ Profilfoto melden');
      button.type = 'button';
      button.dataset.djReportPhoto = photoUrl;
      button.setAttribute('aria-label', 'Profilfoto wegen möglichem Regelverstoß melden');
      button.addEventListener('click', () => openDialog(photoUrl, button));
      target.append(button);
    });
  }
  let queued = false;
  function schedule() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => {queued = false; enhanceCards();});
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once:true});
  else start();
  function start() {
    schedule();
    const observer = new MutationObserver(schedule);
    observer.observe(document.getElementById('app') || document.body, {subtree:true,childList:true});
  }
})();

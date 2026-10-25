/* DoppleJa V1 — replace settings shortcut with explicit logout on main tabs. */
(() => {
  'use strict';
  const root = document.getElementById('app');
  if (!root) return;
  const svg = '<svg viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 17l5-5-5-5"/><path d="M15 12H3"/><path d="M12 3h6a3 3 0 0 1 3 3v12a3 3 0 0 1-3 3h-6"/></svg>';
  function update() {
    // Only the gear shortcuts on signed-in main screens, never the login screen.
    root.querySelectorAll('button[data-go="settings"]').forEach(button => {
      if (button.dataset.djLogoutReady) return;
      button.dataset.djLogoutReady = 'yes';
      button.removeAttribute('data-go');
      button.id = 'logout'; // delegated root click handler already handles this action.
      button.classList.add('dj-logout-shortcut');
      button.setAttribute('aria-label', 'Abmelden');
      button.setAttribute('title', 'Abmelden');
      button.innerHTML = svg;
    });
  }
  new MutationObserver(update).observe(root, {childList:true,subtree:true});
  update();
})();

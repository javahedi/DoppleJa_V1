/* DoppleJa profile-header V1: one logout shortcut, no back arrow on main Profile tab. */
(() => {
  'use strict';
  const root = document.getElementById('app');
  if (!root) return;
  const logoutIcon = '<svg viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 17l5-5-5-5"/><path d="M15 12H3"/><path d="M12 3h6a3 3 0 0 1 3 3v12a3 3 0 0 1-3 3h-6"/></svg>';
  function update() {
    root.querySelectorAll('.dj-pv2-screen .dj-pv2-mast').forEach(mast => {
      const back = mast.querySelector('.dj-pv2-back');
      if (back) back.remove();
      const edit = mast.querySelector('.dj-pv2-edit-top');
      if (!edit || edit.dataset.djProfileLogout === 'yes') return;
      edit.dataset.djProfileLogout = 'yes';
      edit.id = 'logout';
      edit.type = 'button';
      edit.removeAttribute('data-go');
      edit.classList.add('dj-profile-logout');
      edit.setAttribute('aria-label','Abmelden');
      edit.setAttribute('title','Abmelden');
      edit.replaceChildren();
      edit.insertAdjacentHTML('afterbegin',logoutIcon);
      // Keep the existing delegated #logout click handler in app.js.
      // Do not attach a second click handler, to avoid duplicate API requests.
    });
  }
  const observer = new MutationObserver(update);
  observer.observe(root,{childList:true,subtree:true});
  update();
})();

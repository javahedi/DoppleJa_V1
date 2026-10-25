/* DoppleJa: one shared header identity on four signed-in main tabs.
   Does not change existing navigation or logout listeners. */
(() => {
  'use strict';
  const root = document.getElementById('app');
  if (!root) return;
  const LOGO_URL = '/app-assets/assets/brand/doppleja-logo.svg';
  const selectors = [
    '.djv2-discover .djv2-top',
    '.dj-matches-v3 .dj-mv-head',
    '.dj-chat3-list > .header',
    '.dj-pv2-view .dj-pv2-mast'
  ];
  function normalize() {
    for (const header of root.querySelectorAll(selectors.join(','))) {
      if (!header.classList.contains('dj-app-header')) header.classList.add('dj-app-header');
      let image = header.querySelector(':scope > img');
      if (!image) {
        const old = header.querySelector(':scope > .logo');
        image = document.createElement('img');
        if (old) old.replaceWith(image);
        else header.prepend(image);
      }
      if (image.getAttribute('src') !== LOGO_URL) image.setAttribute('src', LOGO_URL);
      image.alt = 'DoppleJa';
      image.classList.add('dj-app-header-logo');
      // Preserve profile/logout controls and pre-existing handlers.
      // Profile-header patch removes the back arrow; don't reintroduce it.
      for (const button of header.querySelectorAll(':scope > button')) {
        if (!button.classList.contains('dj-app-header-action')) button.classList.add('dj-app-header-action');
      }
    }
  }
  let queued = false;
  const schedule = () => {
    if (queued) return;
    queued = true;
    queueMicrotask(() => { queued = false; normalize(); });
  };
  new MutationObserver(schedule).observe(root, {childList:true, subtree:true});
  schedule();
})();

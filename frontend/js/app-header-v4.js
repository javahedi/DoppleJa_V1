/* DoppleJa V4: One physical header slot shared by signed-in main tabs. */
(() => {
  'use strict';
  const root = document.getElementById('app');
  if (!root) return;
  const logo = '/app-assets/assets/brand/doppleja-logo.svg';
  const selectors = [
    '.djv2-discover .djv2-top',
    '.dj-matches-v3 .dj-mv-head',
    '.dj-chat3-list > .header',
    '.dj-pv2-view .dj-pv2-mast'
  ];
  const sourceSelector = selectors.join(',');
  let scheduled = false;
  function reconcile() {
    const source = root.querySelector(sourceSelector);
    let slot = root.querySelector(':scope > .dj-v4-slot');
    if (!source) {
      if (slot) slot.remove();
      return;
    }
    if (!slot) {
      slot = document.createElement('header');
      slot.className = 'dj-v4-slot';
      slot.setAttribute('aria-label','DoppleJa Hauptnavigation');
      root.prepend(slot);
    }
    // The source page remains responsible for the action's existing behavior.
    // Move the actual button rather than cloning it, preserving IDs and handlers.
    let action = source.querySelector(':scope > button:not(.dj-pv2-back)');
    if (action && action.parentElement === source) {
      action.classList.add('dj-v4-action');
      slot.append(action);
    }
    const hasLogo = slot.querySelector(':scope > img.dj-v4-logo');
    if (!hasLogo) {
      const img = document.createElement('img');
      img.className = 'dj-v4-logo'; img.src = logo; img.alt = 'DoppleJa';
      slot.prepend(img);
    }
    source.classList.add('dj-v4-hidden');
    // In case older patches added redundant header controls, hide that entire header.
    for (const header of root.querySelectorAll(sourceSelector)) header.classList.add('dj-v4-hidden');
  }
  function schedule() {
    if (scheduled) return;
    scheduled = true;
    queueMicrotask(() => { scheduled = false; reconcile(); });
  }
  new MutationObserver(schedule).observe(root,{childList:true,subtree:true});
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', schedule, {once:true});
  else schedule();
})();

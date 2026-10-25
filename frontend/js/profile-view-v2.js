/* DoppleJa Profile View V2 – enhancement of the existing rendered profile.
   No independent API requests. Existing form, ratings and SPA navigation remain intact. */
(() => {
  'use strict';
  const root = document.getElementById('app');
  if (!root) return;
  const icon = (name) => ({
    pencil:'✎',pin:'⌖',more:'···',camera:'▧',back:'‹'
  })[name] || '';
  function enhance() {
    const screen = root.querySelector('section.screen');
    if (!screen || screen.classList.contains('dj-pv2-screen')) return;
    const banner = screen.querySelector('.dj-profile-banner');
    const form = screen.querySelector('#profile-form');
    if (!banner || !form || !screen.querySelector('.dj54b-profile-panel')) return;
    const previousHeader = screen.querySelector('.header');
    const nav = root.querySelector('.bottom-nav');
    const ratings = screen.querySelector('.dj54b-profile-panel');
    const details = screen.querySelector('.dj-detail-grid');
    const editor = form.closest('.dj-glass-panel');
    const name = banner.querySelector('.dj-profile-overlay h2')?.textContent?.trim() || 'Mein Profil';
    const role = banner.querySelector('.dj-profile-chip')?.textContent?.trim() || 'Profil';
    const location = banner.querySelector('.dj-profile-overlay p')?.textContent?.replace(/^\s*⌖\s*/, '').trim() || '';
    const worker = /jobsuchend/i.test(role);
    const description = form.querySelector(worker?'textarea[name="bio"]':'textarea[name="description"]')?.value?.trim() || '';
    const image = banner.querySelector('img')?.getAttribute('src') || '';
    const placeholder = banner.querySelector('.dj-photo-label')?.textContent?.trim() === 'Symbolbild';
    const ratingText = ratings.querySelector('.dj54b-rating')?.textContent?.trim() || 'Noch keine Bewertungen';
    const page = document.createElement('div');
    page.className = 'dj-pv2-view';
    const mast = document.createElement('header');
    mast.className = 'dj-pv2-mast';
    mast.innerHTML = `<button type="button" class="dj-pv2-back" data-go="discover" aria-label="Zurück">‹</button><img src="/app-assets/assets/brand/doppleja-logo.svg" alt="DoppleJa" class="dj-pv2-logo"><button type="button" class="dj-pv2-edit-top" aria-label="Profil bearbeiten">✎</button>`;
    const hero = document.createElement('section');
    hero.className = 'dj-pv2-hero';
    const photo = document.createElement('img');
    photo.src = image;
    photo.alt = placeholder ? 'Symbolbild für dieses Profil' : 'Profilbild';
    photo.loading = 'eager';
    hero.append(photo);
    const topbadges = document.createElement('div');
    topbadges.className = 'dj-pv2-topbadges';
    const label = document.createElement('span'); label.textContent = placeholder ? 'Symbolbild' : 'Profilbild';
    topbadges.append(label); hero.append(topbadges);
    const edit = document.createElement('button');
    edit.type = 'button'; edit.className = 'dj-pv2-edit'; edit.textContent = '✎  Profil bearbeiten';
    hero.append(edit);
    const summary = document.createElement('section');
    summary.className = 'dj-pv2-summary';
    const headline = document.createElement('div'); headline.className = 'dj-pv2-headline';
    const h1 = document.createElement('h1'); h1.textContent = name;
    headline.append(h1); summary.append(headline);
    const subtitle = document.createElement('p'); subtitle.className = 'dj-pv2-role'; subtitle.textContent = worker ? (form.querySelector('[name="profession"]')?.value?.trim() || 'Arbeitnehmer') : (form.querySelector('[name="category"]')?.value?.trim() || role);
    summary.append(subtitle);
    const locationLine = document.createElement('p'); locationLine.className = 'dj-pv2-location'; locationLine.textContent = location ? `⌖  ${location}` : 'Standort nicht angegeben';
    summary.append(locationLine);
    const ratingLine = document.createElement('div'); ratingLine.className = 'dj-pv2-rating';
    ratingLine.textContent = ratingText;
    summary.append(ratingLine);
    if (description) {
      const bio = document.createElement('p'); bio.className = 'dj-pv2-bio'; bio.textContent = description; summary.append(bio);
    }
    const detailsSection = document.createElement('section'); detailsSection.className = 'dj-pv2-details';
    const detailTitle = document.createElement('h2'); detailTitle.textContent = worker ? 'Auf einen Blick' : 'Über uns';
    detailsSection.append(detailTitle);
    if (details) detailsSection.append(details);
    const reviews = document.createElement('section'); reviews.className = 'dj-pv2-reviews';
    const reviewsTitle = document.createElement('h2'); reviewsTitle.textContent = 'Bewertungen'; reviews.append(reviewsTitle);
    reviews.append(ratings);
    const editWrap = document.createElement('section'); editWrap.className = 'dj-pv2-editor'; editWrap.hidden = true;
    const editHeading = editor.querySelector('.dj-panel-heading');
    if(editHeading) editHeading.remove();
    const editTitle = document.createElement('h2'); editTitle.textContent = 'Profil bearbeiten'; editWrap.append(editTitle);
    editWrap.append(editor);
    const openEdit = () => { editWrap.hidden = false; editWrap.scrollIntoView({behavior:'smooth',block:'start'}); };
    edit.addEventListener('click',openEdit);
    mast.querySelector('.dj-pv2-edit-top').addEventListener('click',openEdit);
    page.append(mast,hero,summary,detailsSection,reviews,editWrap);
    screen.replaceChildren(page);
    screen.classList.add('dj-pv2-screen');
    if (nav) nav.classList.add('dj-pv2-nav');
  }
  function sync() {
    // Disconnect while modifying DOM so the observer cannot retrigger recursively.
    observer.disconnect();
    try { enhance(); } catch (err) { console.error('DoppleJa profile view enhancement:', err); }
    observer.observe(root,{childList:true,subtree:true});
  }
  const observer = new MutationObserver(sync);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',sync);
  else sync();
})();

/* DoppleJa profile photo editor — persistent authenticated upload. */
(() => {
  'use strict';
  const root = document.getElementById('app');
  if (!root || window.DoppleJaPhotoEditor) return;
  const MAX_BYTES = 5 * 1024 * 1024;
  const MAX_PIXELS = 20_000_000;
  const ACCEPTED = new Set(['image/jpeg','image/png','image/webp']);
  let active = false;
  let lastObjectURL = null;
  const escapeHtml = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function open(options = {}) {
    if (active) return;
    active = true;
    const onSave = typeof options.onSave === 'function' ? options.onSave : (() => {});
    const previousFocus = document.activeElement;
    let image = null, url = null, zoom = 1, offsetX = 0, offsetY = 0, pointer = null, dragX = 0, dragY = 0;
    const overlay = document.createElement('div');
    overlay.className = 'dj-photo-modal';
    overlay.innerHTML = `<section class="dj-photo-dialog" role="dialog" aria-modal="true" aria-labelledby="dj-photo-title">
      <header class="dj-photo-dialog-head"><h2 id="dj-photo-title">Profilfoto bearbeiten</h2><button type="button" class="dj-photo-close" aria-label="Schließen">✕</button></header>
      <p class="dj-photo-instructions">Wähle ein Bild und verschiebe es mit dem Finger oder der Maus innerhalb des Kreises.</p>
      <div class="dj-photo-stage" tabindex="0" aria-label="Bildausschnitt verschieben"><canvas width="320" height="320" aria-hidden="true"></canvas><div class="dj-photo-mask" aria-hidden="true"></div><div class="dj-photo-empty">📷<span>Foto auswählen</span></div></div>
      <label class="dj-photo-choose">Bild auswählen<input type="file" accept="image/jpeg,image/png,image/webp" hidden></label>
      <div class="dj-photo-zoom"><span>−</span><input type="range" min="1" max="3" step="0.01" value="1" aria-label="Bild vergrößern" disabled><span>+</span></div>
      <p class="dj-photo-error" role="alert" hidden></p>
      <p class="dj-photo-note">Das Foto wird sicher in deinem DoppleJa Profil gespeichert.</p>
      <footer><button type="button" class="dj-photo-cancel">Abbrechen</button><button type="button" class="dj-photo-save" disabled>Ausschnitt übernehmen</button></footer>
    </section>`;
    document.body.append(overlay);
    const canvas = overlay.querySelector('canvas'), ctx = canvas.getContext('2d');
    const fileInput = overlay.querySelector('input[type="file"]');
    const slider = overlay.querySelector('input[type="range"]');
    const stage = overlay.querySelector('.dj-photo-stage');
    const save = overlay.querySelector('.dj-photo-save');
    const error = overlay.querySelector('.dj-photo-error');
    const empty = overlay.querySelector('.dj-photo-empty');
    const closeButton = overlay.querySelector('.dj-photo-close');
    function warn(message) { error.textContent = message; error.hidden = !message; }
    function bounds() {
      if (!image) return {w:320,h:320,limitX:0,limitY:0};
      const base = Math.max(320/image.naturalWidth,320/image.naturalHeight);
      const w=image.naturalWidth*base*zoom, h=image.naturalHeight*base*zoom;
      return {w,h,limitX:(w-320)/2,limitY:(h-320)/2};
    }
    function render() {
      ctx.clearRect(0,0,320,320);
      ctx.fillStyle='#ede6fa'; ctx.fillRect(0,0,320,320);
      if (!image) return;
      const b=bounds();
      offsetX=Math.min(b.limitX,Math.max(-b.limitX,offsetX));
      offsetY=Math.min(b.limitY,Math.max(-b.limitY,offsetY));
      ctx.drawImage(image,160-b.w/2+offsetX,160-b.h/2+offsetY,b.w,b.h);
    }
    function cleanup() {
      active=false;
      if (url) URL.revokeObjectURL(url);
      overlay.remove();
      previousFocus?.focus?.();
    }
    async function pick(file) {
      if (!file) return;
      warn('');
      if (!ACCEPTED.has(file.type)) return warn('Bitte JPG, PNG oder WebP auswählen. HEIC folgt später.');
      if (file.size > MAX_BYTES) return warn('Das Foto darf höchstens 5 MB groß sein.');
      const nextURL=URL.createObjectURL(file);
      const nextImage=new Image();
      try {
        await new Promise((resolve,reject)=>{nextImage.onload=resolve;nextImage.onerror=reject;nextImage.src=nextURL;});
        if (!nextImage.naturalWidth || !nextImage.naturalHeight || nextImage.naturalWidth*nextImage.naturalHeight > MAX_PIXELS) throw new Error('Das Bild ist zu groß oder nicht lesbar.');
        if (url) URL.revokeObjectURL(url);
        url=nextURL; image=nextImage; zoom=1; offsetX=0;offsetY=0;
        slider.value='1'; slider.disabled=false; save.disabled=false; empty.hidden=true; render();
      } catch (e) {URL.revokeObjectURL(nextURL);warn(e.message || 'Das Bild konnte nicht gelesen werden.');}
    }
    fileInput.addEventListener('change',()=>pick(fileInput.files?.[0]));
    slider.addEventListener('input',()=>{zoom=Number(slider.value);render();});
    stage.addEventListener('pointerdown',e=>{if(!image)return;pointer=e.pointerId;dragX=e.clientX;dragY=e.clientY;stage.setPointerCapture(pointer);});
    stage.addEventListener('pointermove',e=>{if(e.pointerId!==pointer)return;const ratio=320/stage.getBoundingClientRect().width;offsetX+=(e.clientX-dragX)*ratio;offsetY+=(e.clientY-dragY)*ratio;dragX=e.clientX;dragY=e.clientY;render();});
    stage.addEventListener('pointerup',()=>{pointer=null;});
    stage.addEventListener('pointercancel',()=>{pointer=null;});
    stage.addEventListener('keydown',e=>{if(!image)return;const dir={ArrowLeft:[-8,0],ArrowRight:[8,0],ArrowUp:[0,-8],ArrowDown:[0,8]}[e.key];if(dir){e.preventDefault();offsetX+=dir[0];offsetY+=dir[1];render();}});
    overlay.querySelector('.dj-photo-cancel').addEventListener('click',cleanup);
    closeButton.addEventListener('click',cleanup);
    overlay.addEventListener('click',e=>{if(e.target===overlay)cleanup();});
    const onKey = e=>{if(e.key==='Escape'){document.removeEventListener('keydown',onKey);cleanup();}};
    document.addEventListener('keydown',onKey);
    const oldCleanup=cleanup;
    // Deliver cropped image to the server; update UI only after successful upload.
    save.addEventListener('click',()=>{
      if(!image)return;
      const result=document.createElement('canvas');result.width=512;result.height=512;
      const output=result.getContext('2d');output.drawImage(canvas,0,0,512,512);
      result.toBlob(blob=>{
        if(!blob){warn('Bild konnte nicht verarbeitet werden.');return;}
        if(lastObjectURL) URL.revokeObjectURL(lastObjectURL);
        lastObjectURL=URL.createObjectURL(blob);
        save.disabled=true;
        Promise.resolve(onSave({blob,previewUrl:lastObjectURL,width:512,height:512}))
          .then(()=>{document.removeEventListener('keydown',onKey);oldCleanup();})
          .catch(e=>{save.disabled=false;warn(e.message||'Upload fehlgeschlagen.');});
      },'image/webp',0.85);
    });
    closeButton.focus();
  }
  window.DoppleJaPhotoEditor={open};
  async function upload(blob) {
    const body=new FormData();body.append('photo',blob,'profile.webp');
    const response=await fetch('/api/media/profile-photo',{method:'POST',body,credentials:'same-origin'});
    let result={};try{result=await response.json();}catch(_e){}
    if(!response.ok)throw new Error(response.status===409?'Bitte zuerst dein Profil speichern. Danach kannst du ein Foto hochladen.':(typeof result.detail==='string'?result.detail:'Foto konnte nicht gespeichert werden.'));
    if(!result.photo_url)throw new Error('Ungültige Serverantwort.');
    return result.photo_url;
  }
  function enhance() {
    root.querySelectorAll('.dj-pc-photo:not([data-photo-ready])').forEach(area=>{
      area.dataset.photoReady='1';
      const button=document.createElement('button');button.type='button';button.className='dj-photo-trigger';button.textContent='📷 Foto hochladen';
      area.append(button);
      button.addEventListener('click',()=>open({onSave:async({blob})=>{
        const url=await upload(blob);
        let preview=area.querySelector('.dj-photo-preview');
        if(!preview){preview=document.createElement('img');preview.className='dj-photo-preview';preview.alt='Gespeichertes Profilfoto';area.prepend(preview);}
        preview.src=url;
        area.querySelector('.dj-pc-avatar')?.setAttribute('hidden','');
        const note=area.querySelector('small');if(note)note.textContent='Foto gespeichert!';
      }}));
    });
    root.querySelectorAll('.dj-pv2-hero:not([data-photo-ready])').forEach(hero=>{
      hero.dataset.photoReady='1';
      const btn=document.createElement('button');btn.type='button';btn.className='dj-photo-hero-trigger';btn.textContent='📷 Foto ändern';
      hero.append(btn);
      btn.addEventListener('click',()=>open({onSave:async({blob})=>{
        const url=await upload(blob);
        const img=hero.querySelector('img');if(img)img.src=url;
        const label=hero.querySelector('.dj-pv2-topbadges span');if(label)label.textContent='Profilbild';
      }}));
    });
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',enhance);else enhance();
  new MutationObserver(enhance).observe(root,{childList:true,subtree:true});
})();

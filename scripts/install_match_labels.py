"""Patch existing 5.1B frontend safely; refuses unknown source layouts."""
from pathlib import Path
import re

main = Path('backend/app/main.py')
js = Path('frontend/js/app.js')
assert main.exists() and js.exists(), 'Run from DoppleJa_V1 project root.'
source = main.read_text()
import_line = 'from backend.app.modules.match_summaries.router import router as match_summaries_router'
include_line = 'app.include_router(match_summaries_router)'
if import_line not in source:
    anchor = 'app = FastAPI('
    assert anchor in source, 'FastAPI app declaration not found; do not modify automatically.'
    source = source.replace(anchor, import_line + '\n\n' + anchor, 1)
if include_line not in source:
    anchor = 'app.include_router(auth_router)'
    assert anchor in source, 'Auth router registration not found; do not modify automatically.'
    source = source.replace(anchor, anchor + '\n' + include_line, 1)

script = js.read_text()
assert 'async function likesView()' in script, 'Install Phase 5.1B first.'
helper = '''  const fullDate = v => v ? new Date(v).toLocaleString('de-DE', {day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit'}) : '';
  const summaryHeader = m => `${esc(m.job_title)} · ${esc(m.other_party_name)}`;
  const matchCard = m => `<article class="list-card match-summary-card">
    <div class="avatar">${m.has_messages?'💬':'♥'}</div>
    <div class="grow"><strong>${summaryHeader(m)}</strong>
      <small>${esc(m.city)} · ${m.has_messages?'Unterhaltung läuft':'Neues Match'}</small>
      <small>${m.has_messages ? `${esc(m.last_message.content)} · ${fullDate(m.last_message.created_at)}` : `Match am ${fullDate(m.matched_at)}`}</small>
    </div><button data-open-match="${esc(m.match_id)}">${m.has_messages?'Chat öffnen':'Nachricht senden'} →</button>
  </article>`;
'''
if 'const summaryHeader = m =>' not in script:
    anchor = '  async function matchesView()'
    assert script.count(anchor) == 1
    script = script.replace(anchor, helper + anchor, 1)

matches = '''  async function matchesView(){
    if(!state.user)return navigate('login');
    state.matches=await api('/api/match-summaries');
    render(shell(`<h1 class="title">Deine Matches 💜</h1><p class="subtitle">Neue Matches und laufende Unterhaltungen.</p>
      ${state.matches.length?state.matches.map(matchCard).join(''):`<div class="empty"><div class="emoji">🤝</div><h3>Noch kein Match</h3><p>Wenn ihr euch beide liked, erscheint euer Match hier.</p><button class="btn" data-go="discover">Entdecken</button></div>`}`,'matches'));
  }
'''
chats = '''  async function chatsView(){
    if(!state.user)return navigate('login');
    const summaries=await api('/api/match-summaries');
    state.chats=summaries.sort((a,b)=>new Date(b.last_message?.created_at||b.matched_at)-new Date(a.last_message?.created_at||a.matched_at));
    render(shell(`<h1 class="title">Nachrichten</h1><p class="subtitle">Deine Matches und Unterhaltungen.</p>
      ${state.chats.length?state.chats.map(matchCard).join(''):`<div class="empty"><div class="emoji">💬</div><h3>Hier ist es noch ruhig</h3><p>Deine Matches erscheinen hier, damit ihr ein Gespräch beginnen könnt.</p><button class="btn" data-go="likes">Meine Likes</button></div>`}`,'chats'));
  }
'''
# Replace only exact single-line 5.1B functions, without altering chat or other components.
for name, replacement in [('matchesView', matches), ('chatsView', chats)]:
    pattern = rf'^  async function {name}\(\)\{{[^\n]*\}}\n'
    script, count = re.subn(pattern, lambda m: replacement, script, count=1, flags=re.MULTILINE)
    assert count == 1, f'Unexpected {name} layout. No files changed; inspect manually.'

# Augment liked job cards with latest communication state.
old_likes = "    const items=await api('/api/workers/me/likes');"
assert old_likes in script, 'Cannot locate Phase 5.1B likes endpoint.'
script=script.replace(old_likes, "    const [items, summaries]=await Promise.all([api('/api/workers/me/likes'),api('/api/match-summaries')]);\n    const summariesById=new Map(summaries.map(m=>[m.match_id,m]));", 1)
old_status = "      const [label,cls]=statusInfo[j.status]||statusInfo.pending;"
assert old_status in script
script=script.replace(old_status, old_status + "\n      const details=j.match_id?summariesById.get(j.match_id):null;\n      const activity=details?(details.has_messages?`Unterhaltung läuft · ${esc(details.last_message.content)} · ${fullDate(details.last_message.created_at)}`:`Neues Match · ${esc(details.other_party_name)} · ${fullDate(details.matched_at)}`):'';",1)
old_desc = "<p class=\"desc\">${esc(j.description||'Keine Beschreibung')}</p>"
assert old_desc in script
likes_start=script.index("  async function likesView()")
script=script[:likes_start]+script[likes_start:].replace(old_desc, old_desc + "\n        ${activity?`<p class=\"match-activity\">${activity}</p>`:''}",1)

# The worker's Likes view already displays job title; enhance matched job button copy and timestamp.
old = "<button class=\"btn small\" data-open-match=\"${esc(j.match_id)}\">Zum Chat →</button>"
# Preserve status semantics; primary matches/chats now display all summaries.
if old in script:
    script = script.replace(old, '<button class="btn small" data-open-match="${esc(j.match_id)}">Match ansehen →</button>')

# Save only after validation of all required anchors.
main.write_text(source)
js.write_text(script)
print('Match-summaries API registered; Matches and Chats UI updated.')

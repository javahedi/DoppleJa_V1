"""Apply scoped, repeatable Phase 5.2A UI update, preserving existing backend and SPA logic."""
from pathlib import Path
import re, shutil, sys
root=Path.cwd()
app=root/'frontend/js/app.js'
index=root/'frontend/index.html'
css=root/'frontend/css/styles.css'
pkg=Path(__file__).resolve().parent.parent
for x in (app,index,css):
    if not x.exists(): sys.exit(f'Missing {x}; run from DoppleJa_V1 project root')
old=app.read_text()
if 'PHASE_52A_START' in old:
    print('Phase 5.2A already installed; no changes needed')
    sys.exit(0)
# Validate before writing any files
anchors=[r'^  function home\(\)\{[^\n]*\}\n',r'^  function loginView\(\)\{[^\n]*\}\n',r'^  function registerView\(\)\{[^\n]*\}\n',r'^  function verifyView\(\)\{[^\n]*\}\n']
for anchor in anchors:
    if len(re.findall(anchor,old,re.M))!=1:
        sys.exit(f'Source layout changed: {anchor}. No files modified. Send us this error instead of overwriting your changes.')
if 'id=\'register-form\'' not in old and 'id="register-form"' not in old:
    sys.exit('Registration form not found: refusing to patch')
views=(pkg/'views.js.txt').read_text()
parts={}
for label in ('home','loginView','registerView','verifyView'):
    a=f'// SECTION:{label}\n'; b=f'// END:{label}\n'
    if a not in views or b not in views:sys.exit('Package missing section '+label)
    parts[label]=views.split(a,1)[1].split(b,1)[0]
updated=old
for anchor,label in zip(anchors,parts):
    updated,n=re.subn(anchor,lambda m:parts[label],updated,count=1,flags=re.M)
    if n!=1:sys.exit('Unexpected failure while changing '+label)
updated=updated.replace("if(form.id==='register-form'){await api('/api/auth/register'", "if(form.id==='register-form'){delete v.interest;await api('/api/auth/register'",1)
if updated.count('function home(')!=1 or updated.count('function registerView(')!=1:sys.exit('Validation failed')
backup=root/'.phase5_2a_backup'
backup.mkdir(exist_ok=True)
for f in (app,index,css):shutil.copy2(f,backup/f.name)
app.write_text('/* PHASE_52A_START: premium onboarding; existing application modules remain intact */\n'+updated)
idx=index.read_text()
idx=idx.replace('</head>','  <link rel="stylesheet" href="/app-assets/css/premium-onboarding.css?v=52a1">\n</head>',1)
index.write_text(idx)
shutil.copy2(pkg/'frontend/css/premium-onboarding.css',root/'frontend/css/premium-onboarding.css')
for f in (pkg/'frontend/assets').iterdir(): shutil.copy2(f,root/'frontend/assets'/f.name)
print('Phase 5.2A installed. Backup in .phase5_2a_backup. No backend/database changes.')

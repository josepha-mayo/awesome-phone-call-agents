"""Verify ReturnReady 0.4 and publish only reviewed app files to its existing PR head."""
from pathlib import Path
from datetime import datetime, timezone
import base64, hashlib, json, lzma, os, re, shutil, subprocess, sys, time, traceback, zipfile
ROOT=Path(__file__).resolve().parents[1];APP=ROOT/'apps/python/returnready';E=APP/'evidence04';E.mkdir(exist_ok=True)
BASE='fc940c33882d5f46f244891c15129de911f08c4c';HEAD='feat/returnready-review'
report={'status':'running','started_at':datetime.now(timezone.utc).isoformat(),'commands':[],'provider_calls_in_verification':0,'base_commit':BASE,'workflow_run':os.getenv('GITHUB_RUN_ID'),'contribution_published':False}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(name,command,cwd=ROOT,timeout=300):
 t=time.monotonic();p=subprocess.run(command,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout);(E/(name+'.log')).write_text(p.stdout);report['commands'].append({'name':name,'exit_code':p.returncode,'seconds':round(time.monotonic()-t,2)});print(name,p.returncode,flush=True)
 if p.returncode:raise RuntimeError(name+': '+p.stdout[-5000:])
 return p.stdout
original={name:digest(APP/name)for name in ['test_returnready.py','http_test.py','test_completion.py','browser_completion.py']}
try:
 run('repository-before',[sys.executable,'scripts/validate_repository.py'])
 encoded=''.join((ROOT/'returnready-mcp-input'/name).read_text().strip()for name in ['part1.b64','part2.b64']);raw=base64.b64decode(encoded,validate=True)
 assert hashlib.sha256(raw).hexdigest()=='18bd9b468cba5cec6ac5b43c7e3f34494acb9556f9879c0943bdf4f27a1f9ecc'
 files=json.loads(lzma.decompress(raw));assert set(files)=={'mcp_import.py','test_mcp_import.py','browser_mcp.py','docs/MCP-RESULT-IMPORT.md','patch04.py'}
 for name,text in files.items():
  assert isinstance(text,str)and '..'not in Path(name).parts
  p=(ROOT/'returnready-mcp-input/patch04.py')if name=='patch04.py'else(APP/name);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
 run('patch-reviewed-source',[sys.executable,'returnready-mcp-input/patch04.py',str(APP)])
 output=run('python-tests',[sys.executable,'-m','unittest','test_returnready','http_test','test_completion','test_mcp_import','-v'],cwd=APP)
 n=int(re.search(r'Ran (\d+) tests',output).group(1));assert n==130 and '\nOK\n'in output
 run('inherited-browser',[sys.executable,'browser_completion.py'],cwd=APP,timeout=240)
 old=json.loads((APP/'evidence03/browser-http.json').read_text());assert old['status']=='passed'and old['mode']=='actual local HTTP'and old['count']==18
 shutil.copy2(APP/'evidence03/browser-http.json',E/'inherited-browser.json')
 run('mcp-browser-and-demo',[sys.executable,'browser_mcp.py'],cwd=APP,timeout=480)
 new=json.loads((E/'browser-mcp.json').read_text());assert new['status']=='passed'and new['mode']=='actual local HTTP';assert new['demo_duration_seconds']<180
 assert original=={name:digest(APP/name)for name in original},'Inherited assertions changed'
 # Keep inherited evidence in its historical state, with current outcomes in evidence04.
 run('restore-historical-evidence',['git','restore','--','apps/python/returnready/evidence03'])
 run('repository-after',[sys.executable,'scripts/validate_repository.py'])
 selected=['mcp_import.py','test_mcp_import.py','browser_mcp.py','returnready.py','web/index.html','README.md','docs/MCP-RESULT-IMPORT.md']
 hashes={name:digest(APP/name)for name in selected}
 report.update(status='passed',python_tests=n,inherited_python_tests=92,new_python_tests=38,inherited_browser_workflows=18,new_browser_workflows=new['count'],total_browser_workflows=18+new['count'],demo_duration_seconds=new['demo_duration_seconds'],source_sha256=hashes,inherited_assertions_unchanged=True,scope='Operator-mediated finished MCP import; real localhost tests. The demo uses synthetic review cases and redacted metadata from one blocked hotline attempt. No raw call transcript, voice or provider identifier is published. No REST live validation, merchant success or customer benefit is established.')
 report['finished_at']=datetime.now(timezone.utc).isoformat();(E/'verification.json').write_text(json.dumps(report,indent=2))
 # Publish only app text plus the executed report; never workflow, input archive or video.
 run('read-existing-head',['git','fetch','origin',HEAD])
 current=subprocess.check_output(['git','rev-parse','FETCH_HEAD'],cwd=ROOT,text=True).strip();assert current==BASE,'Existing PR head changed; reconcile instead of overwriting'
 wt=ROOT.parent/'returnready-scoped-publish';run('scoped-worktree',['git','worktree','add','--detach',str(wt),current])
 for name in selected+['evidence04/verification.json']:
  dest=wt/'apps/python/returnready'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(APP/name,dest)
 paths=['apps/python/returnready/'+name for name in selected+['evidence04/verification.json']]
 run('stage-scoped',['git','add','--',*paths],cwd=wt)
 changed=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=wt,text=True).splitlines();assert set(changed)==set(paths),changed
 run('scoped-repository-check',[sys.executable,'scripts/validate_repository.py'],cwd=wt)
 run('identity',['git','config','user.name','ReturnReady Verification'],cwd=wt);run('identity-email',['git','config','user.email','returnready@users.noreply.github.com'],cwd=wt)
 run('commit-reviewed',['git','commit','-m','Add finished MCP result import with explicit blocked outcomes and verified no-call workflow'],cwd=wt)
 sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=wt,text=True).strip()
 run('publish-existing-contribution',['git','push','origin','HEAD:'+HEAD],cwd=wt)
 report.update(contribution_published=True,contribution_commit=sha,contribution_branch=HEAD)
 # Verification in the committed source intentionally predates the push; this artifact adds its receipt.
 (E/'publication.json').write_text(json.dumps({'commit':sha,'branch':HEAD,'paths':changed,'source_sha256':hashes,'new_upstream_pr_created':False},indent=2))
 with zipfile.ZipFile(E/'returnready-source.zip','w',zipfile.ZIP_DEFLATED)as z:
  for path in sorted((wt/'apps/python/returnready').rglob('*')):
   if path.is_file()and'__pycache__'not in path.parts and path.suffix.lower()not in ['.pyc','.ttf','.otf','.woff','.woff2']:
    z.write(path,str(Path('ReturnReady')/path.relative_to(wt/'apps/python/returnready')))
except BaseException as exc:
 report.update(status='failed',error=str(exc),traceback=traceback.format_exc());raise
finally:
 report['finished_at']=datetime.now(timezone.utc).isoformat();E.mkdir(exist_ok=True);(E/'release.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)

"""Actual localhost HTTP checks and narrated recording; never calls a provider."""
from pathlib import Path
from datetime import datetime, timezone
import json, os, shutil, socket, subprocess, sys, tempfile, time, traceback, wave
from playwright.sync_api import sync_playwright, expect
from test_mcp_import import fixture, RUN
import returnready as rr
R=Path(__file__).resolve().parent;E=R/'evidence04';E.mkdir(exist_ok=True)
checks=[];errors=[];requests=[];scenes=[]
report={'status':'running','mode':'actual local HTTP','provider_calls':0,'new_browser_checks':checks}
def ok(message):checks.append(message);print('PASS',message,flush=True)
# Only metadata about the real completed attempt is used. No transcript, phone,
# real run ID or real call ID is included in these public test/recording inputs.
live_meta={'run_id':'redacted_actual_run','status':'COMPLETED','result':{'call_id':'redacted_actual_call','call_ids':['redacted_actual_call'],'batch':None,'outcome':{'task_completed':True},'extracted':{'calling':{'calls':[{'status':'COMPLETED','duration_seconds':36}],'callee_count':1}}},'next_step':{'action':'report_blocked'}}
unknown={key:None for key in rr.FIELDS}
with tempfile.TemporaryDirectory() as td:
 proc=None
 try:
  with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
  base=f'http://127.0.0.1:{port}'
  proc=subprocess.Popen([sys.executable,str(R/'returnready.py'),'--port',str(port),'--database',td+'/cases.sqlite'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  import urllib.request
  for _ in range(60):
   try:
    with urllib.request.urlopen(base+'/api/config',timeout=1) as response:config=json.load(response)
    break
   except OSError:time.sleep(.1)
  else:raise RuntimeError('HTTP server unavailable')
  assert config['live'] is False
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path=os.getenv('CHROMIUM_EXECUTABLE') or shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox'])
   context=browser.new_context(viewport={'width':1280,'height':960},accept_downloads=True,record_video_dir=str(E/'recording'),record_video_size={'width':1280,'height':960})
   page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append({'url':r.url,'method':r.method}));start=time.monotonic()
   def narrate(text,caption):
    idx=len(scenes);voice=E/f'voice-{idx}.wav';tts=shutil.which('espeak-ng') or shutil.which('espeak');assert tts
    subprocess.run([tts,'-v','en-us','-s','153','-w',str(voice),text],check=True)
    with wave.open(str(voice)) as w:seconds=w.getnframes()/w.getframerate()
    began=time.monotonic()-start;scenes.append({'start':began,'duration':seconds,'audio':str(voice),'caption':caption,'narration':text});page.wait_for_timeout(int((seconds+.7)*1000))
   page.goto(base,wait_until='networkidle');expect(page.locator('.counter')).to_contain_text('4/5')
   narrate('ReturnReady checks a return handoff before anyone ships a package. It compares five spoken details with supplied written instructions. These first examples are synthetic, and every final decision stays with the operator.', 'RETURNREADY / five details, one reviewable handoff\nSynthetic examples first; no shipment is authorized.')
   page.get_by_role('button',name='Inspect Return destination',exact=True).click();expect(page.locator('#evidence')).to_contain_text('22 Different Road')
   narrate('Here the destination changed. Four details match, but a matching score cannot cancel out a different address. The original recipient wording and written value stay visible together.', 'A changed destination holds the handoff.\nFour matching fields do not erase the unresolved address.')
   page.select_option('#case','later_correction');page.click('#run');expect(page.locator('.counter')).to_contain_text('4/5');page.get_by_role('button',name='Inspect Return destination',exact=True).click()
   narrate('A later correction matters too. The conversation first contains five matching answers, then revises the destination. ReturnReady keeps the whole later statement and removes the earlier address from the supported count. This is conservative lexical review, not semantic certainty.', 'Later corrections remain in the evidence.\nAn earlier matching extraction is not automatically final.')
   with page.expect_download() as download:page.click('#export')
   ordinary=json.loads(Path(download.value.path()).read_text());assert ordinary['clearance_to_ship'] is False and ordinary['synthetic_example'] is True
   narrate('The downloaded review preserves the input fingerprints, quoted evidence, and unresolved questions. Saving a session stores inputs for a fresh check, not an approval that can be replayed forever.', 'Actual review download, with source-linked questions.\nSaved inputs are rechecked; saved approval is not trusted.')
   # Real received metadata, identifiers redacted. Import is performed by the UI,
   # not by swapping rendered result markup or calling a mocked inspect function.
   page.click('[data-view=source]');page.fill('#policyJson',json.dumps(unknown));page.fill('#responseJson',json.dumps(live_meta));page.get_by_text('Import a finished CALL-E MCP result',exact=True).click();page.fill('#mcpRun',live_meta['run_id']);page.fill('#mcpObserved','2026-09-09T17:49:21.417599+00:00');page.select_option('#mcpConsent','not_granted');page.fill('#mcpBasis','Recorded real hotline attempt: permission was not granted. Metadata only; identifiers redacted, no transcript included.');page.click('#importMcp');expect(page.locator('#mcpOutcome')).to_contain_text('Enquiry evidence blocked');expect(page.locator('.counter')).to_contain_text('0/5');ok('Redacted real-attempt metadata imports through actual HTTP into a blocked review')
   narrate('One real CALL E hotline attempt connected for thirty six seconds. The answering agent could not grant permission, and no return instructions were obtained. This screen imports recorded metadata only, with identifiers redacted and no call transcript.', 'RECORDED LIVE ATTEMPT / metadata only, identifiers redacted\nConnected for 36 seconds; no return instructions obtained.')
   expect(page.locator('#mcpOutcome')).to_contain_text('task_completed: true');expect(page.locator('#mcpOutcome')).to_contain_text('Transcript and extracted claims withheld');expect(page.locator('#sourceBadge')).to_have_text('IMPORTED MCP RESULT');ok('Provider completion remains visible but does not become supported return evidence')
   page.screenshot(path=str(E/'blocked-import.png'))
   narrate('The provider marked the task completed, but ReturnReady does not treat that flag as a usable answer. Permission was not established. The import holds the case at zero supported answers, excludes the transcript, and never redials.', 'A finished call is not a successful return enquiry.\nZero supported answers. Transcript withheld. No automatic retry.')
   with page.expect_download() as download:page.click('#export')
   blocked=json.loads(Path(download.value.path()).read_text());assert blocked['supported_matches']==0 and blocked['clearance_to_ship'] is False and blocked['synthetic_example'] is False;assert blocked['mcp_receipt']['automatic_retry'] is False
   assert blocked['inputs']['call_result']['recipients'][0]['attempts'][0]['transcript_turns']==[];ok('Downloaded blocked review contains no transcript or extracted return values')
   with page.expect_download() as download:page.click('#saveSession')
   saved=json.loads(Path(download.value.path()).read_text());ok('Actual session download retains the blocked receipt')
   page.set_input_files('#sessionFile',{'name':'blocked-session.json','mimeType':'application/json','buffer':json.dumps(saved).encode()});expect(page.locator('.counter')).to_contain_text('0/5');expect(page.locator('#mcpOutcome')).to_contain_text('Enquiry evidence blocked');ok('Reopening rechecks the blocked receipt instead of reviving a successful state')
   narrate('The same blocked outcome survives a save and reopen. This is an operator mediated MCP result workflow. The separate REST adapter still needs a live test. Source code, repeatable checks, and contribution pull request four zero eight are available. No customer benefit or successful merchant trial is claimed.', 'Reusable MCP result workflow, not a verified REST connection.\nSource and checks are supplied; successful merchant testing remains open.')
   clip=Path(page.video.path());context.close();ok('Recorded actual UI actions and real downloads, with disclosed synthetic narration')
   # Extra actual browser regressions, not part of the public walkthrough.
   context=browser.new_context(viewport={'width':1280,'height':960},accept_downloads=True);page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append({'url':r.url,'method':r.method}));page.goto(base,wait_until='networkidle')
   def inputs(raw,policy,consent='unknown',expected=RUN):
    page.click('[data-view=source]');page.fill('#policyJson',json.dumps(policy));page.fill('#responseJson',json.dumps(raw));details=page.get_by_text('Import a finished CALL-E MCP result',exact=True)
    if not page.locator('#mcpRun').is_visible():details.click()
    page.fill('#mcpRun',expected);page.fill('#mcpObserved',datetime.now(timezone.utc).isoformat());page.select_option('#mcpConsent',consent);page.fill('#mcpBasis','Explicit synthetic browser test permission review.')
   raw,policy,fields=fixture(datetime.now(timezone.utc));inputs(raw,policy);page.click('#importMcp');expect(page.locator('.counter')).to_contain_text('0/5');expect(page.locator('#mcpOutcome')).to_contain_text('permission was not established');ok('Default unknown permission blocks an otherwise successful-looking synthetic result')
   inputs(raw,policy,'granted');page.click('#importMcp');expect(page.locator('.counter')).to_contain_text('0/5');expect(page.locator('#mcpOutcome')).to_contain_text('evidence still needs review');ok('Granted synthetic import invents no return extractions')
   # Existing inspector accepts only separately quoted, source-indexed rows.
   page.click('[data-view=source]');normalized=json.loads(page.input_value('#responseJson'));normalized['recipients'][0]['structured_result']['fields']=fields;page.fill('#responseJson',json.dumps(normalized));page.click('#inspectCustom');expect(page.locator('.counter')).to_contain_text('5/5');ok('Explicit synthetic quote annotations reuse the existing field-review engine')
   inputs(raw,policy,'granted','wrong_run');page.click('#importMcp');expect(page.locator('#notice')).to_contain_text('different MCP run');assert page.locator('#export').is_disabled();ok('Wrong run cannot overwrite or export as a current successful review')
   raw['next_step']['action']='report_blocked';inputs(raw,policy,'granted');page.click('#importMcp');expect(page.locator('#mcpOutcome')).to_contain_text('provider itself reported a blocked outcome');ok('Provider blocked action overrides a granted permission selection')
   with page.expect_download() as download:page.click('#saveSession')
   saved=json.loads(Path(download.value.path()).read_text());saved['inputs']['response']['mcp_receipt']['processing_permitted']=True;saved['inputs_sha256']=rr.digest(saved['inputs']);page.set_input_files('#sessionFile',{'name':'forged-session.json','mimeType':'application/json','buffer':json.dumps(saved).encode()});expect(page.locator('#notice')).to_contain_text('contradicts consent or outcome');expect(page.locator('.counter')).to_contain_text('0/5');ok('Even a recomputed session fingerprint cannot hide inconsistent receipt state')
   page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.screenshot(path=str(E/'blocked-mobile.png'),full_page=True);ok('Blocked outcome remains readable without horizontal overflow at 390 pixels')
   assert not errors,errors;ok('No uncaught browser error')
   assert all(r['url'].startswith(base) for r in requests),requests;assert not any(r['url'].endswith('/api/start')or r['url'].endswith('/api/poll')for r in requests);ok('All browser traffic stays on localhost; no provider call or retry request occurs')
   context.close();browser.close()
  # Align generated narration to the recorded actions. No fabricated screen.
  command=['ffmpeg','-v','error','-y','-i',str(clip)]
  for scene in scenes:command+=['-i',scene['audio']]
  duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(clip)],text=True))
  assert duration<180,duration
  def ass_time(value):
   cs=round(value*100);return f'{cs//360000:01}:{cs//6000%60:02}:{cs//100%60:02}.{cs%100:02}'
  ass='[Script Info]\nScriptType: v4.00+\nPlayResX: 1280\nPlayResY: 1080\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,DejaVu Sans,23,&H00FFFFFF,&H00FFFFFF,&H00101722,&H00101722,0,0,0,0,100,100,0,0,1,1,0,2,25,25,20,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
  for scene in scenes:
   ass+=f"Dialogue: 0,{ass_time(scene['start'])},{ass_time(scene['start']+scene['duration']+.4)},Default,,0,0,0,,"+scene['caption'].replace('\n',r'\N')+'\n'
  (E/'demo.ass').write_text(ass)
  audio=';'.join(f"[{i+1}:a]adelay={round(s['start']*1000)}:all=1[a{i}]" for i,s in enumerate(scenes))+';'+''.join(f'[a{i}]'for i in range(len(scenes)))+f'amix=inputs={len(scenes)}:normalize=0,apad[aout]'
  vf=f"[0:v]pad=1280:1080:0:0:color=0x101722,subtitles={E/'demo.ass'}[vout]"
  command+=['-filter_complex',audio+';'+vf,'-map','[vout]','-map','[aout]','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p','-c:a','aac','-t',str(duration),'-movflags','+faststart',str(E/'returnready-demo.mp4')]
  subprocess.run(command,check=True,timeout=180)
  subprocess.run(['ffmpeg','-v','error','-i',str(E/'returnready-demo.mp4'),'-f','null','-'],check=True,timeout=90)
  (E/'demo-script.json').write_text(json.dumps(scenes,indent=2));report.update(status='passed',count=len(checks),demo_duration_seconds=duration,scope='Actual HTTP browser checks. Review examples are synthetic; the blocked hotline scene uses redacted recorded metadata only. No raw call transcript, recording or provider identifiers are published. No live call is made by this script.')
 except BaseException as e:report.update(status='failed',error=str(e),traceback=traceback.format_exc());raise
 finally:
  if proc:proc.terminate();proc.wait(timeout=5)
  (E/'browser-mcp.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))

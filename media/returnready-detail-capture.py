"""High-resolution media capture from the unchanged app. No live provider requests."""
from pathlib import Path
import json,os,socket,subprocess,sys,tempfile,time,urllib.request
from playwright.sync_api import sync_playwright,expect
A=Path('apps/python/returnready').resolve();O=Path('detail-capture-output').resolve();O.mkdir(exist_ok=True)
meta={'run_id':'redacted_actual_run','status':'COMPLETED','result':{'call_id':'redacted_actual_call','call_ids':['redacted_actual_call'],'batch':None,'outcome':{'task_completed':True},'extracted':{'calling':{'calls':[{'status':'COMPLETED','duration_seconds':36}],'callee_count':1}}},'next_step':{'action':'report_blocked'}}
errors=[];requests=[];shots=[]
with tempfile.TemporaryDirectory()as td:
 with socket.socket()as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
 base=f'http://127.0.0.1:{port}'
 server=subprocess.Popen([sys.executable,str(A/'returnready.py'),'--port',str(port),'--database',td+'/review.sqlite'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 try:
  for _ in range(60):
   try:
    with urllib.request.urlopen(base+'/api/config',timeout=1)as response:assert json.load(response)['live']is False
    break
   except OSError:time.sleep(.1)
  with sync_playwright()as p:
   browser=p.chromium.launch(headless=True,args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1280,'height':960},device_scale_factor=2,accept_downloads=True,record_video_dir=str(O/'recording'),record_video_size={'width':1280,'height':960});page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url));page.goto(base,wait_until='networkidle');expect(page.locator('.counter')).to_contain_text('4/5')
   def shot(name,loc):
    loc.screenshot(path=str(O/(name+'.png')));shots.append(name)
   row=page.get_by_role('button',name='Inspect Return destination',exact=True);row.click();shot('address-written',row.locator('.value').nth(0));shot('address-spoken',row.locator('.value').nth(1));shot('address-row',row);shot('mismatch-result',page.locator('.resultbar'))
   page.select_option('#case','later_correction');page.click('#run');row=page.get_by_role('button',name='Inspect Return destination',exact=True);row.click();expect(page.locator('#evidence')).to_contain_text('Different Road');shot('correction-quote',page.locator('#evidence .quote').last);shot('revision-row',row);shot('export-controls',page.locator('#export').locator('..'))
   with page.expect_download()as d:page.click('#export')
   data=json.loads(Path(d.value.path()).read_text());assert data['clearance_to_ship']is False and data['synthetic_example']is True;d.value.save_as(str(O/'actual-review-download.json'))
   with page.expect_download()as d:page.click('#saveSession')
   saved=Path(d.value.path()).read_bytes();page.set_input_files('#sessionFile',{'name':'review.json','mimeType':'application/json','buffer':saved});expect(page.locator('#notice')).to_contain_text('reopened');shot('reopen-notice',page.locator('#notice'))
   page.click('[data-view=source]');page.fill('#policyJson',json.dumps(dict.fromkeys(['authorization','destination','shipping','deadline','terms'])));page.fill('#responseJson',json.dumps(meta));page.get_by_text('Import a finished CALL-E MCP result',exact=True).click();page.fill('#mcpRun',meta['run_id']);page.fill('#mcpObserved','2026-09-09T17:49:21.417599+00:00');page.select_option('#mcpConsent','not_granted');page.fill('#mcpBasis','The recorded hotline attempt did not establish permission. Redacted metadata only; no call transcript.');page.click('#importMcp');expect(page.locator('#mcpOutcome')).to_contain_text('Enquiry evidence blocked');expect(page.locator('.counter')).to_contain_text('0/5');shot('blocked-result',page.locator('.resultbar'));shot('blocked-heading',page.locator('#mcpOutcome h2'));shot('blocked-status',page.locator('#mcpOutcome p').nth(0));shot('blocked-withheld',page.locator('#mcpOutcome p').last);shot('blocked-complete',page.locator('#mcpOutcome'))
   with page.expect_download()as d:page.click('#export')
   data=json.loads(Path(d.value.path()).read_text());assert data['supported_matches']==0 and data['inputs']['call_result']['recipients'][0]['attempts'][0]['transcript_turns']==[];d.value.save_as(str(O/'actual-blocked-download.json'))
   assert not errors,errors;assert all(u.startswith(base)or u.startswith('blob:')for u in requests),requests
   ctx.close();browser.close()
  (O/'capture.json').write_text(json.dumps({'status':'passed','mode':'actual localhost HTTP, unchanged default application security policy','resolution':'device scale factor 2','provider_calls':0,'shots':shots,'errors':errors,'scope':'New media captures and two actual downloads. Synthetic return cases; selected redacted metadata from the existing blocked hotline attempt. No new call, user trial or application release.'},indent=2))
 finally:
  server.terminate();server.wait(timeout=5)

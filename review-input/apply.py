"""Scoped reviewer corrections. Run in a detached worktree before clean-history publication."""
from pathlib import Path
import re, shutil, sys
R=Path(sys.argv[1]).resolve(); A=R/'apps/python/returnready'
assert (A/'returnready.py').is_file()
p=A/'returnready.py';s=p.read_text()
s=s.replace("VERSION = '0.4.0'", "VERSION = '0.4.1'")
old="phone = text(raw['phone'], 'Phone', 16)\n    require(re.fullmatch(r'\\+[1-9]\\d{7,14}', phone) is not None, 'Supply an unambiguous E.164 phone number.')"
new="phone = raw['phone']\n    require(isinstance(phone, str) and re.fullmatch(r'\\+[1-9][0-9]{7,14}', phone) is not None, 'Supply an ASCII E.164 phone number without whitespace.')"
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("r'\\+1\\d{3}55501\\d{2}'", "r'\\+1[0-9]{3}55501[0-9]{2}'")
needle="        headers = {'Authorization': 'Bearer ' + self.key";assert s.count(needle)==1
s=s.replace(needle,"""        # Reserved fixtures are for previews, injected spies and loopback servers only.
        # Recheck the actual transport boundary even when preview was bypassed.
        from urllib.parse import urlsplit
        if method == 'POST' and urlsplit(self.BASE).hostname not in {'127.0.0.1', 'localhost', '::1'}:
            require(isinstance(body, dict) and isinstance(body.get('recipients'), list) and len(body['recipients']) == 1, 'Expected one reviewed recipient.')
            recipient = body['recipients'][0]
            require(isinstance(recipient, dict) and isinstance(recipient.get('phones'), list) and len(recipient['phones']) == 1, 'Expected one reviewed phone number.')
            phone = recipient['phones'][0]
            require(isinstance(phone, str) and re.fullmatch(r'\\+[1-9][0-9]{7,14}', phone) is not None, 'ASCII E.164 required at provider boundary.')
            reserved = re.fullmatch(r'\\+1[0-9]{3}55501[0-9]{2}|\\+442079460[0-9]{3}|\\+447700900[0-9]{3}', phone)
            require(reserved is None, 'Reserved fictional number cannot reach a live provider.')
"""+needle,1);p.write_text(s)
p=A/'test_returnready.py';s=p.read_text();nums=set(re.findall(r'\+44[0-9]{10}',s));assert len(nums)==1
for n in nums:s=s.replace(n,'+442079460123')
p.write_text(s)
p=A/'test_mcp_import.py';s=p.read_text();s=re.sub(r'NOW = datetime\([^\n]+', 'NOW = datetime(2000, 1, 3, 12, 0, tzinfo=timezone.utc)',s)
s=re.sub(r"'duration_seconds': [0-9]+", "'duration_seconds': 48",s)
s=re.sub(r'20[0-9]{2}-[0-9]{2}-[0-9]{2}T', '2000-01-03T',s);p.write_text(s)
# Do not carry earlier call-derived artifacts or their provenance links into the new tree.
for rel in ('evidence03','evidence04','docs'):
 q=A/rel
 if q.exists():shutil.rmtree(q)
(A/'docs').mkdir()
(A/'.gitignore').write_text('__pycache__/\n*.pyc\n*.sqlite*\nevidence*/\n*.webm\n*.mp4\n*.wav\nreview-session.json\n')
(A/'README.md').write_text('''# ReturnReady

Compare five quoted return instructions with the written record, inspect later corrections, and export unresolved questions before a package moves. Matching wording never authorizes shipment.

## Run locally

Python 3.11 or newer, standard library only:

```sh
cd apps/python/returnready
python returnready.py
```

Open the printed localhost address. Default mode needs no API key and makes no provider calls. The example conversations, identifiers, dates, durations and call-like metadata included here are wholly synthetic. They are not redacted provider results or evidence from a real enquiry.

## Complete review workflow

Load written instructions and an example result. Inspect authorization, destination, shipping payer, absolute deadline and refund/replacement conditions beside exact recipient quotations. Later corrections remain visible and remove earlier apparent matches. Caller speech and generated summaries are not recipient evidence. Download a review, save the inputs, then reopen to recompute freshness and findings. Editing inputs invalidates old exports. Fingerprints identify bytes, not consent, identity or truth.

## CALL-E integration

A connected host may use CALL-E's supported planning and confirmation tools, retain the actual run ID and read that same run after it finishes. The operator-mediated importer accepts the narrow result format through Inspect the data, or the CLI in docs/MCP-RESULT-IMPORT.md.

Unknown permission, provider errors or a blocked next step result in a hold. Transcript and extracted claims are withheld from the normalized review. For permitted imports, separately reviewed annotations need exact quotations and turn indices. The importer cannot terminate an active call, erase provider recordings or authenticate an operator-supplied file. Do not publish operational call records in this repository.

The optional REST adapter is not validated against a live CALL-E service by these tests. Live mode requires CALLE_API_KEY on the server, the explicit --live flag, authorization for the specific recipient, a reviewed preview, exact confirmation and the supplied recipient-local 09:00 to 18:00 window. See python returnready.py --help. The SQLite ledger records intent before the provider request, does not retry uncertain starts and retains the first terminal observation. Only an unstarted preview can be cancelled here; active calls require provider controls.

Phone inputs require an ASCII plus sign and ASCII digits, without surrounding whitespace. Reserved fictional numbers are never sent by the live transport. The reserved UK London drama fixture is used only in injected request spies and loopback wire tests. Syntax validation is not country availability, subscriber verification or permission to call. Ofcom's reserved sample ranges: https://www.ofcom.org.uk/phones-and-broadband/phone-numbers/numbers-for-drama

## Reproduce checks

```sh
python -m unittest test_returnready http_test test_completion test_mcp_import test_review_fixes -v
python -m pip install playwright==1.55.0
python -m playwright install chromium
python browser_completion.py
python browser_mcp.py
```

Run python scripts/validate_repository.py from the repository root as well. Browser tests use actual localhost HTTP, actual downloads and the default security policy. All call-like data is fabricated. Output artifacts are ignored by Git and do not belong in the contribution. These checks do not establish live-service compatibility, customer adoption or representative accuracy.

## Scope and provenance

Conservative English lexical review can miss unseen revisions and flag benign wording. No purchase, refund, courier booking, fee acceptance or automatic shipping permission is performed. The software does not make medical, legal, financial or emergency decisions. It is a reference app, not a supported provider SDK.

Original code by Joseph Ayanda, developed with substantial AI assistance, under the MIT license. Review and persistence behavior is retained. Reviewer corrections enforce ASCII inputs and remove operational artifacts from the contribution history. No transcript, recording, real-call date/duration/outcome or provider identifier is included as a repository example.
''')
(A/'docs/MCP-RESULT-IMPORT.md').write_text('''# Finished MCP result import

This is an offline adapter for an operator whose connected host has already completed an authorized CALL-E workflow. It does not fetch from a provider, place calls or validate the separate REST transport.

In Inspect the data, paste the finished object, supply the expected run ID and original observation timestamp, and explicitly review permission. Ready plans, wrong runs, multiple attempts, unsupported transcript formats and inconsistent receipts are rejected. Unknown permission, an explicit provider error, a blocked next step or a recognized refusal creates a hold without transcript or extracted return claims. No retry is requested.

A permitted import supports timestamped [HH:MM:SS] BOT/USER: text turns. Return fields are not inferred. Optional annotations need exact quotes and zero-based turn indices. Caller text cannot become recipient evidence. Reopening checks receipt consistency and recomputes freshness; it does not renew approval.

```sh
python mcp_import.py --input finished-mcp.json --policy policy.json --expected-run-id EXPECTED_RUN_ID --observed-at ORIGINAL_ISO_TIME --consent unknown --consent-basis "Permission has not been established." --output review-session.json
```

The CLI refuses to overwrite an output. Never commit operational inputs, transcripts, recordings, call metadata or generated artifacts. All repository scenarios, dates, durations and identifiers are invented for tests. Processing and publication permission are separate; the importer cannot control an active call or remove provider-side storage. An editable local receipt is not cryptographic provider authentication.
''')
p=A/'browser_mcp.py';s=p.read_text();start=s.index('# Only metadata');end=s.index('unknown=',start)
s=s[:start]+"# Wholly fabricated blocked-result fixture; no provider artifacts are used.\nsynthetic_meta={'run_id':'synthetic_blocked_run','status':'COMPLETED','result':{'call_id':'synthetic_blocked_call','call_ids':['synthetic_blocked_call'],'batch':None,'outcome':{'task_completed':True},'extracted':{'calling':{'calls':[{'status':'COMPLETED','duration_seconds':48}],'callee_count':1}}},'next_step':{'action':'report_blocked'}}\n"+s[end:]
start=s.index('   def narrate(');end=s.index('   page.goto(',start);s=s[:start]+s[end:]
s='\n'.join(l for l in s.splitlines() if not l.startswith('   narrate(') and not l.startswith('   # Real received metadata'))+'\n'
s=s.replace('live_meta','synthetic_meta')
s=re.sub(r"page.fill\('#mcpObserved','[^']+'\)","page.fill('#mcpObserved','2000-01-03T12:00:00+00:00')",s)
s=re.sub(r"page.fill\('#mcpBasis','Recorded[^']+'\)","page.fill('#mcpBasis','Wholly synthetic permission-unavailable example, not a provider result.')",s)
s=s.replace('Redacted real-attempt metadata imports','Wholly synthetic blocked metadata imports')
s=re.sub(r"   clip=Path\(page.video.path\(\)\);context.close\(\);ok\([^\n]+", "   context.close();ok('Actual UI actions and downloads with wholly synthetic fixture inputs')",s)
start=s.index('  # Align generated narration');end=s.index(' except BaseException',start)
s=s[:start]+"  report.update(status='passed',count=len(checks),scope='Actual localhost HTTP and downloads. All call-like inputs are wholly synthetic. No provider calls or operational artifacts.')\n"+s[end:]
p.write_text(s)
(A/'test_review_fixes.py').write_text('''"""ASCII/reserved-fixture checks. No provider requests are allowed."""
import unittest
from unittest.mock import patch
import returnready as rr
from test_returnready import request, NOW
class ReviewFixTests(unittest.TestCase):
 def reject(self,n):
  r=request();r['phone']=n
  with self.assertRaises(ValueError):rr.validate_request(r,NOW)
 def test_ascii_reserved_fixture_for_preview(self):self.assertEqual(rr.validate_request(request(),NOW)['phone'],'+442079460123')
 def test_arabic_digits(self):self.reject('+44'+''.join(chr(0x660+int(x)) for x in '2079460123'))
 def test_fullwidth_digits(self):self.reject('+44'+''.join(chr(0xff10+int(x)) for x in '2079460123'))
 def test_devanagari_digits(self):self.reject('+44'+''.join(chr(0x966+int(x)) for x in '2079460123'))
 def test_fullwidth_plus(self):self.reject(chr(0xff0b)+'442079460123')
 def test_leading_space(self):self.reject(' +442079460123')
 def test_trailing_space(self):self.reject('+442079460123 ')
 def test_trailing_newline(self):self.reject('+442079460123'+chr(10))
 def test_embedded_space(self):self.reject('+44 2079460123')
 def test_zero_country_prefix(self):self.reject('+042079460123')
 def test_overlength(self):self.reject('+'+'1'*16)
 def test_non_string(self):self.reject(123)
 def boundary(self,number,message):
  b=rr.payload(rr.validate_request(request(),NOW),'synthetic_request');b['recipients'][0]['phones']=[number]
  with patch('urllib.request.build_opener') as opener:
   with self.assertRaisesRegex(ValueError,message):rr.CalleHTTP('TEST-ONLY').start(b,'synthetic_request')
   opener.assert_not_called()
 def test_london_reserved_boundary(self):self.boundary('+442079460123','Reserved fictional')
 def test_mobile_reserved_boundary(self):self.boundary('+447700900123','Reserved fictional')
 def test_nanp_reserved_boundary(self):self.boundary('+12025550123','Reserved fictional')
 def test_unicode_transport_boundary(self):self.boundary('+44'+chr(0x661)*10,'ASCII')
 def test_injected_spy_retains_fixture(self):
  calls=[];c=rr.CalleHTTP('TEST-ONLY',transport=lambda *a:calls.append(a) or {'id':'synthetic'})
  c.start(rr.payload(rr.validate_request(request(),NOW),'synthetic_request'),'synthetic_request');self.assertEqual(len(calls),1)
if __name__=='__main__':unittest.main()
''')
# No raw artifact trees may be included, and no old full UK fixture may remain.
for p in A.rglob('*'):
 if p.is_file() and p.suffix in {'.py','.md','.json','.html'}:
  t=p.read_text()
  for n in re.findall(r'\+44[0-9]{10}',t):assert re.fullmatch(r'\+442079460[0-9]{3}|\+447700900[0-9]{3}',n),(p.name,'unreserved sample')
  assert 'redacted_actual_' not in t and 'hotline' not in t.lower(),p.name
print('Scoped corrections applied; no operational artifacts retained.')

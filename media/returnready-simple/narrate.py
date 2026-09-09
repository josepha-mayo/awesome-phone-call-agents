"""Bounded media-only narration generation. No application, call, or submission changes."""
from pathlib import Path
import hashlib, json, re, time
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

scenes = [
 {"title":"Check the address before shipping.","paragraphs":["Return Ready checks return instructions before you send a package. It compares the written record with what the recipient actually said.","Here is a fictional example where the return address has changed, even though the other details match."]},
 {"title":"The two addresses do not match.","paragraphs":["The written address is ten Example Lane. The phone answer says twenty two Different Road.","Four details match, but the destination does not. The review keeps both addresses visible, so the operator can ask for clarification."]},
 {"title":"Keep the later correction.","paragraphs":["Now the recipient changes the address later in the conversation. The first answer is no longer the whole story.","Return Ready keeps that correction and flags the destination for review. It does not treat the earlier matching answer as final."]},
 {"title":"Export the unresolved questions.","paragraphs":["Download the review to keep the source quotes and unanswered questions together. You can also save and reopen the session.","The inputs are checked again when you reopen them. Saving a file does not create a fresh approval."]},
 {"title":"Connected does not mean resolved.","paragraphs":["We also tried the official Call E test hotline. It connected for thirty six seconds, but permission was not granted.","No return instructions were obtained. This screen uses redacted result information, not the call recording or the transcript."]},
 {"title":"Zero answers. No automatic retry.","paragraphs":["The provider marked the call complete. Return Ready still shows zero supported answers, and holds the case for clarification.","It withholds the transcript and does not automatically call again. A finished call is not the same as a usable answer."]},
 {"title":"A record to review. Not permission to ship.","paragraphs":["Return Ready gives the operator a reviewable handoff. The application runs locally, and its source code is available.","The result import is operator mediated. Successful merchant testing and the separate direct API connection still need validation."]},
]
O=Path('simple-voice-output');O.mkdir(exist_ok=True)
expected={'kokoro-v1.0.onnx':'7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5','voices-v1.0.bin':'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d'}
for file,want in expected.items():
 assert hashlib.sha256(Path(file).read_bytes()).hexdigest()==want,file
model=Kokoro('kokoro-v1.0.onnx','voices-v1.0.bin')
voice='bf_emma';report={'voice':voice,'type':'stock neural voice, not a human recording or a cloned identity','provider_calls':0,'model_hashes':expected,'scenes':[]}
for i,scene in enumerate(scenes):
 row={**scene,'index':i,'parts':[]}
 for j,text in enumerate(scene['paragraphs']):
  speed=.76;start=time.monotonic()
  samples,sr=model.create(text,voice=voice,speed=speed,lang='en-gb')
  words=len(re.findall(r"\b[\w]+(?:['-][\w]+)*\b",text));seconds=len(samples)/sr;wpm=60*words/seconds
  # One bounded re-synthesis rather than destructive post-processing of fast speech.
  if wpm>120:
   speed=max(.59,round(speed*115/wpm,3));samples,sr=model.create(text,voice=voice,speed=speed,lang='en-gb');seconds=len(samples)/sr;wpm=60*words/seconds
  assert sr==24000 and np.isfinite(samples).all() and 3<seconds<40
  name=f'scene-{i:02}-part-{j:02}.wav';sf.write(O/name,samples,sr,subtype='PCM_16')
  row['parts'].append({'file':name,'text':text,'words':words,'seconds':seconds,'wpm':wpm,'generation_speed':speed,'peak':float(np.max(np.abs(samples))),'sha256':hashlib.sha256((O/name).read_bytes()).hexdigest()})
  print(name,round(seconds,2),round(wpm,1),flush=True)
 report['scenes'].append(row)
(O/'narration.json').write_text(json.dumps(report,indent=2))
(O/'narration.txt').write_text('\n\n'.join(s['title']+'\n'+'\n\n'.join(s['paragraphs']) for s in scenes))
print('Total words',sum(p['words']for s in report['scenes']for p in s['parts']))

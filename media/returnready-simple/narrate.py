"""Bounded media-only narration generation. No application, call, or submission changes."""
from pathlib import Path
import hashlib, json, re
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

scenes = [
 {"title":"Check the address before shipping.","paragraphs":["Before a package goes back, the return instructions need to be clear. Return Ready compares written instructions with the phone answer. This first example is fictional."]},
 {"title":"The two addresses do not match.","paragraphs":["The written address is ten Example Lane. The phone answer says twenty two Different Road.","Four details match, but the address does not. The review asks for clarification."]},
 {"title":"Keep the later correction.","paragraphs":["Here, the recipient corrects the address later in the conversation. Return Ready keeps the later statement.","The earlier matching answer is no longer treated as the final answer."]},
 {"title":"Export the unresolved questions.","paragraphs":["Export the review to keep the quotes and unresolved questions together. Reopening a saved session checks the inputs again. It does not restore an old approval."]},
 {"title":"Connected does not mean resolved.","paragraphs":["One real test call reached the official Call E hotline for thirty six seconds.","Permission was not granted, and no return instructions were obtained. Only redacted result information appears here."]},
 {"title":"Zero answers. No automatic retry.","paragraphs":["The provider marked the task complete. Return Ready still holds the case at zero supported answers.","The transcript is withheld, and no repeat call is made by the review workflow."]},
 {"title":"A record to review. Not permission to ship.","paragraphs":["The result import is operator mediated. The separate direct API path still needs a live test.","Return Ready provides a record to review, never automatic permission to ship. The source code is available."]},
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
  speed=.76
  samples,sr=model.create(text,voice=voice,speed=speed,lang='en-gb')
  words=len(re.findall(r"\b[\w]+(?:['-][\w]+)*\b",text));seconds=len(samples)/sr;wpm=60*words/seconds
  if wpm>120:
   speed=max(.59,round(speed*113/wpm,3));samples,sr=model.create(text,voice=voice,speed=speed,lang='en-gb');seconds=len(samples)/sr;wpm=60*words/seconds
  assert sr==24000 and np.isfinite(samples).all() and 3<seconds<40
  name=f'scene-{i:02}-part-{j:02}.wav';sf.write(O/name,samples,sr,subtype='PCM_16')
  row['parts'].append({'file':name,'text':text,'words':words,'seconds':seconds,'wpm':wpm,'generation_speed':speed,'peak':float(np.max(np.abs(samples))),'sha256':hashlib.sha256((O/name).read_bytes()).hexdigest()})
  print(name,round(seconds,2),round(wpm,1),flush=True)
 report['scenes'].append(row)
(O/'narration.json').write_text(json.dumps(report,indent=2))
(O/'narration.txt').write_text('\n\n'.join(s['title']+'\n'+'\n\n'.join(s['paragraphs']) for s in scenes))
print('Total words',sum(p['words']for s in report['scenes']for p in s['parts']))

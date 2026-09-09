"""Generate stock neural narration only. No phone calls, credentials or app edits."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, re, subprocess, sys, time
import numpy as np
import soundfile as sf
import onnxruntime as ort
from kokoro_onnx import Kokoro

OUT = Path('voice-output'); OUT.mkdir(exist_ok=True)
SCENES = [
    "Before you send a return, are the instructions actually clear? Return Ready compares what was said on the phone with the written record. It checks five important details, and shows what still needs an answer. These first examples are fictional.",
    "Here, the return address is different. Four details match, but that does not make the destination safe to use. Open the evidence, and you can compare the written address with the recipient's exact words. The mismatch stays visible.",
    "Now the recipient changes the address later in the conversation. The earlier answers matched, but they are no longer the whole story. Return Ready keeps the later correction and flags the address for review. This is a wording check, not a guarantee that it understands every meaning.",
    "Download the review, and the source quotes and unanswered questions go with it. Save a session, then reopen it to check the inputs again. An old approval does not become a fresh answer just because you opened the file.",
    "We also made one real call to the official Call E test hotline. It connected for thirty six seconds. Permission for the test was not granted, and we obtained no return instructions. This screen uses redacted result information, not the call recording or transcript.",
    "The provider marked the task complete. But a finished call is not a completed return enquiry. Return Ready holds the case at zero supported answers, withholds the transcript, and does not call again. It reviews the result after the call; it cannot stop an active call.",
    "That blocked result stays blocked after saving and reopening. The result import is operator mediated; the separate direct A P I connection still needs a live test. The code and contribution are available for review. The goal is a clearer handoff, not automatic permission to ship."
]

# Explicit CPU limits keep this media-only job bounded.
options = ort.SessionOptions(); options.intra_op_num_threads = 2; options.inter_op_num_threads = 1
session = ort.InferenceSession('kokoro-v1.0.onnx', sess_options=options, providers=['CPUExecutionProvider'])
engine = Kokoro.from_session(session, 'voices-v1.0.bin')
voice = 'af_heart'
assert voice in engine.get_voices()
report = {'started_at': datetime.now(timezone.utc).isoformat(), 'voice': voice,
          'voice_type': 'stock neural synthetic narration; no voice cloning or human speaker claim',
          'generation_speed': 0.86, 'sample_rate': 24000, 'provider_calls': 0, 'scenes': []}
for i, text in enumerate(SCENES):
    began = time.monotonic()
    audio, sr = engine.create(text, voice=voice, speed=0.86, lang='en-us', trim=True)
    audio = np.asarray(audio, dtype=np.float32).reshape(-1)
    assert sr == 24000 and np.isfinite(audio).all() and len(audio) > sr
    # Preserve generated speech; only add a tiny click-suppression fade.
    fade = min(int(.008*sr), len(audio)//10)
    audio[:fade] *= np.linspace(0, 1, fade)
    audio[-fade:] *= np.linspace(1, 0, fade)
    peak = float(np.max(np.abs(audio))); assert peak > .01
    if peak > .95: audio *= .95/peak
    file = OUT/f'scene-{i:02d}.wav'; sf.write(file, audio, sr, subtype='PCM_24')
    words = len(re.findall(r"\b[\w]+(?:['-][\w]+)*\b", text))
    item = {'index': i, 'text': text, 'file': file.name, 'words': words,
            'duration': len(audio)/sr, 'words_per_minute': words*60*sr/len(audio),
            'peak': float(np.max(np.abs(audio))), 'generation_seconds': time.monotonic()-began,
            'sha256': hashlib.sha256(file.read_bytes()).hexdigest()}
    report['scenes'].append(item); print(json.dumps(item), flush=True)
for name in ['kokoro-v1.0.onnx','voices-v1.0.bin']:
    report[name+'_sha256'] = hashlib.sha256(Path(name).read_bytes()).hexdigest()
report['finished_at'] = datetime.now(timezone.utc).isoformat()
(OUT/'voice-generation.json').write_text(json.dumps(report, indent=2))
(OUT/'narration.txt').write_text('\n\n'.join(f'SCENE {i+1}\n{s}' for i,s in enumerate(SCENES)))
(OUT/'dependencies.txt').write_text(subprocess.check_output([sys.executable,'-m','pip','freeze'], text=True))
print('Finished seven separate narration files. Assembly must concatenate them; never mix them over the original audio.')

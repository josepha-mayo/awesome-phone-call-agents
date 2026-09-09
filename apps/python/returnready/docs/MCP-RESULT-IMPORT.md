# Finished CALL-E MCP result import

This is a no-network result adapter for an agent host that already has the connected CALL-E tools. It is not another phone client, an authentication service, or proof that the separate REST adapter works.

## Why this exists

A September 9 authorized hotline attempt connected for 36 seconds but returned no return instructions. The answering agent could not grant permission for the recorded/transcribed enquiry. The provider returned COMPLETED and task_completed=true while also reporting a blocked next step. Those flags describe the provider's outcome model; they do not establish usable return evidence.

The caller also continued asking scenario questions after permission was unavailable, despite its stop instruction. This importer operates after a call ends. It cannot force real-time termination, erase provider-side recordings, or fix that caller behavior. There was no second call. Public materials contain no call transcript, recording, phone number or provider identifiers.

## Existing host workflow

Prepare the authorized recipient and bounded purpose. Use CALL-E's supported planning/confirmation flow. Once an attempt has begun, retain the actual run ID and only read that existing run. Never redial to get a more convenient result. Use the provider-supported controls for an active call; ReturnReady's importer cannot cancel it.

After the run is terminal, use the existing **Inspect the data** view. Paste the final MCP object, supply the policy map (unknown fields are null), and open **Import a finished CALL-E MCP result**. Enter the independently expected run ID, original observation timestamp, and explicit permission review. The import rejects another run, multiple attempts/recipients, an unsupported transcript format, future observation times and contradictory receipts.

Permission defaults to unknown. Unknown or unavailable permission, an explicit provider error, provider-reported blocking, or a recognized refusal phrase produces a hold. Transcript and extracted claims are excluded from the normalized input. A saved blocked receipt cannot acquire permission merely by reopening. A manually supplied timestamp is not authenticated by a hash.

For a permitted result, the adapter maps only the observed `[HH:MM:SS] BOT/USER: text` format and retains source turns. Return fields are not inferred. Separately supplied fields need value, exact quote and zero-based turn_index and are checked by the existing review engine. Caller speech cannot count as recipient evidence. Matching wording remains a human-review state, never shipping clearance.

Publication permission is separate from permission for a test. Do not publish a raw transcript, recording or identity merely because a call was answered or a processing checkbox was selected. The refusal guard is conservative English lexical matching, not a general consent classifier. The operator-supplied file and receipt are editable; this is not cryptographic provider authentication.

## CLI, no credentials and no network

```sh
python mcp_import.py --input finished-mcp.json --policy policy.json \
  --expected-run-id ACTUAL_RUN_ID --observed-at ORIGINAL_TIME_WITH_TIMEZONE \
  --consent unknown --consent-basis "Permission is not established." \
  --output review-session.json
```

Open the resulting session in ReturnReady. The CLI refuses to overwrite an existing output. Supply `--fields reviewed-fields.json` only for genuine, explicitly reviewed quote annotations. No provider key, phone call, polling or retry is involved.

## Verification and demonstration

```sh
python -m unittest test_returnready http_test test_completion test_mcp_import -v
python browser_completion.py
python browser_mcp.py
```

The last command needs Playwright, Chromium, FFmpeg and espeak-ng. It runs actual localhost HTTP browser checks and records app actions. The first review scenarios are synthetic. The blocked-attempt scene uses selected, redacted recorded metadata, not a new live call, an authenticated provider fetch or a merchant trial. Narration uses a disclosed stock synthetic voice. Original unit tests are retained. More tests do not imply customer benefit or a likely award.

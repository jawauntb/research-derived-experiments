# Inquiry Black Box Modal Jobs

Modal jobs handle optional batch work for redacted session exports: feature
extraction, smoke reports, toy calibration artifacts, and redacted session
summary reports. They are not required for local replay.

## Local Checks

```bash
python3 -m pytest
```

The test fixture rejects sensitive fields such as camera frame blobs, typed
content, document text, or video bytes before any feature extraction runs.

## Deployment

Use Doppler or Modal-managed secrets. Do not commit `.env` files.

```bash
doppler setup
doppler run -- modal deploy inquiry_jobs.py
doppler run -- modal run inquiry_jobs.py::smoke_job
doppler run -- modal run inquiry_jobs.py::session_summary_job
```

The deployed `job_webhook` FastAPI endpoint accepts the Bun cloud API's job
request shape and returns `modal_call_id` plus `status`. Configure that endpoint
as `MODAL_JOB_WEBHOOK_URL` in Railway and use `MODAL_JOB_WEBHOOK_TOKEN` if the
endpoint is exposed beyond trusted smoke checks.

Expected variables:

- `MODAL_TOKEN_ID`
- `MODAL_TOKEN_SECRET`
- `MODAL_ENVIRONMENT`
- `RAILWAY_PUBLIC_API_URL`
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`,
  `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, and `VOYAGE_API_KEY` when those
  providers are enabled
- `HF_TOKEN`; `HUGGINGFACE_TOKEN` is also accepted for social-cohesion repo
  compatibility
- `MODEL_PROVIDER`, `SESSION_SUMMARY_MODEL`, and `EMBEDDING_MODEL` for routing
- optional research model IDs: `TRIBE_MODEL_ID`, `BRAIN2QWERTY_REPO`,
  `BRAIN2QWERTY_DATASET_ID`, `BRAINDECODE_MODEL_ID`, `VJEPA_MODEL_ID`,
  `VJEPA_LARGE_MODEL_ID`, `INTERNVIDEO_MODEL_ID`, `QWEN_VL_MODEL_ID`,
  `WHISPER_MODEL_ID`, and `FASTER_WHISPER_MODEL_ID`

`smoke_job` and `session_summary_job` include a sanitized `model_environment`
provenance object that reports configured key names and model IDs without
returning secret values. Defaults are intentionally narrow: TRIBE v2 resolves to
`facebook/tribev2`, Brain2Qwerty resolves to the public
`facebookresearch/brain2qwerty` repo marker, and Braindecode resolves to
`braindecode/cbramod-pretrained`. Brain2Qwerty is treated as a research-only,
license-gated path until the data/model terms permit product use.

## Outputs

`smoke_job` returns a report containing:

- redacted feature summary
- toy calibration model card
- provenance with feature/model versions
- limitations that explicitly rule out diagnostic or surveillance use

`session_summary_job` accepts only `redacted-sync` session interpretation
payloads. It rejects raw text fields, app names, bundle IDs, window titles,
desktop event objects, screenshots, and document text aliases before summary
generation. The output is a report payload with counts, theme titles,
suggestion titles, limitations, model routing provenance, and an LLM status of
`model-ready` when `SESSION_SUMMARY_MODEL` is configured.

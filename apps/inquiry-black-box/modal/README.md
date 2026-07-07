# Inquiry Black Box Modal Jobs

Modal jobs handle optional batch work for redacted session exports: feature
extraction, smoke reports, and toy calibration artifacts. They are not required
for local replay.

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
- optional model provider variables for future summarization or embeddings

## Outputs

`smoke_job` returns a report containing:

- redacted feature summary
- toy calibration model card
- provenance with feature/model versions
- limitations that explicitly rule out diagnostic or surveillance use

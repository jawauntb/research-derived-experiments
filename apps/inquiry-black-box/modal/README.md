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

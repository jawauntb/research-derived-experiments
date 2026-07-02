# Railway Autodeploy Runbook

The public atlas is served by Railway from `sites/reafference_attribution`:

- Project: `reafference-attribution-field`
- Project ID: `2fd18d7f-bf1b-42ae-b756-d29f836cb1d9`
- Environment: `production`
- Environment ID: `f97509f3-815f-43c3-9013-f3748a787f39`
- Service: `reafference-attribution-field`
- Service ID: `e4143302-3161-4454-bdd1-742487f1ce99`
- Domain: `https://reafference-attribution-field-production.up.railway.app`
- Root directory: `sites/reafference_attribution`
- Start command: `node server.js`

## What Broke

On 2026-07-02, Railway production was behind `origin/main`:

- `origin/main`: `784b5981ee3310a9fb42897d2040649dd5312e73`
- Railway active deployment before repair: `64b445b67e57c2ceba0ef5091d46aae5fb0439e7`

Railway service config was not the problem. The service still pointed at
`jawauntb/research-derived-experiments`, used branch `main`, had root directory
`sites/reafference_attribution`, and had empty watch paths.

The real blocker was Railway's GitHub trigger state:

- `serviceInstanceAutoDeployStatus.enabled`: `false`
- `serviceInstanceAutoDeployStatus.canEnable`: `false`
- `serviceInstanceAutoDeployStatus.reason`: `NO_INSTALLATION`
- `deploymentTriggers.edges`: `[]`

Trying to enable Railway-native autodeploy failed with:

```text
No workspace member has their GitHub account connected with access to this repository.
```

That matches Railway's documented requirements: GitHub autodeploy only works when a
project member has a connected GitHub account with contributor access to the repo, and
when the Railway GitHub App has access to the repository.

## Current Repair

The service source was reconnected to `jawauntb/research-derived-experiments` on
branch `main`, which queued and successfully deployed `784b5981ee3310a9fb42897d2040649dd5312e73`.

Because the Railway-native trigger still could not be enabled without GitHub account
linkage, this repo also has a GitHub Actions fallback:

- Workflow: `.github/workflows/railway-deploy.yml`
- Trigger: every push to `main`, plus manual `workflow_dispatch`
- Secret: repository Actions secret `RAILWAY_TOKEN`
- Token scope: Railway project token for the production environment

This means future merges to `main` deploy through GitHub Actions even if Railway's
native GitHub App autodeploy remains disabled.

## Verify Deployment State

Fetch latest `main` and compare it with Railway:

```bash
git fetch origin main --prune
git rev-parse origin/main
railway link \
  --project 2fd18d7f-bf1b-42ae-b756-d29f836cb1d9 \
  --environment production \
  --service e4143302-3161-4454-bdd1-742487f1ce99 \
  --json
railway deployment list \
  --environment production \
  --service e4143302-3161-4454-bdd1-742487f1ce99 \
  --limit 5 \
  --json |
  jq '[.[] | {id,status,createdAt,commitHash:.meta.commitHash,branch:.meta.branch,repo:.meta.repo,subject:((.meta.commitMessage // "") | split("\n")[0]),rootDirectory:.meta.rootDirectory}]'
```

Verify the live site:

```bash
curl -fsS -D - https://reafference-attribution-field-production.up.railway.app/ -o /tmp/reafference-atlas.html
```

## Verify Railway-Native Autodeploy

The Railway CLI does not currently print the native autodeploy toggle, but the GraphQL
API does. This reads the local Railway CLI token without printing it:

```bash
TOKEN=$(jq -r '.user.accessToken' ~/.railway/config.json)
BODY=$(jq -nc \
  --arg q 'query($projectId:String!, $environmentId:String!, $serviceId:String!) { serviceInstanceAutoDeployStatus(projectId:$projectId, environmentId:$environmentId, serviceId:$serviceId) { enabled canEnable reason } deploymentTriggers(projectId:$projectId, environmentId:$environmentId, serviceId:$serviceId, first:20) { edges { node { id provider repository branch } } } serviceInstance(environmentId:$environmentId, serviceId:$serviceId) { rootDirectory watchPatterns source { repo image } } }' \
  --arg projectId '2fd18d7f-bf1b-42ae-b756-d29f836cb1d9' \
  --arg environmentId 'f97509f3-815f-43c3-9013-f3748a787f39' \
  --arg serviceId 'e4143302-3161-4454-bdd1-742487f1ce99' \
  '{query:$q, variables:{projectId:$projectId, environmentId:$environmentId, serviceId:$serviceId}}')
curl -sS https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  --data "$BODY" |
  jq '.data'
```

Healthy Railway-native autodeploy should show:

- `serviceInstanceAutoDeployStatus.enabled: true`
- At least one `deploymentTriggers.edges[]` node for repository
  `jawauntb/research-derived-experiments` and branch `main`

If it still shows `NO_INSTALLATION`, use the GitHub Actions workflow as the active
deployment path and fix the Railway account linkage when convenient.

## Restore Railway-Native Autodeploy

Use these steps when you want Railway's own GitHub App trigger back on:

1. In Railway, connect a project member's GitHub account that has contributor access
   to `jawauntb/research-derived-experiments`.
2. In GitHub installation settings, verify the Railway GitHub App has access to this
   repository and has no pending permission update.
3. In Railway service settings, reconnect the source repo and set branch `main`.
4. Enable autodeploy.
5. Re-run the GraphQL check above and confirm a deployment trigger exists.

Useful immediate repair command:

```bash
railway service source connect \
  --project 2fd18d7f-bf1b-42ae-b756-d29f836cb1d9 \
  --environment production \
  --service e4143302-3161-4454-bdd1-742487f1ce99 \
  --repo jawauntb/research-derived-experiments \
  --branch main \
  --json
```

That can deploy the latest commit once, but it does not prove the persistent trigger
was restored. Always verify `serviceInstanceAutoDeployStatus` and `deploymentTriggers`
after reconnecting.

## Sources

- Railway GitHub autodeploy docs: `https://docs.railway.com/deployments/github-autodeploys`
- Railway build configuration docs: `https://docs.railway.com/builds/build-configuration`
- Railway CLI deploying docs: `https://docs.railway.com/cli/deploying`
- Railway GitHub Actions guide: `https://blog.railway.com/p/github-actions`

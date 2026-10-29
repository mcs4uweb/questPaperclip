# Quest Paperclip — system guide

Local control plane for agents, user stories, budgets, and traces.

- API / classic UI: `http://127.0.0.1:8001`
- Next.js UI: `http://localhost:3003`
- SQLite: `data/paperclip.db`
- OpenAPI: `http://127.0.0.1:8001/docs`

Do **not** open `static/index.html` as a file. Always use the http URLs.

---

## Processes

| Process | Port | Command |
|---|---|---|
| FastAPI | 8001 | `python -m uvicorn main:app --host 127.0.0.1 --port 8001` |
| Next.js | 3003 | `cd web && npm run dev` |
| OpenClaw proxy | 18789 | whatever you already run for OpenClaw |
| Hermes | — | system `hermes` CLI (Grok 4.6) |
| Nanoclaw | — | system `nanoclaw` CLI |

Start **uvicorn first**. The Next app calls `http://127.0.0.1:8001` directly.

After pulling code, **restart uvicorn**. A 404 on `/api/openclaw/status` or `/api/nanoclaw/status` means an old process is still bound to 8001.

```powershell
cd C:\Projects\paperclip-app
python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

---

## What “Run” actually does

Creating an agent or a user story does **not** start a model.

1. Agent must have a **goal** (card textarea, or `PATCH /api/agents/{id}/goal`).
2. Click **Run Hermes / OpenClaw / Nanoclaw**, or POST `/api/agents/{id}/run` (kind-specific `/hermes/run`, `/openclaw/run`, `/nanoclaw/run` are thin aliases).
3. Paperclip returns **202** `{ job_id, status: "queued" }` immediately. A worker runs **one job per agent**.
4. A second POST for the same agent while a job is running is **queued behind it**, not rejected.
5. Agent status is `running` only while a job is `running`. Result is stored in **Traces**. Then `idle` / `paused` / `exceeded`.

HTTP **202** means the job was enqueued. Poll `GET /api/jobs/{id}`. Do **not** treat HTTP 200 from a leftover sync client as success.

| Field | Meaning |
|---|---|
| HTTP 202 + `job_id` | Queued. Poll `GET /api/jobs/{id}` |
| Job `succeeded` + non-empty `stdout` | Real success — read stdout and Traces |
| Job `succeeded` + empty `stdout` | Process exited 0 but captured no text |
| Job `failed` | Runner failed; read `error` / `stderr` |
| HTTP 404 `{"detail":"Not Found"}` | Route missing → restart uvicorn |
| HTTP 404 `{"detail":"Agent not found"}` | Wrong **id** (not the display name) |
| HTTP 400 empty goal / display-only kind | No job row created |
| HTTP 403 paused / over-cap | No job row created |
| Card stuck on **Running** | Use **Cancel** or **Force idle** (`POST /api/jobs/{id}/cancel` / `POST /api/agents/{id}/idle`) |

List agents (array — do not use `Select-Object` on the raw result):

```powershell
(Invoke-RestMethod http://127.0.0.1:8001/api/agents) |
  ForEach-Object { "$($_.id)  $($_.name)  $($_.kind)  $($_.status)" }
```

---

## Agent kinds

`kind` chooses the runner. Set it when you create the agent.

| kind | How it runs | Status check | Run URL |
|---|---|---|---|
| `hermes` | `hermes chat -q "<goal>"` | `GET /api/hermes/status` | `POST /api/agents/{id}/hermes/run` |
| `openclaw` | POST `http://127.0.0.1:18789/chat/main` | `GET /api/openclaw/status` | `POST /api/agents/{id}/openclaw/run` |
| `nanoclaw` | `nanoclaw` on PATH (`-p`, `chat -q`, …) | `GET /api/nanoclaw/status` | `POST /api/agents/{id}/nanoclaw/run` |

There is no Anthropic/Claude runner (no API key).

Grok 4.6 is **not** a separate runtime. Create a Hermes agent with `model: grok-4-6`. Hermes must already be configured for that model.

---

## Create agents

### Hermes / Grok 4.6

```powershell
Invoke-RestMethod http://127.0.0.1:8001/api/agents -Method POST -ContentType "application/json" -Body '{
  "name": "Grok 4.6",
  "role": "Hermes coding agent (grok-4-6)",
  "provider": "hermes",
  "model": "grok-4-6",
  "kind": "hermes",
  "goal": "Reply with one line: which model you are, then grok-ok",
  "working_dir": "C:\\Projects\\TaxProgram",
  "daily_cap": 25
}'
```

```powershell
Invoke-RestMethod http://127.0.0.1:8001/api/agents/grok-4-6/hermes/run `
  -Method POST -ContentType "application/json" -TimeoutSec 3600 `
  -Body '{ "goal": "Reply with one line: which model you are, then grok-ok" }'
```

`POST .../hermes/run` returns **202** immediately. Poll `GET /api/jobs/{job_id}`. Hermes itself has no default timeout; the worker waits until the CLI exits or you cancel.

### OpenClaw

Proxy must already be on `:18789`.

```powershell
Invoke-RestMethod http://127.0.0.1:8001/api/openclaw/status

Invoke-RestMethod http://127.0.0.1:8001/api/agents -Method POST -ContentType "application/json" -Body '{
  "name": "OpenClaw Main",
  "role": "Primary OpenClaw chat",
  "provider": "openclaw",
  "model": "openclaw",
  "kind": "openclaw",
  "goal": "Reply with exactly: openclaw-ok",
  "daily_cap": 25
}'

Invoke-RestMethod http://127.0.0.1:8001/api/agents/openclaw-main/openclaw/run `
  -Method POST -ContentType "application/json" `
  -Body '{ "goal": "Reply with exactly: openclaw-ok" }'
```

Override URL: env `OPENCLAW_URL`.

### Nanoclaw

```powershell
Get-Command nanoclaw
Invoke-RestMethod http://127.0.0.1:8001/api/nanoclaw/status

Invoke-RestMethod http://127.0.0.1:8001/api/agents -Method POST -ContentType "application/json" -Body '{
  "name": "Nanoclaw",
  "role": "Local NanoClaw worker",
  "provider": "nanoclaw",
  "model": "nanoclaw",
  "kind": "nanoclaw",
  "goal": "Reply with exactly: nanoclaw-ok",
  "working_dir": "C:\\Projects\\TaxProgram",
  "daily_cap": 25
}'

Invoke-RestMethod http://127.0.0.1:8001/api/agents/nanoclaw/nanoclaw/run `
  -Method POST -ContentType "application/json" `
  -Body '{ "goal": "Reply with exactly: nanoclaw-ok" }'
```

Start uvicorn from a shell where `hermes` / `nanoclaw` work (`Get-Command`). Otherwise status stays `"available": false`.

---

## Goal (required)

Empty goal → 400 `needs a goal`.

- UI: textarea on the agent card (saved on blur and on Run)
- API: `PATCH /api/agents/{id}/goal` with `{ "goal": "...", "working_dir": "..." }`

**Run agent on this story** still uses the **agent goal**, not the story body. To work a story, put the story id and acceptance into the goal, then Run.

---

## User stories

Paperclip's own backlog lives in `userStories/` (index: `userStories/USER_STORIES.md`). Cards on the Next board are the same stories, status `todo`.

Fields match `TaxProgram/userStories/Story Template.md`: `story_id`, epic, priority (`P0`–`P3`), sprint, as_a / i_want / so_that, blocked_by, must_not, files, acceptance, test, pr_size, tags.

Board lanes:

| Lane | Stored status |
|---|---|
| Backlog | `todo` |
| Assigned | `assigned` |
| In Progress | `in-progress` |
| Review Required | `review` |
| Completed | `done` |

Drag a card onto a column or use the dropdown. Persist: `PUT /api/tickets/{id}/status`.

Moving a lane does **not** start an agent.

---

## Traces

`GET /api/traces?limit=50`

Hermes success looks like a boxed `grok-4-6 grok-ok` plus session footer. That is the model output, not a hang.

If `ok: true` and `stdout` is empty, check the uvicorn console — some CLIs only print to a TTY.

Reset a stuck card:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/api/agents/<id>/idle -Method POST
```

---

## Usage and spend (US-P0.4)

Do **not** invent tokens from word counts. `usage.py` parses Hermes session footers (`Tokens: 1,250` / `Cost: $0.0042`) and provider JSON (`usage.total_tokens`, `prompt_tokens` + `completion_tokens`, `cost`). If nothing is present, store `tokens=null` and `usage_source=unknown`. Daily spend is unchanged.

Heartbeat is a liveness ping. Dashboard pings send `{ ping_only: true }` and cost is **0**. Never invent 250 tokens / $0.04.

`daily_spend` resets at local midnight **America/Chicago** (`spend_date` on the agent). `total_tokens` and `monthly_spend` are not reset.

Monthly cap is a stored company number (`meta.monthly_cap`, default 150). `GET /api/company` returns `monthly_spend` and `monthly_cap`. `PATCH /api/company` `{ "monthly_cap": 200 }` updates it. The Next budget bar uses that stored cap — not `daily * 12.4`.

Budget UI shows source: `parsed` vs `unknown` (or `mixed` when both exist).

---

## Layout

```
paperclip-app/
  main.py                 FastAPI
  db.py                   SQLite
  jobs.py                 async job worker
  runner.py               shared Result contract
  usage.py                token/cost parser
  hermes_runner.py
  openclaw_runner.py
  nanoclaw_runner.py
  static/index.html       simple UI on :8001
  web/                    Next.js UI on :3003
  data/paperclip.db
  docs/SYSTEM.md          this file
  start-paperclip.ps1     logon helper
```

Live API list: `http://127.0.0.1:8001/docs`

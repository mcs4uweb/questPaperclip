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
2. Click **Run Hermes / OpenClaw / Nanoclaw**, or POST the matching `/run` URL.
3. Agent status becomes `running` until the CLI/proxy returns.
4. Result is stored in **Traces**. Status goes back to `idle` (or `paused` / `exceeded`).

HTTP **200** only means Paperclip accepted the request and the runner finished talking to the backend. It does **not** mean the model printed something useful.

| Field | Meaning |
|---|---|
| HTTP 200 + `ok: true` + non-empty `stdout` | Real success — read `stdout` and Traces |
| HTTP 200 + `ok: true` + empty `stdout` | Process exited 0 but captured no text (banner-only, TTY, or proxy JSON we did not parse) |
| HTTP 200 + `ok: false` | Runner failed; read `error` / `stderr` |
| HTTP 404 `{"detail":"Not Found"}` | Route missing → restart uvicorn |
| HTTP 404 `{"detail":"Agent not found"}` | Wrong **id** (not the display name) |
| HTTP 400 `needs a goal` | Empty goal box |
| Card stuck on **Running** | Job still in flight, or the browser gave up while uvicorn is still waiting |

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

Hermes has **no default timeout**. Grok can take minutes. PowerShell still needs `-TimeoutSec 3600` or it will abort the HTTP client while the job continues (`running`).

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
Invoke-RestMethod http://127.0.0.1:8001/api/agents/<id>/status `
  -Method PATCH -ContentType "application/json" -Body '{ "status": "idle" }'
```

---

## Layout

```
paperclip-app/
  main.py                 FastAPI
  db.py                   SQLite
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

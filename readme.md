# Quest Paperclip

Local agent control plane for Quest Studio. Self-contained FastAPI + SQLite app (not Paperclip Cloud / `paperclipai`).

**Full operator guide:** [docs/SYSTEM.md](docs/SYSTEM.md) — agents (Hermes/Grok, OpenClaw, Nanoclaw), goals, 200 vs success, stories, traces, 404s.

## What it does

- Company dashboard for Quest, Video Pipeline, and Market Watch
- Task board with create / advance
- Per-agent daily budget caps
- Heartbeats that pause an agent when the cap is hit
- Execution traces
- Persistent storage in `data/paperclip.db` (created on first start)

## Run

```powershell
cd C:\Projects\paperclip-app
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

Open:

- Dashboard: http://127.0.0.1:8001/
- API docs: http://127.0.0.1:8001/docs
- Health: http://127.0.0.1:8001/health

## Frontends

- Classic dashboard (no build): http://127.0.0.1:8001/
- Next.js control plane (Hermes): http://localhost:3003/

```powershell
# terminal 1 — API
python -m uvicorn main:app --host 127.0.0.1 --port 8001

# terminal 2 — React UI
cd web
npm install
npm run dev
```

`web/` is a Next.js app that uses the Paperclip control-plane UI and talks to the FastAPI `/api` via rewrites.

Hermes: create an agent with a **goal** and **working directory**, then **Run Hermes**. The API executes `hermes chat -q "<goal>"` (same idea as `Retirement-app/hermes.ps1`). The `hermes` CLI must be on PATH.

Open **http://127.0.0.1:8001/** in the browser. Do not double-click `static/index.html`.

## Start at Windows logon

Script: `start-paperclip.ps1`

Register a task (run PowerShell **as Administrator** once):

```powershell
$action = New-ScheduledTaskAction `
  -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File `"C:\Projects\paperclip-app\start-paperclip.ps1`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "QuestPaperclip" -Action $action -Trigger $trigger -Settings $settings -Description "Start Quest Paperclip uvicorn on 127.0.0.1:8001"
```

Logs: `C:\Projects\logs\paperclip-yyyy-MM-dd.log`

## Storage

SQLite file: `data/paperclip.db` (gitignored).

Tables: `agents`, `tickets`, `traces`, `meta`. Seeded once if empty. Restarting the process keeps tickets, spend, and traces.

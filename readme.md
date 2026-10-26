# Quest Paperclip

Local agent control plane for Quest Studio. This is a self-contained FastAPI app, not the official Paperclip Cloud / `paperclipai` service.

## What it does

- Company dashboard for Quest, Video Pipeline, and Market Watch
- Task board with create / advance
- Per-agent daily budget caps
- Heartbeats that pause an agent when the cap is hit
- Execution traces

Official `paperclipai` was not installed as a Windows service. This app stays on loopback.

## Run

```powershell
cd C:\Projects\paperclip-app
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Open:

- Dashboard: http://127.0.0.1:8000/
- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

State is in-memory. Restarting the process resets tickets, spend, and traces.

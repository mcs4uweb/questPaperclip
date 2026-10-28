export type Agent = {
  id: string;
  name: string;
  role: string;
  provider: string;
  model: string;
  status: string;
  daily_spend: number;
  daily_cap: number;
  last_heartbeat?: string | null;
  reports_to?: string | null;
  kind?: string;
  goal?: string;
  working_dir?: string;
  total_tokens?: number;
  last_run_summary?: string;
  avatar_color?: string;
};

export type Ticket = {
  id: string;
  title: string;
  description: string;
  assignee_id: string;
  priority: string;
  status: string;
  story_id?: string | null;
  epic?: string;
  sprint?: string;
  as_a?: string;
  i_want?: string;
  so_that?: string;
  blocked_by?: string;
  must_not?: string;
  acceptance?: string;
};

export type Trace = {
  id: string;
  agent_id: string;
  agent_name: string;
  tool_called: string;
  prompt: string;
  response: string;
  latency_ms: number;
  token_count: number;
  status: string;
  timestamp: string;
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ||
  (typeof window !== "undefined" ? "http://127.0.0.1:8001" : "");

function formatDetail(detail: unknown, fallback: string) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => (typeof item === "object" && item && "msg" in item ? String((item as { msg: string }).msg) : JSON.stringify(item)))
      .join("; ");
  }
  return fallback;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = (data as { detail?: unknown }).detail;
    throw new Error(formatDetail(detail, `${res.status} ${res.statusText} for ${path}`));
  }
  return data as T;
}

export const api = {
  company: () => request<any>("/api/company"),
  agents: () => request<Agent[]>("/api/agents"),
  tickets: () => request<Ticket[]>("/api/tickets"),
  traces: () => request<Trace[]>("/api/traces?limit=50"),
  hermesStatus: () => request<{ available: boolean; path?: string }>("/api/hermes/status"),
  openclawStatus: () =>
    request<{ available: boolean; url?: string; error?: string; http_status?: number }>("/api/openclaw/status"),
  nanoclawStatus: () => request<{ available: boolean; path?: string }>("/api/nanoclaw/status"),
  runNanoclaw: (id: string, extra?: Record<string, unknown>) =>
    request<any>(`/api/agents/${id}/nanoclaw/run`, {
      method: "POST",
      body: JSON.stringify(extra || {}),
    }),
  createAgent: (body: Record<string, unknown>) =>
    request<Agent>("/api/agents", { method: "POST", body: JSON.stringify(body) }),
  runOpenClaw: (id: string, extra?: Record<string, unknown>) =>
    request<any>(`/api/agents/${id}/openclaw/run`, {
      method: "POST",
      body: JSON.stringify(extra || {}),
    }),
  heartbeat: (id: string) =>
    request<any>(`/api/agents/${id}/heartbeat`, {
      method: "POST",
      body: JSON.stringify({ tokens_consumed: 250, cost_incurred: 0.04, note: "dashboard ping" }),
    }),
  setStatus: (id: string, status: string) =>
    request<Agent>(`/api/agents/${id}/status`, { method: "PATCH", body: JSON.stringify({ status }) }),
  saveCap: (id: string, daily_cap: number) =>
    request<Agent>(`/api/agents/${id}/budget`, { method: "PATCH", body: JSON.stringify({ daily_cap }) }),
  saveGoal: (id: string, goal: string, working_dir?: string) =>
    request<Agent>(`/api/agents/${id}/goal`, {
      method: "PATCH",
      body: JSON.stringify({ goal, working_dir }),
    }),
  runHermes: (id: string, extra?: Record<string, unknown>) =>
    request<any>(`/api/agents/${id}/hermes/run`, {
      method: "POST",
      body: JSON.stringify(extra || {}),
    }),
  createTicket: (body: Record<string, unknown>) =>
    request<Ticket>("/api/tickets", { method: "POST", body: JSON.stringify(body) }),
  advanceTicket: (id: string, status: string) =>
    request<Ticket>(`/api/tickets/${id}/status`, { method: "PUT", body: JSON.stringify({ status }) }),
  deleteTicket: (id: string) =>
    request<{ deleted: string }>(`/api/tickets/${id}`, { method: "DELETE" }),
};

export function uiStatus(status?: string) {
  const s = (status || "").toLowerCase();
  if (s === "running") return "Running";
  if (s === "paused") return "Paused";
  if (s === "exceeded") return "Exceeded Cap";
  return "Idle";
}

export function boardStatus(status?: string) {
  const s = (status || "").toLowerCase();
  if (s === "done" || s === "completed") return "Completed";
  if (s === "review" || s === "review required") return "Review Required";
  if (s === "in-progress" || s === "in_progress") return "In Progress";
  if (s === "assigned") return "Assigned";
  return "Backlog";
}

export const LANE_STATUSES: Record<string, string> = {
  Backlog: "todo",
  Assigned: "assigned",
  "In Progress": "in-progress",
  "Review Required": "review",
  Completed: "done",
};

"use client";

import React, { useEffect, useMemo, useState } from "react";
import {
  Activity,
  Cpu,
  ShieldAlert,
  CheckCircle2,
  Clock,
  Play,
  Pause,
  RefreshCw,
  Plus,
  Search,
  Terminal,
  DollarSign,
  BarChart3,
  Layers,
  ChevronRight,
  Check,
  X,
  Eye,
  HardDrive,
  Trash2,
  Square,
} from "lucide-react";
import { Agent, Ticket, Trace, api, boardStatus, LANE_STATUSES, uiStatus } from "@/lib/api";

const COLUMNS = ["Backlog", "Assigned", "In Progress", "Review Required", "Completed"];

function UsersIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}

function nextStoryStatus(status: string) {
  const board = boardStatus(status);
  if (board === "Completed") return null;
  if (status === "todo" || status === "backlog") return "in-progress";
  return "done";
}

export default function PaperclipControlPlane() {
  const [activeTab, setActiveTab] = useState("agents");
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [traces, setTraces] = useState<Trace[]>([]);
  const [company, setCompany] = useState<any>(null);
  const [hermes, setHermes] = useState<{ available: boolean; path?: string } | null>(null);
  const [openclaw, setOpenclaw] = useState<{ available: boolean; url?: string; error?: string } | null>(null);
  const [nanoclaw, setNanoclaw] = useState<{ available: boolean; path?: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [activeJobs, setActiveJobs] = useState<Record<string, string>>({});

  const [overallMonthlyCap, setOverallMonthlyCap] = useState(150);
  const [monthlyCapDirty, setMonthlyCapDirty] = useState(false);
  const [autoPauseOnError, setAutoPauseOnError] = useState(true);
  const [fallbackToLocal, setFallbackToLocal] = useState(true);
  const [traceSearch, setTraceSearch] = useState("");
  const [ticketFilterAgent, setTicketFilterAgent] = useState("ALL");
  const [selectedTrace, setSelectedTrace] = useState<Trace | null>(null);
  const [isNewTicketOpen, setIsNewTicketOpen] = useState(false);
  const [isNewAgentOpen, setIsNewAgentOpen] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [goalDrafts, setGoalDrafts] = useState<Record<string, string>>({});

  const [newTicket, setNewTicket] = useState({
    title: "",
    as_a: "",
    i_want: "",
    so_that: "",
    epic: "",
    sprint: "",
    story_id: "",
    assignee_id: "",
    priority: "P1",
    must_not: "",
    acceptance: "",
  });
  const [newAgent, setNewAgent] = useState({
    name: "",
    role: "",
    goal: "",
    working_dir: "C:\\Projects",
    daily_cap: 5,
    reports_to: "",
  });

  async function refresh() {
    try {
      const [c, a, t, tr, h, oc, nc] = await Promise.all([
        api.company(),
        api.agents(),
        api.tickets(),
        api.traces(),
        api.hermesStatus(),
        api.openclawStatus(),
        api.nanoclawStatus(),
      ]);
      setCompany(c);
      if (!monthlyCapDirty && typeof c?.monthly_cap === "number") {
        setOverallMonthlyCap(c.monthly_cap);
      }
      setAgents(a);
      setTickets(t);
      setTraces(tr);
      setHermes(h);
      setOpenclaw(oc);
      setNanoclaw(nc);
      setError(null);
      if (!newTicket.assignee_id && a[0]) {
        setNewTicket((prev) => ({ ...prev, assignee_id: a[0].id }));
      }
    } catch (err: any) {
      setError(err.message || "API unavailable. Start uvicorn on port 8001.");
    }
  }

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 15000);
    return () => clearInterval(id);
  }, []);

  function notify(message: string) {
    setToast(message);
    setTimeout(() => setToast(null), 3000);
  }

  const metrics = useMemo(() => {
    const totalDailySpend = agents.reduce((acc, a) => acc + (a.daily_spend || 0), 0);
    const totalMonthlySpend = company?.monthly_spend ?? agents.reduce((acc, a) => acc + (a.monthly_spend || 0), 0);
    const totalTokens = agents.reduce((acc, a) => acc + (a.total_tokens || 0), 0);
    const activeAgentsCount = agents.filter((a) => a.status === "running").length;
    const activeTasksCount = tickets.filter((t) => !["done", "completed"].includes(t.status)).length;
    const usageSource = company?.usage_source || (agents.some((a) => a.usage_source === "parsed") ? "mixed" : "unknown");
    return { totalDailySpend, totalMonthlySpend, totalTokens, activeAgentsCount, activeTasksCount, usageSource };
  }, [agents, tickets, company]);

  function draftGoal(agent: Agent) {
    return goalDrafts[agent.id] ?? agent.goal ?? "";
  }

  async function persistGoal(agent: Agent) {
    const goal = draftGoal(agent).trim();
    await api.saveGoal(agent.id, goal, agent.working_dir || "");
    setGoalDrafts((prev) => ({ ...prev, [agent.id]: goal }));
    return goal;
  }

  async function queueRun(agent: Agent, kind: "hermes" | "openclaw" | "nanoclaw") {
    setBusyId(agent.id);
    try {
      const goal = await persistGoal(agent);
      if (!goal) {
        notify(`Add a goal in the box on this card, then click Run ${kind === "hermes" ? "Hermes" : kind === "openclaw" ? "OpenClaw" : "Nanoclaw"}.`);
        return;
      }
      const starter = kind === "nanoclaw" ? api.runNanoclaw : kind === "openclaw" ? api.runOpenClaw : api.runHermes;
      const result = await starter(agent.id, { goal });
      if (result.job_id) {
        setActiveJobs((prev) => ({ ...prev, [agent.id]: result.job_id }));
        notify(`${kind} queued ${result.job_id}`);
      } else {
        notify(result.error || `${kind} did not return a job_id`);
      }
      await refresh();
    } catch (err: any) {
      notify(err.message);
      await refresh();
    } finally {
      setBusyId(null);
    }
  }

  async function runHermes(agent: Agent) {
    return queueRun(agent, "hermes");
  }

  async function runOpenClaw(agent: Agent) {
    return queueRun(agent, "openclaw");
  }

  async function runNanoclaw(agent: Agent) {
    return queueRun(agent, "nanoclaw");
  }

  async function cancelAgentJob(agent: Agent) {
    const jobId = activeJobs[agent.id];
    try {
      if (jobId) {
        await api.cancelJob(jobId);
        notify(`Cancelled ${jobId}`);
      } else {
        await api.forceIdle(agent.id);
        notify(`Force idle ${agent.name}`);
      }
      setActiveJobs((prev) => {
        const next = { ...prev };
        delete next[agent.id];
        return next;
      });
      await refresh();
    } catch (err: any) {
      notify(err.message);
      await refresh();
    }
  }

  async function forceIdleAgent(agent: Agent) {
    try {
      await api.forceIdle(agent.id);
      setActiveJobs((prev) => {
        const next = { ...prev };
        delete next[agent.id];
        return next;
      });
      notify(`${agent.name} is idle`);
      await refresh();
    } catch (err: any) {
      notify(err.message);
    }
  }

  function runAgent(agent: Agent) {
    const kind = (agent.kind || agent.provider || "").toLowerCase();
    if (kind.includes("nanoclaw")) return runNanoclaw(agent);
    if (kind.includes("openclaw")) return runOpenClaw(agent);
    return runHermes(agent);
  }

  function runLabel(agent: Agent) {
    const kind = (agent.kind || agent.provider || "").toLowerCase();
    if (kind.includes("nanoclaw")) return "Run Nanoclaw";
    if (kind.includes("openclaw")) return "Run OpenClaw";
    return "Run Hermes";
  }

  async function moveStory(ticketId: string, lane: string) {
    const status = LANE_STATUSES[lane];
    if (!status) return;
    try {
      await api.advanceTicket(ticketId, status);
      await refresh();
    } catch (err: any) {
      notify(err.message);
    }
  }

  async function deleteStory(ticket: Ticket) {
    if (!window.confirm(`Delete "${ticket.title}"? This cannot be undone.`)) return;
    try {
      await api.deleteTicket(ticket.id);
      notify(`Deleted ${ticket.story_id || ticket.id}`);
      await refresh();
    } catch (err: any) {
      notify(err.message);
    }
  }

  async function ping(agentId: string) {
    try {
      const result = await api.heartbeat(agentId);
      notify(`${agentId}: ${result.action}`);
      await refresh();
    } catch (err: any) {
      notify(err.message);
      await refresh();
    }
  }

  async function removeTrace(trace: Trace) {
    if (!window.confirm(`Delete trace ${trace.id}?`)) return;
    try {
      await api.deleteTrace(trace.id);
      if (selectedTrace?.id === trace.id) setSelectedTrace(null);
      notify(`Deleted ${trace.id}`);
      await refresh();
    } catch (err: any) {
      if (err.message === "Trace not found") {
        // already gone (stale grid) — drop it locally and resync
        setTraces((prev) => prev.filter((t) => t.id !== trace.id));
        if (selectedTrace?.id === trace.id) setSelectedTrace(null);
        await refresh();
        return;
      }
      notify(err.message);
    }
  }

  async function removeAgent(agent: Agent) {
    if (!window.confirm(`Delete agent "${agent.name}"? Traces for this agent are removed.`)) return;
    try {
      await api.deleteAgent(agent.id);
      notify(`Deleted ${agent.name}`);
      await refresh();
    } catch (err: any) {
      notify(err.message);
    }
  }

  async function toggle(agent: Agent) {
    await api.setStatus(agent.id, agent.status === "paused" ? "running" : "paused");
    await refresh();
  }

  async function handleCreateAgent(e: React.FormEvent) {
    e.preventDefault();
    try {
      const agent = await api.createAgent({
        name: newAgent.name,
        role: newAgent.role,
        provider: "openclaw",
        model: "openclaw",
        kind: "openclaw",
        goal: newAgent.goal,
        working_dir: newAgent.working_dir,
        daily_cap: Number(newAgent.daily_cap),
        reports_to: newAgent.reports_to || null,
        status: "idle",
      });
      setIsNewAgentOpen(false);
      setNewAgent({ name: "", role: "", goal: "", working_dir: "C:\\Projects", daily_cap: 5, reports_to: "" });
      notify(`Imported OpenClaw agent ${agent.name}`);
      await refresh();
    } catch (err: any) {
      notify(err.message);
    }
  }

  async function handleCreateTicket(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.createTicket({
        title: newTicket.title,
        assignee_id: newTicket.assignee_id,
        priority: newTicket.priority,
        status: "todo",
        story_id: newTicket.story_id || null,
        epic: newTicket.epic,
        sprint: newTicket.sprint,
        as_a: newTicket.as_a,
        i_want: newTicket.i_want,
        so_that: newTicket.so_that,
        must_not: newTicket.must_not,
        acceptance: newTicket.acceptance,
        description: [newTicket.as_a && `As a ${newTicket.as_a}`, newTicket.i_want && `I want ${newTicket.i_want}`, newTicket.so_that && `So that ${newTicket.so_that}`].filter(Boolean).join(". "),
      });
      setIsNewTicketOpen(false);
      notify("User story added");
      await refresh();
    } catch (err: any) {
      notify(err.message);
    }
  }

  const filteredTraces = traces.filter((t) =>
    [t.agent_name, t.tool_called, t.prompt, t.status].join(" ").toLowerCase().includes(traceSearch.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased flex flex-col">
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-indigo-600/20 border border-indigo-500/30 rounded-xl text-indigo-400">
                <Cpu className="w-6 h-6 animate-pulse" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h1 className="text-lg font-bold tracking-tight text-white">PAPERCLIP</h1>
                  <span className="px-2 py-0.5 text-xs font-mono bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-md">
                    OpenClaw + Hermes
                  </span>
                </div>
                <p className="text-xs text-slate-400">
                  {company?.goal || "Run OpenClaw at 127.0.0.1:18789/chat/main and optional Hermes CLI agents"}
                </p>
              </div>
            </div>
            <div className="hidden md:flex items-center space-x-6 text-sm">
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${openclaw?.available ? "bg-emerald-400 animate-ping" : "bg-rose-400"}`} />
                <span className="text-slate-400">OpenClaw:</span>
                <span className="font-semibold font-mono text-white">{openclaw?.available ? "ready" : "down"}</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${hermes?.available ? "bg-emerald-400" : "bg-slate-600"}`} />
                <span className="text-slate-400">Hermes:</span>
                <span className="font-semibold font-mono text-white">{hermes?.available ? "ready" : "off"}</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${nanoclaw?.available ? "bg-emerald-400" : "bg-slate-600"}`} />
                <span className="text-slate-400">Nanoclaw:</span>
                <span className="font-semibold font-mono text-white">{nanoclaw?.available ? "ready" : "off"}</span>
              </div>
              <div className="h-4 w-px bg-slate-800" />
              <div className="flex items-center space-x-2">
                <DollarSign className="w-4 h-4 text-emerald-400" />
                <span className="font-semibold font-mono text-white">${metrics.totalDailySpend.toFixed(2)}</span>
              </div>
              <div className="flex items-center space-x-2">
                <Activity className="w-4 h-4 text-cyan-400" />
                <span className="font-semibold font-mono text-white">{metrics.activeTasksCount}</span>
              </div>
            </div>
            <button
              onClick={() => refresh()}
              className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium flex items-center space-x-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Refresh</span>
            </button>
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 border-t border-slate-800/60">
          <nav className="flex space-x-1 sm:space-x-4 py-2 overflow-x-auto">
            {[
              { id: "agents", label: "Agents", icon: UsersIcon },
              { id: "tasks", label: "User Stories", icon: Layers },
              { id: "budget", label: "Token & Budget", icon: BarChart3 },
              { id: "traces", label: "Traces", icon: Terminal },
            ].map((tab) => {
              const Icon = tab.icon;
              const active = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium ${
                    active ? "bg-slate-800 text-white border border-slate-700" : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${active ? "text-indigo-400" : "text-slate-400"}`} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      {toast && (
        <div className="fixed bottom-4 right-4 z-50 bg-emerald-950/90 border border-emerald-500/40 text-emerald-200 px-4 py-2.5 rounded-xl text-xs">
          {toast}
        </div>
      )}
      {error && (
        <div className="max-w-7xl mx-auto mt-4 px-4 text-sm text-rose-300">
          {error} API must be at http://127.0.0.1:8001
        </div>
      )}

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === "agents" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between bg-slate-900 border border-slate-800 p-4 rounded-2xl">
              <div>
                <h2 className="text-base font-semibold">Hermes agent directory</h2>
                <p className="text-xs text-slate-400">Create a named Hermes worker, give it a role and goal, then run `hermes chat -q`.</p>
              </div>
              <button onClick={() => setIsNewAgentOpen(true)} className="px-3.5 py-2 bg-indigo-600 rounded-xl text-xs font-semibold flex items-center space-x-1.5">
                <Plus className="w-4 h-4" />
                <span>Import Hermes agent</span>
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {agents.map((agent) => {
                const label = uiStatus(agent.status);
                const isOverCap = label === "Exceeded Cap";
                const isRunning = label === "Running" || busyId === agent.id;
                return (
                  <div key={agent.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 relative overflow-hidden">
                    <div className={`absolute top-0 left-0 right-0 h-1 ${isOverCap ? "bg-rose-500" : isRunning ? "bg-emerald-500" : "bg-slate-600"}`} />
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-sm font-semibold">{agent.name}</h3>
                        <p className="text-xs text-slate-400">{agent.role}</p>
                      </div>
                      <div className="flex items-center space-x-1">
                        <span className="px-2 py-0.5 rounded-full text-[10px] border border-slate-700">{label}</span>
                        <button
                          type="button"
                          title="Delete agent"
                          onClick={() => removeAgent(agent)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <div className="mt-4 p-2.5 bg-slate-950/60 rounded-xl border border-slate-800/80 text-xs space-y-1.5">
                      <div className="flex justify-between"><span className="text-slate-400">Runtime</span><span className="font-mono">{agent.provider} / {agent.model}</span></div>
                      <div className="flex justify-between"><span className="text-slate-400">Kind</span><span>{agent.kind || "hermes"}</span></div>
                      <div className="text-slate-400">Goal (required to run)</div>
                      <textarea
                        rows={4}
                        className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2 py-1.5 text-slate-200"
                        placeholder="What should this agent do? Saved when you click Run."
                        value={draftGoal(agent)}
                        onChange={(e) => setGoalDrafts((prev) => ({ ...prev, [agent.id]: e.target.value }))}
                        onBlur={() => persistGoal(agent).catch((err) => notify(err.message))}
                      />
                    </div>
                    <div className="mt-4 text-xs flex justify-between">
                      <span>${agent.daily_spend.toFixed(2)} / ${agent.daily_cap.toFixed(2)} · {agent.usage_source || "unknown"}</span>
                      <span className="text-slate-500 flex items-center space-x-1"><Clock className="w-3 h-3" /><span>{agent.last_heartbeat ? new Date(agent.last_heartbeat).toLocaleTimeString() : "never"}</span></span>
                    </div>
                    <div className="mt-4 flex items-center justify-end space-x-2">
                      <button onClick={() => ping(agent.id)} className="p-1.5 bg-slate-800 rounded-lg" title="Heartbeat only"><RefreshCw className="w-3.5 h-3.5" /></button>
                      <button onClick={() => toggle(agent)} className="px-2.5 py-1 rounded-lg text-xs border border-slate-700 flex items-center space-x-1">
                        {agent.status === "paused" ? <Play className="w-3 h-3" /> : <Pause className="w-3 h-3" />}
                        <span>{agent.status === "paused" ? "Resume" : "Pause"}</span>
                      </button>
                      {(isRunning || agent.status === "paused") && (
                        <button onClick={() => forceIdleAgent(agent)} className="px-2.5 py-1 rounded-lg text-xs border border-amber-700 text-amber-200">
                          Force idle
                        </button>
                      )}
                      {isRunning && (
                        <button onClick={() => cancelAgentJob(agent)} className="px-2.5 py-1 rounded-lg text-xs border border-rose-700 text-rose-200 flex items-center space-x-1">
                          <Square className="w-3 h-3" />
                          <span>Cancel</span>
                        </button>
                      )}
                      <button onClick={() => runAgent(agent)} disabled={busyId === agent.id} className="px-2.5 py-1 rounded-lg text-xs bg-indigo-600 disabled:opacity-50">
                        {busyId === agent.id ? "Queued…" : runLabel(agent)}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {activeTab === "tasks" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between bg-slate-900 border border-slate-800 p-4 rounded-2xl">
              <h2 className="text-base font-semibold">User stories</h2>
              <div className="flex items-center space-x-3">
                <select value={ticketFilterAgent} onChange={(e) => setTicketFilterAgent(e.target.value)} className="bg-slate-950 border border-slate-800 text-xs rounded-xl px-3 py-2">
                  <option value="ALL">All agents</option>
                  {agents.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
                </select>
                <button onClick={() => setIsNewTicketOpen(true)} className="px-3.5 py-2 bg-indigo-600 rounded-xl text-xs font-semibold flex items-center space-x-1.5">
                  <Plus className="w-4 h-4" /><span>Create story</span>
                </button>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
              {COLUMNS.map((columnStatus) => {
                const columnTickets = tickets.filter((t) =>
                  boardStatus(t.status) === columnStatus &&
                  (ticketFilterAgent === "ALL" || t.assignee_id === ticketFilterAgent)
                );
                return (
                  <div
                    key={columnStatus}
                    className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-3 min-h-[420px]"
                    onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = "move"; }}
                    onDrop={(e) => {
                      e.preventDefault();
                      const id = e.dataTransfer.getData("text/ticket-id");
                      if (id) moveStory(id, columnStatus);
                    }}
                  >
                    <div className="flex justify-between pb-2 mb-3 border-b border-slate-800 text-xs">
                      <span>{columnStatus}</span><span>{columnTickets.length}</span>
                    </div>
                    <div className="space-y-3">
                      {columnTickets.map((ticket) => {
                        const assigned = agents.find((a) => a.id === ticket.assignee_id);
                        const currentLane = boardStatus(ticket.status);
                        return (
                          <div
                            key={ticket.id}
                            draggable
                            onDragStart={(e) => {
                              e.dataTransfer.setData("text/ticket-id", ticket.id);
                              e.dataTransfer.effectAllowed = "move";
                            }}
                            className="bg-slate-900 border border-slate-800 p-3.5 rounded-xl space-y-2 cursor-grab active:cursor-grabbing"
                          >
                            <div className="flex justify-between text-[10px] font-mono text-slate-500">
                              <span>{ticket.story_id || ticket.id}</span>
                              <div className="flex items-center space-x-2">
                                <span>{ticket.priority}</span>
                                <button
                                  onClick={(e) => { e.stopPropagation(); deleteStory(ticket); }}
                                  title="Delete story"
                                  className="text-slate-500 hover:text-red-400"
                                >
                                  <Trash2 className="w-3.5 h-3.5" />
                                </button>
                              </div>
                            </div>
                            <h4 className="text-xs font-semibold">{ticket.title}</h4>
                            <p className="text-[11px] text-slate-400 line-clamp-3">{ticket.i_want || ticket.description}</p>
                            <div className="flex justify-between text-[10px] text-slate-300">
                              <span>{assigned?.name || ticket.assignee_id}</span>
                            </div>
                            <select
                              value={currentLane}
                              onChange={(e) => moveStory(ticket.id, e.target.value)}
                              onClick={(e) => e.stopPropagation()}
                              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 text-[10px]"
                            >
                              {COLUMNS.map((lane) => (
                                <option key={lane} value={lane}>{lane}</option>
                              ))}
                            </select>
                            {assigned && (
                              <button onClick={() => runAgent(assigned)} className="w-full text-[10px] py-1 bg-indigo-600/80 rounded-lg">
                                Run agent on this story
                              </button>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {activeTab === "budget" && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-base font-semibold">Monthly spend (stored cap)</h2>
                  <p className="text-[11px] text-slate-400 mt-1">
                    Source: {metrics.usageSource === "parsed" ? "parsed provider usage" : metrics.usageSource === "mixed" ? "parsed + unknown" : "unknown — no invented word counts"}
                  </p>
                </div>
                <input
                  type="number"
                  value={overallMonthlyCap}
                  onChange={(e) => { setMonthlyCapDirty(true); setOverallMonthlyCap(Number(e.target.value)); }}
                  onBlur={async () => {
                    await api.saveMonthlyCap(Number(overallMonthlyCap) || 0);
                    setMonthlyCapDirty(false);
                    refresh();
                  }}
                  className="w-24 bg-slate-950 border border-slate-800 rounded-xl px-2 py-1 text-sm"
                />
              </div>
              <div className="mt-2 text-xs text-slate-300 font-mono">
                ${metrics.totalMonthlySpend.toFixed(2)} / ${Number(overallMonthlyCap || 0).toFixed(2)}
              </div>
              <div className="mt-4 w-full bg-slate-950 h-3 rounded-full overflow-hidden border border-slate-800">
                <div className="bg-indigo-500 h-full" style={{ width: `${Math.min(100, ((metrics.totalMonthlySpend || 0) / Math.max(overallMonthlyCap || 1, 0.01)) * 100)}%` }} />
              </div>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950 text-slate-400"><tr><th className="p-3">Agent</th><th className="p-3">Tokens</th><th className="p-3">Daily</th><th className="p-3">Monthly</th><th className="p-3">Cap</th><th className="p-3">Source</th></tr></thead>
                <tbody>
                  {agents.map((agent) => (
                    <tr key={agent.id} className="border-t border-slate-800">
                      <td className="p-3">{agent.name}</td>
                      <td className="p-3 font-mono">{(agent.total_tokens || 0).toLocaleString()}</td>
                      <td className="p-3">${agent.daily_spend.toFixed(2)}</td>
                      <td className="p-3">${(agent.monthly_spend || 0).toFixed(2)}</td>
                      <td className="p-3">
                        <input type="number" defaultValue={agent.daily_cap} className="w-20 bg-slate-950 border border-slate-800 rounded px-2 py-1"
                          onBlur={async (e) => { await api.saveCap(agent.id, Number(e.target.value)); refresh(); }} />
                      </td>
                      <td className="p-3 font-mono text-slate-400">{agent.usage_source || "unknown"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <label className="bg-slate-900 border border-slate-800 p-5 rounded-2xl flex justify-between">
                <span className="flex items-center space-x-2 text-sm"><ShieldAlert className="w-4 h-4 text-amber-400" /><span>Auto-pause on Hermes error</span></span>
                <input type="checkbox" checked={autoPauseOnError} onChange={(e) => setAutoPauseOnError(e.target.checked)} />
              </label>
              <label className="bg-slate-900 border border-slate-800 p-5 rounded-2xl flex justify-between">
                <span className="flex items-center space-x-2 text-sm"><HardDrive className="w-4 h-4 text-cyan-400" /><span>Keep working dir local</span></span>
                <input type="checkbox" checked={fallbackToLocal} onChange={(e) => setFallbackToLocal(e.target.checked)} />
              </label>
            </div>
          </div>
        )}

        {activeTab === "traces" && (
          <div className="space-y-4">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
              <input value={traceSearch} onChange={(e) => setTraceSearch(e.target.value)} placeholder="Search Hermes traces" className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs" />
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950 text-slate-400"><tr><th className="p-3 w-10"></th><th className="p-3">ID</th><th className="p-3">Result date</th><th className="p-3">Agent</th><th className="p-3">Tool</th><th className="p-3">Prompt</th><th className="p-3">Status</th><th className="p-3">Job results</th><th className="p-3"></th></tr></thead>
                <tbody>
                  {filteredTraces.map((trace) => (
                    <tr key={trace.id} className="border-t border-slate-800">
                      <td className="p-3">
                        <button
                          type="button"
                          title="Delete trace"
                          className="text-slate-500 hover:text-rose-400"
                          onClick={() => removeTrace(trace)}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                      <td className="p-3 font-mono text-indigo-400">{trace.id}</td>
                      <td className="p-3 whitespace-nowrap text-slate-300">{trace.timestamp ? new Date(trace.timestamp).toLocaleString() : "—"}</td>
                      <td className="p-3">{trace.agent_name}</td>
                      <td className="p-3 font-mono text-cyan-300">{trace.tool_called}</td>
                      <td className="p-3 truncate max-w-xs">{trace.prompt}</td>
                      <td className="p-3">{trace.status}</td>
                      <td className="p-3">
                        <button
                          type="button"
                          className="text-indigo-400 hover:text-indigo-300 underline"
                          onClick={() => setSelectedTrace(trace)}
                        >
                          Job results
                        </button>
                      </td>
                      <td className="p-3"><button onClick={() => setSelectedTrace(trace)}><Eye className="w-3.5 h-3.5" /></button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {selectedTrace && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-6xl w-full h-[85vh] p-6 space-y-3 flex flex-col">
            <div className="flex justify-between items-center shrink-0">
              <h3 className="font-bold text-lg">Trace {selectedTrace.id}</h3>
              <button onClick={() => setSelectedTrace(null)}><X className="w-5 h-5" /></button>
            </div>
            <pre className="text-sm leading-relaxed bg-slate-950 p-4 rounded-xl overflow-auto flex-1 min-h-0 whitespace-pre-wrap">{selectedTrace.job_stdout || selectedTrace.response || selectedTrace.job_error || "No job stdout recorded."}</pre>
          </div>
        </div>
      )}

      {isNewAgentOpen && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <form onSubmit={handleCreateAgent} className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-3 text-xs">
            <div className="flex justify-between"><h3 className="text-base font-bold">Import OpenClaw agent</h3><button type="button" onClick={() => setIsNewAgentOpen(false)}><X className="w-5 h-5" /></button></div>
            <input required placeholder="Name" className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2" value={newAgent.name} onChange={(e) => setNewAgent({ ...newAgent, name: e.target.value })} />
            <input required placeholder="Role" className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2" value={newAgent.role} onChange={(e) => setNewAgent({ ...newAgent, role: e.target.value })} />
            <textarea required rows={4} placeholder="Default OpenClaw goal (POST http://127.0.0.1:18789/chat/main)" className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2" value={newAgent.goal} onChange={(e) => setNewAgent({ ...newAgent, goal: e.target.value })} />
            <input placeholder="Working directory" className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2" value={newAgent.working_dir} onChange={(e) => setNewAgent({ ...newAgent, working_dir: e.target.value })} />
            <div className="flex justify-end space-x-2">
              <button type="button" onClick={() => setIsNewAgentOpen(false)} className="px-3 py-2 bg-slate-800 rounded-xl">Cancel</button>
              <button className="px-3 py-2 bg-indigo-600 rounded-xl">Save agent</button>
            </div>
          </form>
        </div>
      )}

      {isNewTicketOpen && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <form onSubmit={handleCreateTicket} className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-3 text-xs">
            <div className="flex justify-between"><h3 className="text-base font-bold">Create user story</h3><button type="button" onClick={() => setIsNewTicketOpen(false)}><X className="w-5 h-5" /></button></div>
            <input placeholder="US-x.y" className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2" value={newTicket.story_id} onChange={(e) => setNewTicket({ ...newTicket, story_id: e.target.value })} />
            <input required placeholder="Title" className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2" value={newTicket.title} onChange={(e) => setNewTicket({ ...newTicket, title: e.target.value })} />
            <input placeholder="As a" className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2" value={newTicket.as_a} onChange={(e) => setNewTicket({ ...newTicket, as_a: e.target.value })} />
            <input placeholder="I want" className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2" value={newTicket.i_want} onChange={(e) => setNewTicket({ ...newTicket, i_want: e.target.value })} />
            <input placeholder="So that" className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2" value={newTicket.so_that} onChange={(e) => setNewTicket({ ...newTicket, so_that: e.target.value })} />
            <select className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2" value={newTicket.assignee_id} onChange={(e) => setNewTicket({ ...newTicket, assignee_id: e.target.value })}>
              {agents.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
            <div className="flex justify-end space-x-2">
              <button type="button" onClick={() => setIsNewTicketOpen(false)} className="px-3 py-2 bg-slate-800 rounded-xl">Cancel</button>
              <button className="px-3 py-2 bg-indigo-600 rounded-xl">Dispatch</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

import React, { useState, useEffect, useMemo } from 'react';
import { 
  Activity, Cpu, ShieldAlert, CheckCircle2, Clock, Play, Pause, RefreshCw, 
  Plus, Search, Filter, Terminal, DollarSign, Database, Server, BarChart3, 
  Layers, ChevronRight, FileCode, Check, X, ArrowUpRight, UserCheck, Settings,
  AlertTriangle, Copy, ChevronDown, Eye, HardDrive, Shield
} from 'lucide-react';

// --- MOCK INITIAL DATA ---

const INITIAL_AGENTS = [
  {
    id: 'agent-1',
    name: 'Lead Orchestrator',
    role: 'Team Lead & Strategist',
    model: 'Claude 3.5 Sonnet',
    provider: 'Anthropic Cloud',
    status: 'Running', // Idle, Running, Paused, Exceeded Cap
    heartbeatInterval: '30s',
    lastHeartbeat: '2s ago',
    dailyBudgetCap: 15.00,
    dailySpend: 4.82,
    totalTokens: 324500,
    reportsTo: null,
    avatarColor: 'bg-indigo-500',
  },
  {
    id: 'agent-2',
    name: 'Python Engineer',
    role: 'Backend Code Generation',
    model: 'Llama 3.3 70B (Local)',
    provider: 'Ollama Local',
    status: 'Running',
    heartbeatInterval: '1m',
    lastHeartbeat: '14s ago',
    dailyBudgetCap: 5.00,
    dailySpend: 0.12,
    totalTokens: 890100,
    reportsTo: 'agent-1',
    avatarColor: 'bg-emerald-500',
  },
  {
    id: 'agent-3',
    name: 'Code Auditor & SecOps',
    role: 'Vulnerability & Policy Review',
    model: 'Gemini 1.5 Pro',
    provider: 'Google Cloud',
    status: 'Idle',
    heartbeatInterval: '5m',
    lastHeartbeat: '2m ago',
    dailyBudgetCap: 10.00,
    dailySpend: 2.15,
    totalTokens: 145000,
    reportsTo: 'agent-1',
    avatarColor: 'bg-amber-500',
  },
  {
    id: 'agent-4',
    name: 'RAG Specialist',
    role: 'Vector Search & Doc Context',
    model: 'Qwen 2.5 Coder',
    provider: 'Ollama Local',
    status: 'Running',
    heartbeatInterval: '30s',
    lastHeartbeat: '5s ago',
    dailyBudgetCap: 2.00,
    dailySpend: 0.00,
    totalTokens: 1200400,
    reportsTo: 'agent-2',
    avatarColor: 'bg-cyan-500',
  },
  {
    id: 'agent-5',
    name: 'Docs & Release Generator',
    role: 'Changelogs & API Specs',
    model: 'GPT-4o Mini',
    provider: 'OpenAI Cloud',
    status: 'Exceeded Cap',
    heartbeatInterval: '10m',
    lastHeartbeat: '8m ago',
    dailyBudgetCap: 1.50,
    dailySpend: 1.52,
    totalTokens: 98000,
    reportsTo: 'agent-1',
    avatarColor: 'bg-rose-500',
  }
];

const INITIAL_TICKETS = [
  {
    id: 'TCK-101',
    title: 'Implement AES-256-GCM chunked file encryption for LiteNetLib streams',
    description: 'Ensure memory-efficient buffer allocations when streaming files over direct P2P sockets.',
    agentId: 'agent-2',
    priority: 'High',
    status: 'In Progress',
    subtasks: [
      { text: 'Create IV initialization vector pool', done: true },
      { text: 'Implement AuthTag verification on final block', done: true },
      { text: 'Bench test transfer throughput with 1GB file', done: false }
    ],
    createdAt: '2026-10-26T09:30:00Z'
  },
  {
    id: 'TCK-102',
    title: 'Audit GCP KMS key path validation in C# initialization',
    description: 'Verify project ID and keyring scope logic against GCP KMS service limits.',
    agentId: 'agent-3',
    priority: 'Critical',
    status: 'Review Required',
    subtasks: [
      { text: 'Check scope syntax format', done: true },
      { text: 'Validate base64 ciphertext decoding logic', done: true }
    ],
    createdAt: '2026-10-26T10:15:00Z'
  },
  {
    id: 'TCK-103',
    title: 'Index dbo.app_chat_messages schema into local vector database',
    description: 'Parse SQL schema tables and generate semantic embeddings for AI agent grounding.',
    agentId: 'agent-4',
    priority: 'Medium',
    status: 'Assigned',
    subtasks: [
      { text: 'Extract table relationships', done: false },
      { text: 'Push embeddings to Qdrant/Chroma', done: false }
    ],
    createdAt: '2026-10-26T10:45:00Z'
  },
  {
    id: 'TCK-104',
    title: 'Generate OpenAPI 3.1 documentation for FastAPI endpoints',
    description: 'Publish full OpenAPI endpoint spec for heartbeats, budget caps, and ticket assignment.',
    agentId: 'agent-5',
    priority: 'Low',
    status: 'Backlog',
    subtasks: [
      { text: 'Export FastAPI JSON schema', done: false }
    ],
    createdAt: '2026-10-26T11:00:00Z'
  },
  {
    id: 'TCK-100',
    title: 'Setup Firestore STUN matchmaking signaling logic',
    description: 'Configure Firestore real-time listener for NAT traversal offer/answer exchanges.',
    agentId: 'agent-1',
    priority: 'High',
    status: 'Completed',
    subtasks: [
      { text: 'Create matchmaking collections', done: true },
      { text: 'Test client peer connection fallback', done: true }
    ],
    createdAt: '2026-10-26T08:00:00Z'
  }
];

const INITIAL_TRACES = [
  {
    id: 'tr-9981',
    timestamp: '11:14:22',
    agentName: 'Python Engineer',
    toolCalled: 'exec_python_script',
    prompt: 'Execute benchmark script for C# AES-256 buffer allocations.',
    response: '{"status": "success", "throughput": "480 MB/s", "allocations_mb": 12.4}',
    tokenCount: 1420,
    latencyMs: 340,
    status: 'Success'
  },
  {
    id: 'tr-9980',
    timestamp: '11:12:05',
    agentName: 'Code Auditor & SecOps',
    toolCalled: 'gcp_kms_inspect',
    prompt: 'Validate scope format projects/my-project/locations/us-central1/keyRings/tax-pii',
    response: '{"valid": true, "key_state": "ENABLED", "crypto_algorithm": "AES_256_GCM"}',
    tokenCount: 890,
    latencyMs: 180,
    status: 'Success'
  },
  {
    id: 'tr-9979',
    timestamp: '11:08:41',
    agentName: 'Docs & Release Generator',
    toolCalled: 'openai_chat_completion',
    prompt: 'Summarize commit log for version v1.4.2 deployment release notes.',
    response: 'Error 429: Daily budget cap ($1.50) reached for Docs Generator. Execution halted.',
    tokenCount: 0,
    latencyMs: 45,
    status: 'Blocked by Cap'
  },
  {
    id: 'tr-9978',
    timestamp: '11:05:12',
    agentName: 'RAG Specialist',
    toolCalled: 'vector_search_hybrid',
    prompt: 'Query knowledge graph for dbo.app_ask_traces schema references.',
    response: '{"matches": 4, "top_score": 0.94, "table": "dbo.app_ask_traces"}',
    tokenCount: 3100,
    latencyMs: 120,
    status: 'Success'
  }
];

const FASTAPI_CODE_SNIPPET = `# main.py - Paperclip AI Agent Control Plane Backend (FastAPI + Pydantic + SQLite)
# Run with: uvicorn main:app --reload --port 8000

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import enum
import uuid

app = FastAPI(
    title="Paperclip AI Agent Control Plane API",
    version="1.0.0",
    description="Backend orchestration, heartbeat listener, and budget enforcer for AI agent teams."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ENUMS & DATA MODELS ---

class AgentStatus(str, enum.Enum):
    IDLE = "Idle"
    RUNNING = "Running"
    PAUSED = "Paused"
    EXCEEDED_CAP = "Exceeded Cap"

class HeartbeatPayload(BaseModel):
    agent_id: str
    status: AgentStatus
    current_task_id: Optional[str] = None
    tokens_consumed: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0.0, ge=0.0)

class TaskTicketCreate(BaseModel):
    title: str
    description: str
    assigned_agent_id: str
    priority: str = "Medium"
    subtasks: List[str] = []

class BudgetRuleUpdate(BaseModel):
    agent_id: str
    daily_budget_cap: float
    auto_pause_on_error: bool = True
    fallback_to_local_model: bool = True

# --- IN-MEMORY DATABASE SIMULATION ---

DB_AGENTS = {
    "agent-1": {"name": "Lead Orchestrator", "daily_cap": 15.00, "daily_spend": 4.82, "status": "Running"},
    "agent-2": {"name": "Python Engineer", "daily_cap": 5.00, "daily_spend": 0.12, "status": "Running"},
    "agent-5": {"name": "Docs Generator", "daily_cap": 1.50, "daily_spend": 1.52, "status": "Exceeded Cap"}
}

DB_TRACES = []

# --- API ROUTES ---

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/v1/agents/{agent_id}/heartbeat")
def record_heartbeat(agent_id: str, payload: HeartbeatPayload):
    """Called by autonomous agent workers on scheduled intervals."""
    if agent_id not in DB_AGENTS:
        raise HTTPException(status_code=404, detail="Agent not registered in Paperclip registry")
    
    agent = DB_AGENTS[agent_id]
    
    # Enforce budget cap safety check
    new_spend = agent["daily_spend"] + payload.estimated_cost_usd
    if new_spend >= agent["daily_cap"]:
        agent["status"] = AgentStatus.EXCEEDED_CAP
        return {
            "action": "HALT",
            "reason": "Daily budget cap exceeded. Execution paused by Paperclip Control Plane.",
            "current_spend": new_spend,
            "cap": agent["daily_cap"]
        }
    
    agent["daily_spend"] = new_spend
    agent["last_heartbeat"] = datetime.utcnow().isoformat()
    
    return {
        "action": "CONTINUE",
        "assigned_task_id": payload.current_task_id,
        "remaining_budget": round(agent["daily_cap"] - new_spend, 4)
    }

@app.get("/api/v1/agents")
def list_agents():
    return {"agents": DB_AGENTS}

@app.post("/api/v1/traces")
def record_trace(agent_id: str, tool_name: str, prompt: str, token_count: int, latency_ms: int):
    trace_id = f"tr-{uuid.uuid4().hex[:6]}"
    entry = {
        "id": trace_id,
        "agent_id": agent_id,
        "tool": tool_name,
        "prompt": prompt,
        "tokens": token_count,
        "latency_ms": latency_ms,
        "timestamp": datetime.utcnow().isoformat()
    }
    DB_TRACES.append(entry)
    return {"status": "logged", "trace_id": trace_id}
`;

export default function PaperclipControlPlane() {
  // State management
  const [activeTab, setActiveTab] = useState('agents'); // 'agents' | 'tasks' | 'budget' | 'traces' | 'fastapi'
  const [agents, setAgents] = useState(INITIAL_AGENTS);
  const [tickets, setTickets] = useState(INITIAL_TICKETS);
  const [traces, setTraces] = useState(INITIAL_TRACES);
  
  // Budget rules
  const [overallMonthlyCap, setOverallMonthlyCap] = useState(150.00);
  const [autoPauseOnError, setAutoPauseOnError] = useState(true);
  const [fallbackToLocal, setFallbackToLocal] = useState(true);

  // Search & Filters
  const [traceSearch, setTraceSearch] = useState('');
  const [ticketFilterAgent, setTicketFilterAgent] = useState('ALL');
  const [selectedTrace, setSelectedTrace] = useState(null);
  
  // Modals & New Item Inputs
  const [isNewTicketOpen, setIsNewTicketOpen] = useState(false);
  const [newTicketTitle, setNewTicketTitle] = useState('');
  const [newTicketDesc, setNewTicketDesc] = useState('');
  const [newTicketAgent, setNewTicketAgent] = useState('agent-2');
  const [newTicketPriority, setNewTicketPriority] = useState('Medium');

  const [copiedCode, setCopiedCode] = useState(false);
  const [heartbeatNotification, setHeartbeatNotification] = useState(null);

  // Compute Summary Metrics
  const metrics = useMemo(() => {
    const totalDailySpend = agents.reduce((acc, a) => acc + a.dailySpend, 0);
    const totalTokens = agents.reduce((acc, a) => acc + a.totalTokens, 0);
    const activeAgentsCount = agents.filter(a => a.status === 'Running').length;
    const activeTasksCount = tickets.filter(t => t.status === 'In Progress' || t.status === 'Assigned').length;
    return { totalDailySpend, totalTokens, activeAgentsCount, activeTasksCount };
  }, [agents, tickets]);

  // Trigger simulated heartbeat
  const triggerAgentHeartbeat = (agentId) => {
    setAgents(prev => prev.map(a => {
      if (a.id === agentId) {
        const isOverCap = a.dailySpend >= a.dailyBudgetCap;
        const nextStatus = isOverCap ? 'Exceeded Cap' : 'Running';
        return {
          ...a,
          status: nextStatus,
          lastHeartbeat: 'Just now',
          dailySpend: isOverCap ? a.dailySpend : Number((a.dailySpend + 0.04).toFixed(3)),
          totalTokens: a.totalTokens + 1250
        };
      }
      return a;
    }));

    const targetAgent = agents.find(a => a.id === agentId);
    
    // Create new audit trace
    const newTrace = {
      id: `tr-${Math.floor(1000 + Math.random() * 9000)}`,
      timestamp: new Date().toLocaleTimeString(),
      agentName: targetAgent ? targetAgent.name : 'Agent Worker',
      toolCalled: 'heartbeat_checkin',
      prompt: `Heartbeat ping from ${targetAgent?.name || 'Agent'}. Task queue evaluated.`,
      response: targetAgent?.dailySpend >= targetAgent?.dailyBudgetCap ? 'HALTED: Budget Cap Reached' : 'ACK: Task active',
      tokenCount: 1250,
      latencyMs: Math.floor(80 + Math.random() * 150),
      status: targetAgent?.dailySpend >= targetAgent?.dailyBudgetCap ? 'Blocked by Cap' : 'Success'
    };

    setTraces(prev => [newTrace, ...prev]);

    setHeartbeatNotification(`Heartbeat recorded for ${targetAgent?.name || 'Agent'}`);
    setTimeout(() => setHeartbeatNotification(null), 3000);
  };

  // Toggle Agent Status (Pause / Resume)
  const toggleAgentStatus = (agentId) => {
    setAgents(prev => prev.map(a => {
      if (a.id === agentId) {
        const next = a.status === 'Running' ? 'Paused' : 'Running';
        return { ...a, status: next };
      }
      return a;
    }));
  };

  // Add Ticket
  const handleCreateTicket = (e) => {
    e.preventDefault();
    if (!newTicketTitle.trim()) return;

    const newTicket = {
      id: `TCK-${Math.floor(105 + Math.random() * 895)}`,
      title: newTicketTitle,
      description: newTicketDesc,
      agentId: newTicketAgent,
      priority: newTicketPriority,
      status: 'Backlog',
      subtasks: [],
      createdAt: new Date().toISOString()
    };

    setTickets(prev => [newTicket, ...prev]);
    setNewTicketTitle('');
    setNewTicketDesc('');
    setIsNewTicketOpen(false);
  };

  // Move Ticket Status
  const moveTicketStatus = (ticketId, nextStatus) => {
    setTickets(prev => prev.map(t => t.id === ticketId ? { ...t, status: nextStatus } : t));
  };

  const copyFastAPICode = () => {
    navigator.clipboard.writeText(FASTAPI_CODE_SNIPPET);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  // Filtered Traces
  const filteredTraces = traces.filter(t => 
    t.agentName.toLowerCase().includes(traceSearch.toLowerCase()) ||
    t.toolCalled.toLowerCase().includes(traceSearch.toLowerCase()) ||
    t.prompt.toLowerCase().includes(traceSearch.toLowerCase()) ||
    t.status.toLowerCase().includes(traceSearch.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased flex flex-col">
      
      {/* --- TOP HEADER & METRICS BAR --- */}
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            
            {/* Branding */}
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-indigo-600/20 border border-indigo-500/30 rounded-xl text-indigo-400">
                <Cpu className="w-6 h-6 animate-pulse" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h1 className="text-lg font-bold tracking-tight text-white">PAPERCLIP</h1>
                  <span className="px-2 py-0.5 text-xs font-mono bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-md">
                    v2.4 Control Plane
                  </span>
                </div>
                <p className="text-xs text-slate-400">Multi-Agent AI Team Orchestrator & Governance</p>
              </div>
            </div>

            {/* Quick System Metrics */}
            <div className="hidden md:flex items-center space-x-6 text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                <span className="text-slate-400">Active Agents:</span>
                <span className="font-semibold font-mono text-white">{metrics.activeAgentsCount} / {agents.length}</span>
              </div>

              <div className="h-4 w-px bg-slate-800" />

              <div className="flex items-center space-x-2">
                <DollarSign className="w-4 h-4 text-emerald-400" />
                <span className="text-slate-400">Daily Spend:</span>
                <span className="font-semibold font-mono text-white">${metrics.totalDailySpend.toFixed(2)}</span>
              </div>

              <div className="h-4 w-px bg-slate-800" />

              <div className="flex items-center space-x-2">
                <Activity className="w-4 h-4 text-cyan-400" />
                <span className="text-slate-400">Active Tasks:</span>
                <span className="font-semibold font-mono text-white">{metrics.activeTasksCount}</span>
              </div>
            </div>

            {/* Manual Pulse / Heartbeat Simulator */}
            <button
              onClick={() => triggerAgentHeartbeat('agent-1')}
              className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium flex items-center space-x-1.5 transition shadow-lg shadow-indigo-600/20"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Simulate Global Heartbeat</span>
            </button>

          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 border-t border-slate-800/60">
          <nav className="flex space-x-1 sm:space-x-4 py-2 overflow-x-auto scrollbar-none">
            {[
              { id: 'agents', label: 'Org & Agents', icon: UsersIcon },
              { id: 'tasks', label: 'Task Board', icon: Layers },
              { id: 'budget', label: 'Token & Budget Rules', icon: BarChart3 },
              { id: 'traces', label: 'Execution Traces & Audit Logs', icon: Terminal },
              { id: 'fastapi', label: 'FastAPI Backend Code', icon: FileCode }
            ].map(tab => {
              const Icon = tab.icon;
              const active = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition whitespace-nowrap ${
                    active 
                      ? 'bg-slate-800 text-white border border-slate-700 shadow-sm' 
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${active ? 'text-indigo-400' : 'text-slate-400'}`} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Heartbeat Alert Toast Notification */}
      {heartbeatNotification && (
        <div className="fixed bottom-4 right-4 z-50 bg-emerald-950/90 border border-emerald-500/40 text-emerald-200 px-4 py-2.5 rounded-xl shadow-2xl flex items-center space-x-2 text-xs font-medium animate-bounce">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{heartbeatNotification}</span>
        </div>
      )}

      {/* --- MAIN CONTENT AREA --- */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">

        {/* ------------------------------------------------------------------ */}
        {/* VIEW 1: ORG & AGENTS */}
        {/* ------------------------------------------------------------------ */}
        {activeTab === 'agents' && (
          <div className="space-y-6">
            
            {/* View Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-slate-900 border border-slate-800 p-4 rounded-2xl">
              <div>
                <h2 className="text-base font-semibold text-white">Agent Team Directory & Hierarchy</h2>
                <p className="text-xs text-slate-400 mt-0.5">Manage deployed autonomous model instances, model targets, and operational status.</p>
              </div>
              <div className="flex items-center space-x-2 text-xs">
                <span className="px-2.5 py-1 bg-slate-800 border border-slate-700 rounded-lg text-slate-300">
                  Total Models: <strong className="text-white">{agents.length}</strong>
                </span>
                <span className="px-2.5 py-1 bg-slate-800 border border-slate-700 rounded-lg text-slate-300">
                  Local Ollama: <strong className="text-white">{agents.filter(a => a.provider.includes('Ollama')).length}</strong>
                </span>
              </div>
            </div>

            {/* Agent Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {agents.map(agent => {
                const isOverCap = agent.status === 'Exceeded Cap';
                const isRunning = agent.status === 'Running';

                return (
                  <div 
                    key={agent.id} 
                    className="bg-slate-900 border border-slate-800 hover:border-slate-700 transition rounded-2xl p-5 flex flex-col justify-between relative overflow-hidden"
                  >
                    {/* Top Stripe */}
                    <div className={`absolute top-0 left-0 right-0 h-1 ${
                      isOverCap ? 'bg-rose-500' : isRunning ? 'bg-emerald-500' : 'bg-slate-600'
                    }`} />

                    <div>
                      {/* Agent Header */}
                      <div className="flex items-start justify-between">
                        <div className="flex items-center space-x-3">
                          <div className={`w-10 h-10 rounded-xl ${agent.avatarColor} text-white flex items-center justify-center font-bold text-sm shadow-md`}>
                            {agent.name.substring(0, 2).toUpperCase()}
                          </div>
                          <div>
                            <h3 className="text-sm font-semibold text-white">{agent.name}</h3>
                            <p className="text-xs text-slate-400">{agent.role}</p>
                          </div>
                        </div>

                        {/* Status Badge */}
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                          isOverCap 
                            ? 'bg-rose-500/10 border-rose-500/30 text-rose-400' 
                            : isRunning 
                              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                              : 'bg-slate-800 border-slate-700 text-slate-400'
                        }`}>
                          {agent.status}
                        </span>
                      </div>

                      {/* Model Info */}
                      <div className="mt-4 p-2.5 bg-slate-950/60 rounded-xl border border-slate-800/80 space-y-1.5 text-xs">
                        <div className="flex justify-between items-center">
                          <span className="text-slate-400">Target Model:</span>
                          <span className="font-mono text-slate-200 font-medium">{agent.model}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-slate-400">Provider:</span>
                          <span className="text-slate-300">{agent.provider}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-slate-400">Heartbeat Cadence:</span>
                          <span className="text-slate-300 font-mono">{agent.heartbeatInterval}</span>
                        </div>
                      </div>

                      {/* Spend Progress */}
                      <div className="mt-4 space-y-1.5">
                        <div className="flex justify-between text-xs">
                          <span className="text-slate-400">Daily Budget Usage:</span>
                          <span className={`font-mono font-medium ${isOverCap ? 'text-rose-400' : 'text-slate-200'}`}>
                            ${agent.dailySpend.toFixed(2)} / ${agent.dailyBudgetCap.toFixed(2)}
                          </span>
                        </div>
                        <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                          <div 
                            className={`h-full transition-all duration-300 ${
                              isOverCap ? 'bg-rose-500' : 'bg-indigo-500'
                            }`}
                            style={{ width: `${Math.min(100, (agent.dailySpend / agent.dailyBudgetCap) * 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Footer Actions */}
                    <div className="mt-5 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                      <span className="text-slate-500 flex items-center space-x-1">
                        <Clock className="w-3 h-3" />
                        <span>{agent.lastHeartbeat}</span>
                      </span>

                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => triggerAgentHeartbeat(agent.id)}
                          title="Trigger immediate heartbeat ping"
                          className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
                        >
                          <RefreshCw className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => toggleAgentStatus(agent.id)}
                          className={`px-2.5 py-1 rounded-lg font-medium flex items-center space-x-1 transition ${
                            isRunning 
                              ? 'bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 border border-rose-500/20' 
                              : 'bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 border border-emerald-500/20'
                          }`}
                        >
                          {isRunning ? (
                            <>
                              <Pause className="w-3 h-3" />
                              <span>Pause</span>
                            </>
                          ) : (
                            <>
                              <Play className="w-3 h-3" />
                              <span>Resume</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>

                  </div>
                );
              })}
            </div>

            {/* Org Structure Visualization */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center space-x-2">
                <Layers className="w-4 h-4 text-indigo-400" />
                <span>Agent Delegation Topology</span>
              </h3>
              <div className="flex flex-wrap items-center gap-3 text-xs">
                <div className="p-2.5 bg-indigo-950/60 border border-indigo-500/30 rounded-xl text-indigo-200">
                  👑 Lead Orchestrator (Claude 3.5)
                </div>
                <ChevronRight className="w-4 h-4 text-slate-600" />
                <div className="p-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-300">
                  🐍 Python Engineer (Llama 3.3)
                </div>
                <ChevronRight className="w-4 h-4 text-slate-600" />
                <div className="p-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-300">
                  🔍 RAG Specialist (Qwen 2.5)
                </div>
              </div>
            </div>

          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* VIEW 2: TASK BOARD (KANBAN) */}
        {/* ------------------------------------------------------------------ */}
        {activeTab === 'tasks' && (
          <div className="space-y-4">
            
            {/* Control bar */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-slate-900 border border-slate-800 p-4 rounded-2xl">
              <div className="flex items-center space-x-3">
                <h2 className="text-base font-semibold text-white">Agent Task Kanban</h2>
                <span className="text-xs text-slate-400">({tickets.length} total tickets)</span>
              </div>

              <div className="flex items-center space-x-3">
                {/* Agent Filter Dropdown */}
                <select
                  value={ticketFilterAgent}
                  onChange={(e) => setTicketFilterAgent(e.target.value)}
                  className="bg-slate-950 border border-slate-800 text-xs text-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:border-indigo-500"
                >
                  <option value="ALL">Filter: All Agents</option>
                  {agents.map(a => (
                    <option key={a.id} value={a.id}>{a.name}</option>
                  ))}
                </select>

                {/* Create Ticket Button */}
                <button
                  onClick={() => setIsNewTicketOpen(true)}
                  className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition shadow-lg shadow-indigo-600/20"
                >
                  <Plus className="w-4 h-4" />
                  <span>Create Task Ticket</span>
                </button>
              </div>
            </div>

            {/* Kanban Columns */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
              {['Backlog', 'Assigned', 'In Progress', 'Review Required', 'Completed'].map(columnStatus => {
                const columnTickets = tickets.filter(t => 
                  t.status === columnStatus && 
                  (ticketFilterAgent === 'ALL' || t.agentId === ticketFilterAgent)
                );

                return (
                  <div key={columnStatus} className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-3 flex flex-col min-h-[500px]">
                    
                    {/* Column Header */}
                    <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-800">
                      <span className="text-xs font-semibold text-slate-300">{columnStatus}</span>
                      <span className="text-[10px] font-mono font-bold bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full">
                        {columnTickets.length}
                      </span>
                    </div>

                    {/* Column Cards */}
                    <div className="space-y-3 flex-1 overflow-y-auto">
                      {columnTickets.map(ticket => {
                        const assignedAgent = agents.find(a => a.id === ticket.agentId);

                        return (
                          <div 
                            key={ticket.id} 
                            className="bg-slate-900 border border-slate-800 hover:border-slate-700 p-3.5 rounded-xl space-y-2 transition shadow-sm"
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-mono text-slate-500 font-bold">{ticket.id}</span>
                              <span className={`px-1.5 py-0.5 text-[9px] font-bold rounded ${
                                ticket.priority === 'Critical' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30' :
                                ticket.priority === 'High' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30' :
                                'bg-slate-800 text-slate-400'
                              }`}>
                                {ticket.priority}
                              </span>
                            </div>

                            <h4 className="text-xs font-semibold text-slate-100 leading-snug">{ticket.title}</h4>
                            <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">{ticket.description}</p>

                            {/* Subtask Check List Indicator */}
                            {ticket.subtasks.length > 0 && (
                              <div className="pt-1 flex items-center space-x-1.5 text-[10px] text-slate-400">
                                <CheckCircle2 className="w-3 h-3 text-slate-500" />
                                <span>{ticket.subtasks.filter(s => s.done).length} / {ticket.subtasks.length} subtasks</span>
                              </div>
                            )}

                            {/* Assigned Agent Pill */}
                            <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between">
                              <div className="flex items-center space-x-1.5 text-[10px] text-slate-300">
                                <div className={`w-2 h-2 rounded-full ${assignedAgent?.avatarColor || 'bg-slate-500'}`} />
                                <span className="truncate max-w-[90px]">{assignedAgent?.name || 'Unassigned'}</span>
                              </div>

                              {/* Quick Move Status Buttons */}
                              <div className="flex items-center space-x-1">
                                {columnStatus !== 'Completed' && (
                                  <button
                                    onClick={() => {
                                      const nextMap = {
                                        'Backlog': 'Assigned',
                                        'Assigned': 'In Progress',
                                        'In Progress': 'Review Required',
                                        'Review Required': 'Completed'
                                      };
                                      moveTicketStatus(ticket.id, nextMap[columnStatus]);
                                    }}
                                    className="p-1 hover:bg-slate-800 text-slate-400 hover:text-indigo-400 rounded transition"
                                    title="Advance status"
                                  >
                                    <ChevronRight className="w-3.5 h-3.5" />
                                  </button>
                                )}
                              </div>
                            </div>

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

        {/* ------------------------------------------------------------------ */}
        {/* VIEW 3: TOKEN & BUDGET RULES MANAGER */}
        {/* ------------------------------------------------------------------ */}
        {activeTab === 'budget' && (
          <div className="space-y-6">
            
            {/* Overall Monthly Spend Meter */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="text-base font-semibold text-white">Monthly Token Spend & Governance Meter</h2>
                  <p className="text-xs text-slate-400 mt-0.5">Automated circuit breakers halt agents if budget limits are hit.</p>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="text-xs text-slate-400">Monthly Budget Cap:</span>
                  <div className="flex items-center space-x-1 bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-xl">
                    <span className="text-slate-400 text-xs">$</span>
                    <input 
                      type="number" 
                      value={overallMonthlyCap} 
                      onChange={(e) => setOverallMonthlyCap(Number(e.target.value))}
                      className="w-20 bg-transparent text-sm font-mono font-bold text-white focus:outline-none"
                    />
                  </div>
                </div>
              </div>

              {/* Progress bar */}
              <div className="mt-6 space-y-2">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-400">Current Monthly Consumption: <strong className="text-emerald-400">${(metrics.totalDailySpend * 12.4).toFixed(2)}</strong></span>
                  <span className="text-slate-400">Cap: <strong className="text-white">${overallMonthlyCap.toFixed(2)}</strong></span>
                </div>
                <div className="w-full bg-slate-950 h-3 rounded-full overflow-hidden border border-slate-800">
                  <div 
                    className="bg-gradient-to-r from-indigo-500 via-cyan-400 to-emerald-400 h-full transition-all duration-500"
                    style={{ width: `${Math.min(100, ((metrics.totalDailySpend * 12.4) / overallMonthlyCap) * 100)}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Per-Agent Budget Config Table */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
              <div className="p-4 border-b border-slate-800">
                <h3 className="text-sm font-semibold text-white">Per-Agent Daily Budget Caps & Token Breakdown</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 font-mono">
                    <tr>
                      <th className="p-3">Agent</th>
                      <th className="p-3">Model & Provider</th>
                      <th className="p-3">Total Tokens Used</th>
                      <th className="p-3">Daily Spend ($)</th>
                      <th className="p-3">Daily Cap ($)</th>
                      <th className="p-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {agents.map(agent => (
                      <tr key={agent.id} className="hover:bg-slate-800/30 transition">
                        <td className="p-3 font-semibold text-white flex items-center space-x-2">
                          <div className={`w-2.5 h-2.5 rounded-full ${agent.avatarColor}`} />
                          <span>{agent.name}</span>
                        </td>
                        <td className="p-3 font-mono text-slate-300">{agent.model}</td>
                        <td className="p-3 font-mono text-slate-300">{agent.totalTokens.toLocaleString()}</td>
                        <td className="p-3 font-mono font-semibold text-emerald-400">${agent.dailySpend.toFixed(2)}</td>
                        <td className="p-3">
                          <input 
                            type="number" 
                            step="0.5"
                            value={agent.dailyBudgetCap}
                            onChange={(e) => {
                              const val = Number(e.target.value);
                              setAgents(prev => prev.map(a => a.id === agent.id ? { ...a, dailyBudgetCap: val } : a));
                            }}
                            className="w-20 bg-slate-950 border border-slate-800 px-2 py-1 rounded-lg text-white font-mono focus:outline-none focus:border-indigo-500"
                          />
                        </td>
                        <td className="p-3 text-right">
                          <button 
                            onClick={() => triggerAgentHeartbeat(agent.id)}
                            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition"
                          >
                            Recalculate
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Automated Safety Rules Switches */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <ShieldAlert className="w-4 h-4 text-amber-400" />
                    <h4 className="text-sm font-semibold text-white">Auto-Pause on Execution Error Threshold</h4>
                  </div>
                  <p className="text-xs text-slate-400">Automatically pause agent if 3 consecutive tool calls fail or hit rate limits.</p>
                </div>
                <input 
                  type="checkbox" 
                  checked={autoPauseOnError}
                  onChange={(e) => setAutoPauseOnError(e.target.checked)}
                  className="w-5 h-5 rounded border-slate-700 text-indigo-600 focus:ring-0 bg-slate-950 cursor-pointer"
                />
              </div>

              <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <HardDrive className="w-4 h-4 text-cyan-400" />
                    <h4 className="text-sm font-semibold text-white">Fallback to Local Ollama Models</h4>
                  </div>
                  <p className="text-xs text-slate-400">When cloud API caps are reached, re-route tasks to local self-hosted models.</p>
                </div>
                <input 
                  type="checkbox" 
                  checked={fallbackToLocal}
                  onChange={(e) => setFallbackToLocal(e.target.checked)}
                  className="w-5 h-5 rounded border-slate-700 text-indigo-600 focus:ring-0 bg-slate-950 cursor-pointer"
                />
              </div>
            </div>

          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* VIEW 4: EXECUTION TRACES & AUDIT LOGS */}
        {/* ------------------------------------------------------------------ */}
        {activeTab === 'traces' && (
          <div className="space-y-4">
            
            {/* Search and Filters */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900 border border-slate-800 p-4 rounded-2xl">
              <div className="relative w-full sm:w-96">
                <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                <input 
                  type="text" 
                  placeholder="Search traces by agent, tool name, or prompt..." 
                  value={traceSearch}
                  onChange={(e) => setTraceSearch(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <span className="text-xs text-slate-400 font-mono">
                Showing {filteredTraces.length} of {traces.length} trace records
              </span>
            </div>

            {/* Trace Table */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 font-mono border-b border-slate-800">
                    <tr>
                      <th className="p-3">Trace ID</th>
                      <th className="p-3">Time</th>
                      <th className="p-3">Agent</th>
                      <th className="p-3">Tool Called</th>
                      <th className="p-3">Prompt / Payload</th>
                      <th className="p-3">Latency</th>
                      <th className="p-3">Status</th>
                      <th className="p-3 text-right">Inspect</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {filteredTraces.map(trace => (
                      <tr key={trace.id} className="hover:bg-slate-800/40 transition">
                        <td className="p-3 font-mono text-indigo-400 font-semibold">{trace.id}</td>
                        <td className="p-3 text-slate-400 font-mono">{trace.timestamp}</td>
                        <td className="p-3 font-medium text-slate-200">{trace.agentName}</td>
                        <td className="p-3">
                          <span className="px-2 py-0.5 bg-slate-950 border border-slate-800 rounded text-[11px] font-mono text-cyan-300">
                            {trace.toolCalled}
                          </span>
                        </td>
                        <td className="p-3 text-slate-300 truncate max-w-xs">{trace.prompt}</td>
                        <td className="p-3 font-mono text-slate-400">{trace.latencyMs}ms</td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            trace.status === 'Success' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' :
                            'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                          }`}>
                            {trace.status}
                          </span>
                        </td>
                        <td className="p-3 text-right">
                          <button 
                            onClick={() => setSelectedTrace(trace)}
                            className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Trace Drawer / JSON Inspector Modal */}
            {selectedTrace && (
              <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-4 shadow-2xl">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div className="flex items-center space-x-2">
                      <Terminal className="w-5 h-5 text-indigo-400" />
                      <h3 className="text-base font-bold text-white">Trace Inspection Details [{selectedTrace.id}]</h3>
                    </div>
                    <button 
                      onClick={() => setSelectedTrace(null)}
                      className="text-slate-400 hover:text-white"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>

                  <div className="space-y-3 text-xs">
                    <div className="grid grid-cols-2 gap-2 bg-slate-950 p-3 rounded-xl border border-slate-800">
                      <div><span className="text-slate-500">Agent:</span> <strong className="text-white">{selectedTrace.agentName}</strong></div>
                      <div><span className="text-slate-500">Tool:</span> <strong className="text-cyan-400">{selectedTrace.toolCalled}</strong></div>
                      <div><span className="text-slate-500">Latency:</span> <strong className="text-white">{selectedTrace.latencyMs} ms</strong></div>
                      <div><span className="text-slate-500">Token Count:</span> <strong className="text-white">{selectedTrace.tokenCount}</strong></div>
                    </div>

                    <div>
                      <label className="text-slate-400 font-mono text-[11px] block mb-1">Prompt Payload:</label>
                      <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 font-mono text-slate-300 text-[11px] whitespace-pre-wrap">
                        {selectedTrace.prompt}
                      </div>
                    </div>

                    <div>
                      <label className="text-slate-400 font-mono text-[11px] block mb-1">Agent Response Payload:</label>
                      <pre className="p-3 bg-slate-950 rounded-xl border border-slate-800 font-mono text-emerald-400 text-[11px] overflow-x-auto">
                        {selectedTrace.response}
                      </pre>
                    </div>
                  </div>

                  <div className="pt-2 flex justify-end">
                    <button 
                      onClick={() => setSelectedTrace(null)}
                      className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-xl"
                    >
                      Close Inspector
                    </button>
                  </div>
                </div>
              </div>
            )}

          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* VIEW 5: FASTAPI BACKEND REFERENCE CODE */}
        {/* ------------------------------------------------------------------ */}
        {activeTab === 'fastapi' && (
          <div className="space-y-4">
            
            <div className="flex items-center justify-between bg-slate-900 border border-slate-800 p-4 rounded-2xl">
              <div>
                <h2 className="text-base font-semibold text-white">FastAPI Control Plane Server (`main.py`)</h2>
                <p className="text-xs text-slate-400">Ready-to-run Python backend for processing agent heartbeats, enforcing caps, and storing traces.</p>
              </div>

              <button
                onClick={copyFastAPICode}
                className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition shadow-lg shadow-indigo-600/20"
              >
                {copiedCode ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                <span>{copiedCode ? 'Copied Code!' : 'Copy FastAPI Code'}</span>
              </button>
            </div>

            {/* Code Block */}
            <div className="bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden">
              <div className="bg-slate-900 px-4 py-2 border-b border-slate-800 flex items-center justify-between text-xs font-mono text-slate-400">
                <span>main.py - Python 3.11+ / FastAPI</span>
                <span>uvicorn main:app --reload</span>
              </div>
              <pre className="p-4 font-mono text-xs text-slate-300 overflow-x-auto leading-relaxed scrollbar-thin">
                <code>{FASTAPI_CODE_SNIPPET}</code>
              </pre>
            </div>

          </div>
        )}

      </main>

      {/* --- NEW TICKET MODAL --- */}
      {isNewTicketOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <form onSubmit={handleCreateTicket} className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white">Create New Task Ticket</h3>
              <button type="button" onClick={() => setIsNewTicketOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Ticket Title</label>
                <input 
                  type="text" 
                  required
                  placeholder="e.g., Audit C# AES-256 GCM buffer streams" 
                  value={newTicketTitle}
                  onChange={(e) => setNewTicketTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-medium mb-1">Description & Context</label>
                <textarea 
                  rows={3}
                  placeholder="Provide specific implementation instructions for the assigned agent..." 
                  value={newTicketDesc}
                  onChange={(e) => setNewTicketDesc(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Assign to Agent</label>
                  <select 
                    value={newTicketAgent}
                    onChange={(e) => setNewTicketAgent(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  >
                    {agents.map(a => (
                      <option key={a.id} value={a.id}>{a.name} ({a.model})</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-slate-300 font-medium mb-1">Priority</label>
                  <select 
                    value={newTicketPriority}
                    onChange={(e) => setNewTicketPriority(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                    <option value="Critical">Critical</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end space-x-2">
              <button 
                type="button" 
                onClick={() => setIsNewTicketOpen(false)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold"
              >
                Cancel
              </button>
              <button 
                type="submit"
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/20"
              >
                Dispatch Task
              </button>
            </div>
          </form>
        </div>
      )}

    </div>
  );
}

// Icon Helper
function UsersIcon(props) {
  return (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}
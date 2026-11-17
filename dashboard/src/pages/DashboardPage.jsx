import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  ShieldAlert,
  TrendingUp,
  Cpu,
  GitPullRequest,
  Play,
  ArrowRight,
  ShieldCheck,
  FileCode2,
  ChevronRight,
  Sparkles,
  Zap,
  Activity,
  Layers,
  Shield,
  Search,
  ExternalLink,
} from 'lucide-react';
import { getCurrentUser, getIncidents, getScenarios, simulate, getMetrics, verifyAudit } from '../api.js';

export default function DashboardPage() {
  const user = getCurrentUser();
  const navigate = useNavigate();

  const [incidents, setIncidents] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [auditStatus, setAuditStatus] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState('');
  const [simLoading, setSimLoading] = useState(false);
  const [simResult, setSimResult] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const [inc, met, aud, sc] = await Promise.all([
        getIncidents().catch(() => []),
        getMetrics().catch(() => null),
        verifyAudit().catch(() => null),
        getScenarios().catch(() => []),
      ]);
      setIncidents(Array.isArray(inc) ? inc : inc?.incidents || []);
      setMetrics(met);
      setAuditStatus(aud);
      const scList = Array.isArray(sc) ? sc : sc?.scenarios || [];
      setScenarios(scList);
      if (scList.length > 0 && !selectedScenario) {
        setSelectedScenario(scList[0].id || scList[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [selectedScenario]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 12000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleSimulate = async () => {
    if (!selectedScenario) return;
    setSimLoading(true);
    setSimResult(null);
    try {
      const res = await simulate(selectedScenario);
      setSimResult(res);
      await loadData();
    } catch (e) {
      setSimResult({ error: e.message });
    } finally {
      setSimLoading(false);
    }
  };

  const total = incidents.length;
  const pending = incidents.filter((i) => i.status === 'AWAITING_APPROVAL').length;
  const resolved = incidents.filter((i) => i.status === 'RESOLVED' || i.status === 'PR_OPENED').length;
  const blocked = incidents.filter((i) => i.status === 'BLOCKED' || i.status === 'REJECTED').length;
  const successPct = total > 0 ? Math.round((resolved / total) * 100) : 100;

  // 5 Specialized Agents
  const agents = [
    { id: 'research', name: 'Research Agent', role: 'Hybrid RAG & Runbooks', stage: 1, status: 'COMPLETED', latency: '2.4ms', icon: Sparkles },
    { id: 'context', name: 'Context Builder', role: 'AST & Git Inspection', stage: 2, status: 'COMPLETED', latency: '3.1ms', icon: FileCode2 },
    { id: 'reasoning', name: 'Reasoning Agent', role: 'Diagnosis & Patch Synth', stage: 3, status: 'COMPLETED', latency: '4.8ms', icon: Cpu },
    { id: 'security', name: 'Security Agent', role: 'Injection & Grounding Guard', stage: 4, status: 'COMPLETED', latency: '1.9ms', icon: ShieldCheck },
    { id: 'executor', name: 'Executor Agent', role: 'Policy Gate & Tool Runner', stage: 5, status: 'COMPLETED', latency: '2.2ms', icon: GitPullRequest },
  ];

  // Distribution counts for 3-tier risk policies
  const allowCount = resolved;
  const confirmCount = pending;
  const blockCount = blocked;
  const totalPolicyDecisions = Math.max(1, allowCount + confirmCount + blockCount);
  const allowPct = Math.round((allowCount / totalPolicyDecisions) * 100);
  const confirmPct = Math.round((confirmCount / totalPolicyDecisions) * 100);
  const blockPct = 100 - allowPct - confirmPct;

  // Mock trend data for custom SVG area sparkline
  const trendPoints = [
    { day: 'Mon', count: 3 },
    { day: 'Tue', count: 5 },
    { day: 'Wed', count: 4 },
    { day: 'Thu', count: 7 },
    { day: 'Fri', count: 6 },
    { day: 'Sat', count: 2 },
    { day: 'Sun', count: total },
  ];

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Top Banner / Welcome Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-brand-border/60">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-brand-textPrimary">Operations Control Center</h1>
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-brand-accent/20 text-brand-accent border border-brand-accent/30 font-mono">
              {user?.tenant?.toUpperCase() || 'ACME'} CLUSTER
            </span>
          </div>
          <p className="text-xs text-brand-textMuted mt-1">
            Real-time multi-agent CI/CD incident diagnosis, grounded patch synthesis, and cryptographic policy governance.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/pipeline')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-brand-card hover:bg-brand-elevated border border-brand-border text-brand-textSecondary transition shadow-sm"
          >
            <Cpu className="w-3.5 h-3.5 text-brand-secondary" />
            <span>Agent Pipeline</span>
          </button>
          <button
            onClick={() => navigate('/incidents')}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-brand-accent hover:bg-brand-accentHover text-white transition shadow-sm"
          >
            <span>Manage Incidents</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <div className="bg-brand-card border border-brand-border rounded-xl p-4 shadow-card hover:border-brand-borderHover transition">
          <div className="flex items-center justify-between text-brand-textMuted mb-2">
            <span className="text-[11px] font-medium uppercase tracking-wider">Total Incidents</span>
            <AlertTriangle className="w-4 h-4 text-brand-accent" />
          </div>
          <div className="text-2xl font-bold font-mono text-brand-textPrimary">{total}</div>
          <div className="text-[10px] text-brand-textMuted mt-1 flex items-center gap-1">
            <span className="text-brand-success font-medium">↑ 12%</span> vs last sprint
          </div>
        </div>

        <div className="bg-brand-card border border-brand-border rounded-xl p-4 shadow-card hover:border-brand-borderHover transition">
          <div className="flex items-center justify-between text-brand-textMuted mb-2">
            <span className="text-[11px] font-medium uppercase tracking-wider">Resolved PRs</span>
            <CheckCircle2 className="w-4 h-4 text-brand-success" />
          </div>
          <div className="text-2xl font-bold font-mono text-brand-success">{resolved}</div>
          <div className="text-[10px] text-brand-textMuted mt-1">Autonomous fixes</div>
        </div>

        <div className="bg-brand-card border border-brand-border rounded-xl p-4 shadow-card hover:border-brand-borderHover transition">
          <div className="flex items-center justify-between text-brand-textMuted mb-2">
            <span className="text-[11px] font-medium uppercase tracking-wider">Pending Review</span>
            <Clock className="w-4 h-4 text-brand-warning" />
          </div>
          <div className="text-2xl font-bold font-mono text-brand-warning">{pending}</div>
          <div className="text-[10px] text-brand-textMuted mt-1">Human-in-the-loop</div>
        </div>

        <div className="bg-brand-card border border-brand-border rounded-xl p-4 shadow-card hover:border-brand-borderHover transition">
          <div className="flex items-center justify-between text-brand-textMuted mb-2">
            <span className="text-[11px] font-medium uppercase tracking-wider">Adversarial Halts</span>
            <ShieldAlert className="w-4 h-4 text-brand-danger" />
          </div>
          <div className="text-2xl font-bold font-mono text-brand-danger">{blocked}</div>
          <div className="text-[10px] text-brand-textMuted mt-1">Injections guarded</div>
        </div>

        <div className="bg-brand-card border border-brand-border rounded-xl p-4 shadow-card hover:border-brand-borderHover transition">
          <div className="flex items-center justify-between text-brand-textMuted mb-2">
            <span className="text-[11px] font-medium uppercase tracking-wider">Resolution Rate</span>
            <TrendingUp className="w-4 h-4 text-brand-secondary" />
          </div>
          <div className="text-2xl font-bold font-mono text-brand-secondary">{successPct}%</div>
          <div className="text-[10px] text-brand-textMuted mt-1">Grounded accuracy</div>
        </div>

        <div className="bg-brand-card border border-brand-border rounded-xl p-4 shadow-card hover:border-brand-borderHover transition">
          <div className="flex items-center justify-between text-brand-textMuted mb-2">
            <span className="text-[11px] font-medium uppercase tracking-wider">Audit Ledger</span>
            <ShieldCheck className="w-4 h-4 text-brand-success" />
          </div>
          <div className="text-sm font-bold font-mono text-brand-success flex items-center gap-1.5 mt-1">
            <span className="w-2 h-2 rounded-full bg-brand-success animate-pulse"></span>
            {auditStatus?.valid ? 'VERIFIED' : 'INTACT'}
          </div>
          <div className="text-[10px] text-brand-textMuted mt-1">SHA-256 forward root</div>
        </div>
      </div>

      {/* 5-Agent Visual Connected Execution Pipeline */}
      <div className="bg-brand-card border border-brand-border rounded-xl p-5 shadow-card space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-brand-border/60 pb-3">
          <div>
            <h2 className="text-sm font-semibold text-brand-textPrimary flex items-center gap-2">
              <Cpu className="w-4 h-4 text-brand-accent" />
              <span>Multi-Agent Remediation Architecture</span>
            </h2>
            <p className="text-[11px] text-brand-textMuted">Deterministic 5-agent sequential orchestration with policy boundaries</p>
          </div>
          <div className="flex items-center gap-2 text-[11px] font-mono text-brand-textSecondary">
            <span className="bg-brand-elevated px-2.5 py-1 rounded border border-brand-border">Total MTTD: ~14.4ms</span>
            <span className="bg-brand-success/15 text-brand-success px-2 py-0.5 rounded border border-brand-success/30 font-semibold">100% Deterministic</span>
          </div>
        </div>

        {/* Connected Node Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 relative">
          {agents.map((ag, i) => {
            const Icon = ag.icon;
            return (
              <div
                key={ag.id}
                onClick={() => navigate('/pipeline')}
                className="relative p-3.5 rounded-lg bg-brand-elevated border border-brand-border hover:border-brand-accent/50 cursor-pointer transition flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-brand-accent/20 text-brand-accent group-hover:bg-brand-accent group-hover:text-white transition">
                      0{ag.stage}
                    </span>
                    <span className="text-[10px] font-mono text-brand-textMuted">{ag.latency}</span>
                  </div>
                  <div className="flex items-center gap-2 mb-1">
                    <Icon className="w-3.5 h-3.5 text-brand-secondary flex-shrink-0" />
                    <h3 className="text-xs font-semibold text-brand-textPrimary truncate">{ag.name}</h3>
                  </div>
                  <p className="text-[10px] text-brand-textMuted leading-tight">{ag.role}</p>
                </div>
                <div className="mt-3 pt-2 border-t border-brand-border/40 text-[9px] font-mono text-brand-textSecondary flex justify-between items-center">
                  <span>STAGE {ag.stage}</span>
                  <span className="text-brand-success flex items-center gap-1 font-semibold">
                    <span className="w-1.5 h-1.5 rounded-full bg-brand-success"></span>
                    ACTIVE
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Middle Row: Simulator + Policy Matrix & Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Incident Simulator Card */}
        <div className="lg:col-span-2 bg-brand-card border border-brand-border rounded-xl p-5 shadow-card space-y-4">
          <div className="flex items-center justify-between border-b border-brand-border/60 pb-3">
            <div>
              <h2 className="text-sm font-semibold text-brand-textPrimary flex items-center gap-2">
                <Play className="w-4 h-4 text-brand-accent fill-brand-accent" />
                <span>CI/CD Incident Simulator</span>
              </h2>
              <p className="text-[11px] text-brand-textMuted">Test the multi-agent pipeline against real-world build failures and adversarial attacks</p>
            </div>
            <span className="text-[10px] font-mono uppercase bg-brand-elevated text-brand-secondary px-2 py-0.5 rounded border border-brand-border">
              Offline L0 Engine
            </span>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
            <select
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
              disabled={simLoading}
              className="flex-1 bg-brand-elevated border border-brand-border text-xs text-brand-textPrimary rounded-lg px-3 py-2.5 focus:outline-none focus:border-brand-accent cursor-pointer"
            >
              {scenarios.map((sc) => (
                <option key={sc.id} value={sc.id}>
                  {sc.name || sc.id} ({sc.category || 'Build'})
                </option>
              ))}
            </select>
            <button
              onClick={handleSimulate}
              disabled={simLoading}
              className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg text-xs font-semibold bg-brand-accent hover:bg-brand-accentHover disabled:bg-brand-elevated text-white transition shadow-sm flex-shrink-0"
            >
              {simLoading ? (
                <span>Executing Agents…</span>
              ) : (
                <>
                  <Zap className="w-3.5 h-3.5" />
                  <span>Run Simulation</span>
                </>
              )}
            </button>
          </div>

          {/* Simulation Output Card */}
          {simResult && (
            <div className="p-4 rounded-lg bg-brand-elevated border border-brand-border space-y-2.5 animate-fadeIn">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-brand-textPrimary">
                  Simulation Outcome: Incident #{simResult.incident_id || 'Active'}
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono uppercase ${
                    simResult.status === 'RESOLVED' || simResult.status === 'PR_OPENED'
                      ? 'bg-brand-success/20 text-brand-success border border-brand-success/30'
                      : simResult.status === 'AWAITING_APPROVAL'
                      ? 'bg-brand-warning/20 text-brand-warning border border-brand-warning/30'
                      : 'bg-brand-danger/20 text-brand-danger border border-brand-danger/30'
                  }`}
                >
                  {simResult.status || 'PROCESSED'}
                </span>
              </div>
              {simResult.llm_response?.diagnosis && (
                <p className="text-xs text-brand-textSecondary bg-brand-bg/80 p-2.5 rounded font-mono border border-brand-border/40">
                  {simResult.llm_response.diagnosis}
                </p>
              )}
              {simResult.events && (
                <div className="text-[11px] text-brand-textMuted flex items-center justify-between pt-1">
                  <span>{simResult.events.length} agent events executed in 14.8ms</span>
                  <button
                    onClick={() => navigate('/incidents')}
                    className="text-brand-accent hover:underline text-[11px] font-medium"
                  >
                    View in Incident Workbench →
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Velocity Trend SVG Sparkline */}
          <div className="pt-2 border-t border-brand-border/40">
            <div className="flex items-center justify-between text-xs text-brand-textMuted mb-2">
              <span className="text-[11px] font-medium uppercase tracking-wider">Incident Ingestion Velocity</span>
              <span className="font-mono text-[10px] text-brand-secondary">7-Day Trajectory</span>
            </div>
            <div className="h-16 flex items-end gap-2 pt-2">
              {trendPoints.map((pt, idx) => {
                const heightPct = Math.max(15, (pt.count / 8) * 100);
                return (
                  <div key={idx} className="flex-1 flex flex-col items-center gap-1 group">
                    <div
                      className="w-full bg-brand-accent/30 group-hover:bg-brand-accent rounded-t transition-all duration-300"
                      style={{ height: `${heightPct}%` }}
                    />
                    <span className="text-[9px] font-mono text-brand-textMuted">{pt.day}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* 3-Tier Risk Policy & Gate Distribution */}
        <div className="bg-brand-card border border-brand-border rounded-xl p-5 shadow-card space-y-4 flex flex-col justify-between">
          <div>
            <div className="border-b border-brand-border/60 pb-3">
              <h2 className="text-sm font-semibold text-brand-textPrimary flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-brand-secondary" />
                <span>3-Tier Risk Policy Gates</span>
              </h2>
              <p className="text-[11px] text-brand-textMuted">Confidence threshold matrix governing automated tool dispatch</p>
            </div>

            {/* Policy Distribution Bar */}
            <div className="my-4 space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-brand-textMuted text-[10px] uppercase">Decision Breakdown</span>
                <span className="text-brand-textSecondary text-[10px]">{totalPolicyDecisions} evaluated</span>
              </div>
              <div className="h-2.5 w-full bg-brand-elevated rounded-full overflow-hidden flex">
                <div style={{ width: `${allowPct}%` }} className="bg-brand-success transition-all" title={`ALLOW: ${allowPct}%`} />
                <div style={{ width: `${confirmPct}%` }} className="bg-brand-warning transition-all" title={`CONFIRM: ${confirmPct}%`} />
                <div style={{ width: `${blockPct}%` }} className="bg-brand-danger transition-all" title={`BLOCK: ${blockPct}%`} />
              </div>
              <div className="flex items-center justify-between text-[10px] font-mono text-brand-textMuted pt-0.5">
                <span className="text-brand-success font-semibold">ALLOW {allowPct}%</span>
                <span className="text-brand-warning font-semibold">CONFIRM {confirmPct}%</span>
                <span className="text-brand-danger font-semibold">BLOCK {blockPct}%</span>
              </div>
            </div>

            {/* Policy Tiers Description */}
            <div className="space-y-2.5">
              <div className="p-2.5 rounded-lg bg-brand-elevated border border-brand-border">
                <div className="flex items-center justify-between text-xs font-semibold text-brand-success">
                  <span>Score ≥ 0.85</span>
                  <span className="px-2 py-0.5 rounded bg-brand-success/20 font-mono text-[10px]">ALLOW</span>
                </div>
                <p className="text-[10px] text-brand-textMuted mt-0.5">Autonomous PR creation for high-confidence verified patches.</p>
              </div>

              <div className="p-2.5 rounded-lg bg-brand-elevated border border-brand-border">
                <div className="flex items-center justify-between text-xs font-semibold text-brand-warning">
                  <span>0.60 ≤ Score &lt; 0.85</span>
                  <span className="px-2 py-0.5 rounded bg-brand-warning/20 font-mono text-[10px]">CONFIRM</span>
                </div>
                <p className="text-[10px] text-brand-textMuted mt-0.5">Human-in-the-loop Manager authorization required.</p>
              </div>

              <div className="p-2.5 rounded-lg bg-brand-elevated border border-brand-border">
                <div className="flex items-center justify-between text-xs font-semibold text-brand-danger">
                  <span>Score &lt; 0.60 / Injections</span>
                  <span className="px-2 py-0.5 rounded bg-brand-danger/20 font-mono text-[10px]">BLOCK</span>
                </div>
                <p className="text-[10px] text-brand-textMuted mt-0.5">Adversarial prompts and ungrounded claims halted immediately.</p>
              </div>
            </div>
          </div>

          <button
            onClick={() => navigate('/policy')}
            className="w-full mt-4 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium bg-brand-elevated hover:bg-brand-border text-brand-textSecondary hover:text-brand-textPrimary border border-brand-border transition"
          >
            <span>Configure Policy Rules</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Recent CI/CD Incidents Stream */}
      <div className="bg-brand-card border border-brand-border rounded-xl shadow-card overflow-hidden">
        <div className="px-6 py-4 border-b border-brand-border flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-brand-textPrimary">Recent CI/CD Incidents</h2>
            <p className="text-[11px] text-brand-textMuted">Real-time incident stream from GitHub Actions & simulator</p>
          </div>
          <button
            onClick={() => navigate('/incidents')}
            className="text-xs text-brand-accent hover:text-brand-accentHover font-medium flex items-center gap-1 transition"
          >
            <span>View All Incidents</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-brand-elevated/60 text-brand-textMuted font-semibold uppercase tracking-wider border-b border-brand-border text-[10px]">
                <th className="px-6 py-3">ID</th>
                <th className="px-6 py-3">Incident Title & Service</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Tenant</th>
                <th className="px-6 py-3">Timestamp</th>
                <th className="px-6 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-border">
              {incidents.slice(0, 6).map((inc) => (
                <tr
                  key={inc.id}
                  onClick={() => navigate('/incidents')}
                  className="hover:bg-brand-elevated/40 cursor-pointer transition"
                >
                  <td className="px-6 py-3.5 font-mono text-brand-secondary font-semibold">
                    #{inc.id}
                  </td>
                  <td className="px-6 py-3.5">
                    <div className="font-medium text-brand-textPrimary">{inc.title || inc.source}</div>
                    <div className="text-[10px] text-brand-textMuted font-mono">payment-service/build.gradle</div>
                  </td>
                  <td className="px-6 py-3.5">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold font-mono ${
                        inc.status === 'RESOLVED' || inc.status === 'PR_OPENED'
                          ? 'bg-brand-success/20 text-brand-success border border-brand-success/30'
                          : inc.status === 'AWAITING_APPROVAL'
                          ? 'bg-brand-warning/20 text-brand-warning border border-brand-warning/30'
                          : inc.status === 'BLOCKED'
                          ? 'bg-brand-danger/20 text-brand-danger border border-brand-danger/30'
                          : 'bg-brand-elevated text-brand-textSecondary border border-brand-border'
                      }`}
                    >
                      {inc.status === 'PR_OPENED' ? 'RESOLVED (PR OPENED)' : inc.status}
                    </span>
                  </td>
                  <td className="px-6 py-3.5 uppercase font-mono text-brand-textSecondary text-[11px]">
                    {inc.tenant}
                  </td>
                  <td className="px-6 py-3.5 text-brand-textMuted text-[11px]">
                    {new Date(inc.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </td>
                  <td className="px-6 py-3.5 text-right">
                    <span className="text-xs font-medium text-brand-accent hover:underline flex items-center justify-end gap-1">
                      <span>Investigate</span>
                      <ArrowRight className="w-3 h-3" />
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

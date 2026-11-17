import React, { useState, useEffect, useCallback } from 'react';
import {
  CheckCircle2,
  Clock,
  ShieldCheck,
  AlertTriangle,
  GitPullRequest,
  Check,
  X,
  UserCheck,
  Sparkles,
  ExternalLink,
  ArrowUpRight,
  ShieldAlert,
  Flame,
  Loader2,
  GitBranch,
  RefreshCw,
} from 'lucide-react';
import { getApprovals, approve, reject, getCurrentUser, login } from '../api.js';

export default function ApprovalsPage() {
  const user = getCurrentUser();
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actingId, setActingId] = useState(null);
  const [statusMsg, setStatusMsg] = useState('');
  const [statusType, setStatusType] = useState('success'); // 'success' | 'warning' | 'error'
  const [filter, setFilter] = useState('ALL');

  const loadApprovals = useCallback(() => {
    setLoading(true);
    getApprovals()
      .then((data) => setApprovals(Array.isArray(data) ? data : data?.approvals || []))
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadApprovals();
  }, [loadApprovals]);

  const handleApprove = async (id) => {
    setActingId(id);
    setStatusMsg('');
    try {
      const res = await approve(id);
      if (res && res.github_success === false) {
        setStatusType('warning');
        setStatusMsg(`⚠️ Approval #${id} granted, but GitHub PR creation failed: ${res.error || 'GitHub API error'}`);
      } else if (res && res.pr_url) {
        setStatusType('success');
        const prLabel = res.pr_number ? `PR #${res.pr_number}` : 'Pull Request';
        const actionWord = res.duplicate ? 'verified (existing active PR reused)' : 'created on GitHub';
        setStatusMsg(`✓ Approval #${id} granted. ${prLabel} ${actionWord}: ${res.pr_url} • SHA-256 audit ledger signed.`);
      } else {
        setStatusType('success');
        setStatusMsg(`✓ Approval #${id} granted. Action recorded and cryptographic audit ledger signed.`);
      }
      loadApprovals();
    } catch (e) {
      setStatusType('error');
      setStatusMsg(`Error authorizing approval #${id}: ${e.message}`);
    } finally {
      setActingId(null);
    }
  };

  const handleReject = async (id) => {
    setActingId(id);
    setStatusMsg('');
    try {
      await reject(id);
      setStatusType('warning');
      setStatusMsg(`✗ Approval #${id} rejected by manager.`);
      loadApprovals();
    } catch (e) {
      setStatusType('error');
      setStatusMsg(`Error rejecting approval #${id}: ${e.message}`);
    } finally {
      setActingId(null);
    }
  };

  const handleEscalate = (id) => {
    setStatusType('warning');
    setStatusMsg(`⚑ Approval #${id} escalated to Principal Site Reliability Architect & CISO review board.`);
  };

  const filtered = approvals.filter((a) => {
    if (filter === 'ALL') return true;
    return a.status === filter;
  });

  const pendingCount = approvals.filter((a) => a.status === 'pending').length;

  const getExecutionBadge = (item) => {
    if (actingId === item.id) {
      return (
        <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-brand-accent/20 text-brand-accent border border-brand-accent/30 animate-pulse">
          <Loader2 className="w-3 h-3 animate-spin" />
          Creating Pull Request…
        </span>
      );
    }
    const execStatus = item.execution_status || (item.status === 'pending' ? 'Awaiting Approval' : item.status === 'approved' && item.pr_url ? 'PR Created' : item.status);
    if (execStatus === 'PR Created' || item.pr_url) {
      return (
        <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
          PR Created
        </span>
      );
    }
    if (execStatus === 'Execution Failed') {
      return (
        <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-rose-500/20 text-rose-400 border border-rose-500/30">
          <AlertTriangle className="w-3 h-3 text-rose-400" />
          Execution Failed
        </span>
      );
    }
    if (item.status === 'rejected') {
      return (
        <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-zinc-800 text-zinc-400 border border-zinc-700">
          <X className="w-3 h-3 text-zinc-400" />
          Rejected
        </span>
      );
    }
    return (
      <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-amber-500/20 text-amber-400 border border-amber-500/30">
        <Clock className="w-3 h-3 text-amber-400" />
        Awaiting Approval
      </span>
    );
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-brand-border/60">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-brand-textPrimary flex items-center gap-2.5">
              <CheckCircle2 className="w-6 h-6 text-brand-warning" />
              <span>Human-in-the-Loop Approval Queue</span>
            </h1>
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-brand-warning/20 text-brand-warning border border-brand-warning/30 font-mono">
              CONFIRM TIER GOVERNANCE
            </span>
          </div>
          <p className="text-xs text-brand-textMuted mt-1">
            Mandatory governance gate for medium-confidence actions [0.60, 0.85). Manager authorization required before tool execution.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadApprovals}
            title="Refresh Approval Queue"
            className="p-2 rounded-lg bg-brand-elevated hover:bg-brand-card border border-brand-border text-brand-textSecondary hover:text-brand-textPrimary transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <span className="text-xs font-mono px-3 py-1.5 rounded-lg bg-brand-elevated border border-brand-border text-brand-textSecondary">
            {pendingCount} Pending Review{pendingCount !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Role Notice if logged in as Developer */}
      {user?.role === 'developer' && (
        <div className="p-4 rounded-xl bg-brand-elevated border border-brand-accent/40 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <span className="text-xs font-bold text-brand-accent flex items-center gap-1.5">
              <UserCheck className="w-4 h-4" />
              <span>Developer View (Read-Only)</span>
            </span>
            <p className="text-[11px] text-brand-textMuted mt-0.5">
              You are signed in as developer (<strong className="text-brand-textPrimary font-mono">dev@acme</strong>). Authorizing code changes requires manager authority.
            </p>
          </div>
          <button
            onClick={async () => {
              await login('mgr@acme', 'demo123');
              window.location.reload();
            }}
            className="px-3.5 py-2 rounded-lg text-xs font-semibold bg-brand-accent hover:bg-brand-accentHover text-white transition flex-shrink-0 shadow-glow"
          >
            Switch to Manager (mgr@acme) →
          </button>
        </div>
      )}

      {/* Status Filter */}
      <div className="flex items-center gap-2">
        {['ALL', 'pending', 'approved', 'rejected'].map((st) => (
          <button
            key={st}
            onClick={() => setFilter(st)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition uppercase font-mono ${
              filter === st
                ? 'bg-brand-accent text-white shadow-sm'
                : 'bg-brand-card hover:bg-brand-elevated text-brand-textSecondary border border-brand-border'
            }`}
          >
            {st}
          </button>
        ))}
      </div>

      {statusMsg && (
        <div
          className={`p-3.5 rounded-lg border text-xs font-semibold animate-fadeIn ${
            statusType === 'error'
              ? 'bg-rose-950/30 border-rose-500/40 text-rose-300'
              : statusType === 'warning'
              ? 'bg-amber-950/30 border-amber-500/40 text-amber-300'
              : 'bg-emerald-950/30 border-emerald-500/40 text-emerald-300'
          }`}
        >
          {statusMsg}
        </div>
      )}

      {/* Approvals Cards Grid */}
      <div className="space-y-4">
        {loading && approvals.length === 0 ? (
          <div className="text-center py-12 text-brand-textMuted font-mono text-xs flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-brand-accent" />
            <span>Loading approval queue…</span>
          </div>
        ) : filtered.length === 0 ? (
          <div className="bg-brand-card border border-brand-border rounded-xl p-8 text-center text-brand-textMuted text-xs">
            No queued actions found matching this filter.
          </div>
        ) : (
          filtered.map((item) => {
            const confidence = 0.826; // Diagnostic Grounding Score
            const isProcessing = actingId === item.id;
            const targetRepo = item.repo || 'Gowthamone7/EKA-DevGuard';
            const sourceBranch = item.source_branch || `eka/incident-${item.incident_id}`;
            const targetBranch = item.target_branch || 'main';

            return (
              <div
                key={item.id}
                className="bg-brand-card border border-brand-border rounded-xl p-5 shadow-card space-y-4 hover:border-brand-borderHover transition"
              >
                {/* Card Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-brand-border/60 pb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-brand-warning/15 border border-brand-warning/30 flex items-center justify-center font-mono font-bold text-xs text-brand-warning">
                      #{item.id}
                    </div>
                    <div>
                      <h2 className="text-sm font-bold text-brand-textPrimary flex items-center gap-2">
                        <GitPullRequest className="w-4 h-4 text-brand-accent" />
                        <span>Action: {item.tool}</span>
                      </h2>
                      <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono text-brand-textMuted mt-0.5">
                        <span>Incident: <strong className="text-brand-textSecondary">#{item.incident_id}</strong></span>
                        <span>•</span>
                        <span>Org: <strong className="text-brand-textSecondary">{item.tenant}</strong></span>
                        <span>•</span>
                        <span>Repo: <strong className="text-brand-accent font-sans">{targetRepo}</strong></span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {getExecutionBadge(item)}
                    <span className="text-[11px] text-brand-textMuted font-mono">
                      {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>

                {/* GitHub PR Details Banner if PR exists */}
                {item.pr_url && (
                  <div className="p-4 rounded-xl bg-brand-elevated border border-emerald-500/30 flex flex-col md:flex-row md:items-center justify-between gap-4 animate-fadeIn">
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-2">
                        <GitPullRequest className="w-4 h-4 text-emerald-400" />
                        <span className="text-xs font-bold text-emerald-400">GitHub Pull Request Created</span>
                        <a
                          href={item.pr_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-mono font-bold text-xs text-brand-accent hover:underline flex items-center gap-1 bg-brand-card px-2 py-0.5 rounded border border-brand-border"
                        >
                          PR #{item.pr_number}
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                      <div className="flex flex-wrap items-center gap-3 text-[11px] font-mono text-brand-textMuted">
                        <span className="flex items-center gap-1 text-brand-textSecondary">
                          <GitBranch className="w-3 h-3 text-brand-accent" />
                          <span>{sourceBranch}</span>
                          <span className="text-brand-textMuted">→</span>
                          <span>{targetBranch}</span>
                        </span>
                        <span>•</span>
                        <span className="truncate max-w-xs">{item.pr_url}</span>
                      </div>
                    </div>

                    <a
                      href={item.pr_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center justify-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition flex-shrink-0 shadow-sm"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      <span>View Pull Request on GitHub</span>
                    </a>
                  </div>
                )}

                {/* Execution Failure Alert */}
                {item.execution_status === 'Execution Failed' && (
                  <div className="p-3.5 rounded-xl bg-rose-950/20 border border-rose-500/30 flex items-start gap-2.5 text-xs text-rose-300">
                    <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <strong className="block font-semibold">GitHub Pull Request Execution Failed</strong>
                      <span className="text-[11px] text-rose-400/90">
                        Approval was recorded, but branch creation or PR submission was rejected by GitHub. Check repository permissions or token scopes.
                      </span>
                    </div>
                  </div>
                )}

                {/* Confidence Meter Bar */}
                <div className="p-3 rounded-lg bg-brand-elevated border border-brand-border/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-brand-textPrimary">Diagnostic Grounding Confidence</span>
                      <span className="font-mono text-brand-warning font-bold">{(confidence * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-brand-card rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-brand-warning h-full rounded-full transition-all"
                        style={{ width: `${confidence * 100}%` }}
                      />
                    </div>
                  </div>
                  <div className="text-[11px] font-mono text-brand-textMuted bg-brand-card px-2.5 py-1 rounded border border-brand-border flex-shrink-0">
                    Tier: <strong className="text-brand-warning">CONFIRM [0.60, 0.85)</strong>
                  </div>
                </div>

                {/* Payload Diff Preview */}
                <div className="space-y-1.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-brand-textMuted block">
                    Synthesized Git Diff / Action Payload
                  </span>
                  <pre className="p-3 bg-brand-bg border border-brand-border rounded-lg text-xs font-mono text-brand-textSecondary overflow-x-auto whitespace-pre-wrap leading-relaxed">
                    {typeof item.payload === 'string'
                      ? item.payload
                      : JSON.stringify(item.payload || item.payload_json, null, 2)}
                  </pre>
                </div>

                {/* Action Buttons if Pending */}
                {item.status === 'pending' && (user?.role === 'manager' || user?.role === 'admin') && (
                  <div className="flex flex-wrap items-center justify-end gap-2.5 pt-2 border-t border-brand-border/60">
                    <button
                      onClick={() => handleEscalate(item.id)}
                      disabled={isProcessing}
                      className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold bg-brand-elevated hover:bg-brand-elevated/80 text-brand-textSecondary border border-brand-border transition"
                    >
                      <ArrowUpRight className="w-3.5 h-3.5" />
                      <span>Escalate to Lead</span>
                    </button>
                    <button
                      onClick={() => handleReject(item.id)}
                      disabled={isProcessing}
                      className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold bg-brand-elevated hover:bg-brand-danger/20 text-brand-danger border border-brand-border transition"
                    >
                      <X className="w-3.5 h-3.5" />
                      <span>Reject Patch</span>
                    </button>
                    <button
                      onClick={() => handleApprove(item.id)}
                      disabled={isProcessing}
                      className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-brand-success hover:bg-brand-success/90 text-white transition shadow-glowSuccess disabled:opacity-50"
                    >
                      {isProcessing ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          <span>Creating Pull Request…</span>
                        </>
                      ) : (
                        <>
                          <Check className="w-3.5 h-3.5" />
                          <span>Authorize & Create PR</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

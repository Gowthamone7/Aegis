import React from 'react';
import {
  Scale,
  ShieldCheck,
  CheckCircle2,
  Clock,
  ShieldAlert,
  UserCheck,
  BookOpen,
  Lock,
} from 'lucide-react';

export default function PolicyPage() {
  const policyTiers = [
    {
      tier: 'Tier 1: High Confidence',
      range: 'Score ≥ 0.85',
      decision: 'ALLOW',
      color: 'success',
      badge: 'bg-brand-success/20 text-brand-success border-brand-success/30',
      description: 'Autonomous execution authorized. The agent is permitted to create branches, open pull requests, and dispatch non-blocking notifications.',
      examples: 'Well-known out-of-memory heap expansions, documented missing npm/pip dependency additions, known port conflict resolution.',
    },
    {
      tier: 'Tier 2: Partial Confidence',
      range: '0.60 ≤ Score < 0.85',
      decision: 'CONFIRM',
      color: 'warning',
      badge: 'bg-brand-warning/20 text-brand-warning border-brand-warning/30',
      description: 'Human-in-the-loop authorization required. The agent drafts the diagnostic diff, links supporting runbook citations, and holds execution in AWAITING_APPROVAL.',
      examples: 'Complex environment variable drifts, multi-module build timeouts, build configuration updates requiring managerial sign-off.',
    },
    {
      tier: 'Tier 3: Low Confidence & Threat',
      range: 'Score < 0.60 or Injection',
      decision: 'BLOCK / ESCALATE',
      color: 'danger',
      badge: 'bg-brand-danger/20 text-brand-danger border-brand-danger/30',
      description: 'Immediate pipeline termination. No automated tool calls permitted. Unknown failures are escalated to human on-call engineers; adversarial prompts are permanently logged.',
      examples: 'Unrecognized stack traces with zero matching runbooks, adversarial prompt injection payloads ("ignore previous instructions").',
    },
  ];

  const rbacMatrix = [
    { role: 'Developer', simulate: true, viewTrace: true, viewAudit: true, approvePR: false, systemConfig: false },
    { role: 'Manager', simulate: true, viewTrace: true, viewAudit: true, approvePR: true, systemConfig: false },
    { role: 'Viewer', simulate: false, viewTrace: true, viewAudit: true, approvePR: false, systemConfig: false },
    { role: 'Admin', simulate: true, viewTrace: true, viewAudit: true, approvePR: true, systemConfig: true },
  ];

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-brand-border/60">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-brand-textPrimary flex items-center gap-2.5">
            <Scale className="w-6 h-6 text-brand-accent" />
            <span>Risk Policy Engine & RBAC Matrix</span>
          </h1>
          <p className="text-xs text-brand-textMuted mt-1">
            Deterministic governance rules intercepting, evaluating, and bounding all autonomous agent actions before execution.
          </p>
        </div>
      </div>

      {/* Golden Invariant Rule Banner */}
      <div className="p-4 rounded-xl bg-brand-elevated border border-brand-accent/40 flex items-start gap-3.5">
        <BookOpen className="w-5 h-5 text-brand-accent flex-shrink-0 mt-0.5" />
        <div className="text-xs space-y-1">
          <strong className="text-brand-textPrimary font-semibold text-sm">
            Core Grounding Invariant: "No Citation, No Action"
          </strong>
          <p className="text-brand-textSecondary leading-relaxed">
            The Reasoning Agent is strictly forbidden from proposing any remediation or patch unless it cites an exact runbook ID, document title, and page number retrieved from the verified enterprise knowledge base. Any response lacking verified evidence is immediately intercepted by the Security Agent and marked <strong className="text-brand-danger font-mono">BLOCK</strong>.
          </p>
        </div>
      </div>

      {/* 3-Tier Risk Policy Grid */}
      <div className="space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-brand-textMuted">
          Three-Tier Confidence Matrix
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {policyTiers.map((tier) => (
            <div
              key={tier.decision}
              className="bg-brand-card border border-brand-border rounded-xl p-5 shadow-card space-y-3 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-brand-textPrimary">{tier.tier}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${tier.badge}`}>
                    {tier.decision}
                  </span>
                </div>
                <div className="font-mono text-xs font-bold text-brand-secondary mb-2">
                  {tier.range}
                </div>
                <p className="text-xs text-brand-textSecondary leading-relaxed">
                  {tier.description}
                </p>
              </div>

              <div className="pt-3 border-t border-brand-border/60 text-[11px] text-brand-textMuted">
                <span className="font-semibold block text-[10px] uppercase text-brand-textMuted mb-0.5">Applies to</span>
                <span>{tier.examples}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Role-Based Access Control (RBAC) Table */}
      <div className="bg-brand-card border border-brand-border rounded-xl shadow-card overflow-hidden space-y-3">
        <div className="p-4 border-b border-brand-border">
          <h2 className="text-xs font-bold uppercase tracking-wider text-brand-textPrimary flex items-center gap-2">
            <UserCheck className="w-4 h-4 text-brand-accent" />
            <span>Role-Based Access Control (RBAC) Privileges</span>
          </h2>
          <p className="text-[11px] text-brand-textMuted mt-0.5">Granular authorization enforced across JWT claims and endpoint middleware</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-brand-elevated/60 text-brand-textMuted font-semibold uppercase tracking-wider border-b border-brand-border text-[10px]">
                <th className="px-6 py-3">Role</th>
                <th className="px-6 py-3">Simulate Incidents</th>
                <th className="px-6 py-3">View Diagnostic Traces</th>
                <th className="px-6 py-3">View Audit Ledger</th>
                <th className="px-6 py-3">Approve Pull Requests</th>
                <th className="px-6 py-3">System Admin</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-border font-mono text-[11px]">
              {rbacMatrix.map((row) => (
                <tr key={row.role} className="hover:bg-brand-elevated/40 transition">
                  <td className="px-6 py-3.5 font-bold text-brand-textPrimary font-sans">
                    {row.role}
                  </td>
                  <td className="px-6 py-3.5">
                    {row.simulate ? <CheckCircle2 className="w-4 h-4 text-brand-success" /> : <span className="text-brand-textMuted">—</span>}
                  </td>
                  <td className="px-6 py-3.5">
                    {row.viewTrace ? <CheckCircle2 className="w-4 h-4 text-brand-success" /> : <span className="text-brand-textMuted">—</span>}
                  </td>
                  <td className="px-6 py-3.5">
                    {row.viewAudit ? <CheckCircle2 className="w-4 h-4 text-brand-success" /> : <span className="text-brand-textMuted">—</span>}
                  </td>
                  <td className="px-6 py-3.5">
                    {row.approvePR ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-brand-success/20 text-brand-success border border-brand-success/30">
                        AUTHORIZED
                      </span>
                    ) : (
                      <span className="text-brand-textMuted text-[10px]">FORBIDDEN</span>
                    )}
                  </td>
                  <td className="px-6 py-3.5">
                    {row.systemConfig ? <CheckCircle2 className="w-4 h-4 text-brand-success" /> : <span className="text-brand-textMuted">—</span>}
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


import React, { useState } from 'react';
import {
  Building2,
  Shield,
  Key,
  FolderGit2,
  Cpu,
  Database,
  Lock,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  RefreshCw,
  Users,
  HardDrive,
  Layers,
} from 'lucide-react';
import { getCurrentUser, login } from '../api.js';

export default function OrganizationsPage() {
  const currentUser = getCurrentUser();
  const [switching, setSwitching] = useState(false);

  const orgs = [
    {
      id: 'acme',
      name: 'ACME Corporation',
      tier: 'Enterprise Platinum',
      domain: 'acme.corp.internal',
      status: 'Active',
      isolatedDatabase: 'eka.db (tenant_id="acme" partition)',
      kmsKeyId: 'kms-us-east-1-acme-sec-9982',
      repositories: [
        { name: 'Gowthamone7/EKA-DevGuard', branch: 'main', sync: 'Live Connected (PAT Active)', webhook: 'Active (HMAC SHA-256)' },
        { name: 'acme/payment-service', branch: 'main', sync: 'Synchronized', webhook: 'Active (HMAC SHA-256)' },
        { name: 'acme/auth-service', branch: 'main', sync: 'Synchronized', webhook: 'Active (HMAC SHA-256)' },
      ],
      users: 142,
      activeIncidents: 4,
      monthlySimulations: 840,
      quotaUsed: '68%',
      runbookCount: 12,
      complianceStatus: 'SOC2 Type II / ISO 27001 Certified',
    },
    {
      id: 'globex',
      name: 'GLOBEX Industries',
      tier: 'Enterprise Gold',
      domain: 'globex-tech.io',
      status: 'Active',
      isolatedDatabase: 'eka.db (tenant_id="globex" partition)',
      kmsKeyId: 'kms-eu-west-1-globex-sec-4421',
      repositories: [
        { name: 'globex/order-service', branch: 'master', sync: 'Synchronized', webhook: 'Active (HMAC SHA-256)' },
        { name: 'globex/inventory-api', branch: 'main', sync: 'Synchronized', webhook: 'Active (HMAC SHA-256)' },
      ],
      users: 68,
      activeIncidents: 1,
      monthlySimulations: 320,
      quotaUsed: '34%',
      runbookCount: 7,
      complianceStatus: 'SOC2 Type II Certified',
    },
  ];

  const handleSwitchTenant = async (tenantId) => {
    if (tenantId === currentUser?.tenant) return;
    setSwitching(true);
    try {
      const username = tenantId === 'globex' ? 'mgr@globex' : 'mgr@acme';
      await login(username, 'demo123');
      window.location.reload();
    } catch (e) {
      console.error(e);
    } finally {
      setSwitching(false);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-brand-border/60">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-brand-textPrimary flex items-center gap-2.5">
              <Building2 className="w-6 h-6 text-brand-accent" />
              <span>Multi-Tenant Organizations</span>
            </h1>
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-brand-accent/20 text-brand-accent border border-brand-accent/30 font-mono">
              TENANT ISOLATION GUARANTEED
            </span>
          </div>
          <p className="text-xs text-brand-textMuted mt-1">
            Enterprise boundary enforcement, cryptographic ledger partitioning, dedicated KMS keys, and repository mappings.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-brand-elevated border border-brand-border text-xs font-mono text-brand-textSecondary">
            <Shield className="w-3.5 h-3.5 text-brand-success" />
            <span>Active: <strong className="text-brand-textPrimary uppercase">{currentUser?.tenant || 'acme'}</strong></span>
          </div>
        </div>
      </div>

      {/* Tenant Isolation Architecture Banner */}
      <div className="bg-brand-card border border-brand-border rounded-xl p-5 shadow-card">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-lg bg-brand-accent/20 border border-brand-accent/40 flex items-center justify-center flex-shrink-0 text-brand-accent">
            <Lock className="w-5 h-5" />
          </div>
          <div className="space-y-1 flex-1">
            <h3 className="text-sm font-semibold text-brand-textPrimary">
              Strict Multi-Tenant Isolation Architecture
            </h3>
            <p className="text-xs text-brand-textMuted leading-relaxed">
              Engineering Knowledge Agent enforces absolute tenant boundaries at every layer. Queries, runbooks, AST context, incident traces, unified diffs, and cryptographic audit ledger blocks are hard-partitioned by <code className="text-brand-secondary bg-brand-elevated px-1.5 py-0.5 rounded border border-brand-border text-[11px]">tenant_id</code>. Cross-tenant leakage is strictly prevented via JWT claims validation and SQL-level parameter binding.
            </p>
          </div>
        </div>
      </div>

      {/* Organizations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {orgs.map((org) => {
          const isCurrent = currentUser?.tenant === org.id;
          return (
            <div
              key={org.id}
              className={`bg-brand-card border rounded-xl p-6 shadow-card transition-all flex flex-col justify-between ${
                isCurrent
                  ? 'border-brand-accent ring-1 ring-brand-accent/40 bg-brand-elevated/60'
                  : 'border-brand-border hover:border-brand-borderHover'
              }`}
            >
              <div className="space-y-5">
                {/* Org Card Header */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-brand-elevated border border-brand-border flex items-center justify-center text-brand-accent font-bold">
                      {org.name.charAt(0)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 className="text-base font-bold text-brand-textPrimary">{org.name}</h2>
                        {isCurrent && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-brand-success/20 text-brand-success border border-brand-success/30">
                            CURRENT CONTEXT
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-brand-textMuted font-mono">{org.domain}</span>
                    </div>
                  </div>
                  <span className="text-[11px] font-mono px-2.5 py-1 rounded bg-brand-elevated border border-brand-border text-brand-secondary font-semibold">
                    {org.tier}
                  </span>
                </div>

                {/* Key Metrics Grid */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="p-3 rounded-lg bg-brand-elevated/80 border border-brand-border/60">
                    <span className="text-[10px] uppercase font-semibold text-brand-textMuted block">Active Repos</span>
                    <span className="text-base font-bold font-mono text-brand-textPrimary mt-0.5 block">{org.repositories.length}</span>
                  </div>
                  <div className="p-3 rounded-lg bg-brand-elevated/80 border border-brand-border/60">
                    <span className="text-[10px] uppercase font-semibold text-brand-textMuted block">Runbooks</span>
                    <span className="text-base font-bold font-mono text-brand-textPrimary mt-0.5 block">{org.runbookCount}</span>
                  </div>
                  <div className="p-3 rounded-lg bg-brand-elevated/80 border border-brand-border/60">
                    <span className="text-[10px] uppercase font-semibold text-brand-textMuted block">Compute Quota</span>
                    <span className="text-base font-bold font-mono text-brand-secondary mt-0.5 block">{org.quotaUsed}</span>
                  </div>
                </div>

                {/* Technical Configuration Details */}
                <div className="space-y-2 text-xs">
                  <div className="flex items-center justify-between py-1.5 border-b border-brand-border/40 font-mono">
                    <span className="text-brand-textMuted flex items-center gap-1.5">
                      <Database className="w-3.5 h-3.5 text-brand-accent" />
                      Storage Partition:
                    </span>
                    <span className="text-brand-textSecondary text-[11px] truncate max-w-[220px]">{org.isolatedDatabase}</span>
                  </div>
                  <div className="flex items-center justify-between py-1.5 border-b border-brand-border/40 font-mono">
                    <span className="text-brand-textMuted flex items-center gap-1.5">
                      <Key className="w-3.5 h-3.5 text-brand-warning" />
                      Tenant KMS Key:
                    </span>
                    <span className="text-brand-textSecondary text-[11px]">{org.kmsKeyId}</span>
                  </div>
                  <div className="flex items-center justify-between py-1.5 border-b border-brand-border/40 font-mono">
                    <span className="text-brand-textMuted flex items-center gap-1.5">
                      <Shield className="w-3.5 h-3.5 text-brand-success" />
                      Compliance:
                    </span>
                    <span className="text-brand-success text-[11px] font-semibold">{org.complianceStatus}</span>
                  </div>
                </div>

                {/* Bound Repositories */}
                <div className="space-y-2 pt-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-brand-textMuted block">
                    Authorized GitHub Repositories
                  </span>
                  <div className="space-y-1.5">
                    {org.repositories.map((repo) => (
                      <div
                        key={repo.name}
                        className="flex items-center justify-between p-2 rounded bg-brand-bg/80 border border-brand-border/60 text-xs font-mono"
                      >
                        <div className="flex items-center gap-2 truncate">
                          <FolderGit2 className="w-3.5 h-3.5 text-brand-secondary flex-shrink-0" />
                          <span className="text-brand-textPrimary font-semibold truncate">{repo.name}</span>
                          <span className="text-[10px] text-brand-textMuted">({repo.branch})</span>
                        </div>
                        <span className="text-[10px] text-brand-success flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" />
                          {repo.webhook}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-6 border-t border-brand-border/60 mt-6 flex items-center justify-between">
                <span className="text-xs text-brand-textMuted font-mono">Tenant ID: #{org.id}</span>
                <button
                  onClick={() => handleSwitchTenant(org.id)}
                  disabled={isCurrent || switching}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition ${
                    isCurrent
                      ? 'bg-brand-elevated text-brand-textMuted cursor-default border border-brand-border'
                      : 'bg-brand-accent hover:bg-brand-accentHover text-white shadow-glow'
                  }`}
                >
                  {switching ? (
                    <span>Switching context…</span>
                  ) : isCurrent ? (
                    <span>Active Session</span>
                  ) : (
                    <>
                      <span>Switch to {org.name}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}


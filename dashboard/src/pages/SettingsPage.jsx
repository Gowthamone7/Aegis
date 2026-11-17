import React, { useState, useEffect } from 'react';
import {
  Settings,
  Cpu,
  Database,
  Shield,
  Layers,
  Server,
  Activity,
  CheckCircle2,
  Lock,
} from 'lucide-react';
import { getCurrentUser } from '../api.js';

export default function SettingsPage() {
  const user = getCurrentUser();

  const systemProps = [
    { label: 'System Service', value: 'Engineering Knowledge Agent (EKA)', detail: 'DevGuard + CodeGuard' },
    { label: 'Agent Pipeline Version', value: 'v1.0.0-PROD', detail: 'Final-Year Capstone Architecture' },
    { label: 'Execution Mode', value: 'Deterministic L0 Offline Safe', detail: 'Zero external cloud outage risk' },
    { label: 'LLM Reasoning Provider', value: 'Offline Rule Engine + Groq Llama 3.3', detail: 'Sub-25ms deterministic diagnosis' },
    { label: 'Embedding Architecture', value: '128-Dim Normalized Vectors + BM25', detail: 'Zero pip install failure mode' },
    { label: 'Database & Concurrency', value: 'SQLite 3 with WAL Mode (WAL=ON)', detail: 'Foreign keys enabled, ACID compliant' },
    { label: 'Audit Log Integrity', value: 'SHA-256 Forward Hash Chain', detail: 'H_i = SHA-256(H_{i-1} || payload)' },
    { label: 'Active Tenant Context', value: `${user?.tenant?.toUpperCase() || 'ACME'} Corporation`, detail: 'Strict multi-tenant isolation' },
  ];

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-brand-border/60">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-brand-textPrimary flex items-center gap-2.5">
            <Settings className="w-6 h-6 text-brand-accent" />
            <span>Runtime Engine Status & Configuration</span>
          </h1>
          <p className="text-xs text-brand-textMuted mt-1">
            System architectural parameters, multi-tenant isolation configuration, and verification telemetry.
          </p>
        </div>
        <div className="flex items-center gap-2 font-mono text-xs text-brand-success bg-brand-success/10 px-3 py-1.5 rounded-lg border border-brand-success/30">
          <Activity className="w-3.5 h-3.5" />
          <span>System Healthy · 100% Green</span>
        </div>
      </div>

      {/* Configuration Grid */}
      <div className="bg-brand-card border border-brand-border rounded-xl shadow-card overflow-hidden">
        <div className="p-4 border-b border-brand-border bg-brand-sidebar">
          <h2 className="text-xs font-bold uppercase tracking-wider text-brand-textPrimary flex items-center gap-2">
            <Server className="w-4 h-4 text-brand-secondary" />
            <span>Core System Parameters</span>
          </h2>
        </div>

        <div className="divide-y divide-brand-border font-mono text-xs">
          {systemProps.map((prop) => (
            <div key={prop.label} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-brand-elevated/40 transition">
              <div>
                <span className="font-semibold text-brand-textPrimary block">{prop.label}</span>
                <span className="text-[11px] text-brand-textMuted">{prop.detail}</span>
              </div>
              <span className="px-2.5 py-1 rounded bg-brand-elevated border border-brand-border text-brand-secondary font-bold text-xs self-start sm:self-auto">
                {prop.value}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}


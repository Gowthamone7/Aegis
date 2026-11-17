import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  Lock,
  RefreshCw,
  Hash,
  Clock,
  User,
  CheckCircle2,
  Database,
  ExternalLink,
  ArrowRight,
  Link as LinkIcon,
  Layers,
} from 'lucide-react';
import { getAudit, verifyAudit, getCurrentUser } from '../api.js';

export default function AuditPage() {
  const user = getCurrentUser();
  const [logs, setLogs] = useState([]);
  const [verification, setVerification] = useState(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [selectedBlock, setSelectedBlock] = useState(null);

  const loadData = async () => {
    try {
      const [entries, res] = await Promise.all([
        getAudit().catch(() => []),
        verifyAudit().catch(() => null),
      ]);
      setLogs(Array.isArray(entries) ? entries : entries?.logs || []);
      setVerification(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleVerify = async () => {
    setVerifying(true);
    try {
      const res = await verifyAudit();
      setVerification(res);
      await loadData();
    } catch (e) {
      console.error(e);
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-brand-border/60">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-brand-textPrimary flex items-center gap-2.5">
              <Lock className="w-6 h-6 text-brand-accent" />
              <span>Cryptographic SHA-256 Audit Ledger</span>
            </h1>
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-brand-success/20 text-brand-success border border-brand-success/30 font-mono">
              TAMPER-EVIDENT LEDGER
            </span>
          </div>
          <p className="text-xs text-brand-textMuted mt-1">
            Tamper-evident forward-chained ledger. Every action, tool execution, and approval is cryptographically bound to its predecessor.
          </p>
        </div>
        <button
          onClick={handleVerify}
          disabled={verifying}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold bg-brand-accent hover:bg-brand-accentHover disabled:bg-brand-elevated text-white transition shadow-glow flex-shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${verifying ? 'animate-spin' : ''}`} />
          <span>{verifying ? 'Computing Hashes…' : 'Verify Chain Integrity'}</span>
        </button>
      </div>

      {/* Verification Status Banner */}
      <div
        className={`p-5 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
          verification?.valid
            ? 'bg-brand-success/10 border-brand-success/40 text-brand-success'
            : 'bg-brand-danger/10 border-brand-danger/40 text-brand-danger'
        }`}
      >
        <div className="flex items-center gap-3.5">
          {verification?.valid ? (
            <ShieldCheck className="w-7 h-7 text-brand-success flex-shrink-0" />
          ) : (
            <ShieldAlert className="w-7 h-7 text-brand-danger flex-shrink-0" />
          )}
          <div>
            <h2 className="text-sm font-bold">
              {verification?.valid
                ? 'Cryptographic Hash Chain Verified Intact'
                : 'Warning: Hash Inconsistency Detected'}
            </h2>
            <p className="text-xs opacity-90 mt-0.5 font-mono">
              {verification?.valid
                ? `All ${logs.length} entries verified against SHA-256 forward hash formula: H_i = SHA-256(H_{i-1} || payload)`
                : 'Ledger root hash mismatch. Possible unauthorized modification.'}
            </p>
          </div>
        </div>
        <div className="text-xs font-mono font-bold px-3 py-1.5 rounded-lg bg-black/40 border border-current">
          ROOT: {verification?.root_hash ? verification.root_hash.slice(0, 16) + '…' : 'GENESIS_ROOT'}
        </div>
      </div>

      {/* Visual Block Hash Chain Explorer */}
      <div className="bg-brand-card border border-brand-border rounded-xl p-5 shadow-card space-y-4">
        <div className="flex items-center justify-between border-b border-brand-border/60 pb-3">
          <div>
            <h2 className="text-sm font-semibold text-brand-textPrimary flex items-center gap-2">
              <LinkIcon className="w-4 h-4 text-brand-accent" />
              <span>Forward-Chain Hash Linkages</span>
            </h2>
            <p className="text-[11px] text-brand-textMuted">Immutable block linkages where block N embeds the SHA-256 digest of block N-1</p>
          </div>
          <span className="text-[10px] font-mono text-brand-secondary bg-brand-elevated px-2.5 py-1 rounded border border-brand-border">
            H_i = SHA256(H_i-1 || data)
          </span>
        </div>

        {/* Scrollable Horizontal Block Chain Nodes */}
        <div className="flex items-center gap-3 overflow-x-auto pb-3 pt-1">
          {logs.slice(-5).map((log, index) => (
            <React.Fragment key={log.id || index}>
              <div
                onClick={() => setSelectedBlock(log)}
                className={`flex-shrink-0 w-56 p-3.5 rounded-xl border transition cursor-pointer ${
                  selectedBlock?.id === log.id
                    ? 'border-brand-accent bg-brand-elevated ring-1 ring-brand-accent/50'
                    : 'bg-brand-elevated/70 border-brand-border hover:border-brand-borderHover'
                }`}
              >
                <div className="flex items-center justify-between text-xs mb-2">
                  <span className="font-mono font-bold text-brand-accent">BLOCK #{log.id}</span>
                  <span className="w-2 h-2 rounded-full bg-brand-success"></span>
                </div>
                <div className="text-[11px] font-semibold text-brand-textPrimary truncate">{log.event_type}</div>
                <div className="text-[10px] text-brand-textMuted font-mono mt-1">Tenant: {log.tenant}</div>
                <div className="mt-3 pt-2 border-t border-brand-border/60 space-y-1 text-[9px] font-mono">
                  <div className="text-brand-textMuted truncate">PREV: {log.prev_hash?.slice(0, 12)}…</div>
                  <div className="text-brand-secondary font-semibold truncate">CURR: {log.current_hash?.slice(0, 12)}…</div>
                </div>
              </div>
              {index < Math.min(4, logs.length - 1) && (
                <div className="flex items-center text-brand-accent flex-shrink-0">
                  <ArrowRight className="w-4 h-4" />
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Audit Log Entries Table */}
      <div className="bg-brand-card border border-brand-border rounded-xl shadow-card overflow-hidden">
        <div className="px-6 py-4 border-b border-brand-border flex items-center justify-between">
          <h2 className="text-sm font-semibold text-brand-textPrimary">Audit Ledger Records ({logs.length})</h2>
          <span className="text-[11px] font-mono text-brand-textMuted">Append-only WAL transaction log</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-brand-elevated/60 text-brand-textMuted font-semibold uppercase tracking-wider border-b border-brand-border text-[10px]">
                <th className="px-6 py-3">Block ID</th>
                <th className="px-6 py-3">Event Type</th>
                <th className="px-6 py-3">Actor & Tenant</th>
                <th className="px-6 py-3">Previous Hash</th>
                <th className="px-6 py-3">Current Block Hash</th>
                <th className="px-6 py-3">Timestamp</th>
                <th className="px-6 py-3 text-right">Integrity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-border font-mono text-[11px]">
              {loading ? (
                <tr>
                  <td colSpan="7" className="px-6 py-8 text-center text-brand-textMuted">
                    Reading cryptographic ledger…
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-8 text-center text-brand-textMuted">
                    Ledger empty. Run simulations to generate cryptographic audit records.
                  </td>
                </tr>
              ) : (
                logs.map((item) => (
                  <tr
                    key={item.id}
                    onClick={() => setSelectedBlock(item)}
                    className="hover:bg-brand-elevated/40 transition cursor-pointer"
                  >
                    <td className="px-6 py-3.5 text-brand-accent font-semibold">#{item.id}</td>
                    <td className="px-6 py-3.5 font-sans font-medium text-brand-textPrimary">
                      {item.event_type}
                    </td>
                    <td className="px-6 py-3.5 text-brand-textSecondary">
                      {item.actor} @ <span className="uppercase text-brand-secondary font-bold">{item.tenant}</span>
                    </td>
                    <td className="px-6 py-3.5 text-brand-textMuted truncate max-w-[140px]" title={item.prev_hash}>
                      {item.prev_hash ? `${item.prev_hash.slice(0, 10)}…` : 'GENESIS'}
                    </td>
                    <td className="px-6 py-3.5 text-brand-secondary font-semibold truncate max-w-[140px]" title={item.current_hash}>
                      {item.current_hash ? `${item.current_hash.slice(0, 10)}…` : 'NULL'}
                    </td>
                    <td className="px-6 py-3.5 text-brand-textMuted whitespace-nowrap">
                      {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </td>
                    <td className="px-6 py-3.5 text-right whitespace-nowrap">
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-brand-success bg-brand-success/15 px-2 py-0.5 rounded border border-brand-success/30">
                        <CheckCircle2 className="w-3 h-3" />
                        VALID
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

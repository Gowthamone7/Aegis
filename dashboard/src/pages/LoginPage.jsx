import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Cpu, ShieldCheck, ArrowRight, Lock, User, Building2, Sparkles } from 'lucide-react';
import { login } from '../api.js';

export default function LoginPage() {
  const [username, setUsername] = useState('mgr@acme');
  const [password, setPassword] = useState('demo123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const setDemo = (u, p) => {
    setUsername(u);
    setPassword(p);
  };

  return (
    <div className="min-h-screen bg-brand-bg flex items-center justify-center p-4 selection:bg-brand-accent selection:text-white">
      {/* Subtle minimal background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-40">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-brand-elevated/50 rounded-full blur-3xl"></div>
      </div>

      <div className="relative w-full max-w-md space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-brand-accent shadow-sm mb-2">
            <Cpu className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-brand-textPrimary">
            Engineering Knowledge Agent
          </h1>
          <p className="text-xs text-brand-textMuted">
            Trustworthy Multi-Agent Operations · DevGuard + CodeGuard
          </p>
        </div>

        {/* Card */}
        <div className="bg-brand-card border border-brand-border rounded-2xl shadow-card p-6 sm:p-8 space-y-5">
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-brand-textSecondary block">
                Username / Email
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-brand-textMuted absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="mgr@acme"
                  required
                  className="w-full bg-brand-elevated border border-brand-border rounded-lg pl-9 pr-3 py-2 text-xs text-brand-textPrimary placeholder:text-brand-textMuted focus:outline-none focus:border-brand-accent font-mono"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-brand-textSecondary block">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-brand-textMuted absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full bg-brand-elevated border border-brand-border rounded-lg pl-9 pr-3 py-2 text-xs text-brand-textPrimary placeholder:text-brand-textMuted focus:outline-none focus:border-brand-accent font-mono"
                />
              </div>
            </div>

            {error && (
              <div className="p-3 rounded-lg bg-brand-danger/15 border border-brand-danger/30 text-xs font-semibold text-brand-danger">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-semibold bg-brand-accent hover:bg-brand-accentHover text-white transition shadow-glow disabled:opacity-50"
            >
              {loading ? (
                <span>Authenticating…</span>
              ) : (
                <>
                  <span>Sign In to Workspace</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Credentials Autofill */}
          <div className="pt-4 border-t border-brand-border/60 space-y-2.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-brand-textMuted block">
              Quick Sign-In (Pre-Seeded Roles)
            </span>
            <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
              <button
                type="button"
                onClick={() => setDemo('mgr@acme', 'demo123')}
                className="p-2 rounded-lg bg-brand-elevated hover:bg-brand-elevated/80 border border-brand-border text-left transition"
              >
                <div className="font-bold text-brand-warning">mgr@acme</div>
                <div className="text-[10px] text-brand-textMuted">Manager (Approver)</div>
              </button>

              <button
                type="button"
                onClick={() => setDemo('dev@acme', 'demo123')}
                className="p-2 rounded-lg bg-brand-elevated hover:bg-brand-elevated/80 border border-brand-border text-left transition"
              >
                <div className="font-bold text-brand-secondary">dev@acme</div>
                <div className="text-[10px] text-brand-textMuted">Developer (Simulate)</div>
              </button>

              <button
                type="button"
                onClick={() => setDemo('viewer@acme', 'demo123')}
                className="p-2 rounded-lg bg-brand-elevated hover:bg-brand-elevated/80 border border-brand-border text-left transition"
              >
                <div className="font-bold text-brand-textPrimary">viewer@acme</div>
                <div className="text-[10px] text-brand-textMuted">Viewer (Read-Only)</div>
              </button>

              <button
                type="button"
                onClick={() => setDemo('dev@globex', 'demo123')}
                className="p-2 rounded-lg bg-brand-elevated hover:bg-brand-elevated/80 border border-brand-border text-left transition"
              >
                <div className="font-bold text-brand-accent">dev@globex</div>
                <div className="text-[10px] text-brand-textMuted">Globex Tenant</div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

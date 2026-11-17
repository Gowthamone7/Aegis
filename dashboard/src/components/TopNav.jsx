import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Shield,
  Activity,
  Menu,
  UserCheck,
  Search,
  Bell,
  Cpu,
  Command,
  X,
  AlertTriangle,
  FileCode2,
  BookOpen,
  ArrowRight,
  CheckCircle2,
} from 'lucide-react';
import { getCurrentUser, login } from '../api.js';

export default function TopNav({ collapsed, onToggleMobile }) {
  const location = useLocation();
  const navigate = useNavigate();
  const user = getCurrentUser();

  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  // Keyboard shortcut Ctrl+K / Cmd+K
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setSearchOpen((prev) => !prev);
      }
      if (e.key === 'Escape') {
        setSearchOpen(false);
        setNotificationsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const getBreadcrumb = () => {
    const path = location.pathname;
    const search = location.search;

    if (path === '/') return ['OVERVIEW', 'Dashboard'];
    if (path === '/incidents') return ['DEVGUARD', 'Incidents & Diagnostics'];
    if (path === '/pipeline') return ['DEVGUARD', 'Agent Pipeline'];
    if (path === '/knowledge') return ['DEVGUARD', 'Knowledge Base (Hybrid RAG)'];
    if (path === '/codeguard') {
      if (search.includes('analysis')) return ['CODEGUARD', 'Code Analysis'];
      if (search.includes('patch')) return ['CODEGUARD', 'Patch Review'];
      if (search.includes('security')) return ['CODEGUARD', 'Security Verification'];
      return ['CODEGUARD', 'Repositories'];
    }
    if (path === '/approvals') return ['GOVERNANCE', 'Approvals'];
    if (path === '/audit') return ['GOVERNANCE', 'Audit Ledger (SHA-256)'];
    if (path === '/policy') return ['GOVERNANCE', 'Policy Management'];
    if (path === '/organizations') return ['GOVERNANCE', 'Organizations & Isolation'];
    if (path === '/settings') return ['SYSTEM', 'Settings'];
    return ['EKA', 'Control Center'];
  };

  const [group, page] = getBreadcrumb();

  const handleRoleToggle = async () => {
    const target = user?.role === 'manager' ? 'dev@acme' : 'mgr@acme';
    try {
      await login(target, 'demo123');
      window.location.reload();
    } catch (e) {
      console.error(e);
    }
  };

  const quickLinks = [
    { label: 'Incidents Workbench', path: '/incidents', icon: AlertTriangle, desc: 'View build failures and root causes' },
    { label: '5-Agent Pipeline', path: '/pipeline', icon: Cpu, desc: 'Monitor multi-agent execution telemetry' },
    { label: 'Patch Review & Diff', path: '/codeguard?tab=patch', icon: FileCode2, desc: 'Inspect synthesized unified git diffs' },
    { label: 'Runbook Knowledge Base', path: '/knowledge', icon: BookOpen, desc: 'Search hybrid RAG runbook citations' },
    { label: 'Human-in-the-Loop Approvals', path: '/approvals', icon: CheckCircle2, desc: 'Authorize or reject pending PR patches' },
  ];

  const filteredLinks = quickLinks.filter(
    (l) => l.label.toLowerCase().includes(searchQuery.toLowerCase()) || l.desc.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const notifications = [
    { id: 1, title: 'Remediation PR Proposed', desc: 'payment-service remediation patch awaiting approval', time: '2m ago', unread: true },
    { id: 2, title: 'Adversarial Prompt Blocked', desc: 'Prompt injection halted by Security Agent', time: '14m ago', unread: false },
    { id: 3, title: 'Audit Ledger Verified', desc: 'SHA-256 forward-chain root validated', time: '1h ago', unread: false },
  ];

  return (
    <>
      <header className="h-16 px-4 sm:px-6 border-b border-brand-border bg-brand-topnav/95 backdrop-blur-md sticky top-0 z-30 flex items-center justify-between">
        {/* Left: Mobile hamburger + Breadcrumb */}
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleMobile}
            className="md:hidden p-2 -ml-2 rounded-lg text-brand-textMuted hover:text-brand-textPrimary hover:bg-brand-elevated transition"
            aria-label="Open navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2 text-xs">
            <span className="text-brand-textMuted font-semibold tracking-wider text-[11px] hidden sm:inline">{group}</span>
            <span className="text-brand-border hidden sm:inline">/</span>
            <span className="text-brand-textPrimary font-semibold tracking-tight">{page}</span>
          </div>
        </div>

        {/* Center: Search Trigger (Command Palette shortcut) */}
        <div className="hidden md:flex items-center">
          <button
            onClick={() => setSearchOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-brand-card hover:bg-brand-elevated border border-brand-border hover:border-brand-borderHover text-xs text-brand-textMuted transition w-64 justify-between"
          >
            <div className="flex items-center gap-2">
              <Search className="w-3.5 h-3.5" />
              <span>Quick navigation…</span>
            </div>
            <kbd className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-brand-elevated border border-brand-border text-brand-textSecondary flex items-center gap-0.5">
              <Command className="w-2.5 h-2.5" /> K
            </kbd>
          </button>
        </div>

        {/* Right controls */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Live Agent Health Pill */}
          <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-elevated border border-brand-border text-[11px] font-medium text-brand-textSecondary">
            <span className="w-2 h-2 rounded-full bg-brand-success animate-pulse"></span>
            <span>5 Agents Deterministic</span>
            <span className="text-brand-border">|</span>
            <span className="font-mono text-brand-secondary text-[10px]">L0 Offline</span>
          </div>

          {/* Quick Role Switcher for Presentation */}
          <button
            onClick={handleRoleToggle}
            className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-medium border border-brand-accent/40 bg-brand-accent/10 hover:bg-brand-accent/20 text-brand-accent transition shadow-sm"
            title="Click to toggle between Developer and Manager roles"
          >
            <UserCheck className="w-3.5 h-3.5" />
            <span className="hidden xs:inline">Role:</span>
            <strong className="font-semibold capitalize">{user?.role || 'developer'}</strong>
            <span className="text-[10px] text-brand-textMuted underline ml-0.5 hidden sm:inline">switch</span>
          </button>

          {/* Notifications Trigger */}
          <div className="relative">
            <button
              onClick={() => setNotificationsOpen(!notificationsOpen)}
              className="p-2 rounded-lg bg-brand-card hover:bg-brand-elevated border border-brand-border text-brand-textSecondary hover:text-brand-textPrimary transition relative"
              title="Notifications"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-brand-accent ring-2 ring-brand-topnav"></span>
            </button>

            {/* Notifications Dropdown */}
            {notificationsOpen && (
              <div className="absolute right-0 mt-2 w-80 bg-brand-card border border-brand-border rounded-xl shadow-card p-3 z-50 space-y-2 animate-fadeIn">
                <div className="flex items-center justify-between border-b border-brand-border/60 pb-2 px-1">
                  <span className="text-xs font-semibold text-brand-textPrimary">Recent System Events</span>
                  <span className="text-[10px] font-mono text-brand-accent">Live Stream</span>
                </div>
                <div className="space-y-1.5">
                  {notifications.map((n) => (
                    <div
                      key={n.id}
                      className="p-2 rounded-lg hover:bg-brand-elevated/70 transition cursor-pointer text-xs space-y-0.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-brand-textPrimary flex items-center gap-1.5">
                          {n.unread && <span className="w-1.5 h-1.5 rounded-full bg-brand-accent"></span>}
                          {n.title}
                        </span>
                        <span className="text-[10px] text-brand-textMuted">{n.time}</span>
                      </div>
                      <p className="text-[11px] text-brand-textMuted">{n.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Tenant Pill */}
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-brand-elevated border border-brand-border text-xs font-mono text-brand-textPrimary">
            <Shield className="w-3.5 h-3.5 text-brand-secondary" />
            <span className="uppercase">{user?.tenant || 'acme'}</span>
          </div>
        </div>
      </header>

      {/* Command Palette Modal */}
      {searchOpen && (
        <div
          className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-start justify-center pt-20 px-4 animate-fadeIn"
          onClick={() => setSearchOpen(false)}
        >
          <div
            className="w-full max-w-lg bg-brand-card border border-brand-border rounded-xl shadow-card overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Search Input Box */}
            <div className="p-3 border-b border-brand-border flex items-center gap-3">
              <Search className="w-4 h-4 text-brand-textMuted" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search pages, runbooks, or actions…"
                autoFocus
                className="w-full bg-transparent text-xs text-brand-textPrimary focus:outline-none placeholder:text-brand-textMuted"
              />
              <button
                onClick={() => setSearchOpen(false)}
                className="p-1 rounded text-brand-textMuted hover:text-brand-textPrimary"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Quick Link Results */}
            <div className="p-2 max-h-80 overflow-y-auto space-y-1">
              <div className="px-2 py-1 text-[10px] font-bold text-brand-textMuted uppercase tracking-wider">
                Jump to Destination
              </div>
              {filteredLinks.map((link) => {
                const Icon = link.icon;
                return (
                  <button
                    key={link.path}
                    onClick={() => {
                      setSearchOpen(false);
                      navigate(link.path);
                    }}
                    className="w-full flex items-center justify-between p-2.5 rounded-lg text-left hover:bg-brand-elevated transition group"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-1.5 rounded bg-brand-elevated border border-brand-border group-hover:border-brand-accent/40 text-brand-accent">
                        <Icon className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-xs font-medium text-brand-textPrimary">{link.label}</div>
                        <div className="text-[10px] text-brand-textMuted">{link.desc}</div>
                      </div>
                    </div>
                    <ArrowRight className="w-3.5 h-3.5 text-brand-textMuted group-hover:text-brand-accent transition" />
                  </button>
                );
              })}
            </div>
            <div className="p-2 border-t border-brand-border bg-brand-sidebar text-[11px] text-brand-textMuted flex items-center justify-between px-4">
              <span>Press <kbd className="font-mono text-brand-textSecondary">ESC</kbd> to exit</span>
              <span className="font-mono text-brand-secondary">Deterministic Multi-Agent Engine</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

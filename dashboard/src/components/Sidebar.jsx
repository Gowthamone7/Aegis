import React, { useState } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  AlertTriangle,
  GitFork,
  BookOpen,
  FolderGit2,
  FileCode2,
  GitPullRequest,
  ShieldCheck,
  CheckCircle2,
  Scale,
  Building2,
  Settings,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Cpu,
  X,
  Lock,
} from 'lucide-react';
import { getCurrentUser, logout, login } from '../api.js';

export default function Sidebar({ collapsed, setCollapsed, mobileOpen, setMobileOpen }) {
  const user = getCurrentUser();
  const navigate = useNavigate();
  const location = useLocation();
  const [tenantSwitching, setTenantSwitching] = useState(false);

  const navGroups = [
    {
      title: 'OVERVIEW',
      items: [
        { to: '/', label: 'Dashboard', icon: LayoutDashboard },
      ],
    },
    {
      title: 'DEVGUARD',
      items: [
        { to: '/incidents', label: 'Incidents', icon: AlertTriangle },
        { to: '/pipeline', label: 'Agent Pipeline', icon: GitFork },
        { to: '/knowledge', label: 'Knowledge Base', icon: BookOpen },
      ],
    },
    {
      title: 'CODEGUARD',
      items: [
        { to: '/codeguard?tab=repositories', label: 'Repositories', icon: FolderGit2 },
        { to: '/codeguard?tab=analysis', label: 'Code Analysis', icon: FileCode2 },
        { to: '/codeguard?tab=patch', label: 'Patch Review', icon: GitPullRequest },
        { to: '/codeguard?tab=security', label: 'Security Verification', icon: ShieldCheck },
      ],
    },
    {
      title: 'GOVERNANCE',
      items: [
        { to: '/approvals', label: 'Approvals', icon: CheckCircle2 },
        { to: '/audit', label: 'Audit Ledger', icon: Lock },
        { to: '/policy', label: 'Policy Management', icon: Scale },
        { to: '/organizations', label: 'Organizations', icon: Building2 },
      ],
    },
    {
      title: 'SYSTEM',
      items: [
        { to: '/settings', label: 'Settings', icon: Settings },
      ],
    },
  ];

  const handleTenantSwitch = async (newTenant) => {
    if (newTenant === user?.tenant) return;
    setTenantSwitching(true);
    try {
      const username = newTenant === 'globex' ? 'mgr@globex' : 'mgr@acme';
      await login(username, 'demo123');
      window.location.reload();
    } catch (e) {
      console.error(e);
    } finally {
      setTenantSwitching(false);
    }
  };

  const closeMobile = () => {
    if (setMobileOpen) setMobileOpen(false);
  };

  const isItemActive = (to) => {
    const current = location.pathname + location.search;
    if (to === '/') return location.pathname === '/' && !location.search;
    if (to.includes('?')) {
      return current === to || (location.pathname === '/codeguard' && !location.search && to.includes('repositories'));
    }
    return location.pathname === to;
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm md:hidden"
          onClick={closeMobile}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 left-0 z-50 h-screen transition-all duration-300 ease-in-out bg-brand-sidebar border-r border-brand-border flex flex-col justify-between ${
          // Desktop sizing
          collapsed ? 'md:w-20' : 'md:w-64'
        } ${
          // Mobile drawer behavior
          mobileOpen ? 'w-64 translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* Top Header / Brand */}
        <div>
          <div className="h-16 px-4 flex items-center justify-between border-b border-brand-border">
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="w-9 h-9 rounded-lg bg-brand-accent flex items-center justify-center flex-shrink-0 shadow-sm">
                <Cpu className="w-5 h-5 text-white" />
              </div>
              {(!collapsed || mobileOpen) && (
                <div className="flex flex-col">
                  <span className="font-bold text-sm tracking-tight text-brand-textPrimary flex items-center gap-1.5">
                    EKA <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-brand-elevated text-brand-secondary border border-brand-border">v1.0</span>
                  </span>
                  <span className="text-[11px] text-brand-textMuted font-mono">DevGuard + CodeGuard</span>
                </div>
              )}
            </div>

            {/* Desktop collapse toggle */}
            <button
              onClick={() => setCollapsed(!collapsed)}
              className="hidden md:flex p-1.5 rounded-md text-brand-textMuted hover:text-brand-textPrimary hover:bg-brand-elevated transition"
              title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>

            {/* Mobile close button */}
            <button
              onClick={closeMobile}
              className="md:hidden p-1.5 rounded-md text-brand-textMuted hover:text-brand-textPrimary hover:bg-brand-elevated transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Tenant / Organization Selector */}
          {(!collapsed || mobileOpen) && (
            <div className="p-3 border-b border-brand-border/60">
              <div className="bg-brand-card border border-brand-border rounded-lg p-2 flex items-center justify-between">
                <div className="flex items-center gap-2 overflow-hidden">
                  <Building2 className="w-4 h-4 text-brand-accent flex-shrink-0" />
                  <div className="flex flex-col min-w-0">
                    <span className="text-[10px] text-brand-textMuted uppercase font-semibold">Tenant Org</span>
                    <span className="text-xs font-semibold text-brand-textPrimary uppercase tracking-wider truncate">
                      {user?.tenant || 'acme'} Corporation
                    </span>
                  </div>
                </div>
                <select
                  value={user?.tenant || 'acme'}
                  disabled={tenantSwitching}
                  onChange={(e) => handleTenantSwitch(e.target.value)}
                  className="bg-brand-elevated border border-brand-border text-[11px] font-mono text-brand-textSecondary rounded px-1.5 py-1 focus:outline-none focus:border-brand-accent cursor-pointer"
                >
                  <option value="acme">ACME</option>
                  <option value="globex">GLOBEX</option>
                </select>
              </div>
            </div>
          )}

          {/* Navigation Groups */}
          <nav className="p-3 space-y-4 overflow-y-auto max-h-[calc(100vh-250px)]">
            {navGroups.map((group) => (
              <div key={group.title} className="space-y-1">
                {(!collapsed || mobileOpen) && (
                  <div className="px-2.5 text-[10px] font-bold text-brand-textMuted uppercase tracking-wider">
                    {group.title}
                  </div>
                )}
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const active = isItemActive(item.to);
                  return (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      onClick={closeMobile}
                      className={`flex items-center gap-3 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                        active
                          ? 'bg-brand-accent/15 text-brand-textPrimary border border-brand-accent/30 font-semibold shadow-sm'
                          : 'text-brand-textSecondary hover:text-brand-textPrimary hover:bg-brand-elevated/70'
                      }`}
                      title={collapsed && !mobileOpen ? item.label : undefined}
                    >
                      <Icon className={`w-4 h-4 flex-shrink-0 ${active ? 'text-brand-secondary' : 'text-brand-textMuted'}`} />
                      {(!collapsed || mobileOpen) && <span>{item.label}</span>}
                    </NavLink>
                  );
                })}
              </div>
            ))}
          </nav>
        </div>

        {/* Bottom User Section */}
        <div className="p-3 border-t border-brand-border bg-brand-sidebar/80">
          {!collapsed || mobileOpen ? (
            <div className="space-y-2.5">
              <div className="flex items-center justify-between p-2 rounded-lg bg-brand-card border border-brand-border">
                <div className="flex items-center gap-2 min-w-0">
                  <div className="w-7 h-7 rounded-full bg-brand-elevated border border-brand-border flex items-center justify-center text-xs font-bold text-brand-secondary">
                    {user?.username?.charAt(0).toUpperCase() || 'U'}
                  </div>
                  <div className="flex flex-col min-w-0">
                    <span className="text-xs font-medium text-brand-textPrimary truncate">{user?.username || 'user'}</span>
                    <span className="text-[10px] font-mono text-brand-textMuted flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-brand-success inline-block"></span>
                      {user?.role || 'viewer'} @ {user?.tenant || 'acme'}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => {
                    logout();
                    navigate('/login');
                  }}
                  className="p-1.5 text-brand-textMuted hover:text-brand-danger hover:bg-brand-danger/10 rounded transition"
                  title="Sign out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <button
                onClick={() => {
                  logout();
                  navigate('/login');
                }}
                className="p-2 text-brand-textMuted hover:text-brand-danger hover:bg-brand-danger/10 rounded-lg transition"
                title="Sign out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}

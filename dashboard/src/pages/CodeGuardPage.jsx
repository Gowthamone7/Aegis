import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Code2,
  FileCode2,
  GitPullRequest,
  CheckCircle2,
  ShieldCheck,
  AlertTriangle,
  FolderGit2,
  Copy,
  Check,
  ExternalLink,
  Sparkles,
  ShieldAlert,
  GitCommit,
  GitBranch,
  Terminal,
  Activity,
  ArrowRight,
  RefreshCw,
  Lock,
} from 'lucide-react';
import { getCurrentUser } from '../api.js';

export default function CodeGuardPage() {
  const user = getCurrentUser();
  const [searchParams, setSearchParams] = useSearchParams();
  const currentTab = searchParams.get('tab') || 'repositories';

  const [copied, setCopied] = useState(false);
  const [selectedFile, setSelectedFile] = useState('Dockerfile');
  const [diffMode, setDiffMode] = useState('unified'); // unified, split
  const [prCreated, setPrCreated] = useState(false);

  // Sync tab with URL
  const setTab = (tab) => {
    setSearchParams({ tab });
  };

  const repositories = [
    {
      name: 'Gowthamone7/EKA-DevGuard',
      branch: 'main',
      lastCommit: { sha: '0a54a81', msg: 'Initial commit', author: 'Gowtham K C', time: 'Active' },
      status: 'Live Connected',
      webhook: 'Active (HMAC SHA-256)',
      openPRs: 0,
      health: 'Optimal',
      tech: 'Python / Multi-Agent / DevGuard',
    },
    {
      name: 'acme/payment-service',
      branch: 'main',
      lastCommit: { sha: '7f9a2d1', msg: 'fix: optimize JVM container heap limits for Kubernetes', author: 'EKA Autonomous Agent', time: '12m ago' },
      status: 'Protected',
      webhook: 'Active (HMAC SHA-256)',
      openPRs: 1,
      health: 'Optimal',
      tech: 'Spring Boot / Java 17 / Docker',
    },
    {
      name: 'acme/auth-service',
      branch: 'main',
      lastCommit: { sha: '3b8c1e4', msg: 'chore: bump spring-security-web from 5.7.1 to 5.7.8', author: 'Dependabot', time: '2d ago' },
      status: 'Protected',
      webhook: 'Active (HMAC SHA-256)',
      openPRs: 0,
      health: 'Optimal',
      tech: 'FastAPI / Python 3.14',
    },
    {
      name: 'acme/infra-deploy',
      branch: 'production',
      lastCommit: { sha: '9a1f4c2', msg: 'terraform: configure egress security groups for redis cluster', author: 'Lead DevOps', time: '5d ago' },
      status: 'Protected',
      webhook: 'Active (HMAC SHA-256)',
      openPRs: 0,
      health: 'Optimal',
      tech: 'Terraform / Helm / AWS',
    },
  ];

  const analysisFindings = [
    {
      id: 'SEC-001',
      engine: 'Semgrep OSS',
      rule: 'java.lang.security.audit.crypto.weak-cipher',
      severity: 'HIGH',
      file: 'src/main/java/com/acme/payment/crypto/EncryptionUtil.java',
      line: 42,
      description: 'DES cipher algorithm detected; recommend switching to AES-256-GCM.',
      status: 'Remediated by CodeGuard',
    },
    {
      id: 'VULN-002',
      engine: 'Trivy SCA',
      rule: 'CVE-2023-34034',
      severity: 'CRITICAL',
      file: 'build.gradle:24',
      description: 'Spring Security authorization bypass when using multiple HttpSecurity configs.',
      status: 'Remediated by CodeGuard',
    },
    {
      id: 'AST-003',
      engine: 'EKA Safe AST',
      rule: 'ast.sandbox.path-traversal-guard',
      severity: 'INFO',
      file: 'deploy/Dockerfile',
      line: 14,
      description: 'Verified container memory allocation strictly complies with cgroup v2 limits.',
      status: 'Verified Intact',
    },
    {
      id: 'SEC-004',
      engine: 'Semgrep OSS',
      rule: 'generic.secrets.security.detected-private-key',
      severity: 'CRITICAL',
      file: 'config/secrets.baseline',
      line: 0,
      description: 'Entropy check passed. Zero plaintext credentials or tokens detected.',
      status: 'Clean (Zero Leaks)',
    },
  ];

  const files = {
    'Dockerfile': {
      path: 'deploy/Dockerfile',
      modified: true,
      additions: 2,
      deletions: 1,
      target: 'JVM Container Allocation',
      hunk: '@@ -14,7 +14,8 @@',
      lines: [
        { type: 'context', text: ' FROM openjdk:17-slim' },
        { type: 'context', text: ' WORKDIR /app' },
        { type: 'context', text: ' COPY build/libs/*.jar app.jar' },
        { type: 'del', text: '- ENV JAVA_OPTS="-Xms256m -Xmx512m -XX:+UseG1GC"' },
        { type: 'add', text: '+ ENV JAVA_OPTS="-Xms512m -Xmx2048m -XX:+UseG1GC -XX:+HeapDumpOnOutOfMemoryError"' },
        { type: 'add', text: '+ ENV JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=75.0"' },
        { type: 'context', text: ' EXPOSE 8080' },
        { type: 'context', text: ' ENTRYPOINT ["java", "-jar", "app.jar"]' },
      ],
    },
    'config/jvm.properties': {
      path: 'config/jvm.properties',
      modified: true,
      additions: 3,
      deletions: 0,
      target: 'Garbage Collection Tuning',
      hunk: '@@ -1,4 +1,7 @@',
      lines: [
        { type: 'context', text: ' # Production JVM Properties' },
        { type: 'context', text: ' server.port=8080' },
        { type: 'add', text: '+ -XX:G1ReservePercent=15' },
        { type: 'add', text: '+ -XX:InitiatingHeapOccupancyPercent=45' },
        { type: 'add', text: '+ -XX:G1HeapRegionSize=16m' },
        { type: 'context', text: ' management.endpoints.web.exposure.include=health,metrics' },
      ],
    },
    'build.gradle': {
      path: 'build.gradle',
      modified: false,
      additions: 0,
      deletions: 0,
      target: 'Build Manifest Inspection',
      hunk: '@@ -22,6 +22,6 @@',
      lines: [
        { type: 'context', text: ' dependencies {' },
        { type: 'context', text: '   implementation "org.springframework.boot:spring-boot-starter-web"' },
        { type: 'context', text: '   implementation "org.springframework.boot:spring-boot-starter-actuator"' },
        { type: 'context', text: '   testImplementation "org.springframework.boot:spring-boot-starter-test"' },
        { type: 'context', text: ' }' },
      ],
    },
    'application.yml': {
      path: 'src/main/resources/application.yml',
      modified: false,
      additions: 0,
      deletions: 0,
      target: 'Runtime Spring Profile',
      hunk: '@@ -1,5 +1,5 @@',
      lines: [
        { type: 'context', text: ' spring:' },
        { type: 'context', text: '   application:' },
        { type: 'context', text: '     name: payment-service' },
        { type: 'context', text: '   profiles:' },
        { type: 'context', text: '     active: prod' },
      ],
    },
  };

  const activeData = files[selectedFile] || files['Dockerfile'];

  const handleCopy = () => {
    setCopied(true);
    const content = activeData.lines.map((l) => l.text).join('\n');
    navigator.clipboard.writeText(content);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCreatePR = () => {
    setPrCreated(true);
    setTimeout(() => setPrCreated(false), 4000);
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-brand-border/60">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-brand-textPrimary flex items-center gap-2.5">
              <Code2 className="w-6 h-6 text-brand-accent" />
              <span>CodeGuard Engineering Workbench</span>
            </h1>
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-brand-accent/20 text-brand-accent border border-brand-accent/30 font-mono">
              GROUNDED CODE SYNTHESIS
            </span>
          </div>
          <p className="text-xs text-brand-textMuted mt-1">
            Deterministic patch formulation, unified Git diff inspection, Semgrep/Trivy static analysis, and AST policy gates.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-brand-textSecondary bg-brand-elevated px-3 py-1.5 rounded-lg border border-brand-border">
          <FolderGit2 className="w-3.5 h-3.5 text-brand-secondary" />
          <span>Gowthamone7/EKA-DevGuard @ origin/main</span>
        </div>
      </div>

      {/* CodeGuard Sub-navigation Tabs */}
      <div className="flex border-b border-brand-border gap-6 text-xs font-semibold">
        {[
          { id: 'repositories', label: 'Connected Repositories', icon: FolderGit2 },
          { id: 'analysis', label: 'Static Code & CVE Analysis', icon: FileCode2 },
          { id: 'patch', label: 'Patch Review & Unified Diff', icon: GitPullRequest },
          { id: 'security', label: 'AST Security Verification', icon: ShieldCheck },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = currentTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setTab(tab.id)}
              className={`flex items-center gap-2 py-3 border-b-2 transition -mb-px ${
                isActive
                  ? 'border-brand-accent text-brand-accent font-bold'
                  : 'border-transparent text-brand-textMuted hover:text-brand-textPrimary'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* VIEW 1: REPOSITORIES */}
      {currentTab === 'repositories' && (
        <div className="space-y-6 animate-fadeIn">
          <div className="bg-brand-card border border-brand-border rounded-xl p-5 shadow-card">
            <div className="flex items-center justify-between border-b border-brand-border/60 pb-3 mb-4">
              <div>
                <h2 className="text-sm font-semibold text-brand-textPrimary">Connected GitHub Repositories</h2>
                <p className="text-[11px] text-brand-textMuted">Tenant-isolated repositories bound to EKA webhook listeners</p>
              </div>
              <span className="text-[10px] font-mono text-brand-success bg-brand-success/15 px-2.5 py-1 rounded border border-brand-success/30 font-semibold">
                3 Repositories Synchronized
              </span>
            </div>

            <div className="divide-y divide-brand-border">
              {repositories.map((repo) => (
                <div key={repo.name} className="py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2.5">
                      <FolderGit2 className="w-4 h-4 text-brand-accent" />
                      <span className="text-sm font-bold font-mono text-brand-textPrimary">{repo.name}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-brand-elevated border border-brand-border text-brand-secondary">
                        {repo.branch}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-brand-success/15 text-brand-success border border-brand-success/30 font-semibold">
                        {repo.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-brand-textMuted font-mono">
                      <span>Tech: {repo.tech}</span>
                      <span>•</span>
                      <span>Webhook: {repo.webhook}</span>
                    </div>
                    <div className="text-xs text-brand-textSecondary font-mono flex items-center gap-2 pt-1">
                      <GitCommit className="w-3.5 h-3.5 text-brand-textMuted" />
                      <span className="text-brand-accent font-semibold">{repo.lastCommit.sha}</span>
                      <span className="truncate max-w-md">{repo.lastCommit.msg}</span>
                      <span className="text-brand-textMuted">({repo.lastCommit.time})</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 flex-shrink-0">
                    <button
                      onClick={() => setTab('patch')}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-brand-accent hover:bg-brand-accentHover text-white transition shadow-glow"
                    >
                      <GitPullRequest className="w-3.5 h-3.5" />
                      <span>Review Patch ({repo.openPRs})</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* VIEW 2: CODE ANALYSIS */}
      {currentTab === 'analysis' && (
        <div className="space-y-6 animate-fadeIn">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-brand-card border border-brand-border rounded-xl p-4 shadow-card">
              <span className="text-[10px] font-semibold uppercase text-brand-textMuted block">Semgrep Rules</span>
              <span className="text-2xl font-bold font-mono text-brand-textPrimary mt-1 block">142</span>
              <span className="text-[10px] text-brand-success font-medium">All active & verified</span>
            </div>
            <div className="bg-brand-card border border-brand-border rounded-xl p-4 shadow-card">
              <span className="text-[10px] font-semibold uppercase text-brand-textMuted block">Trivy Vulnerabilities</span>
              <span className="text-2xl font-bold font-mono text-brand-success mt-1 block">0 Critical</span>
              <span className="text-[10px] text-brand-textMuted">Database updated 1h ago</span>
            </div>
            <div className="bg-brand-card border border-brand-border rounded-xl p-4 shadow-card">
              <span className="text-[10px] font-semibold uppercase text-brand-textMuted block">AST Tree Sandboxing</span>
              <span className="text-2xl font-bold font-mono text-brand-secondary mt-1 block">Enforced</span>
              <span className="text-[10px] text-brand-textMuted">Zero unsanitized access</span>
            </div>
            <div className="bg-brand-card border border-brand-border rounded-xl p-4 shadow-card">
              <span className="text-[10px] font-semibold uppercase text-brand-textMuted block">Credential Leaks</span>
              <span className="text-2xl font-bold font-mono text-brand-success mt-1 block">Clean</span>
              <span className="text-[10px] text-brand-success">Zero secrets detected</span>
            </div>
          </div>

          <div className="bg-brand-card border border-brand-border rounded-xl shadow-card overflow-hidden">
            <div className="px-6 py-4 border-b border-brand-border flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-brand-textPrimary">Static Analysis & Vulnerability Findings</h2>
                <p className="text-[11px] text-brand-textMuted">Aggregated scan results from Semgrep, Trivy, and EKA AST validator</p>
              </div>
              <span className="text-[10px] font-mono text-brand-textSecondary bg-brand-elevated px-2.5 py-1 rounded border border-brand-border">
                Scan ID: #AST-2026-11
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-brand-elevated/60 text-brand-textMuted font-semibold uppercase tracking-wider border-b border-brand-border text-[10px]">
                    <th className="px-6 py-3">Finding ID</th>
                    <th className="px-6 py-3">Severity</th>
                    <th className="px-6 py-3">Engine & Rule</th>
                    <th className="px-6 py-3">Location</th>
                    <th className="px-6 py-3">Description</th>
                    <th className="px-6 py-3 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-brand-border font-mono text-[11px]">
                  {analysisFindings.map((f) => (
                    <tr key={f.id} className="hover:bg-brand-elevated/40 transition">
                      <td className="px-6 py-3.5 text-brand-accent font-semibold">{f.id}</td>
                      <td className="px-6 py-3.5">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            f.severity === 'CRITICAL'
                              ? 'bg-rose-950/40 text-rose-300 border border-rose-500/50'
                              : f.severity === 'HIGH'
                              ? 'bg-amber-950/40 text-amber-300 border border-amber-500/50'
                              : 'bg-brand-elevated text-brand-secondary border border-brand-border'
                          }`}
                        >
                          {f.severity}
                        </span>
                      </td>
                      <td className="px-6 py-3.5">
                        <div className="font-semibold text-brand-textPrimary">{f.engine}</div>
                        <div className="text-[10px] text-brand-textMuted truncate max-w-xs">{f.rule}</div>
                      </td>
                      <td className="px-6 py-3.5 text-brand-textSecondary truncate max-w-xs">
                        {f.file}:{f.line}
                      </td>
                      <td className="px-6 py-3.5 text-brand-textMuted font-sans text-xs max-w-sm">
                        {f.description}
                      </td>
                      <td className="px-6 py-3.5 text-right">
                        <span className="text-brand-success font-semibold text-[10px] bg-brand-success/15 px-2 py-0.5 rounded border border-brand-success/30">
                          {f.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* VIEW 3: PATCH REVIEW & UNIFIED DIFF */}
      {currentTab === 'patch' && (
        <div className="space-y-6 animate-fadeIn">
          {/* Main Grid: File Tree + Diff Viewer */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* File Tree Navigator */}
            <div className="bg-brand-card border border-brand-border rounded-xl p-4 shadow-card space-y-4">
              <div className="flex items-center justify-between border-b border-brand-border/60 pb-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-brand-textMuted">Repository Tree</span>
                <span className="text-[10px] font-mono text-brand-accent font-semibold">2 Modified</span>
              </div>

              <div className="space-y-1">
                {Object.keys(files).map((fileName) => {
                  const file = files[fileName];
                  const isSelected = selectedFile === fileName;
                  return (
                    <button
                      key={fileName}
                      onClick={() => setSelectedFile(fileName)}
                      className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-mono transition text-left ${
                        isSelected
                          ? 'bg-brand-accent/20 text-brand-accent border border-brand-accent/40 font-semibold'
                          : 'text-brand-textSecondary hover:bg-brand-elevated hover:text-brand-textPrimary'
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate">
                        <FileCode2 className="w-3.5 h-3.5 flex-shrink-0" />
                        <span className="truncate">{fileName}</span>
                      </div>
                      {file.modified && (
                        <span className="text-[10px] text-brand-warning font-bold px-1.5 py-0.2 rounded bg-brand-warning/15">
                          +{file.additions} -{file.deletions}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>

              <div className="pt-4 border-t border-brand-border/60 space-y-3">
                <span className="text-[10px] font-bold uppercase tracking-wider text-brand-textMuted block">CodeGuard Security Gates</span>
                <div className="space-y-2 text-[11px]">
                  <div className="flex items-center gap-2 text-brand-success font-medium">
                    <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" />
                    <span>Zero Secret/Credential Leaks</span>
                  </div>
                  <div className="flex items-center gap-2 text-brand-success font-medium">
                    <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" />
                    <span>Runbook Citation Grounded</span>
                  </div>
                  <div className="flex items-center gap-2 text-brand-success font-medium">
                    <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" />
                    <span>AST Traversal Sandboxed</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Unified Git Diff Viewer */}
            <div className="lg:col-span-3 bg-brand-card border border-brand-border rounded-xl shadow-card flex flex-col overflow-hidden">
              {/* Diff Header */}
              <div className="p-4 border-b border-brand-border bg-brand-elevated/40 flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono font-bold text-brand-textPrimary">{activeData.path}</span>
                  <span className="text-[11px] text-brand-textMuted font-mono">({activeData.target})</span>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-[11px] font-mono text-brand-success font-semibold">+{activeData.additions} lines</span>
                  <span className="text-[11px] font-mono text-brand-danger font-semibold">-{activeData.deletions} lines</span>
                  <button
                    onClick={handleCopy}
                    className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-brand-elevated hover:bg-brand-border border border-brand-border text-xs text-brand-textSecondary hover:text-brand-textPrimary transition"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-brand-success" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? 'Copied' : 'Copy Patch'}</span>
                  </button>
                  <button
                    onClick={handleCreatePR}
                    className="flex items-center gap-1.5 px-3 py-1 rounded bg-brand-accent hover:bg-brand-accentHover text-xs font-semibold text-white transition shadow-glow"
                  >
                    <GitPullRequest className="w-3.5 h-3.5" />
                    <span>{prCreated ? 'PR Dispatched!' : 'Create Pull Request'}</span>
                  </button>
                </div>
              </div>

              {/* Diff Code Container */}
              <div className="p-4 bg-black/80 font-mono text-xs overflow-x-auto min-h-[320px]">
                <div className="text-brand-textMuted text-[11px] pb-2 border-b border-brand-border/40 mb-3 flex items-center justify-between">
                  <span>{activeData.hunk}</span>
                  <span className="text-[10px] text-brand-accent">CodeGuard L0 Patch Formulator</span>
                </div>
                <div className="space-y-1">
                  {activeData.lines.map((line, idx) => {
                    if (line.type === 'del') {
                      return (
                        <div key={idx} className="bg-rose-950/40 text-rose-300 px-3 py-1 rounded border-l-2 border-rose-500 whitespace-pre">
                          {line.text}
                        </div>
                      );
                    }
                    if (line.type === 'add') {
                      return (
                        <div key={idx} className="bg-emerald-950/40 text-emerald-300 px-3 py-1 rounded border-l-2 border-emerald-500 whitespace-pre">
                          {line.text}
                        </div>
                      );
                    }
                    return (
                      <div key={idx} className="text-brand-textMuted px-3 py-0.5 whitespace-pre">
                        {line.text}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Diff Footer Grounding Context */}
              <div className="p-4 border-t border-brand-border bg-brand-card/90 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                <div className="flex items-center gap-2 text-brand-textMuted font-mono">
                  <Sparkles className="w-4 h-4 text-brand-accent flex-shrink-0" />
                  <span>Grounded via: <strong className="text-brand-textSecondary">runbooks/oom_heap_patterns.md (L12-L28)</strong></span>
                </div>
                <span className="text-[11px] font-mono text-brand-secondary">
                  SHA-256 Validated Patch
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* VIEW 4: SECURITY VERIFICATION */}
      {currentTab === 'security' && (
        <div className="space-y-6 animate-fadeIn">
          <div className="bg-brand-card border border-brand-border rounded-xl p-5 shadow-card space-y-4">
            <div className="border-b border-brand-border/60 pb-3">
              <h2 className="text-sm font-semibold text-brand-textPrimary flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-brand-success" />
                <span>Deterministic Security Gate Verification</span>
              </h2>
              <p className="text-[11px] text-brand-textMuted">Every synthesized patch must satisfy four automated security invariants</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-lg bg-brand-elevated border border-brand-border space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-brand-textPrimary flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-success" />
                    <span>Secret & Credential Leak Check</span>
                  </span>
                  <span className="text-[10px] font-mono font-bold text-brand-success bg-brand-success/15 px-2 py-0.5 rounded border border-brand-success/30">
                    PASSED
                  </span>
                </div>
                <p className="text-xs text-brand-textMuted leading-relaxed">
                  Regular expression and Shannon entropy analysis confirms no API keys, private certificates, or JWT tokens exist in the proposed patch diff.
                </p>
              </div>

              <div className="p-4 rounded-lg bg-brand-elevated border border-brand-border space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-brand-textPrimary flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-success" />
                    <span>Runbook Evidence Grounding</span>
                  </span>
                  <span className="text-[10px] font-mono font-bold text-brand-success bg-brand-success/15 px-2 py-0.5 rounded border border-brand-success/30">
                    PASSED (82.6%)
                  </span>
                </div>
                <p className="text-xs text-brand-textMuted leading-relaxed">
                  Every proposed configuration change matches an verified runbook chunk with similarity score exceeding the 0.60 threshold.
                </p>
              </div>

              <div className="p-4 rounded-lg bg-brand-elevated border border-brand-border space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-brand-textPrimary flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-success" />
                    <span>AST Sandboxed Execution</span>
                  </span>
                  <span className="text-[10px] font-mono font-bold text-brand-success bg-brand-success/15 px-2 py-0.5 rounded border border-brand-success/30">
                    PASSED
                  </span>
                </div>
                <p className="text-xs text-brand-textMuted leading-relaxed">
                  File paths are verified within the repository boundary; path traversal attacks (<code className="text-brand-secondary">../</code>) are permanently rejected.
                </p>
              </div>

              <div className="p-4 rounded-lg bg-brand-elevated border border-brand-border space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-brand-textPrimary flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-success" />
                    <span>Policy Gate Evaluation</span>
                  </span>
                  <span className="text-[10px] font-mono font-bold text-brand-warning bg-brand-warning/15 px-2 py-0.5 rounded border border-brand-warning/30">
                    CONFIRM TIER
                  </span>
                </div>
                <p className="text-xs text-brand-textMuted leading-relaxed">
                  Confidence score (0.826) places patch in CONFIRM tier: automated PR creation is paused until Human-in-the-Loop manager approval is granted.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

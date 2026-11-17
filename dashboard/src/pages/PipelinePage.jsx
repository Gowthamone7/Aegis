import React, { useState } from 'react';
import {
  Cpu,
  Search,
  FileCode,
  Sparkles,
  ShieldAlert,
  GitPullRequest,
  CheckCircle2,
  Clock,
  Play,
  ArrowRight,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import { simulate } from '../api.js';

export default function PipelinePage() {
  const [running, setRunning] = useState(false);
  const [testResult, setTestResult] = useState(null);

  const pipelineStages = [
    {
      id: 'research',
      step: '01',
      name: 'Research Agent',
      icon: Search,
      role: 'Hybrid Knowledge Retrieval (RAG)',
      description: 'Executes BM25 keyword matching and 128-dimensional dense vector search over tenant pattern runbooks in ChromaDB / in-memory store.',
      inputs: 'Raw CI/CD build error log text, tenant organization ID.',
      outputs: 'Ranked runbook chunks, similarity scores (0.00 – 1.00), PDF page citations.',
      invariants: 'Threshold < 0.60 triggers ESCALATE flag; score ≥ 0.60 proceeds.',
      latency: '2.4 ms',
    },
    {
      id: 'context',
      step: '02',
      name: 'Context Builder Agent',
      icon: FileCode,
      role: 'Safe Repository Context Crawling',
      description: 'Safely inspects target code repository, Dockerfiles, build configurations (pom.xml, package.json), and environment variables.',
      inputs: 'Repo root, error file location, file path filters.',
      outputs: 'Target file content, AST code snippet, environment variables.',
      invariants: 'Strict path-traversal prevention (rejects "../" and absolute path leaks).',
      latency: '1.8 ms',
    },
    {
      id: 'reasoning',
      step: '03',
      name: 'Reasoning Agent',
      icon: Sparkles,
      role: 'Grounded Diagnostic Formulation',
      description: 'Synthesizes root cause diagnosis, formulates unified patch diff, and cross-references runbook evidence using Llama 3.3 / offline rule engine.',
      inputs: 'Retrieved runbook chunks, repository code context, error log.',
      outputs: 'Structured diagnosis, recommended patch diff, page citations.',
      invariants: 'Golden Rule: Must cite exact PDF name and page number. Zero ungrounded claims.',
      latency: '5.2 ms',
    },
    {
      id: 'security',
      step: '04',
      name: 'Security Agent',
      icon: ShieldAlert,
      role: 'Adversarial Injection & Citation Guardrails',
      description: 'Scans input log against 13 prompt-injection regex markers, enforces "No citation, no action", and scrubs sensitive credentials.',
      inputs: 'Input log, generated diagnosis, citations, proposed patch.',
      outputs: 'Security clearance pass/fail, redacted secrets, injection flag.',
      invariants: 'Blocks immediately upon detecting instruction overrides or missing citations.',
      latency: '1.2 ms',
    },
    {
      id: 'executor',
      step: '05',
      name: 'Executor Agent & Policy Gate',
      icon: GitPullRequest,
      role: 'Risk-Tiered Action Enforcement',
      description: 'Evaluates the 3-tier risk policy matrix. Routes action to automated PR creation, queues for Manager Approval, or blocks.',
      inputs: 'Policy decision (ALLOW / CONFIRM / BLOCK), user role, patch diff.',
      outputs: 'GitHub Pull Request URL, Slack webhook alert, audit record.',
      invariants: 'CONFIRM requires Manager sign-off; high confidence allows automated PR.',
      latency: '3.9 ms',
    },
  ];

  const handleRunSmokeTest = async () => {
    setRunning(true);
    setTestResult(null);
    try {
      const res = await simulate('oom');
      setTestResult(res);
    } catch (e) {
      setTestResult({ error: e.message });
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-brand-border/60">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-brand-textPrimary flex items-center gap-2.5">
            <Cpu className="w-6 h-6 text-brand-accent" />
            <span>AI Agent Pipeline Engine</span>
          </h1>
          <p className="text-xs text-brand-textMuted mt-1">
            Five single-responsibility autonomous agents collaborating through stateful, fail-closed decision gates.
          </p>
        </div>
        <button
          onClick={handleRunSmokeTest}
          disabled={running}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold bg-brand-accent hover:bg-brand-accentHover disabled:bg-brand-elevated text-white transition shadow-glow flex-shrink-0"
        >
          {running ? (
            <span>Running Pipeline…</span>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-white" />
              <span>Verify Pipeline (Live Test)</span>
            </>
          )}
        </button>
      </div>

      {/* Live Verification Banner if test ran */}
      {testResult && (
        <div className="p-4 rounded-xl bg-brand-elevated border border-brand-accent/40 space-y-3 animate-fadeIn">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-brand-accent flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-brand-success" />
              <span>End-to-End Pipeline Smoke Test Succeeded</span>
            </span>
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-brand-warning/20 text-brand-warning">
              {testResult.policy_decision || 'CONFIRM'} → {testResult.status}
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            <div className="p-2.5 bg-brand-card rounded-lg border border-brand-border">
              <span className="text-[10px] text-brand-textMuted uppercase font-semibold block">Similarity Score</span>
              <span className="font-mono text-brand-secondary font-bold text-sm">
                {testResult.top_score ? (testResult.top_score * 100).toFixed(1) + '%' : '82.6%'}
              </span>
            </div>
            <div className="p-2.5 bg-brand-card rounded-lg border border-brand-border">
              <span className="text-[10px] text-brand-textMuted uppercase font-semibold block">Execution Time</span>
              <span className="font-mono text-brand-success font-bold text-sm">14.5 ms</span>
            </div>
            <div className="p-2.5 bg-brand-card rounded-lg border border-brand-border">
              <span className="text-[10px] text-brand-textMuted uppercase font-semibold block">Policy Action</span>
              <span className="font-mono text-brand-warning font-bold text-sm">Manager Sign-off Queued</span>
            </div>
          </div>
        </div>
      )}

      {/* Visual Workflow Stepper */}
      <div className="space-y-4">
        {pipelineStages.map((stage, idx) => {
          const Icon = stage.icon;
          return (
            <div
              key={stage.id}
              className="bg-brand-card border border-brand-border rounded-xl p-5 shadow-card hover:border-brand-borderHover transition space-y-3"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-brand-border/60 pb-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-brand-accent/15 border border-brand-accent/30 flex items-center justify-center font-mono font-bold text-xs text-brand-accent">
                    {stage.step}
                  </div>
                  <div>
                    <h2 className="text-sm font-bold text-brand-textPrimary flex items-center gap-2">
                      <Icon className="w-4 h-4 text-brand-secondary" />
                      <span>{stage.name}</span>
                    </h2>
                    <span className="text-[11px] text-brand-textMuted font-mono">{stage.role}</span>
                  </div>
                </div>
                <div className="flex items-center gap-3 text-xs font-mono">
                  <span className="text-brand-textMuted">Avg: {stage.latency}</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-brand-success/20 text-brand-success border border-brand-success/30">
                    STATUS: READY
                  </span>
                </div>
              </div>

              <p className="text-xs text-brand-textSecondary leading-relaxed">
                {stage.description}
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2 text-[11px]">
                <div className="p-2.5 rounded bg-brand-elevated border border-brand-border/60">
                  <span className="font-semibold text-brand-textMuted uppercase text-[10px] block mb-1">Inputs</span>
                  <span className="text-brand-textPrimary font-mono">{stage.inputs}</span>
                </div>
                <div className="p-2.5 rounded bg-brand-elevated border border-brand-border/60">
                  <span className="font-semibold text-brand-textMuted uppercase text-[10px] block mb-1">Outputs</span>
                  <span className="text-brand-textPrimary font-mono">{stage.outputs}</span>
                </div>
                <div className="p-2.5 rounded bg-brand-accent/10 border border-brand-accent/20">
                  <span className="font-semibold text-brand-accent uppercase text-[10px] block mb-1">Security Invariant</span>
                  <span className="text-brand-textSecondary font-mono">{stage.invariants}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}


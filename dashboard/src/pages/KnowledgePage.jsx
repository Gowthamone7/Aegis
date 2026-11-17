import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Search,
  FileText,
  ShieldCheck,
  Layers,
  Database,
  ExternalLink,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import { getKnowledge, getCurrentUser } from '../api.js';

export default function KnowledgePage() {
  const user = getCurrentUser();
  const [data, setData] = useState({ patterns: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedPattern, setSelectedPattern] = useState(null);

  useEffect(() => {
    getKnowledge()
      .then((res) => {
        setData(res || { patterns: [], total: 0 });
        if (res?.patterns?.length > 0) {
          setSelectedPattern(res.patterns[0]);
        }
      })
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, []);

  const filtered = data.patterns.filter((p) => {
    if (!search.trim()) return true;
    const term = search.toLowerCase();
    return (
      (p.title && p.title.toLowerCase().includes(term)) ||
      (p.id && p.id.toLowerCase().includes(term)) ||
      (p.excerpt && p.excerpt.toLowerCase().includes(term))
    );
  });

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-brand-border/60">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-brand-textPrimary flex items-center gap-2.5">
            <BookOpen className="w-6 h-6 text-brand-accent" />
            <span>Enterprise Runbook Knowledge Base</span>
          </h1>
          <p className="text-xs text-brand-textMuted mt-1">
            Hybrid semantic retrieval (BM25 + normalized vectors) indexing tenant runbooks and verified resolution patterns.
          </p>
        </div>
        <div className="flex items-center gap-2 font-mono text-xs text-brand-textSecondary bg-brand-elevated px-3 py-1.5 rounded-lg border border-brand-border">
          <Database className="w-3.5 h-3.5 text-brand-secondary" />
          <span>Tenant: {user?.tenant?.toUpperCase() || 'ACME'} ({data.total} Indexed Documents)</span>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative w-full sm:w-96">
        <Search className="w-4 h-4 text-brand-textMuted absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search runbook patterns, error codes, JVM flags…"
          className="w-full bg-brand-card border border-brand-border text-xs text-brand-textPrimary rounded-lg pl-9 pr-3 py-2 focus:outline-none focus:border-brand-accent placeholder:text-brand-textMuted shadow-sm"
        />
      </div>

      {/* Main Grid: Runbook List + Document Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Runbook List */}
        <div className="space-y-3">
          {loading ? (
            <div className="p-8 text-center text-xs font-mono text-brand-textMuted bg-brand-card rounded-xl border border-brand-border">
              Loading indexed runbooks…
            </div>
          ) : filtered.length === 0 ? (
            <div className="p-8 text-center text-xs text-brand-textMuted bg-brand-card rounded-xl border border-brand-border">
              No matching runbooks found.
            </div>
          ) : (
            filtered.map((p) => (
              <div
                key={p.id}
                onClick={() => setSelectedPattern(p)}
                className={`p-4 rounded-xl border cursor-pointer transition ${
                  selectedPattern?.id === p.id
                    ? 'bg-brand-elevated border-brand-accent shadow-card'
                    : 'bg-brand-card border-brand-border hover:border-brand-borderHover'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-mono text-[10px] font-bold text-brand-secondary bg-brand-bg px-2 py-0.5 rounded border border-brand-border">
                    {p.id}
                  </span>
                  <span className="text-[10px] font-mono text-brand-textMuted">
                    Page {p.page || 1}
                  </span>
                </div>
                <h3 className="text-xs font-semibold text-brand-textPrimary">{p.title}</h3>
                <p className="text-[11px] text-brand-textMuted mt-1 line-clamp-2">
                  {p.excerpt}
                </p>
                <div className="mt-3 pt-2 border-t border-brand-border/40 flex items-center justify-between text-[10px] font-mono text-brand-textSecondary">
                  <span>{p.pdf_source}</span>
                  <span className="text-brand-success">HYBRID INDEXED</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Selected Document Detail View */}
        <div className="lg:col-span-2 bg-brand-card border border-brand-border rounded-xl shadow-card p-6 space-y-5">
          {selectedPattern ? (
            <>
              <div className="border-b border-brand-border/60 pb-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-mono text-xs font-bold text-brand-accent bg-brand-elevated px-2 py-0.5 rounded border border-brand-border">
                    {selectedPattern.id}
                  </span>
                  <span className="text-[10px] font-mono uppercase bg-brand-elevated text-brand-secondary px-2 py-0.5 rounded border border-brand-border">
                    {selectedPattern.pdf_source} (Page {selectedPattern.page})
                  </span>
                </div>
                <h2 className="text-base font-bold text-brand-textPrimary">{selectedPattern.title}</h2>
                <p className="text-xs text-brand-textMuted mt-1 font-mono">
                  Organization Scope: {selectedPattern.tenant.toUpperCase()} · Retrieval: BM25 + Cosine Distance
                </p>
              </div>

              {/* Full Text View */}
              <div className="space-y-2">
                <span className="text-xs font-bold uppercase tracking-wider text-brand-textMuted block">
                  Grounding Document Body
                </span>
                <pre className="p-4 bg-brand-bg border border-brand-border rounded-lg text-xs font-mono text-brand-textSecondary leading-relaxed whitespace-pre-wrap max-h-96 overflow-y-auto">
                  {selectedPattern.full_text || selectedPattern.excerpt}
                </pre>
              </div>

              {/* Indexing Stats */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 text-xs">
                <div className="p-3 bg-brand-elevated rounded-lg border border-brand-border">
                  <span className="text-[10px] font-semibold text-brand-textMuted uppercase block">BM25 Ranking</span>
                  <span className="font-mono text-brand-secondary font-bold">Inverted Index Active</span>
                </div>
                <div className="p-3 bg-brand-elevated rounded-lg border border-brand-border">
                  <span className="text-[10px] font-semibold text-brand-textMuted uppercase block">Dense Embeddings</span>
                  <span className="font-mono text-brand-success font-bold">128-Dim Normalized</span>
                </div>
                <div className="p-3 bg-brand-elevated rounded-lg border border-brand-border">
                  <span className="text-[10px] font-semibold text-brand-textMuted uppercase block">Grounding Compliance</span>
                  <span className="font-mono text-brand-accent font-bold">Strict Citation Mandatory</span>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-20 text-brand-textMuted text-xs">
              Select a runbook on the left to view document content.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


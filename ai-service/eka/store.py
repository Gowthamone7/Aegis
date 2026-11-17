"""
EKA Hybrid Vector + BM25 Store

Primary backend: ChromaDB HTTP client (Docker).
Fallback: in-memory dict store when ChromaDB is unreachable.

hybrid_search combines:
  - 0.7 × semantic (cosine similarity via embeddings)
  - 0.3 × BM25 (rank_bm25.BM25Okapi)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from rank_bm25 import BM25Okapi  # type: ignore

from .config import settings
from .embeddings import get_embedder, cosine_similarity

log = logging.getLogger(__name__)


# ─────────────────────────── result type ─────────────────────────────────────

@dataclass
class SearchResult:
    id: str
    text: str
    metadata: dict[str, Any]
    score: float
    escalate: bool = False


# ─────────────────────────── in-memory fallback store ─────────────────────────

class _InMemoryStore:
    """Simple dict-backed store used when ChromaDB is unreachable."""

    def __init__(self) -> None:
        # {collection_name: {doc_id: {text, embedding, metadata}}}
        self._data: dict[str, dict[str, dict[str, Any]]] = {}

    def _col(self, name: str) -> dict[str, dict[str, Any]]:
        return self._data.setdefault(name, {})

    def upsert(
        self,
        collection: str,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        col = self._col(collection)
        for doc_id, emb, doc, meta in zip(ids, embeddings, documents, metadatas):
            col[doc_id] = {"text": doc, "embedding": emb, "metadata": meta}

    def query(
        self,
        collection: str,
        query_embedding: list[float],
        n: int,
    ) -> list[dict[str, Any]]:
        col = self._col(collection)
        if not col:
            return []
        scored = [
            {
                "id": doc_id,
                "text": item["text"],
                "metadata": item["metadata"],
                "score": cosine_similarity(query_embedding, item["embedding"]),
            }
            for doc_id, item in col.items()
        ]
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:n]

    def get_all(self, collection: str) -> list[dict[str, Any]]:
        col = self._col(collection)
        return [
            {"id": k, "text": v["text"], "metadata": v["metadata"]}
            for k, v in col.items()
        ]


# ─────────────────────────── HybridStore ──────────────────────────────────────

class HybridStore:
    """
    Wraps ChromaDB HttpClient with graceful fallback to _InMemoryStore.
    """

    def __init__(self) -> None:
        self._chroma = None
        self._fallback = _InMemoryStore()
        self._using_fallback = False
        self._embedder = get_embedder()
        self._init_chroma()

    def _init_chroma(self) -> None:
        try:
            import chromadb  # type: ignore

            self._chroma = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
            )
            # Ping to verify connectivity
            self._chroma.heartbeat()
            log.info(
                "ChromaDB connected at %s:%s",
                settings.chroma_host,
                settings.chroma_port,
            )
        except Exception as exc:
            log.warning(
                "ChromaDB unreachable (%s) — using in-memory fallback.", exc
            )
            self._chroma = None
            self._using_fallback = True
            self._auto_load_patterns()

    def _auto_load_patterns(self) -> None:
        """Auto-loads patterns from data/patterns/ if in-memory store is empty."""
        try:
            import json
            from pathlib import Path
            data_dir = Path(__file__).resolve().parent.parent.parent / "data"
            patterns_root = data_dir / "patterns"
            if not patterns_root.exists():
                return
            for tenant_dir in patterns_root.iterdir():
                if not tenant_dir.is_dir():
                    continue
                tenant = tenant_dir.name
                docs = []
                for jf in tenant_dir.glob("*.json"):
                    try:
                        d = json.loads(jf.read_text(encoding="utf-8"))
                        d.setdefault("page", 1)
                        d.setdefault("pdf_name", jf.stem)
                        emb = self._embedder.embed(d.get("text", ""))
                        docs.append({
                            "id": d["id"],
                            "text": d["text"],
                            "embedding": emb,
                            "metadata": {
                                "title": d.get("title", ""),
                                "page": d["page"],
                                "pdf_name": d["pdf_name"],
                                "tenant": tenant,
                            }
                        })
                    except Exception:
                        pass
                if docs:
                    self.add_documents(tenant, docs)
                    log.info("Auto-loaded %d patterns for tenant %s into in-memory store", len(docs), tenant)
        except Exception as e:
            log.warning("Could not auto-load patterns: %s", e)

    def _collection_name(self, tenant: str) -> str:
        # Sanitize tenant name to safe collection name
        safe = "".join(c if c.isalnum() or c == "_" else "_" for c in tenant)
        return f"{safe}_patterns"

    def _get_or_create_chroma_collection(self, name: str):
        assert self._chroma is not None
        return self._chroma.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    # ── Public API ─────────────────────────────────────────────────────────────

    def add_documents(self, tenant: str, docs: list[dict[str, Any]]) -> None:
        """
        docs: list of {id, text, metadata}
        metadata should contain at least: pdf, page, chunk
        """
        if not docs:
            return

        col_name = self._collection_name(tenant)
        texts = [d["text"] for d in docs]
        ids = [d["id"] for d in docs]
        metadatas = [d.get("metadata", {}) for d in docs]
        embeddings = self._embedder.embed_batch(texts)

        if self._using_fallback or self._chroma is None:
            self._fallback.upsert(col_name, ids, embeddings, texts, metadatas)
            return

        try:
            col = self._get_or_create_chroma_collection(col_name)
            col.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )
        except Exception as exc:
            log.warning("ChromaDB write failed (%s) — falling back to memory.", exc)
            self._using_fallback = True
            self._fallback.upsert(col_name, ids, embeddings, texts, metadatas)

    def hybrid_search(
        self, tenant: str, query: str, n: int = 5, top_k: int | None = None
    ) -> list[SearchResult]:
        if top_k is not None:
            n = top_k
        """
        Run hybrid search: semantic + BM25 rerank.
        Returns up to n SearchResult objects, each with an .escalate flag
        set True when score < T_PARTIAL.
        """
        col_name = self._collection_name(tenant)
        query_embedding = self._embedder.embed(query)
        t_partial = settings.t_partial

        # ── Semantic retrieval ─────────────────────────────────────────────
        raw: list[dict[str, Any]] = []

        if not self._using_fallback and self._chroma is not None:
            try:
                col = self._get_or_create_chroma_collection(col_name)
                result = col.query(
                    query_embeddings=[query_embedding],
                    n_results=max(n * 3, 20),
                    include=["documents", "metadatas", "distances"],
                )
                docs_list = result.get("documents", [[]])[0]
                ids_list = result.get("ids", [[]])[0]
                metas_list = result.get("metadatas", [[]])[0]
                dists_list = result.get("distances", [[]])[0]

                for doc_id, doc, meta, dist in zip(
                    ids_list, docs_list, metas_list, dists_list
                ):
                    # ChromaDB cosine distance = 1 − similarity
                    score = 1.0 - float(dist)
                    raw.append(
                        {"id": doc_id, "text": doc, "metadata": meta, "score": score}
                    )
            except Exception as exc:
                log.warning("ChromaDB query failed (%s) — falling back to memory.", exc)
                self._using_fallback = True

        if self._using_fallback or self._chroma is None:
            raw = self._fallback.query(col_name, query_embedding, max(n * 3, 20))

        if not raw:
            return []

        # ── BM25 rerank ───────────────────────────────────────────────────────
        corpus = [item["text"] for item in raw]
        tokenized = [text.lower().split() for text in corpus]
        bm25 = BM25Okapi(tokenized)
        bm25_scores_raw = bm25.get_scores(query.lower().split())

        # Normalize BM25 scores to [0, 1]
        bm25_max = max(bm25_scores_raw) if max(bm25_scores_raw) > 0 else 1.0
        bm25_scores = [s / bm25_max for s in bm25_scores_raw]

        # Combine: 0.7 × semantic + 0.3 × BM25
        combined: list[dict[str, Any]] = []
        for item, bm25_score in zip(raw, bm25_scores):
            combined_score = 0.7 * item["score"] + 0.3 * bm25_score
            combined.append({**item, "combined_score": combined_score})

        combined.sort(key=lambda x: x["combined_score"], reverse=True)
        top = combined[:n]

        results = []
        for item in top:
            escalate = item["combined_score"] < t_partial
            results.append(
                SearchResult(
                    id=item["id"],
                    text=item["text"],
                    metadata=item["metadata"],
                    score=item["combined_score"],
                    escalate=escalate,
                )
            )
        return results

    @property
    def is_using_fallback(self) -> bool:
        return self._using_fallback


# ─────────────────────────── singleton ───────────────────────────────────────

_store_instance: HybridStore | None = None


def get_store() -> HybridStore:
    global _store_instance
    if _store_instance is None:
        _store_instance = HybridStore()
    return _store_instance

"""
ingest.py — Indexes pattern documents into the vector store.

Usage:
    python -m scripts.ingest [--tenant TENANT]

Reads from data/patterns/{tenant}/*.json.
Each JSON file must contain: id, title, text, page, pdf_name.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Ensure ai-service root is on the path when run directly
_HERE = Path(__file__).resolve().parent.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from eka.config import get_settings
from eka.embeddings import get_embedder
from eka.store import get_store, HybridStore

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
PATTERNS_CACHE = DATA_DIR / "patterns_cache.json"


def load_pattern_files(tenant: str, data_root: Path) -> list[dict]:
    """Load all JSON pattern files for a tenant."""
    pattern_dir = data_root / "patterns" / tenant
    if not pattern_dir.exists():
        print(f"  [WARN] Pattern directory not found: {pattern_dir}")
        return []

    docs = []
    for json_file in sorted(pattern_dir.glob("*.json")):
        try:
            with json_file.open("r", encoding="utf-8") as fh:
                doc = json.load(fh)
            required = {"id", "title", "text"}
            missing = required - doc.keys()
            if missing:
                print(f"  [WARN] {json_file.name} missing fields: {missing} — skipping")
                continue
            doc.setdefault("page", 1)
            doc.setdefault("pdf_name", json_file.stem)
            docs.append(doc)
        except json.JSONDecodeError as exc:
            print(f"  [WARN] {json_file.name} JSON parse error: {exc} — skipping")
    return docs


def ingest_tenant(tenant: str, store: HybridStore, embedder, data_root: Path) -> list[dict]:
    """Ingest all patterns for a single tenant."""
    print(f"\n[INGEST] Tenant: {tenant}")
    docs = load_pattern_files(tenant, data_root)
    if not docs:
        print(f"  No documents found for tenant '{tenant}'.")
        return []

    store_docs = []
    for doc in docs:
        embedding = embedder.embed(doc["text"])
        store_docs.append(
            {
                "id": doc["id"],
                "text": doc["text"],
                "embedding": embedding,
                "metadata": {
                    "title": doc["title"],
                    "page": doc.get("page", 1),
                    "pdf_name": doc.get("pdf_name", ""),
                    "tenant": tenant,
                },
            }
        )

    store.add_documents(tenant, store_docs)
    print(f"  Indexed {len(store_docs)} document(s).")
    for d in store_docs:
        print(f"    ✓ {d['id']} — {d['metadata']['title'][:60]}")
    return store_docs


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest pattern documents into the EKA vector store.")
    parser.add_argument("--tenant", default=None, help="Tenant to ingest (default: all)")
    args = parser.parse_args()

    settings = get_settings()
    embedder = get_embedder()
    store = get_store()

    data_root = DATA_DIR
    patterns_root = data_root / "patterns"
    if not patterns_root.exists():
        print(f"[ERROR] patterns directory not found: {patterns_root}")
        sys.exit(1)

    if args.tenant:
        tenants = [args.tenant]
    else:
        tenants = [d.name for d in patterns_root.iterdir() if d.is_dir()]

    print(f"[INGEST] Starting ingestion. Embeddings: {settings.embeddings}, Mode: {'ChromaDB' if not store.is_using_fallback else 'in-memory fallback'}")
    print(f"[INGEST] Tenants: {tenants}")

    t0 = time.monotonic()
    all_indexed = {}
    for tenant in tenants:
        docs = ingest_tenant(tenant, store, embedder, data_root)
        all_indexed[tenant] = docs
    elapsed = time.monotonic() - t0

    # Persist cache so in-memory store reloads immediately on server start
    try:
        PATTERNS_CACHE.write_text(json.dumps(all_indexed, indent=2), encoding="utf-8")
        print(f"[INGEST] Cached pattern documents to {PATTERNS_CACHE.name}")
    except Exception as e:
        print(f"[WARN] Could not write cache file: {e}")

    total = sum(len(d) for d in all_indexed.values())
    print(f"\n[INGEST] ✓ Done. {total} document(s) indexed across {len(tenants)} tenant(s) in {elapsed:.2f}s")


if __name__ == "__main__":
    main()

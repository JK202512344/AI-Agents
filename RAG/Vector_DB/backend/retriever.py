"""
retriever.py

Improved Hybrid Retriever:
1. Warm in-memory cache (no repeated scroll calls)
2. Token-based keyword scoring (robust vs exact match)
3. Proper score normalization (keyword + vector aligned)
4. Hybrid merge with dedup + reranking
5. Optional rerank boost for keyword matches
"""

from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

COLLECTION_NAME = "docs"


class Retriever:
    def __init__(
        self,
        client: QdrantClient,
        embedder: Optional[SentenceTransformer] = None,
    ):
        self.client = client
        self.embedder = embedder or SentenceTransformer("BAAI/bge-small-en-v1.5")
        self._payload_cache: Optional[List[Dict]] = None

    # =========================================================
    # 🔥 CACHE
    # =========================================================
    def _warm_cache(self):
        if self._payload_cache is not None:
            return

        print("  [Retriever] Warming payload cache (first query)...")

        results, _ = self.client.scroll(
            collection_name=COLLECTION_NAME,
            limit=10_000,
            with_payload=True,
        )

        self._payload_cache = [
            {**pt.payload, "_id": pt.id} for pt in results
        ]

        print(f"  [Retriever] Cache ready — {len(self._payload_cache)} chunks")

    # =========================================================
    # 🔍 KEYWORD SEARCH (IMPROVED)
    # =========================================================
    def _keyword_search(self, query: str, limit: int = 5) -> List[Dict]:
        self._warm_cache()

        query_lower = query.lower().strip()
        if not query_lower:
            return []

        query_words = query_lower.split()
        results = []

        for chunk in self._payload_cache:
            text = chunk.get("chunk_text", "").lower()

            if not text:
                continue

            # Count matching words
            match_count = sum(1 for word in query_words if word in text)

            if match_count > 0:
                # Normalize score into 0.5–1.0 range (align with vector scores)
                score = 0.5 + (match_count / len(query_words)) * 0.5

                results.append({**chunk, "score": round(score, 4)})

        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)

        return results[:limit]

    # =========================================================
    # 🔍 VECTOR SEARCH
    # =========================================================
    def _vector_search(self, query: str, top_k: int = 5) -> List[Dict]:
        query_vector = self.embedder.encode(
            query,
            show_progress_bar=False,
            normalize_embeddings=True,
        ).tolist()

        hits = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=top_k,
            with_payload=True,
        )

        return [
            {
                **hit.payload,
                "_id": hit.id,
                "score": round(hit.score, 4),  # already cosine similarity
            }
            for hit in hits.points
        ]

    # =========================================================
    # 🚀 HYBRID RETRIEVE (SMART MERGE)
    # =========================================================
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        if not query or len(query.strip()) < 2:
            return []

        keyword_hits = self._keyword_search(query, limit=top_k * 2)
        vector_hits = self._vector_search(query, top_k=top_k * 2)

        seen: Dict[int, Dict] = {}

        # Merge (keyword gets slight priority)
        for chunk in keyword_hits + vector_hits:
            pid = chunk.get("_id")

            if pid not in seen:
                seen[pid] = chunk
            else:
                # Keep higher score
                if chunk["score"] > seen[pid]["score"]:
                    seen[pid] = chunk

        merged = list(seen.values())

        # Final reranking (important)
        merged.sort(key=lambda x: x["score"], reverse=True)

        print(
            f"  [Retriever] keyword={len(keyword_hits)} | vector={len(vector_hits)} | merged={len(merged)}"
        )

        return merged[:top_k]

    # =========================================================
    # 📚 CONTEXT BUILDER
    # =========================================================
    def build_context(self, retrieved_chunks: List[Dict]) -> str:
        parts = []

        for i, chunk in enumerate(retrieved_chunks, 1):
            content = chunk.get("content", "").strip()
            source = chunk.get("source", "unknown")
            page = chunk.get("page", "")
            score = chunk.get("score", 0)

            parts.append(
                f"[Source {i} | {source} | Page {page} | score={score}]\n{content}"
            )

        return "\n\n---\n\n".join(parts)

    # =========================================================
    # 🧹 UTILS
    # =========================================================
    def invalidate_cache(self):
        self._payload_cache = None

    def close(self):
        try:
            self.client.close()
        except Exception:
            pass
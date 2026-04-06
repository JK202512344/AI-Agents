"""
chunker.py

Handles document chunking using Docling HierarchicalChunker.
"""

from typing import List, Dict
from pathlib import Path
import json

from docling.chunking import HierarchicalChunker


class DocumentChunker:
    def __init__(self):
        self.chunker = HierarchicalChunker()

    def chunk_document(self, doc, source: str = "", page: int = None) -> List[Dict]:
        """
        Convert Docling Document → structured chunks
        """
        raw_chunks = list(self.chunker.chunk(doc))
        print(f"Total chunks: {len(raw_chunks)}")

        processed = []

        for c in raw_chunks:
            chunk = self._convert_chunk(c)

            # attach metadata
            chunk["source"] = source
            if page is not None:
                chunk["page"] = page

            processed.append(chunk)

        return processed

    def _convert_chunk(self, doc_chunk) -> Dict:
        headings = doc_chunk.meta.headings or []
        content = doc_chunk.text.strip()

        breadcrumb = " > ".join(headings)
        chunk_text = f"""HEADINGS: {' > '.join(headings)}CONTENT:{content}""" if breadcrumb else content

        return {
            "headings": headings,
            "content": content,
            "chunk_text": chunk_text,
        }

    def save_chunks(self, chunks: List[Dict], output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)

        print(f"Saved → {output_path}")
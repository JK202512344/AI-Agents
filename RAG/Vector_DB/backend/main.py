"""
main.py

Pipeline:
Reader → Chunker → Qdrant
"""

from ingest import load_all_files
from chunker import DocumentChunker
from vectordb import QdrantStore


chunker = DocumentChunker()
vectordb = QdrantStore()


def process():
    all_docs = load_all_files()
    all_chunks = []

    for item in all_docs:
        file = item["file"]
        doc_type = item["type"]

        print(f"\n⚙️ Chunking: {file}")

        file_chunks = []

        # ---------- PDF ----------
        if doc_type == "pdf":
            for page, doc in item["content"]:
                chunks = chunker.chunk_document(
                    doc,
                    source=str(file),
                    page=page
                )
                file_chunks.extend(chunks)

        # ---------- CSV ----------
        elif doc_type == "csv":
            file_chunks.extend(item["content"])

        # ---------- DOC ----------
        else:
            chunks = chunker.chunk_document(
                item["content"],
                source=str(file)
            )
            file_chunks.extend(chunks)

        print(f"✅ {file.name}: {len(file_chunks)} chunks")

        all_chunks.extend(file_chunks)

    # 🔥 Store ALL chunks in Qdrant
    vectordb.store_chunks(all_chunks)

    vectordb.info()

    vectordb.close()


if __name__ == "__main__":
    process()
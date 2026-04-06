"""
vectordb.py

Handles:
- Embeddings
- Qdrant storage
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from sentence_transformers import SentenceTransformer


class QdrantStore:
    def __init__(self, collection_name="docs"):
        self.collection_name = collection_name

        # ✅ Embedding model
        self.embedder = SentenceTransformer("BAAI/bge-small-en-v1.5")
        self.dim = self.embedder.get_sentence_embedding_dimension()

        # ✅ Qdrant client (local, no server)
        self.client = QdrantClient(path="./qdrant_db")

        self._create_collection()

    def _create_collection(self):
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.dim,
                distance=Distance.COSINE,
            ),
        )
        print(f"✅ Qdrant collection '{self.collection_name}' ready")

    def store_chunks(self, chunks):
        """
        Convert chunks → embeddings → store in Qdrant
        """
        texts = [c["chunk_text"] for c in chunks]

        # 🔥 Generate embeddings
        embeddings = self.embedder.encode(texts, show_progress_bar=False)

        # 🔥 Create points
        points = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            points.append(
                PointStruct(
                    id=idx,
                    vector=embedding.tolist(),
                    payload={
                        "headings": chunk.get("headings"),
                        "content": chunk.get("content"),
                        "chunk_text": chunk.get("chunk_text"),
                        "source": chunk.get("source"),
                        "page": chunk.get("page"),
                    },
                )
            )

        # 🔥 Upload
        result = self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )

        print(f"🚀 Indexed {len(points)} chunks → {result.status}")

    def info(self):
        info = self.client.get_collection(self.collection_name)

        print(f"Points     : {info.points_count}")
        print(f"Dimensions : {info.config.params.vectors.size}")

    def close(self):
        self.client.close()
        print("Qdrant connection closed")    
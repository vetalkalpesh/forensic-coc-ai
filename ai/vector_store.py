"""
ai/vector_store.py
Vector database interface using ChromaDB.
Stores embeddings of forensic report chunks with full metadata filtering support.
Does NOT replace MySQL — acts purely as a semantic index.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION
from ai.embeddings import EmbeddingEngine


class VectorStore:

    def __init__(self, persist_dir: str = CHROMA_PERSIST_DIR, collection_name: str = CHROMA_COLLECTION):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.embedding_engine = EmbeddingEngine()
        self._client = None
        self._collection = None
        self._fallback_store = []
        self._init_chroma()

    def _init_chroma(self):
        try:
            import chromadb
            os.makedirs(self.persist_dir, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self.persist_dir)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self._mode = "chroma"
        except Exception as e:
            self._mode = "fallback"
            print(f"[VectorStore] Warning: ChromaDB not available ({e}). Using in-memory fallback store.")

    def upsert_chunks(self, chunks: list) -> int:
        """Upsert a list of chunk dicts into vector database."""
        if not chunks:
            return 0

        texts = [c["text"] for c in chunks]
        ids = [c["chunk_id"] for c in chunks]

        # Sanitize metadata for ChromaDB (no None values permitted)
        metadatas = []
        for c in chunks:
            meta = {
                "report_id": int(c.get("report_id") or 0),
                "exam_id": int(c.get("exam_id") or 0),
                "evidence_id": int(c.get("evidence_id") or 0),
                "case_id": int(c.get("case_id") or 0),
                "fir_number": str(c.get("fir_number") or ""),
                "examiner_id": int(c.get("examiner_id") or 0),
                "examiner_name": str(c.get("examiner_name") or ""),
                "lab_name": str(c.get("lab_name") or ""),
                "filed_on": str(c.get("filed_on") or ""),
                "chunk_index": int(c.get("chunk_index") or 0),
            }
            metadatas.append(meta)

        embeddings = self.embedding_engine.embed_texts(texts)

        if self._mode == "chroma":
            self._collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
        else:
            # Fallback in-memory upsert
            for i, chunk_id in enumerate(ids):
                self._fallback_store.append({
                    "id": chunk_id,
                    "text": texts[i],
                    "embedding": embeddings[i],
                    "metadata": metadatas[i]
                })

        return len(chunks)

    def search(self, query: str, limit: int = 5, evidence_id: int = None, case_id: int = None) -> list:
        """Search vector store by similarity, with optional metadata filtering."""
        query_vec = self.embedding_engine.embed_query(query)

        where_filter = {}
        if evidence_id:
            where_filter["evidence_id"] = int(evidence_id)
        elif case_id:
            where_filter["case_id"] = int(case_id)

        if self._mode == "chroma":
            kwargs = {
                "query_embeddings": [query_vec],
                "n_results": limit,
            }
            if where_filter:
                kwargs["where"] = where_filter

            try:
                results = self._collection.query(**kwargs)
            except Exception:
                # If filter matching fails (e.g., no match), retry without where
                kwargs.pop("where", None)
                results = self._collection.query(**kwargs)

            formatted = []
            if results and results.get("ids") and results["ids"][0]:
                for idx in range(len(results["ids"][0])):
                    doc = results["documents"][0][idx]
                    meta = results["metadatas"][0][idx]
                    dist = results["distances"][0][idx] if "distances" in results else 0.0
                    score = round(1.0 - float(dist), 4)  # cosine similarity
                    formatted.append({
                        "chunk_id": results["ids"][0][idx],
                        "text": doc,
                        "metadata": meta,
                        "score": score
                    })

            return formatted
        else:
            # Fallback cosine search
            formatted = []
            for item in self._fallback_store:
                if evidence_id and item["metadata"].get("evidence_id") != evidence_id:
                    continue
                if case_id and item["metadata"].get("case_id") != case_id:
                    continue

                # Cosine similarity
                vec_a = query_vec
                vec_b = item["embedding"]
                dot = sum(a * b for a, b in zip(vec_a, vec_b))
                score = round(dot, 4)

                formatted.append({
                    "chunk_id": item["id"],
                    "text": item["text"],
                    "metadata": item["metadata"],
                    "score": score
                })

            formatted.sort(key=lambda x: x["score"], reverse=True)
            return formatted[:limit]

"""
ai/chunker.py
Splits documents into overlapping chunks retaining all forensic metadata for vector storage.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.config import CHUNK_SIZE, CHUNK_OVERLAP


class Chunker:

    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, doc: dict) -> list:
        """Splits a single document dict into a list of chunk dicts with full metadata."""
        text = doc.get("text", "")
        if not text:
            return []

        words = text.split()
        chunks = []

        if len(words) <= self.chunk_size:
            # Single chunk
            chunk_id = f"{doc['doc_id']}_chk0"
            chunks.append({
                "chunk_id": chunk_id,
                "text": text,
                "chunk_index": 0,
                "report_id": doc.get("report_id"),
                "exam_id": doc.get("exam_id"),
                "evidence_id": doc.get("evidence_id"),
                "case_id": doc.get("case_id"),
                "fir_number": doc.get("fir_number"),
                "examiner_id": doc.get("examiner_id"),
                "examiner_name": doc.get("examiner_name"),
                "lab_name": doc.get("lab_name"),
                "filed_on": doc.get("filed_on"),
            })
            return chunks

        # Sliding window over words
        step = max(1, self.chunk_size - self.chunk_overlap)
        idx = 0

        for start in range(0, len(words), step):
            end = min(len(words), start + self.chunk_size)
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)
            chunk_id = f"{doc['doc_id']}_chk{idx}"

            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "chunk_index": idx,
                "report_id": doc.get("report_id"),
                "exam_id": doc.get("exam_id"),
                "evidence_id": doc.get("evidence_id"),
                "case_id": doc.get("case_id"),
                "fir_number": doc.get("fir_number"),
                "examiner_id": doc.get("examiner_id"),
                "examiner_name": doc.get("examiner_name"),
                "lab_name": doc.get("lab_name"),
                "filed_on": doc.get("filed_on"),
            })
            idx += 1
            if end >= len(words):
                break

        return chunks

    def chunk_all(self, docs: list) -> list:
        """Chunk a list of document dicts."""
        all_chunks = []
        for d in docs:
            all_chunks.extend(self.chunk_document(d))
        return all_chunks

"""
ai/indexer.py
CLI script to build/rebuild ChromaDB vector index from ExaminationReport records in MySQL.
Run once after database creation or dataset generation.

Usage:
    python indexer.py
    python indexer.py --rebuild
"""
import argparse
import sys, os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.document_processor import DocumentProcessor
from ai.chunker import Chunker
from ai.vector_store import VectorStore


def main():
    parser = argparse.ArgumentParser(description="Forensic Report Vector Indexer")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild collection from scratch")
    args = parser.parse_args()

    print("=" * 60)
    print("  FORENSIC REPORT VECTOR INDEXER")
    print("=" * 60)

    start_time = time.time()

    processor = DocumentProcessor()
    chunker = Chunker()
    vector_store = VectorStore()

    print("\n1. Fetching ExaminationReport records from MySQL...")
    docs = processor.fetch_all_reports_for_indexing()
    print(f"   Found {len(docs)} report document(s).")

    if not docs:
        print("   No reports found in database. Exiting.")
        return

    print("\n2. Chunking report documents...")
    chunks = chunker.chunk_all(docs)
    print(f"   Created {len(chunks)} chunk(s) (chunk_size=512, overlap=64).")

    print("\n3. Generating embeddings & upserting to ChromaDB...")
    count = vector_store.upsert_chunks(chunks)

    elapsed = round(time.time() - start_time, 2)
    print("\n" + "=" * 60)
    print(f"  INDEXING COMPLETE: {count} chunk(s) indexed in {elapsed}s")
    print("=" * 60)


if __name__ == "__main__":
    main()

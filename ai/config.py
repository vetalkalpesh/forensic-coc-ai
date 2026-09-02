"""
ai/config.py
Configuration parameters for the AI / RAG Core Layer.
Reads environment variables with sensible local defaults.
"""
import os

try:
    import dotenv
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_env = os.path.abspath(os.path.join(current_dir, "..", ".env"))
    root_env = os.path.abspath(os.path.join(current_dir, "..", "..", ".env"))
    if os.path.exists(parent_env):
        dotenv.load_dotenv(parent_env)
    if os.path.exists(root_env):
        dotenv.load_dotenv(root_env)
    dotenv.load_dotenv()
except ImportError:
    pass

# ── LLM CONFIGURATION ─────────────────────────────────────────
LLM_PROVIDER   = os.environ.get("LLM_PROVIDER", "gemini")     # 'gemini', 'openai', 'ollama', or 'mock'
LLM_API_KEY    = os.environ.get("LLM_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")
LLM_MODEL      = os.environ.get("LLM_MODEL", "gemini-3.6-flash")

# ── EMBEDDINGS CONFIGURATION ──────────────────────────────────
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# ── VECTOR DB CONFIGURATION (ChromaDB) ───────────────────────
BASE_DIR          = os.path.dirname(os.path.abspath(__file__))
CHROMA_PERSIST_DIR = os.environ.get("CHROMA_PERSIST_DIR", os.path.join(BASE_DIR, "chroma_data"))
CHROMA_COLLECTION  = os.environ.get("CHROMA_COLLECTION", "forensic_reports")

# ── CHUNKING CONFIGURATION ────────────────────────────────────
CHUNK_SIZE    = int(os.environ.get("CHUNK_SIZE", 512))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", 64))

# ── FULLTEXT SEARCH CONFIG ───────────────────────────────────
FULLTEXT_MIN_RELEVANCE = float(os.environ.get("FULLTEXT_MIN_RELEVANCE", 0.0001))

# ── MYSQL DATABASE CONFIG ─────────────────────────────────────
DB_HOST     = os.environ.get("DB_HOST", "localhost")
DB_USER     = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME     = os.environ.get("DB_NAME", "forensic_coc")

DB_CONFIG = dict(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    charset="utf8mb4",
)

# ── SECRET KEY FOR JWT ────────────────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-forensic-key")

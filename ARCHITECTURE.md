# ARCHITECTURE.md — Hybrid RAG Forensic Intelligence Platform

## System Title
**A Security-Aware Hybrid Retrieval-Augmented Generation Framework for Intelligent Forensic Evidence Management**

---

## 1. High-Level System Architecture

```
                                  USER QUERY
                                      │
                                      ▼
                            Frontend Interface
                         (frontend/ai_assistant.html)
                                      │
                                      ▼
                            JWT Authentication &
                            RBAC Data Scope Filter
                                      │
                                      ▼
                          POST /api/ai/query
                                      │
                                      ▼
                    ┌───────────────────────────────────┐
                    │          Query Analyzer           │
                    │  ┌─────────────────────────────┐  │
                    │  │ Intent Classifier           │  │
                    │  │ (15 intents pattern-matched)│  │
                    │  └─────────────────────────────┘  │
                    │  ┌─────────────────────────────┐  │
                    │  │ Entity Extractor            │  │
                    │  │ (regex + pattern match)     │  │
                    │  └─────────────────────────────┘  │
                    └───────────────────────────────────┘
                                      │
                                      ▼
                    ┌───────────────────────────────────┐
                    │   Hybrid Retrieval Orchestrator   │
                    │       (ai/hybrid_retriever.py)    │
                    │                                   │
                    │  ┌─────────────────────────────┐  │
                    │  │ Fact Calculator             │  │
                    │  │ (SQL-only pre-calculation)  │  │
                    │  └──────────────┬──────────────┘  │
                    │                 │                 │
                    │   ┌─────────────┴─────────────┐   │
                    │   ▼                           ▼   │
                    │ Structured SQL           Semantic │
                    │ Retriever                Retriever│
                    │ (sql_retriever.py) (vector_retriever)
                    │   │                           │   │
                    │   ▼                           ▼   │
                    │ MySQL 8.0 DB               ChromaDB
                    │ (Source of Truth)         (Vector)│
                    └─────────────────┬─────────────────┘
                                      │
                                      ▼
                    ┌───────────────────────────────────┐
                    │    Context Validation Layer       │
                    │  • Source Conflict Detector       │
                    │    (DB State vs Report Text)      │
                    │  • Context Builder                │
                    └─────────────────┬─────────────────┘
                                      │
                                      ▼
                    ┌───────────────────────────────────┐
                    │      Grounded LLM Interface       │
                    │  • System Prompt Enforcement      │
                    │  • Source Citation                │
                    │  • Prompt Injection Guard         │
                    └─────────────────┬─────────────────┘
                                      │
                                      ▼
                    ┌───────────────────────────────────┐
                    │      Hallucination Guard          │
                    │  (Post-Generation Entity Check)   │
                    └─────────────────┬─────────────────┘
                                      │
                                      ▼
                         Answer + Sources + Conflict
                          Warnings + Tiered Why?
                                      │
                                      ▼
                             AI Query Audit Log
                           (AIQueryAuditLog Table)
```

---

## 2. Key Architectural Decisions & Rationale

### Vector Database Choice: **ChromaDB**
- **Deployment**: Local, embedded, serverless Python-native storage.
- **Persistence**: File-backed at `ai/chroma_data/`.
- **Metadata Filtering**: Native key-value metadata filtering (`evidence_id`, `case_id`, `report_id`).
- **Role**: ChromaDB acts **strictly as a semantic index** over forensic report chunks. It does **NOT** replace MySQL as the authoritative source of truth.

### LLM Interface: **Provider-Agnostic Grounded LLM**
- Supported providers: **Google Gemini** (`gemini-1.5-flash`), **OpenAI** (`gpt-4o-mini`), or local fallback synthesis.
- Configurable via environment variables (`LLM_PROVIDER`, `GEMINI_API_KEY`, `LLM_MODEL`).

### Embeddings: **Sentence-Transformers (`all-MiniLM-L6-v2`)**
- Local 384-dimensional dense vector embeddings.
- Operates entirely on CPU without external API calls or GPU requirements.

---

## 3. Core Architectural Rules

### Rule 1 — Single Source of Truth
MySQL 8.0 remains the single source of truth for all evidence, custody, forensic lab, storage, and court records. Vector embeddings and LLM outputs are never treated as authoritative.

### Rule 2 — Pre-Calculated Database Facts (SQL Only)
The LLM is **strictly prohibited** from performing factual calculations (such as custody delay hours, remaining biological expiry days, examination SLA breach status, or dead-man switch inactivity days). All numeric facts are computed via MySQL SQL queries (`fact_calculator.py`) and passed into the LLM context as verified truths.

### Rule 3 — Source Conflict Detection
When historical report text conflicts with current authoritative database state (e.g., old report states "in pristine condition" while current database status is "Compromised"), the `ConflictDetector` module:
1. Flags the discrepancy in the answer (`⚠ Source Conflict Warning`).
2. Prioritizes the current database state as authoritative.
3. Preserves report provenance for forensic transparency.

### Rule 4 — Tiered "Why?" Explanation
The "Why?" feature (`ai/why_explainer.py`) adapts based on the user's JWT RBAC role:
- **Junior / Senior Users**: Plain-language provenance summary showing cited sources, verified facts, and conflict warnings.
- **Admin / Supervisor Users**: Full technical developer view containing raw SQL query results, vector chunks, cosine similarity scores, prompt details, and latency breakdowns.

### Rule 5 — Prompt Injection Resistance
Retrieved forensic report text and evidence descriptions are treated strictly as **DATA**, never as system instructions. Prompt injection attempts within user queries or report texts are trapped and neutralized by security filters.

---

## 4. Retrieval Baselines & Hybrid Architecture

The platform supports three distinct retrieval modes for scientific evaluation:

| Mode | Identifier | Retriever Module | Description |
|---|---|---|---|
| **Baseline A** | `FULLTEXT` | `fulltext_retriever.py` | MySQL `MATCH() AGAINST()` keyword search over reports and evidence. |
| **Baseline B** | `VECTOR` | `vector_retriever.py` | Pure ChromaDB cosine similarity search over embedded report chunks. |
| **Proposed** | `HYBRID` | `hybrid_retriever.py` | Structured SQL queries + ChromaDB vector search + pre-calculated facts + conflict detection. |

---

## 5. Evaluation Framework & Metrics

The system includes a reproducible evaluation suite (`evaluation/`) with 200+ programmatically generated ground-truth questions across 17 categories:

### Metrics Computed
- **Recall@5**: Fraction of relevant documents retrieved in top 5.
- **Precision@5**: Fraction of top 5 retrieved documents that are relevant.
- **MRR (Mean Reciprocal Rank)**: Reciprocal rank of first relevant result.
- **nDCG@5**: Normalized Discounted Cumulative Gain.
- **Answer Faithfulness**: Word overlap and factual alignment with ground truth.
- **Answer Relevance**: Semantic alignment between generated answer and question.
- **Hallucination Rate**: Percentage of answers containing ungrounded entity IDs.
- **Retrieval & Total Latency**: Response time in milliseconds.

---

## 6. Reproducible Synthetic Dataset Generator

Located in `dataset_generator/`, the generator produces realistic, synthetic forensic data with:
- Fixed random seed (`--seed 42`) for 100% deterministic reproducibility.
- Scalable size presets (`--size small`, `medium`, `large`).
- Controlled insertion of **Scenarios A through J** (normal clean, hash mismatch, custody delay, derived cascade, expiring bio, overdue exam, dead-man switch, clean case, multi-anomaly, and ambiguous/insufficient).
- Strict foreign key integrity enforcement (`fk_validator.py`).
- All synthetic reports tagged with `[SYNTHETIC DATA — NOT REAL]`.

---

## 7. API Contract (AI Routes)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/ai/query` | JWT | RAG query endpoint. Accepts `question` and optional `method=HYBRID\|FULLTEXT\|VECTOR`. |
| `GET` | `/api/ai/query/<id>/why` | JWT | Tiered Why? explanation (user vs admin mode). |
| `POST` | `/api/ai/investigate/<eid>` | JWT | Evidence investigation workflow. |
| `POST` | `/api/ai/summarize/<cid>` | JWT | Case summary workflow. |
| `GET` | `/api/ai/anomalies` | JWT | Pre-calculated anomaly dashboard data. |
| `GET` | `/api/ai/suggested-queries` | None | Suggested query pills. |
| `GET` | `/api/ai/audit` | JWT (Admin) | AI query audit log table. |

---

*Hybrid RAG Forensic Intelligence Platform — Architectural Specifications Complete.*

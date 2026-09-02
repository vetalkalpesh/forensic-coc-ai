-- ============================================================
--  HYBRID RAG FORENSIC INTELLIGENCE PLATFORM
--  AI Tables Migration — ADDITIVE ONLY
--  Does NOT modify any existing tables, triggers, or procedures
--  Run AFTER complete_database.sql has been loaded
-- ============================================================
USE forensic_coc;

-- ── AI QUERY AUDIT LOG ─────────────────────────────────────
-- Tracks every AI query: retrieval method, sources, answer, metrics
CREATE TABLE IF NOT EXISTS AIQueryAuditLog (
    query_id             VARCHAR(36)   NOT NULL PRIMARY KEY,  -- UUID
    officer_id           INT,
    queried_at           DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    original_question    TEXT          NOT NULL,
    detected_intent      VARCHAR(50),
    extracted_entities   JSON,                                -- {evidence_id, case_id, fir_number, ...}
    retrieval_method     ENUM('FULLTEXT','VECTOR','HYBRID')  NOT NULL DEFAULT 'HYBRID',
    sql_sources          JSON,                                -- list of {table, record_id, query_type}
    vector_sources       JSON,                                -- list of {chunk_id, score, report_id}
    retrieval_score      DECIMAL(6,4),                        -- combined retrieval confidence
    conflict_detected    TINYINT(1)    NOT NULL DEFAULT 0,    -- 1 if DB vs report conflict found
    conflict_details     TEXT,                                -- description of conflict if detected
    model_used           VARCHAR(100),
    generated_answer     TEXT,
    response_latency_ms  INT,                                 -- end-to-end latency
    retrieval_latency_ms INT,                                 -- retrieval-only latency
    hallucination_flag   TINYINT(1)    NOT NULL DEFAULT 0,    -- 1 if hallucination detected
    status               ENUM('success','insufficient','error','injection_blocked','conflict') NOT NULL DEFAULT 'success',
    FOREIGN KEY (officer_id) REFERENCES Officer(officer_id)
);

-- ── INDEX FOR AUDIT QUERIES ────────────────────────────────
CREATE INDEX idx_aiqal_officer   ON AIQueryAuditLog (officer_id);
CREATE INDEX idx_aiqal_queried   ON AIQueryAuditLog (queried_at);
CREATE INDEX idx_aiqal_intent    ON AIQueryAuditLog (detected_intent);
CREATE INDEX idx_aiqal_status    ON AIQueryAuditLog (status);
CREATE INDEX idx_aiqal_method    ON AIQueryAuditLog (retrieval_method);

SELECT 'AI TABLES MIGRATION COMPLETE' AS status,
       '1 table added (AIQueryAuditLog) — 0 existing tables modified' AS summary;

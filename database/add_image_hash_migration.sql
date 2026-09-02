-- ============================================================
--  ADD IMAGE HASH MIGRATION — ADDITIVE ONLY
--  Adds sha256_hash column to EvidenceMedia table if not present
-- ============================================================
USE forensic_coc;

SET @dbname = DATABASE();
SET @tablename = "EvidenceMedia";
SET @columnname = "sha256_hash";
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      TABLE_SCHEMA = @dbname
      AND TABLE_NAME = @tablename
      AND COLUMN_NAME = @columnname
  ) > 0,
  "SELECT 1",
  "ALTER TABLE EvidenceMedia ADD COLUMN sha256_hash VARCHAR(64) NULL AFTER notes;"
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Ensure file_path points to evidence_photos/file_name
UPDATE EvidenceMedia SET file_path = CONCAT('evidence_photos/', file_name) WHERE file_name IS NOT NULL AND (file_path IS NULL OR file_path = 'evidence_photos/placeholder.png');

SELECT 'EVIDENCE MEDIA HASH MIGRATION COMPLETE' AS status;

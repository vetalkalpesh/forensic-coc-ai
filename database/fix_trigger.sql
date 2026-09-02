DELIMITER //

DROP TRIGGER IF EXISTS trg_tamper_cascade //

CREATE TRIGGER trg_tamper_cascade
AFTER UPDATE ON Evidence
FOR EACH ROW
BEGIN
    IF NEW.current_status = 'Compromised' AND OLD.current_status != 'Compromised' THEN
        INSERT INTO AlertLog (alert_type, evidence_id, message)
        VALUES ('Tamper', NEW.evidence_id,
                CONCAT('TAMPER CASCADE: Evidence E', LPAD(NEW.evidence_id,3,'0'),
                       ' marked Compromised. All derived evidence auto-flagged.'));
        INSERT INTO AuditLog (table_name, record_id, old_values, new_values)
        VALUES ('Evidence', NEW.evidence_id,
                CONCAT('{"status":"', OLD.current_status, '"}'),
                CONCAT('{"status":"', NEW.current_status, '"}'));
    END IF;
END //

DELIMITER ;

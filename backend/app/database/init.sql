-- =====================================================================
-- Plataforma de Firma Digital eIDAS — Esquema MariaDB
-- Referencia: docs/DATABASE.md
-- Ejecutado automáticamente por el contenedor mariadb en el primer arranque
-- (docker-entrypoint-initdb.d).
-- =====================================================================

SET NAMES utf8mb4;
SET time_zone = '+01:00';

-- ---------------------------------------------------------------------
-- 1.1 users
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id BIGINT NOT NULL AUTO_INCREMENT,
    cert_fingerprint VARCHAR(64) NOT NULL,
    cert_subject JSON NOT NULL,
    cert_issuer JSON NOT NULL,
    cert_serial VARCHAR(64),
    cert_not_before DATETIME NOT NULL,
    cert_not_after DATETIME NOT NULL,
    email VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    organization VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    last_login DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY unique_fingerprint (cert_fingerprint),
    INDEX idx_email (email),
    INDEX idx_organization (organization),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 1.2 documents
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(36) NOT NULL,
    owner_id BIGINT NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    original_filename VARCHAR(500) NOT NULL,
    mongodb_id VARCHAR(255) NOT NULL,
    status ENUM('pending', 'pending_signatures', 'fully_signed', 'rejected', 'archived') DEFAULT 'pending',
    file_size BIGINT,
    content_hash VARCHAR(64),
    version INT DEFAULT 1,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    FOREIGN KEY (owner_id) REFERENCES users(id),
    INDEX idx_owner (owner_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 1.3 signatures
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS signatures (
    id BIGINT NOT NULL AUTO_INCREMENT,
    document_id VARCHAR(36) NOT NULL,
    signer_id BIGINT NOT NULL,
    signer_cert_fingerprint VARCHAR(64) NOT NULL,
    signer_cert_subject JSON NOT NULL,
    signature_hash VARCHAR(64) NOT NULL,
    signature_algorithm VARCHAR(50),
    hash_algorithm VARCHAR(50),
    tsa_response_base64 LONGTEXT,
    tsa_timestamp DATETIME,
    tsa_authority VARCHAR(255),
    signature_order INT,
    rejected BOOLEAN DEFAULT FALSE,
    rejection_reason TEXT,
    signed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (signer_id) REFERENCES users(id),
    UNIQUE KEY unique_signature (document_id, signer_id),
    INDEX idx_document (document_id),
    INDEX idx_signer (signer_id),
    INDEX idx_signed_at (signed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 1.4 signature_workflows
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS signature_workflows (
    id BIGINT NOT NULL AUTO_INCREMENT,
    document_id VARCHAR(36) NOT NULL,
    creator_id BIGINT NOT NULL,
    status ENUM('pending', 'in_progress', 'completed', 'cancelled') DEFAULT 'pending',
    required_signers INT NOT NULL,
    completed_signers INT DEFAULT 0,
    sequence_type ENUM('parallel', 'sequential') DEFAULT 'parallel',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at DATETIME,

    PRIMARY KEY (id),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (creator_id) REFERENCES users(id),
    INDEX idx_document (document_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 1.5 workflow_assignments
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS workflow_assignments (
    id BIGINT NOT NULL AUTO_INCREMENT,
    workflow_id BIGINT NOT NULL,
    signer_id BIGINT NOT NULL,
    signer_cert_fingerprint VARCHAR(64) NOT NULL,
    status ENUM('pending', 'signed', 'rejected') DEFAULT 'pending',
    sequence_number INT,
    signed_at DATETIME,
    rejection_reason TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    FOREIGN KEY (workflow_id) REFERENCES signature_workflows(id) ON DELETE CASCADE,
    FOREIGN KEY (signer_id) REFERENCES users(id),
    UNIQUE KEY unique_assignment (workflow_id, signer_id),
    INDEX idx_workflow (workflow_id),
    INDEX idx_signer (signer_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 1.6 audit_logs (INMUTABLE)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT NOT NULL AUTO_INCREMENT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action VARCHAR(100) NOT NULL,
    actor_id BIGINT,
    actor_cert_fingerprint VARCHAR(64),
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    old_value JSON,
    new_value JSON,
    details JSON,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    FOREIGN KEY (actor_id) REFERENCES users(id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_action (action),
    INDEX idx_resource (resource_type, resource_id),
    INDEX idx_actor (actor_cert_fingerprint)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Inmutabilidad: impedir DELETE y UPDATE sobre audit_logs a nivel de BD.
DELIMITER //
CREATE TRIGGER trg_audit_logs_no_delete
BEFORE DELETE ON audit_logs FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'audit_logs es inmutable: DELETE no permitido';
END//

CREATE TRIGGER trg_audit_logs_no_update
BEFORE UPDATE ON audit_logs FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'audit_logs es inmutable: UPDATE no permitido';
END//
DELIMITER ;

-- ---------------------------------------------------------------------
-- 1.7 certificate_cache
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS certificate_cache (
    id BIGINT NOT NULL AUTO_INCREMENT,
    fingerprint VARCHAR(64) NOT NULL,
    cert_pem LONGTEXT NOT NULL,
    subject JSON,
    issuer JSON,
    serial VARCHAR(64),
    not_before DATETIME,
    not_after DATETIME,
    is_valid BOOLEAN DEFAULT TRUE,
    validation_timestamp DATETIME,
    revocation_status ENUM('valid', 'revoked', 'unknown') DEFAULT 'unknown',
    last_revocation_check DATETIME,
    expires_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY unique_fingerprint (fingerprint),
    INDEX idx_expires (expires_at),
    INDEX idx_is_valid (is_valid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 1.8 audit_events (análisis)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_events (
    id BIGINT NOT NULL AUTO_INCREMENT,
    timestamp DATETIME NOT NULL,
    event_type VARCHAR(100),
    severity ENUM('INFO', 'WARNING', 'ERROR', 'CRITICAL'),
    message TEXT,
    metadata JSON,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_type (event_type),
    INDEX idx_severity (severity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 5. Índices estratégicos de performance (nombres distintos de los inline)
-- ---------------------------------------------------------------------
CREATE INDEX idx_documents_owner ON documents(owner_id, status, created_at DESC);
CREATE INDEX idx_audit_logs_datetime ON audit_logs(timestamp DESC, action);
CREATE INDEX idx_signatures_document_signer ON signatures(document_id, signer_id);
CREATE INDEX idx_workflows_document_status ON signature_workflows(document_id, status);
CREATE INDEX idx_cert_cache_validity ON certificate_cache(is_valid, expires_at);

-- SMART FIR 360: Database Schema for MySQL
-- Aligned with BNSS (Bharatiya Nagarik Suraksha Sanhita, 2023) Section 173

CREATE DATABASE IF NOT EXISTS smart_fir_360 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smart_fir_360;

-- 1. Users Table (Citizens, Police Officers, Admins)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    aadhar_last4 VARCHAR(4) NULL,
    role ENUM('citizen', 'police_officer', 'police_admin') DEFAULT 'citizen',
    badge_number VARCHAR(50) NULL,
    police_station VARCHAR(100) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_role (role),
    INDEX idx_user_email (email)
) ENGINE=InnoDB;

-- 2. Complaints Table (BNSS 173 e-Complaint Lifecycle)
CREATE TABLE IF NOT EXISTS complaints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    complaint_number VARCHAR(50) NOT NULL UNIQUE,
    citizen_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    incident_date VARCHAR(50) NOT NULL,
    incident_time VARCHAR(50) NULL,
    location_name VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    police_station VARCHAR(100) NOT NULL,
    accused_details TEXT NULL,
    witness_details TEXT NULL,
    status VARCHAR(50) DEFAULT 'submitted',
    is_e_complaint BOOLEAN DEFAULT TRUE,
    verification_deadline DATETIME NULL, -- BNSS 173(1): 3 days for signature/verification
    verified_at DATETIME NULL,
    inquiry_deadline DATETIME NULL,      -- BNSS 173(3): 14 days preliminary inquiry limit
    inquiry_notes TEXT NULL,
    rejection_reason TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (citizen_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_complaint_status (status),
    INDEX idx_complaint_station (police_station),
    INDEX idx_complaint_citizen (citizen_id)
) ENGINE=InnoDB;

-- 3. FIRs Table (Bharatiya Nagarik Suraksha Sanhita Registered FIRs)
CREATE TABLE IF NOT EXISTS firs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fir_number VARCHAR(50) NOT NULL UNIQUE,
    complaint_id INT NOT NULL UNIQUE,
    police_station VARCHAR(100) NOT NULL,
    investigating_officer_id INT NOT NULL,
    bns_sections TEXT NOT NULL, -- e.g. BNS 303(2), BNS 318(4)
    acts_and_sections TEXT NULL,
    date_of_occurrence VARCHAR(50) NOT NULL,
    date_reported DATETIME DEFAULT CURRENT_TIMESTAMP,
    place_of_occurrence VARCHAR(255) NOT NULL,
    complainant_name VARCHAR(150) NOT NULL,
    accused_details TEXT NULL,
    investigation_summary TEXT NULL,
    status VARCHAR(50) DEFAULT 'registered', -- registered, under_investigation, chargesheet_filed, closed
    chargesheet_summary TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
    FOREIGN KEY (investigating_officer_id) REFERENCES users(id),
    INDEX idx_fir_number (fir_number),
    INDEX idx_fir_station (police_station)
) ENGINE=InnoDB;

-- 4. Evidence Locker with SHA-256 Digital Chain of Custody
CREATE TABLE IF NOT EXISTS evidences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL,
    fir_id INT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size_kb INT NOT NULL,
    description TEXT NULL,
    hash_sha256 VARCHAR(64) NOT NULL,
    uploaded_by_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by_id) REFERENCES users(id),
    INDEX idx_evidence_complaint (complaint_id)
) ENGINE=InnoDB;

-- 5. Case Timeline Audit Events
CREATE TABLE IF NOT EXISTS timeline_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL,
    fir_id INT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- bnss_action, status_change, evidence_added, io_assigned, inquiry_note, chargesheet
    actor_name VARCHAR(150) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
    INDEX idx_timeline_complaint (complaint_id)
) ENGINE=InnoDB;

-- 6. AI Model Analysis Table (Inbound from Partner's AI/NLP Engine)
CREATE TABLE IF NOT EXISTS ai_analyses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL UNIQUE,
    recommended_sections JSON NULL,
    urgency_level VARCHAR(20) DEFAULT 'MEDIUM', -- LOW, MEDIUM, HIGH, CRITICAL
    duplicate_risk_score DECIMAL(5, 2) DEFAULT 0.00,
    duplicate_candidate_ids JSON NULL,
    extracted_entities JSON NULL,
    complaint_summary TEXT NULL,
    sentiment_emotion VARCHAR(50) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
    INDEX idx_ai_complaint (complaint_id)
) ENGINE=InnoDB;

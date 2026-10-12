-- =======================================================
-- Doctor Appointment Management System Database Schema
-- Database Name: doctor_appointment_db
-- =======================================================

CREATE DATABASE IF NOT EXISTS doctor_appointment_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE doctor_appointment_db;

-- -------------------------------------------------------
-- Table 1: users
-- Stores Patients, Doctors, and Administrators accounts
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(20) NULL,
    date_of_birth DATE NULL,
    gender ENUM('Male', 'Female', 'Other') DEFAULT 'Other',
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('patient', 'doctor', 'admin') NOT NULL DEFAULT 'patient',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_users_email (email),
    INDEX idx_users_role (role)
) ENGINE=InnoDB;

-- -------------------------------------------------------
-- Table 2: specializations
-- Medical specialties available at the clinic / hospital
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS specializations (
    specialization_id INT AUTO_INCREMENT PRIMARY KEY,
    specialization_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NULL
) ENGINE=InnoDB;

-- -------------------------------------------------------
-- Table 3: doctors
-- Doctor professional profiles linked to user accounts
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS doctors (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    specialization_id INT NOT NULL,
    qualification VARCHAR(150) NOT NULL,
    experience INT NOT NULL DEFAULT 0,
    consultation_fee DECIMAL(10,2) NOT NULL DEFAULT 50.00,
    biography TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_doctors_user FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_doctors_spec FOREIGN KEY (specialization_id)
        REFERENCES specializations(specialization_id) ON DELETE RESTRICT,
    INDEX idx_doctors_specialization (specialization_id),
    INDEX idx_doctors_active (is_active)
) ENGINE=InnoDB;

-- -------------------------------------------------------
-- Table 4: doctor_availability
-- Date and time blocks when a doctor accepts appointments
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS doctor_availability (
    availability_id INT AUTO_INCREMENT PRIMARY KEY,
    doctor_id INT NOT NULL,
    available_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    slot_duration INT NOT NULL DEFAULT 30, -- minutes per slot
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_avail_doctor FOREIGN KEY (doctor_id)
        REFERENCES doctors(doctor_id) ON DELETE CASCADE,
    INDEX idx_avail_doc_date (doctor_id, available_date)
) ENGINE=InnoDB;

-- -------------------------------------------------------
-- Table 5: appointments
-- Patient bookings with assigned doctor, date, time, and status
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    reason TEXT NOT NULL,
    status ENUM('Pending', 'Confirmed', 'Rejected', 'Cancelled', 'Completed') NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_apt_patient FOREIGN KEY (patient_id)
        REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_apt_doctor FOREIGN KEY (doctor_id)
        REFERENCES doctors(doctor_id) ON DELETE CASCADE,
    INDEX idx_apt_patient (patient_id),
    INDEX idx_apt_doctor (doctor_id),
    INDEX idx_apt_slot (doctor_id, appointment_date, appointment_time),
    INDEX idx_apt_status (status)
) ENGINE=InnoDB;

-- -------------------------------------------------------
-- Table 6: contact_messages
-- Public contact inquiries submitted through website
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS contact_messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL,
    subject VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- =======================================================
-- SEED DATA
-- Default Admin: admin@carepoint.com / Admin@123
-- Sample Doctors: Doctor@123
-- Sample Patients: Patient@123
-- =======================================================

-- 1. Insert Specializations
INSERT INTO specializations (specialization_id, specialization_name, description) VALUES
(1, 'Cardiology', 'Expert diagnosis and management of heart, vascular, and circulatory disorders.'),
(2, 'Neurology', 'Specialized care for brain, spine, peripheral nervous system, and stroke rehabilitation.'),
(3, 'Pediatrics', 'Comprehensive physical, behavioral, and developmental healthcare for infants, children, and teens.'),
(4, 'Dermatology', 'Advanced medical, surgical, and cosmetic treatments for skin, hair, and nail conditions.'),
(5, 'Orthopedics', 'Surgical and non-surgical solutions for bone, joint, ligament, and sports injuries.'),
(6, 'General Medicine', 'Primary care, diagnostic screening, preventative health exams, and chronic illness management.')
ON DUPLICATE KEY UPDATE specialization_name = VALUES(specialization_name);

-- 2. Insert Users (Admin, Doctors, Patients)
-- Passwords:
-- Admin@123: scrypt:32768:8:1$8foPf0WMisD30TmQ$dd186102cf40f055360c9bceb624e3d26e398a591a3721311bc4e004881a70cb561ebf0f5fd9ec47c3a6deb2f1de2bd8d1351389cb5bd0d7dacb208fde0b86e8
-- Doctor@123: scrypt:32768:8:1$X672wTZ1ybALXtjV$35e11992d6b7ffc649c9e10d46a3f3fa60d067f4a6288a967f83c3e2ee1a521f319435c2ac4c15b3afe30f22679d773cb3a8cd1be23edd488c1f79753acfb97e
-- Patient@123: scrypt:32768:8:1$oNQQlC37JiXFsAUA$795f805bae9523a172648e9a4fcf32893b5e02eaac01b68c77cd1271707592ae26cbc5926688809cf4287981b0519cf5d64b22426fb924af9256dffd411616e8

INSERT INTO users (user_id, full_name, email, phone, date_of_birth, gender, password_hash, role) VALUES
(1, 'System Administrator', 'admin@carepoint.com', '+1 (555) 010-0001', '1985-06-15', 'Male', 'scrypt:32768:8:1$8foPf0WMisD30TmQ$dd186102cf40f055360c9bceb624e3d26e398a591a3721311bc4e004881a70cb561ebf0f5fd9ec47c3a6deb2f1de2bd8d1351389cb5bd0d7dacb208fde0b86e8', 'admin'),
(2, 'Dr. Sarah Jenkins', 'sarah.jenkins@carepoint.com', '+1 (555) 010-0002', '1980-03-22', 'Female', 'scrypt:32768:8:1$X672wTZ1ybALXtjV$35e11992d6b7ffc649c9e10d46a3f3fa60d067f4a6288a967f83c3e2ee1a521f319435c2ac4c15b3afe30f22679d773cb3a8cd1be23edd488c1f79753acfb97e', 'doctor'),
(3, 'Dr. Michael Chen', 'michael.chen@carepoint.com', '+1 (555) 010-0003', '1978-11-09', 'Male', 'scrypt:32768:8:1$X672wTZ1ybALXtjV$35e11992d6b7ffc649c9e10d46a3f3fa60d067f4a6288a967f83c3e2ee1a521f319435c2ac4c15b3afe30f22679d773cb3a8cd1be23edd488c1f79753acfb97e', 'doctor'),
(4, 'Dr. Emily Rodriguez', 'emily.rodriguez@carepoint.com', '+1 (555) 010-0004', '1986-07-14', 'Female', 'scrypt:32768:8:1$X672wTZ1ybALXtjV$35e11992d6b7ffc649c9e10d46a3f3fa60d067f4a6288a967f83c3e2ee1a521f319435c2ac4c15b3afe30f22679d773cb3a8cd1be23edd488c1f79753acfb97e', 'doctor'),
(5, 'Dr. David Patel', 'david.patel@carepoint.com', '+1 (555) 010-0005', '1982-09-30', 'Male', 'scrypt:32768:8:1$X672wTZ1ybALXtjV$35e11992d6b7ffc649c9e10d46a3f3fa60d067f4a6288a967f83c3e2ee1a521f319435c2ac4c15b3afe30f22679d773cb3a8cd1be23edd488c1f79753acfb97e', 'doctor'),
(6, 'John Doe', 'patient@carepoint.com', '+1 (555) 010-0006', '1992-04-18', 'Male', 'scrypt:32768:8:1$oNQQlC37JiXFsAUA$795f805bae9523a172648e9a4fcf32893b5e02eaac01b68c77cd1271707592ae26cbc5926688809cf4287981b0519cf5d64b22426fb924af9256dffd411616e8', 'patient'),
(7, 'Jane Smith', 'jane.smith@example.com', '+1 (555) 010-0007', '1995-12-03', 'Female', 'scrypt:32768:8:1$oNQQlC37JiXFsAUA$795f805bae9523a172648e9a4fcf32893b5e02eaac01b68c77cd1271707592ae26cbc5926688809cf4287981b0519cf5d64b22426fb924af9256dffd411616e8', 'patient')
ON DUPLICATE KEY UPDATE email = VALUES(email);

-- 3. Insert Doctor Profiles
INSERT INTO doctors (doctor_id, user_id, specialization_id, qualification, experience, consultation_fee, biography, is_active) VALUES
(1, 2, 1, 'MD (Cardiology), FACC - Harvard Medical School', 14, 120.00, 'Senior interventional cardiologist with over 14 years of clinical experience specializing in preventive heart health and arrhythmias.', TRUE),
(2, 3, 2, 'MD, PhD (Neurology) - Johns Hopkins University', 16, 150.00, 'Board-certified neurologist specializing in neuro-muscular disorders, headache management, and stroke rehabilitation.', TRUE),
(3, 4, 3, 'MD (Pediatrics), FAAP - Stanford University', 9, 90.00, 'Compassionate pediatrician devoted to child wellness, developmental milestones, preventive care, and pediatric nutrition.', TRUE),
(4, 5, 4, 'MBBS, MD (Dermatology) - Mayo Clinic', 11, 110.00, 'Expert clinical dermatologist offering treatment for eczema, psoriasis, acne therapy, and preventive skin screening.', TRUE)
ON DUPLICATE KEY UPDATE qualification = VALUES(qualification);

-- 4. Insert Doctor Availability (using current and upcoming dates)
-- Dr. Sarah Jenkins (doctor_id = 1)
INSERT INTO doctor_availability (doctor_id, available_date, start_time, end_time, slot_duration, is_available) VALUES
(1, CURDATE(), '09:00:00', '13:00:00', 30, TRUE),
(1, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '09:00:00', '14:00:00', 30, TRUE),
(1, DATE_ADD(CURDATE(), INTERVAL 2 DAY), '14:00:00', '18:00:00', 30, TRUE),
(1, DATE_ADD(CURDATE(), INTERVAL 3 DAY), '09:00:00', '13:00:00', 30, TRUE);

-- Dr. Michael Chen (doctor_id = 2)
INSERT INTO doctor_availability (doctor_id, available_date, start_time, end_time, slot_duration, is_available) VALUES
(2, CURDATE(), '10:00:00', '15:00:00', 45, TRUE),
(2, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '10:00:00', '15:00:00', 45, TRUE),
(2, DATE_ADD(CURDATE(), INTERVAL 2 DAY), '10:00:00', '16:00:00', 45, TRUE);

-- Dr. Emily Rodriguez (doctor_id = 3)
INSERT INTO doctor_availability (doctor_id, available_date, start_time, end_time, slot_duration, is_available) VALUES
(3, CURDATE(), '08:30:00', '13:30:00', 30, TRUE),
(3, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '08:30:00', '13:30:00', 30, TRUE),
(3, DATE_ADD(CURDATE(), INTERVAL 3 DAY), '09:00:00', '14:00:00', 30, TRUE);

-- Dr. David Patel (doctor_id = 4)
INSERT INTO doctor_availability (doctor_id, available_date, start_time, end_time, slot_duration, is_available) VALUES
(4, CURDATE(), '13:00:00', '17:00:00', 30, TRUE),
(4, DATE_ADD(CURDATE(), INTERVAL 2 DAY), '09:00:00', '13:00:00', 30, TRUE),
(4, DATE_ADD(CURDATE(), INTERVAL 4 DAY), '11:00:00', '16:00:00', 30, TRUE);

-- 5. Insert Sample Appointments
INSERT INTO appointments (appointment_id, patient_id, doctor_id, appointment_date, appointment_time, reason, status) VALUES
(1, 6, 1, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '09:30:00', 'Routine cardiology review and blood pressure checkup.', 'Confirmed'),
(2, 6, 3, DATE_ADD(CURDATE(), INTERVAL 3 DAY), '10:00:00', 'Annual pediatric wellness checkup and vaccine consultation.', 'Pending'),
(3, 7, 2, DATE_ADD(CURDATE(), INTERVAL 2 DAY), '11:30:00', 'Recurring migraine episodes and tension headache screening.', 'Confirmed'),
(4, 7, 4, DATE_SUB(CURDATE(), INTERVAL 5 DAY), '14:00:00', 'Skin rash consultation and allergy assessment.', 'Completed')
ON DUPLICATE KEY UPDATE reason = VALUES(reason);

-- 6. Insert Sample Contact Messages
INSERT INTO contact_messages (message_id, name, email, subject, message) VALUES
(1, 'Alice Morgan', 'alice.m@example.com', 'Emergency Appointment Inquiry', 'Do you offer same-day urgent consultation slots on weekends?'),
(2, 'Robert Hayes', 'robert.hayes@example.com', 'Insurance Coverage Question', 'I would like to verify if Medicare Advantage plans are accepted at your clinic.')
ON DUPLICATE KEY UPDATE subject = VALUES(subject);

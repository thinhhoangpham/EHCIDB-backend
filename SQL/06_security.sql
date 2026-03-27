-- ========================================
-- SECURITY / ROLE-BASED ACCESS CONTROL
-- Provides role-based authorization layer
-- for Admin, Doctor, Patient, and Viewer
-- ========================================




USE ehcidb;

-- =========================
-- Security / Authorization
-- =========================

DROP TABLE IF EXISTS doctor_patient_access;
DROP TABLE IF EXISTS role_permission;
DROP TABLE IF EXISTS user_role;
DROP TABLE IF EXISTS permission;
DROP TABLE IF EXISTS role;
DROP TABLE IF EXISTS app_user;

CREATE TABLE app_user (
    user_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    patient_id BIGINT NULL,
    doctor_id BIGINT NULL,
    CONSTRAINT fk_app_user_patient
        FOREIGN KEY (patient_id) REFERENCES patient(patient_id),
    CONSTRAINT fk_app_user_doctor
        FOREIGN KEY (doctor_id) REFERENCES doctor(doctor_id)
);

CREATE TABLE role (
    role_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE permission (
    permission_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    permission_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE user_role (
    user_role_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    CONSTRAINT fk_user_role_user
        FOREIGN KEY (user_id) REFERENCES app_user(user_id),
    CONSTRAINT fk_user_role_role
        FOREIGN KEY (role_id) REFERENCES role(role_id),
    CONSTRAINT uq_user_role UNIQUE (user_id, role_id)
);

CREATE TABLE role_permission (
    role_permission_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    role_id BIGINT NOT NULL,
    permission_id BIGINT NOT NULL,
    CONSTRAINT fk_role_permission_role
        FOREIGN KEY (role_id) REFERENCES role(role_id),
    CONSTRAINT fk_role_permission_permission
        FOREIGN KEY (permission_id) REFERENCES permission(permission_id),
    CONSTRAINT uq_role_permission UNIQUE (role_id, permission_id)
);

CREATE TABLE doctor_patient_access (
    doctor_id BIGINT NOT NULL,
    patient_id BIGINT NOT NULL,
    PRIMARY KEY (doctor_id, patient_id),
    CONSTRAINT fk_doctor_patient_access_doctor
        FOREIGN KEY (doctor_id) REFERENCES doctor(doctor_id),
    CONSTRAINT fk_doctor_patient_access_patient
        FOREIGN KEY (patient_id) REFERENCES patient(patient_id)
);

-- =========================
-- Seed Roles
-- =========================

INSERT INTO role (role_name)
VALUES
    ('Admin'),
    ('Doctor'),
    ('Patient'),
    ('Viewer');

-- =========================
-- Seed Permissions
-- =========================

INSERT INTO permission (permission_name)
VALUES
    ('READ'),
    ('WRITE'),
    ('UPDATE'),
    ('DELETE');

-- =========================
-- Role -> Permission Mapping
-- =========================

-- Admin gets full CRUD
INSERT INTO role_permission (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM role r
JOIN permission p
WHERE r.role_name = 'Admin';

-- Doctor gets READ, WRITE, UPDATE
INSERT INTO role_permission (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM role r
JOIN permission p
WHERE r.role_name = 'Doctor'
  AND p.permission_name IN ('READ', 'WRITE', 'UPDATE');

-- Patient gets READ only
INSERT INTO role_permission (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM role r
JOIN permission p
WHERE r.role_name = 'Patient'
  AND p.permission_name = 'READ';

-- Viewer gets READ only
INSERT INTO role_permission (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM role r
JOIN permission p
WHERE r.role_name = 'Viewer'
  AND p.permission_name = 'READ';

-- =========================
-- Admin User
-- =========================

INSERT INTO app_user (username, password_hash, full_name, email)
VALUES
    ('admin', '$2b$12$/aodZvOnQAKAKpyyExoxOeibucbN7bS9yw81KTbldgf7d0tqJ2QFK', 'System Admin', 'admin@ehcidb.local');

-- =========================
-- Assign Admin Role
-- =========================

INSERT INTO user_role (user_id, role_id)
SELECT u.user_id, r.role_id
FROM app_user u
JOIN role r
WHERE u.username = 'admin'
  AND r.role_name = 'Admin';

-- =========================
-- Bulk-insert Patient Users
-- =========================

INSERT INTO app_user (username, password_hash, full_name, email, patient_id)
SELECT
    CONCAT('p_', p.patient_id),
    '$2b$12$/aodZvOnQAKAKpyyExoxOeibucbN7bS9yw81KTbldgf7d0tqJ2QFK',
    p.patient_name,
    CONCAT('p_', p.patient_id, '@ehcidb.local'),
    p.patient_id
FROM patient p;

-- =========================
-- Bulk-insert Doctor Users
-- =========================

INSERT INTO app_user (username, password_hash, full_name, email, doctor_id)
SELECT
    CONCAT('d_', d.doctor_id),
    '$2b$12$/aodZvOnQAKAKpyyExoxOeibucbN7bS9yw81KTbldgf7d0tqJ2QFK',
    d.doctor_name,
    CONCAT('d_', d.doctor_id, '@ehcidb.local'),
    d.doctor_id
FROM doctor d;

-- =========================
-- Assign Patient Role to All Patient Users
-- =========================

INSERT INTO user_role (user_id, role_id)
SELECT u.user_id, r.role_id
FROM app_user u
JOIN role r ON r.role_name = 'Patient'
WHERE u.patient_id IS NOT NULL;

-- =========================
-- Assign Doctor Role to All Doctor Users
-- =========================

INSERT INTO user_role (user_id, role_id)
SELECT u.user_id, r.role_id
FROM app_user u
JOIN role r ON r.role_name = 'Doctor'
WHERE u.doctor_id IS NOT NULL;

-- =========================
-- Populate doctor_patient_access from admission
-- =========================

INSERT INTO doctor_patient_access (doctor_id, patient_id)
SELECT DISTINCT doctor_id, patient_id
FROM admission;

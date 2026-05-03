USE ehcidb;

-- Drop tables in reverse-dependency order so FK constraints don't block the drops.
-- Emergency/security leaf tables (reference patient) are dropped before patient.
DROP TABLE IF EXISTS patient_insurance;
DROP TABLE IF EXISTS insurance_provider_detail;
DROP TABLE IF EXISTS access_log;
DROP TABLE IF EXISTS emergency_contact;
DROP TABLE IF EXISTS device;
DROP TABLE IF EXISTS patient_medication;
DROP TABLE IF EXISTS medical_condition;
DROP TABLE IF EXISTS allergy;
DROP TABLE IF EXISTS doctor_patient_access;
DROP TABLE IF EXISTS user_role;
DROP TABLE IF EXISTS role_permission;
DROP TABLE IF EXISTS permission;
DROP TABLE IF EXISTS role;
DROP TABLE IF EXISTS app_user;
DROP TABLE IF EXISTS admission;
DROP TABLE IF EXISTS patient;
DROP TABLE IF EXISTS doctor;
DROP TABLE IF EXISTS hospital;
DROP TABLE IF EXISTS dim_blood_type;
DROP TABLE IF EXISTS dim_medical_condition;
DROP TABLE IF EXISTS dim_insurance_provider;
DROP TABLE IF EXISTS dim_admission_type;
DROP TABLE IF EXISTS dim_medication;
DROP TABLE IF EXISTS dim_test_result;

CREATE TABLE dim_blood_type (blood_type_code VARCHAR(10) PRIMARY KEY);

DROP TABLE IF EXISTS dim_medical_condition;
CREATE TABLE dim_medical_condition (medical_condition VARCHAR(255) PRIMARY KEY);

DROP TABLE IF EXISTS dim_insurance_provider;
CREATE TABLE dim_insurance_provider (insurance_provider VARCHAR(255) PRIMARY KEY);

DROP TABLE IF EXISTS dim_admission_type;
CREATE TABLE dim_admission_type (admission_type VARCHAR(100) PRIMARY KEY);

DROP TABLE IF EXISTS dim_medication;
CREATE TABLE dim_medication (medication VARCHAR(255) PRIMARY KEY);

DROP TABLE IF EXISTS dim_test_result;
CREATE TABLE dim_test_result (test_result VARCHAR(100) PRIMARY KEY);

DROP TABLE IF EXISTS hospital;
CREATE TABLE hospital (
  hospital_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  hospital_name VARCHAR(255) NOT NULL,
  UNIQUE KEY uq_hospital_name (hospital_name)
);

DROP TABLE IF EXISTS doctor;
CREATE TABLE doctor (
  doctor_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  doctor_name VARCHAR(255) NOT NULL,
  UNIQUE KEY uq_doctor_name (doctor_name)
);

DROP TABLE IF EXISTS patient;
CREATE TABLE patient (
  patient_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  patient_name VARCHAR(255) NOT NULL,
  gender VARCHAR(50) NOT NULL,
  blood_type_code VARCHAR(10) NOT NULL,
  date_of_birth DATE NOT NULL,
  phone_number VARCHAR(20),
  email VARCHAR(255),
  address VARCHAR(500),
  UNIQUE KEY uq_patient (patient_name, gender, blood_type_code, date_of_birth),
  CONSTRAINT fk_patient_blood
    FOREIGN KEY (blood_type_code) REFERENCES dim_blood_type(blood_type_code)
);

DROP TABLE IF EXISTS admission;
CREATE TABLE admission (
  admission_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  patient_id BIGINT NOT NULL,
  doctor_id BIGINT NOT NULL,
  hospital_id BIGINT NOT NULL,

  medical_condition VARCHAR(255) NOT NULL,
  insurance_provider VARCHAR(255) NOT NULL,
  admission_type VARCHAR(100) NOT NULL,
  medication VARCHAR(255) NOT NULL,
  test_result VARCHAR(100) NOT NULL,

  age_at_admission INT NOT NULL,
  room_number INT NOT NULL,
  date_of_admission DATE NOT NULL,
  discharge_date DATE NOT NULL,
  billing_amount DECIMAL(12,2) NOT NULL,

  CONSTRAINT fk_adm_patient FOREIGN KEY (patient_id) REFERENCES patient(patient_id),
  CONSTRAINT fk_adm_doctor  FOREIGN KEY (doctor_id) REFERENCES doctor(doctor_id),
  CONSTRAINT fk_adm_hosp    FOREIGN KEY (hospital_id) REFERENCES hospital(hospital_id),

  CONSTRAINT fk_adm_cond    FOREIGN KEY (medical_condition) REFERENCES dim_medical_condition(medical_condition),
  CONSTRAINT fk_adm_ins     FOREIGN KEY (insurance_provider) REFERENCES dim_insurance_provider(insurance_provider),
  CONSTRAINT fk_adm_type    FOREIGN KEY (admission_type) REFERENCES dim_admission_type(admission_type),
  CONSTRAINT fk_adm_med     FOREIGN KEY (medication) REFERENCES dim_medication(medication),
  CONSTRAINT fk_adm_test    FOREIGN KEY (test_result) REFERENCES dim_test_result(test_result)
);


DROP TABLE IF EXISTS doctor_patient_assignment;

CREATE TABLE doctor_patient_assignment (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,

  doctor_id BIGINT NOT NULL,
  patient_id BIGINT NOT NULL,

  date_of_admission DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (doctor_id) REFERENCES doctor(doctor_id),
  FOREIGN KEY (patient_id) REFERENCES patient(patient_id)
);

-- DROP TABLE IF EXISTS doctor_patient_assignment;
-- CREATE TABLE doctor_patient_assignment (
--   id BIGINT AUTO_INCREMENT PRIMARY KEY,

--   doctor_id BIGINT NOT NULL,
--   patient_id BIGINT NOT NULL,

--   -- date_of_admission DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
--   assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

--   FOREIGN KEY (doctor_id) REFERENCES doctor(doctor_id),
--   FOREIGN KEY (patient_id) REFERENCES patient(patient_id)
-- );

-- ALTER TABLE doctor_patient_assignment
-- CHANGE COLUMN date_of_admission assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;
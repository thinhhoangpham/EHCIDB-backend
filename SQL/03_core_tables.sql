USE ehcidb;

DROP TABLE IF EXISTS dim_blood_type;
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
  UNIQUE KEY uq_patient (patient_name, gender, blood_type_code),
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
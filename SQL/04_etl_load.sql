USE ehcidb;

INSERT IGNORE INTO dim_blood_type(blood_type_code)
SELECT DISTINCT blood_type FROM stg_healthcare;

INSERT IGNORE INTO dim_medical_condition(medical_condition)
SELECT DISTINCT medical_condition FROM stg_healthcare;

INSERT IGNORE INTO dim_insurance_provider(insurance_provider)
SELECT DISTINCT insurance_provider FROM stg_healthcare;

INSERT IGNORE INTO dim_admission_type(admission_type)
SELECT DISTINCT admission_type FROM stg_healthcare;

INSERT IGNORE INTO dim_medication(medication)
SELECT DISTINCT medication FROM stg_healthcare;

INSERT IGNORE INTO dim_test_result(test_result)
SELECT DISTINCT test_results FROM stg_healthcare;

INSERT IGNORE INTO hospital(hospital_name)
SELECT DISTINCT hospital FROM stg_healthcare;

INSERT IGNORE INTO doctor(doctor_name)
SELECT DISTINCT doctor FROM stg_healthcare;

INSERT IGNORE INTO patient(patient_name, gender, blood_type_code)
SELECT DISTINCT name, gender, blood_type FROM stg_healthcare;

INSERT INTO admission (
  patient_id, doctor_id, hospital_id,
  medical_condition, insurance_provider, admission_type,
  medication, test_result,
  age_at_admission, room_number, date_of_admission, discharge_date,
  billing_amount
)
SELECT
  p.patient_id,
  d.doctor_id,
  h.hospital_id,
  s.medical_condition,
  s.insurance_provider,
  s.admission_type,
  s.medication,
  s.test_results,
  s.age,
  s.room_number,
  s.date_of_admission,
  s.discharge_date,
  s.billing_amount
FROM stg_healthcare s
JOIN patient p
  ON p.patient_name = s.name
 AND p.gender = s.gender
 AND p.blood_type_code = s.blood_type
JOIN doctor d
  ON d.doctor_name = s.doctor
JOIN hospital h
  ON h.hospital_name = s.hospital;
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

-- Build one row per (name, gender, blood_type) using the age from the earliest admission.
-- A subquery finds (name, gender, blood_type, age, min_date) with ONLY_FULL_GROUP_BY-safe
-- aggregation, then computes DOB and synthesizes contact fields in the outer query.
INSERT IGNORE INTO patient(patient_name, gender, blood_type_code, date_of_birth, phone_number, email, address)
SELECT
  s.name,
  s.gender,
  s.blood_type,
  -- DOB: earliest admission date minus the age recorded on that row
  DATE_SUB(s.date_of_admission, INTERVAL s.age YEAR)                           AS date_of_birth,
  -- Phone: deterministic 555-XXXX from CRC32 of name
  CONCAT('555-', LPAD(CRC32(s.name) % 10000, 4, '0'))                         AS phone_number,
  -- Email: firstname.lastname@example.com
  CONCAT(LOWER(REPLACE(s.name, ' ', '.')), '@example.com')                    AS email,
  -- Address: house number + one of 8 street names, both derived from name hash
  CONCAT(
    (CRC32(s.name) % 9000) + 1000, ' ',
    CASE CRC32(CONCAT(s.name, 'addr')) % 8
      WHEN 0 THEN 'Maple St'
      WHEN 1 THEN 'Oak Ave'
      WHEN 2 THEN 'Cedar Blvd'
      WHEN 3 THEN 'Elm Dr'
      WHEN 4 THEN 'Pine Rd'
      WHEN 5 THEN 'Willow Ln'
      WHEN 6 THEN 'Birch Way'
      WHEN 7 THEN 'Spruce Ct'
    END
  )                                                                             AS address
FROM stg_healthcare s
-- Pick only the row that matches the earliest admission for each (name, gender, blood_type).
-- Using MIN() in a subquery is ONLY_FULL_GROUP_BY-safe.
JOIN (
  SELECT name, gender, blood_type, MIN(date_of_admission) AS min_date
  FROM stg_healthcare
  GROUP BY name, gender, blood_type
) earliest
  ON  s.name        = earliest.name
  AND s.gender      = earliest.gender
  AND s.blood_type  = earliest.blood_type
  AND s.date_of_admission = earliest.min_date
-- Dedupe: if two rows share the same (name, gender, blood_type, min_date) pick any one.
GROUP BY s.name, s.gender, s.blood_type, s.date_of_admission, s.age;

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
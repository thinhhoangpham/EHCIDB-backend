USE ehcidb;

CREATE INDEX ix_adm_dates    ON admission(date_of_admission, discharge_date);
CREATE INDEX ix_adm_hospital ON admission(hospital_id);
CREATE INDEX ix_adm_doctor   ON admission(doctor_id);
CREATE INDEX ix_adm_patient  ON admission(patient_id);
CREATE INDEX ix_adm_cond     ON admission(medical_condition);
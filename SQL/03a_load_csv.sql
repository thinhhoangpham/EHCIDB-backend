USE ehcidb;

LOAD DATA INFILE '/data/healthcare_dataset_cleaned.csv'
INTO TABLE stg_healthcare
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(name, age, gender, blood_type, medical_condition, date_of_admission, doctor, hospital, insurance_provider, billing_amount, room_number, admission_type, discharge_date, medication, test_results);
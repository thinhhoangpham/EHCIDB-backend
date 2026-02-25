USE ehcidb;

DROP TABLE IF EXISTS stg_healthcare;

CREATE TABLE stg_healthcare (
  name               VARCHAR(255),
  age                INT,
  gender             VARCHAR(50),
  blood_type         VARCHAR(10),
  medical_condition  VARCHAR(255),
  date_of_admission  DATE,
  doctor             VARCHAR(255),
  hospital           VARCHAR(255),
  insurance_provider VARCHAR(255),
  billing_amount     DECIMAL(12,2),
  room_number        INT,
  admission_type     VARCHAR(100),
  discharge_date     DATE,
  medication         VARCHAR(255),
  test_results       VARCHAR(100)
);
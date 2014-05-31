DROP TABLE IF EXISTS surgeon_procedure;
DROP TABLE IF EXISTS provider_procedure;
ALTER TABLE provider RENAME TO provider_procedure;

DROP TABLE IF EXISTS procedure;
CREATE TABLE provider AS SELECT DISTINCT
  name, street, city, state, country, zipcode, email, phone, website
FROM   provider_procedure;

ALTER TABLE provider ADD COLUMN provider_id SERIAL;
UPDATE provider SET provider_id = DEFAULT;
ALTER TABLE provider ADD PRIMARY KEY (provider_id);
ALTER TABLE provider_procedure DROP CONSTRAINT provider_pkey;

UPDATE provider_procedure ss SET provider_id = 
  ( SELECT s.provider_id FROM provider s 
    WHERE  COALESCE(s.name, '') = COALESCE(ss.name, '')
    AND    COALESCE(s.street, '') = COALESCE(ss.street, '')
    AND    COALESCE(s.city, '') = COALESCE(ss.city, '')
    AND    COALESCE(s.country, '') = COALESCE(ss.country, '')
    AND    COALESCE(s.zipcode, '') = COALESCE(ss.zipcode, '')
    AND    COALESCE(s.email, '') = COALESCE(ss.email, '')
    AND    COALESCE(s.phone, '') = COALESCE(ss.phone, '')
    AND    COALESCE(s.website, '') = COALESCE(ss.website, '')
  );
ALTER TABLE provider_procedure DROP COLUMN name, 
                            DROP COLUMN street, 
                            DROP COLUMN city, 
                            DROP COLUMN country, 
                            DROP COLUMN zipcode, 
                            DROP COLUMN email, 
                            DROP COLUMN phone, 
                            DROP COLUMN website,
                            DROP COLUMN location_code, 
                            DROP COLUMN additional_procedures;

ALTER TABLE provider ADD COLUMN source text DEFAULT 'Eliot';

CREATE TABLE procedure AS SELECT DISTINCT procedure FROM provider_procedure;

ALTER TABLE procedure ADD COLUMN procedure_id SERIAL;
UPDATE procedure SET procedure_id = DEFAULT;
ALTER TABLE procedure ADD PRIMARY KEY (procedure_id);

ALTER TABLE provider_procedure ADD COLUMN procedure_id INTEGER;
UPDATE provider_procedure ss SET procedure_id = 
  ( SELECT s.procedure_id FROM procedure s WHERE ss.procedure = s.procedure);
ALTER TABLE provider_procedure ALTER COLUMN procedure_id SET NOT NULL;
ALTER TABLE provider_procedure ADD FOREIGN KEY (procedure_id) REFERENCES procedure (procedure_id);
ALTER TABLE provider_procedure DROP COLUMN procedure;


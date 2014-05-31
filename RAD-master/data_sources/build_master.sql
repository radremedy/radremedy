DROP TABLE IF EXISTS resource CASCADE;
CREATE TABLE resource
  ( id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    category    TEXT,
    street      TEXT,
    city        TEXT,
    state       TEXT,
    country     TEXT,
    zipcode     TEXT,
    email       TEXT,
    phone       TEXT,
    fax         TEXT,
    url         TEXT,
    description TEXT,
    source      TEXT);
    
INSERT INTO resource (id, name, category, street, city, state, country, zipcode, email, phone, url, description, source)
SELECT provider_id, name, 'provider', street, city, state, country, zipcode,
       email, phone, website,
       NULL, 'Eliot'
FROM provider;

ALTER SEQUENCE resource_id_seq RESTART WITH 800;
ALTER TABLE provider_procedure ADD FOREIGN KEY (provider_id) REFERENCES resource (id);

INSERT INTO resource (name, category, street, city, state, country, zipcode, email, phone, fax, url, description, source)
SELECT individual_name || office_name, type,
       address, city, state, 'United States', zip, 
       email, phone || '   ' || toll_free_phone, fax, url,
       services, 'TGAP'
FROM tgap;

DROP TABLE IF EXISTS tag;
CREATE TABLE tag
  ( id    SERIAL PRIMARY KEY,
    name  TEXT );
INSERT INTO tag (name) VALUES ('Youth');
DROP TABLE IF EXISTS tag_resource;
CREATE TABLE tag_resource
  ( tag_id      INTEGER NOT NULL,
    resource_id INTEGER NOT NULL );
INSERT INTO tag_resource (tag_id, resource_id)
SELECT 1, id FROM resource WHERE name IN ( 
  select individual_name || office_name from tgap where population = 'Youth'
  );
 
INSERT INTO resource (name, category, url, description, source)
SELECT link_text, category, link_target, description, 'Brown'
FROM brown_resources;

 
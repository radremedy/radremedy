
WITH new_values (id, field1, field2) as (
  values 
     (1, 'A', 'X'),
     (2, 'B', 'Y'),
     (3, 'C', 'Z')

),
upsert as
( 
    update mytable m 
        set field1 = nv.field1,
            field2 = nv.field2
    FROM new_values nv
    WHERE m.id = nv.id
    RETURNING m.*
)
INSERT INTO mytable (id, field1, field2)
SELECT id, field1, field2
FROM new_values
WHERE NOT EXISTS (SELECT 1 
                  FROM upsert up 
                  WHERE up.id = new_values.id)

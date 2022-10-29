SELECT id
FROM corelle.plate
WHERE model_id = (
  SELECT id
  FROM corelle.model
  WHERE name = :model_name)

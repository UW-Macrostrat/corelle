SELECT id
FROM corelle.plate
WHERE model_id = (
  SELECT id
  FROM model
  WHERE name = :model_name)

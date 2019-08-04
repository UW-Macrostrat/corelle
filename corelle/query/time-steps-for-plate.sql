SELECT *
FROM rotation
WHERE model_id = (SELECT id FROM model WHERE name = :model_name)
  AND plate_id = :plate_id
ORDER BY t_step

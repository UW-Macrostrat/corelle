/* Get rotations at or before a time by plate ID */
SELECT *
FROM rotation
WHERE t_step > :time
  AND model_id = (SELECT id FROM model WHERE name = :model_name)
  AND plate_id = :plate_id
ORDER BY t_step

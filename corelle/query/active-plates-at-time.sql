SELECT
  p.id
FROM plate p
JOIN plate_polygon pp
  ON p.id = pp.plate_id
JOIN model m
  ON p.model_id = m.id
WHERE m.name = :model_name
  AND pp.old_lim > :time
  AND coalesce(pp.young_lim, 0) < :time

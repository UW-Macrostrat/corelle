SELECT
  p.id
FROM plate p
JOIN plate_polygon pp
  ON p.id = pp.plate_id
 AND p.model_id = pp.model_id
JOIN model m
  ON p.model_id = m.id
WHERE m.name = :model_name
  AND coalesce(pp.old_lim, m.max_age) > :time
  AND coalesce(pp.young_lim, m.min_age) < :time

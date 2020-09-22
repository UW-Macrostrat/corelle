SELECT
  p.id,
  coalesce(pp.old_lim, m.max_age) old_lim,
  coalesce(pp.young_lim, m.min_age) young_lim
FROM plate p
JOIN plate_polygon pp
  ON p.id = pp.plate_id
 AND p.model_id = pp.model_id
JOIN model m
  ON p.model_id = m.id
WHERE m.name = :model_name

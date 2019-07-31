SELECT
  pp.id,
  pp.plate_id,
  coalesce(young_lim, 0) young_lim,
  old_lim,
  ST_AsGeoJSON(geometry) geometry,
  p.name
FROM plate_polygon pp
JOIN plate p
  ON pp.plate_id = p.id
 AND pp.model_id = p.model_id
JOIN model m
  ON p.model_id = m.id
WHERE m.name = :model_name

SELECT
  pp.id,
  pp.plate_id,
  coalesce(young_lim, 0) young_lim,
  old_lim,
  ST_AsGeoJSON(geometry) geometry,
  name
FROM plate_polygon pp
JOIN plate p
  ON pp.plate_id = p.id
WHERE model_id = 1

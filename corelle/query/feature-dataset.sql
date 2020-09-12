SELECT
  f.id,
	properties || jsonb_build_object(
		'plate_id', plate_id,
		'young_lim', coalesce(young_lim, m.min_age),
		'old_lim', coalesce(old_lim, m.max_age)) properties,
	ST_AsGeoJSON(
    ST_Intersection(
      ST_Buffer(p.geometry,0),
      ST_Buffer(f.geometry, 0)
    )
  )::json geometry,
	'Feature' "type"
FROM feature f
JOIN plate_polygon p
  ON p.geometry && f.geometry
 AND ST_Intersects(p.geometry, f.geometry)
JOIN model m
  ON m.id = p.model_id
WHERE dataset_id = :dataset
  AND model_id = (SELECT id FROM model WHERE name = :model_name)

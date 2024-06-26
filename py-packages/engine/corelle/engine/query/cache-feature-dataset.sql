WITH a AS (
SELECT
  model_id,
  json_agg(json_build_object(
  'id', f.id,
  'properties', properties || jsonb_build_object(
		'plate_id', plate_id,
		'young_lim', coalesce(young_lim, m.min_age),
		'old_lim', coalesce(old_lim, m.max_age)
  ),
  'geometry', ST_AsGeoJSON(
    ST_Intersection(
      ST_Buffer(p.geometry,0),
      ST_Buffer(f.geometry, 0)
    )
  )::jsonb,
  'type', 'Feature'
  )) geojson
FROM corelle.feature f
JOIN corelle.plate_polygon p
  ON p.geometry && f.geometry
 AND ST_Intersects(p.geometry, f.geometry)
JOIN corelle.model m
  ON m.id = p.model_id
WHERE dataset_id = :dataset_id
GROUP BY model_id
)
INSERT INTO corelle.feature_cache (model_id, model_name, geojson, dataset_id)
SELECT
	model_id,
	(SELECT name FROM corelle.model WHERE id = model_id) AS model_name,
	geojson,
	:dataset_id dataset_id
FROM a
ON CONFLICT (model_id, dataset_id)
DO UPDATE SET
  geojson = EXCLUDED.geojson;

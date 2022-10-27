DROP MATERIALIZED VIEW IF EXISTS corelle.plate_polygon_cache;
CREATE MATERIALIZED VIEW corelle.plate_polygon_cache AS
WITH a AS (
-- Basic query for plate polygons
SELECT
  pp.id,
  pp.plate_id,
  coalesce(young_lim, 0) young_lim,
  old_lim,
  p.name,
  ST_AsGeoJSON(geometry)::jsonb geometry,
  pp.model_id
FROM plate_polygon pp
JOIN plate p
  ON pp.plate_id = p.id
 AND pp.model_id = p.model_id
),
b AS (
SELECT json_build_object(
	'id', plate_id,
	'properties', json_build_object(
		'id', a.id,
		'plate_id', plate_id,
		'young_lim', young_lim,
		'old_lim', old_lim,
		'name', name
	),
	'type', 'Feature',
	'geometry', geometry
 ) r,
 model_id
FROM a
),
c AS (
SELECT
	model_id,
	json_agg(r) geojson
FROM b
GROUP BY model_id
)
SELECT
  m.id model_id,
  m.name model_name,
  c.geojson
FROM c
JOIN model m
  ON m.id = c.model_id;

SELECT
  plate_id
FROM plate_polygon p
WHERE model_id = (SELECT id FROM model WHERE name = :model_name)
  AND ST_Intersects(p.geometry, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
  AND coalesce(young_lim,0) < :time
  AND :time < old_lim

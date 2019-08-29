SELECT geojson
FROM cache.feature
WHERE model_name = :model_name
  AND dataset_id = :dataset

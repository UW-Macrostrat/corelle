SELECT geojson
FROM corelle.feature_cache
WHERE model_name = :model_name
  AND dataset_id = :dataset

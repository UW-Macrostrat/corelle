SELECT
	plate_id id,
	model_id,
	coalesce(p.old_lim, m.max_age, 4500) old_lim,
	coalesce(p.young_lim, m.min_age, 0) young_lim
FROM corelle.plate_polygon p
JOIN corelle.model m
  ON m.id = p.model_id
WHERE m.name = :model_name
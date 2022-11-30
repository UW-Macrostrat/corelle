UPDATE corelle.rotation_cache rc SET
  proj4text = corelle.build_proj_string(rotation),
  proj4inv = corelle.build_proj_string(corelle.invert_rotation(rotation)),
  envelope = ST_Envelope(corelle.rotate_geometry(pp.geometry, rotation))
FROM corelle.plate_polygon pp
WHERE rc.model_id = :model_id
  AND t_step = :t_step
  AND rc.plate_id = pp.plate_id
  AND rc.model_id = pp.model_id;
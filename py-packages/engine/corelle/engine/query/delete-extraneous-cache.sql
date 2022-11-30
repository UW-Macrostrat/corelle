DELETE
FROM corelle.rotation_cache rc
USING corelle.plate_polygon pp
WHERE rc.model_id = pp.model_id
  AND rc.plate_id = pp.plate_id
  AND t_step > coalesce(old_lim, 2500)
   OR t_step < coalesce(young_lim, 0);
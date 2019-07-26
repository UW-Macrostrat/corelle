SELECT
 p.id
FROM plate p
JOIN plate_polygon pp
  ON p.id = pp.plate_id
WHERE pp.old_lim > :time
  AND coalesce(pp.young_lim, 0) < :time

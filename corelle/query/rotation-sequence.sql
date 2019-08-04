/*
This query returns the previous and next time steps for a measurement
It should return zero, one, or two rows:
0 - the rotation doesn't exist (time out of range)
1 - we hit a time step exactly
2 - we are between two time steps
*/
WITH a AS (
SELECT
	plate_id,
	t_step,
	LAG(t_step) OVER (ORDER BY t_step) prev_step,
	LAG(t_step) OVER (ORDER BY t_step DESC) next_step,
	latitude,
	longitude,
	angle,
	ref_plate_id
FROM rotation
WHERE plate_id = :plate_id
  AND model_id = (SELECT id FROM model WHERE name = :model_name)
ORDER BY t_step
)
SELECT
	plate_id,
	prev_step,
	next_step,
	t_step,
	latitude,
	longitude,
	angle,
	ref_plate_id
FROM a
WHERE (prev_step < :time AND t_step > :time)
   OR (t_step <= :time AND next_step > :time)

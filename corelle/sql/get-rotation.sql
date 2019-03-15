/*
Stored procedure to get the plate-rotation sequence
for a single plate
*/
WITH plate_rotation AS (
SELECT
	plate_id,
	LAG(t_step) OVER (ORDER BY t_step) t_start,
	t_step t_orig_end,
	latitude,
	longitude,
	angle orig_angle,
	ref_plate_id
FROM rotation
WHERE plate_id = 10802
ORDER BY t_step
),
reduced_time AS (
SELECT
	*,
	least(t_orig_end, 4000) t_end
FROM plate_rotation
WHERE t_start < 4000
)
SELECT *,
	CASE
		WHEN t_orig_end > 4000
		THEN (t_end-t_start)/(t_orig_end-t_start)*orig_angle
		ELSE orig_angle
	END angle
FROM reduced_time

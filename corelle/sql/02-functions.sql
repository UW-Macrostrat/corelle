CREATE OR REPLACE FUNCTION rotation_sequence(plate_id integer, rot_time numeric)
RETURNS SETOF rotation_returntype AS $$
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
WHERE plate_id = plate_id
ORDER BY t_step
),
reduced_time AS (
SELECT
	*,
	least(t_orig_end, rot_time) t_end
FROM plate_rotation
WHERE t_start < rot_time
),
c AS (
SELECT *,
	CASE
		WHEN t_orig_end > rot_time
		THEN (t_end-t_start)/(t_orig_end-t_start)*orig_angle
		ELSE orig_angle
	END angle
FROM reduced_time
)
SELECT (
	plate_id,
	ref_plate_id,
	t_start,
	t_end,
	ARRAY[
		latitude,
		longitude,
		angle
	])::rotation_returntype
FROM c
$$ LANGUAGE 'sql';

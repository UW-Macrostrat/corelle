CREATE TYPE rotation_returntype AS (
	plate_id integer,
	ref_plate_id integer,
	t_start numeric,
	t_end numeric,
	euler_angle numeric[3]
);

/*
Function to get the rotation sequence for a single
plate up to a point in time. This function clips
the last Euler rotation to be representative of the
time requested, allowing the poles to be further
processed without scaling.
*/
CREATE OR REPLACE FUNCTION rotation_sequence(
  integer, numeric
)
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
WHERE plate_id = $1
ORDER BY t_step
),
reduced_time AS (
SELECT
	*,
	least(t_orig_end, $2) t_end
FROM plate_rotation
WHERE t_start < $2
),
c AS (
SELECT *,
	CASE
		WHEN t_orig_end > $2
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

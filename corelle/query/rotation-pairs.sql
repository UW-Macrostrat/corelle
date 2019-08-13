WITH plate_steps AS (
/*
Rotations for a specific plate and model id
*/
SELECT
  plate_id,
  ref_plate_id,
  metadata,
  t_step,
  ARRAY[latitude, longitude, angle] rotation,
  lag(t_step, 1) OVER (
    ORDER BY ref_plate_id, t_step
  ) prev_step
FROM rotation
WHERE plate_id = :plate_id
  AND model_id = (
    SELECT id
    FROM model
    WHERE name = :model_name)
ORDER BY t_step
),
step_pairs AS (
/*
Paired steps for interpolated rotations.
Unlike our previous attempt at the math, these
MUST have the same ref_plate_id, because this is
how GPlates is actually structured.
*/
SELECT
  p1.plate_id,
  p1.ref_plate_id,
  p1.t_step r1_step,
  p2.t_step r2_step,
  p1.rotation r1_rotation,
  p2.rotation r2_rotation,
  p1.metadata r1_metadata,
  p2.metadata r2_metadata
FROM plate_steps p1
JOIN plate_steps p2
  ON p1.t_step = p2.prev_step
 AND p1.ref_plate_id = p2.ref_plate_id
)
-- Get rotation that are exactly at `time`, if they exist
SELECT
	plate_id,
	ref_plate_id,
	t_step r1_step,
	null r2_step,
	rotation r1_rotation,
	null r2_rotation,
	metadata r1_metadata,
	null r2_metadata,
	false interpolated
FROM plate_steps
WHERE t_step = :time
UNION ALL
-- Get rotations that are after `time`
SELECT
  *,
  true interpolated
FROM step_pairs
WHERE r1_step < :time
  AND r2_step > :time

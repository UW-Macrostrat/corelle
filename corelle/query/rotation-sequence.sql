SELECT (
  rotation_sequence(
    (SELECT id FROM model WHERE name = :model_name),
    :plate_id,
    :time
  )
).*

CREATE TABLE IF NOT EXISTS model (
  id serial PRIMARY KEY,
  name text NOT NULL
);

CREATE TABLE IF NOT EXISTS plate (
  id integer PRIMARY KEY,
  model_id integer NOT NULL REFERENCES model(id),
  name text,
  cotid text,
  coid text,
  young_lim numeric,
  old_lim numeric,
  geometry geometry(MultiPolygon, 4326)
);

ALTER TABLE model
ADD COLUMN IF NOT EXISTS mantle_frame integer REFERENCES plate(id),
ADD COLUMN IF NOT EXISTS spin_axis integer REFERENCES plate(id);

CREATE TABLE IF NOT EXISTS rotation (
  plate_id integer REFERENCES plate(id),
  t_step numeric NOT NULL,
  latitude numeric,
  longitude numeric,
  angle numeric,
  ref_plate_id integer REFERENCES plate(id),
  metadata text
);

CREATE TABLE IF NOT EXISTS model (
  id serial PRIMARY KEY,
  name text UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS plate (
  id integer,
  model_id integer NOT NULL REFERENCES model(id),
  parent_id integer,
  name text,
  cotid text,
  coid text,
  PRIMARY KEY (id, model_id),
  FOREIGN KEY (parent_id, model_id) REFERENCES plate (id, model_id)
);

CREATE TABLE IF NOT EXISTS plate_polygon (
  id serial PRIMARY KEY,
  plate_id integer NOT NULL,
  model_id integer NOT NULL,
  young_lim numeric,
  old_lim numeric,
  geometry geometry(MultiPolygon, 4326),
  FOREIGN KEY (plate_id, model_id) REFERENCES plate (id, model_id)
);

CREATE TABLE IF NOT EXISTS rotation (
  plate_id integer NOT NULL,
  model_id integer NOT NULL,
  t_step numeric NOT NULL,
  latitude numeric,
  longitude numeric,
  angle numeric,
  ref_plate_id integer,
  metadata text,
  PRIMARY KEY (plate_id, model_id, t_step, ref_plate_id),
  FOREIGN KEY (plate_id, model_id) REFERENCES plate (id, model_id),
  FOREIGN KEY (ref_plate_id, model_id) REFERENCES plate (id, model_id)
);

-- Features that can be clipped by plate IDs and returned
CREATE TABLE IF NOT EXISTS feature (
  id serial PRIMARY KEY,
  dataset_id text NOT NULL,
  geometry geometry(Geometry, 4326),
  properties jsonb
);

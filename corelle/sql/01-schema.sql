CREATE TABLE IF NOT EXISTS model (
  id serial PRIMARY KEY,
  name text UNIQUE NOT NULL,
  min_age numeric DEFAULT 0,
  max_age numeric
);

CREATE TABLE IF NOT EXISTS plate (
  id integer,
  model_id integer NOT NULL REFERENCES model(id),
  parent_id integer,
  name text,
  cotid text,
  coid text,
  PRIMARY KEY (id, model_id),
  FOREIGN KEY (parent_id, model_id)
    REFERENCES plate (id, model_id)
    ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS plate_polygon (
  id serial PRIMARY KEY,
  plate_id integer NOT NULL,
  model_id integer NOT NULL,
  young_lim numeric,
  old_lim numeric,
  geometry geometry(MultiPolygon, 4326),
  FOREIGN KEY (plate_id, model_id)
    REFERENCES plate (id, model_id)
    ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS rotation (
  id serial PRIMARY KEY,
  plate_id integer NOT NULL,
  model_id integer NOT NULL,
  t_step numeric NOT NULL,
  latitude numeric NOT NULL,
  longitude numeric NOT NULL,
  angle numeric NOT NULL,
  ref_plate_id integer NOT NULL,
  metadata text,
  UNIQUE (plate_id, model_id, t_step, ref_plate_id),
  FOREIGN KEY (plate_id, model_id)
    REFERENCES plate (id, model_id)
    ON DELETE CASCADE,
  FOREIGN KEY (ref_plate_id, model_id)
    REFERENCES plate (id, model_id)
    ON DELETE CASCADE
);

-- Features that can be clipped by plate IDs and returned
CREATE TABLE IF NOT EXISTS corelle.feature (
  id serial PRIMARY KEY,
  dataset_id text NOT NULL,
  geometry geometry(Geometry, 4326),
  properties jsonb
);

/* Cache of features pre-converted to GeoJSON (probably should be deprecated!)*/
CREATE TABLE IF NOT EXISTS corelle.feature_cache (
  model_id integer NOT NULL REFERENCES model(id),
  model_name text NOT NULL REFERENCES model(name),
  dataset_id text NOT NULL,
  geojson json NOT NULL,
  PRIMARY KEY (model_id, dataset_id)
);

CREATE TABLE topology.meta
(
  topology_id integer NOT NULL,
  author character varying NOT NULL,
  creation timestamp without time zone NOT NULL,
  snapping double precision,
  kind character varying NOT NULL,
  grid_resolution double precision,
  CONSTRAINT meta_pkey PRIMARY KEY (topology_id),
  CONSTRAINT meta_topology_id_fkey FOREIGN KEY (topology_id)
      REFERENCES topology.topology (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
)
WITH (
  OIDS=FALSE
);
ALTER TABLE topology.meta
  OWNER TO postgres;

#!/usr/bin/env python3

from __future__ import annotations
import os
from io import StringIO

from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import sessionmaker

from sneparse import RESOURCES
from sneparse.coordinates import DecimalDegrees, DegreesMinutesSeconds
from sneparse.db.models import CLEANED_TABLE_NAME
from sneparse.util import unwrap

if __name__ == "__main__":
    # Setup a connection to db with our catalog
    local_engine = create_engine(URL.create(
        drivername=unwrap(os.getenv("DRIVER_NAME")),
        username  =os.getenv("ASTRO_USERNAME"),
        password  =os.getenv("ASTRO_PASSWORD"),
        host      =os.getenv("ASTRO_HOST"),
        database  =os.getenv("ASTRO_DATABASE")
    ))

    catalog_buffer = StringIO()

    local_session_maker = sessionmaker(local_engine)  
    with local_session_maker() as session:
        # Copy local catalog to memory
        copy_to = f"COPY {CLEANED_TABLE_NAME} TO STDOUT WITH (FORMAT csv);\n"
        print(copy_to)
        session.connection().connection.cursor().copy_expert(copy_to, catalog_buffer)

    catalog_buffer.seek(0)

    # Setup a connection to CIERA's VLASS db.
    remote_engine = create_engine(URL.create(
        drivername=unwrap(os.getenv("DRIVER_NAME")),
        username  =os.getenv("VLASS_USERNAME"),
        password  =os.getenv("VLASS_PASSWORD"),
        host      =os.getenv("VLASS_HOST"),
        database  =os.getenv("VLASS_DATABASE"),
        port      =int(unwrap(os.getenv("VLASS_PORT")))
    ))

    remote_session_maker = sessionmaker(remote_engine)  
    with remote_session_maker() as session:
        # Create a temporary table to hold our catalog, and fill it with the
        # table we previously put in memory.
        #
        # Ideally, we could use posgres_fdw for this, but it is far too slow.
        temp_catalog = "temp_catalog"
        create_temp_catalog = text(
            f"CREATE TEMPORARY TABLE {temp_catalog} (       \n"
             "    cleaned_id integer NOT NULL,              \n"
             "    master_id integer NOT NULL,               \n"
             "    name character varying NOT NULL,          \n"
             "    right_ascension double precision,         \n"
             "    declination double precision,             \n"
             "    discover_date timestamp without time zone,\n"
             "    claimed_type character varying,           \n"
             "    source text NOT NULL                      \n"
             ");                                            \n"
        )
        print(create_temp_catalog)
        session.execute(create_temp_catalog)

        copy_from = f"COPY {temp_catalog} FROM STDIN WITH (FORMAT csv);\n"
        print(copy_from)
        session.connection().connection.cursor().copy_expert(copy_from, catalog_buffer)

        # Prepare the temp catalog table for cross matching
        q3c_prepare_catalog = text(
            f"CREATE INDEX ON {temp_catalog} (q3c_ang2ipix(\"right_ascension\", \"declination\"));\n"
            f"CLUSTER {temp_catalog}_q3c_ang2ipix_idx ON {temp_catalog};                          \n"
            f"ANALYZE {temp_catalog};                                                             \n"
        )
        print(q3c_prepare_catalog)
        session.execute(q3c_prepare_catalog);

        # The foreign VLASS sources table is not indexed properly, so we create a temp
        # copy of it and prepare it for cross matching.
        temp_gaussian = "temp_gaussian"
        create_temp_gaussian = text(f"CREATE TEMPORARY TABLE {temp_gaussian} AS TABLE pybdsf_gaussian_epoch1;\n")
        print(create_temp_gaussian)
        session.execute(create_temp_gaussian)

        q3c_prepare_gaussian = text(
            f"CREATE INDEX ON {temp_gaussian} (q3c_ang2ipix(\"ra\", \"decl\"));\n"
            f"CLUSTER {temp_gaussian}_q3c_ang2ipix_idx ON {temp_gaussian};     \n"
            f"ANALYZE {temp_gaussian};                                         \n"
        )
        print(q3c_prepare_gaussian)
        session.execute(q3c_prepare_gaussian);

        # Do the actual cross matching.
        separation = DecimalDegrees.from_dms(DegreesMinutesSeconds(1, 0, 0, 5)).degrees

        temp_cross_match = "temp_cross_match"
        cross_match = text(
            f"CREATE TEMPORARY TABLE {temp_cross_match} AS                                    \n"
            f"    SELECT * FROM {temp_catalog} AS a, {temp_gaussian} AS b                     \n"
            f"    WHERE q3c_join(a.right_ascension, a.declination, b.ra, b.decl, {separation})\n"
            f"        AND a.discover_date < TIMESTAMP '2019-08-01'                            \n"
        )
        print(cross_match)
        session.execute(cross_match)

        # Copy cross matches into memory
        cross_matches_buffer = StringIO()
        copy_cross_matches = f"COPY {temp_cross_match} TO STDOUT WITH (FORMAT csv, HEADER);\n"
        print(copy_cross_matches)
        session.connection().connection.cursor().copy_expert(copy_cross_matches, cross_matches_buffer)
        cross_matches_buffer.seek(0)

    output_file = RESOURCES.joinpath("cross_matches.csv")
    print(f"Writing results to {output_file}")
    with open(output_file, "w") as csvfile:
        # Save the results to an output file.
        print(cross_matches_buffer.getvalue(), file=csvfile)

#!/usr/bin/env python3
from __future__ import annotations
import os
from io import StringIO
from pathlib import Path
from pprint import pprint

from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import sessionmaker

from sneparse.definitions import ROOT_DIR
from sneparse.util import unwrap

if __name__ == "__main__":
    # Initialize Postgres connection
    engine = create_engine(URL.create(
        drivername=unwrap(os.getenv("DRIVER_NAME")),
        username  =os.getenv("VLASS_USERNAME"),
        password  =os.getenv("VLASS_PASSWORD"),
        host      =os.getenv("VLASS_HOST"),
        database  =os.getenv("VLASS_DATABASE"),
        port      =int(unwrap(os.getenv("VLASS_PORT")))
    ))

    session_maker = sessionmaker(engine)  
    with session_maker() as session:
        vlass_dir = Path(ROOT_DIR).joinpath("resources", "vlass_files");
        names = [line.strip() for f in vlass_dir.glob("*.txt") for line in f.open()]

        # Create a temporary table in the database to hold the names from the file.
        temp_table_name = "temp_file_names"
        create_temp_table = text(f"CREATE TEMPORARY TABLE {temp_table_name} (file_name text)")
        print(create_temp_table)
        session.execute(create_temp_table)

        # Create a CSV buffer in-memory for the table insertion.
        csv_buffer = StringIO()
        csv_buffer.writelines(name + '\n' for name in names)
        csv_buffer.seek(0)

        # Copy the observed file names into the temporary table.
        # COPY is much much faster than INSERT for bulk data insertion (due to round trip
        # latency).
        copy_names = f"COPY {temp_table_name} (file_name) FROM STDIN WITH (FORMAT csv)"
        print(copy_names)
        session.connection().connection.cursor().copy_expert(copy_names, csv_buffer)

        # Find which observed files don't exist in the file_definition table.
        check_names = \
                text(f"SELECT file_name FROM {temp_table_name} EXCEPT SELECT file_name FROM file_definition")
        print(check_names)
        result = session.execute(check_names)

        missing_files = [r[0] for r in result.all()]

        # Cleanup: Drop the temporary table. (It should be dropped when the session ends anyway, so
        # this is probably unnecessary).
        drop_temp_table = text(f"DROP TABLE {temp_table_name}")
        print(drop_temp_table)
        session.execute(drop_temp_table)

        print("\nThe following files were not found in the `file_definition` table:")
        pprint(missing_files)

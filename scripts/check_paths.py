#!/usr/bin/env python3
from __future__ import annotations
from pprint import pprint
from pathlib import Path
import os
from tqdm import tqdm

from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import sessionmaker

from sneparse.util import unwrap

if __name__ == "__main__":
    # Setup a connection to CIERA's VLASS db.
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
        get_all_paths = text(f"SELECT path_to_file FROM file_definition;\n")
        print(get_all_paths)
        paths = session.execute(get_all_paths).all()

        fails: list[Path] = []
        for (path,) in tqdm(paths):
            f = Path("/projects/b1094/software/catalogs/").joinpath(path)
            if not f.exists():
                fails.append(f)

        if (len(fails) != 0):
            print("The following paths in 'file_definition' do not exist on Quest:")
            pprint(fails)
        else:
            print("All paths in 'file_definition' exist on Quest.")



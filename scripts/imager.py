#!/usr/bin/env python3
from typing import Optional
from pprint import pprint
from csv import DictReader
from dataclasses import dataclass
import os
from pathlib import Path
import re
import traceback
import subprocess
import argparse
import pickle

from tqdm import tqdm
from aplpy.core import log
from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from sneparse import RESOURCES
from sneparse.util import unwrap
from sneparse.imaging import plot_image_apl

EPOCH_RE = re.compile(r"(?<=VLASS).+(?=\.ql)")
VERSION_RE = re.compile(r"(?<=\.v).+(?=\.I\.iter)")

def find_paths(session: Session, file_name: str, epoch: int) -> set[Path]:
    like = re.sub(VERSION_RE, "%", re.sub(EPOCH_RE, f"{epoch}.%", file_name))

    select_path_name = text(
        f"SELECT concat(path_to_file, file_name) FROM file_definition WHERE file_name LIKE '{like}';"
    )
    result = session.execute(select_path_name).all()

    return { Path("/projects/b1094/software/catalogs/").joinpath(row[0]) for row in result }

@dataclass
class CrossMatchInfo():
    file_paths: set[Path]
    ra: float
    dec: float
 
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("start", type=int)
    parser.add_argument("count", type=int)
    parser.add_argument("--cache-file", type=str)
    parser.add_argument("--make-cache-file", type=str)

    args = parser.parse_args()

    start: int = args.start
    count: int = args.count
    cache_file: Optional[str] = args.cache_file
    make_cache_file: Optional[str] = args.make_cache_file

    sne: dict[str, CrossMatchInfo] = {}

    if cache_file is not None:
        with open(cache_file, "rb") as f:
            sne = pickle.load(f)
    else:
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
            fails: list[str] = []

            epoch = 1

            # Total for tqdm to display. -2 for header and trailing newline (but it doesnt
            # have to be precise).
            total = sum(1 for _ in RESOURCES.joinpath("cross_matches.csv").open()) - 2;

            with RESOURCES.joinpath("cross_matches.csv").open() as f:
                for row in tqdm(DictReader(f), total=total):
                    file_paths = find_paths(session, row["file_name"], epoch)

                    if len(file_paths) == 0:
                        fails.append(row["file_name"])

                    if row["name"] not in sne:
                        sne[row["name"]] = CrossMatchInfo(file_paths,
                                                          float(row["right_ascension"]),
                                                          float(row["declination"]))
                    else:
                        sne[row["name"]].file_paths.update(file_paths)

        if len(fails) > 0:
            print(f"Unable to find FITS files for the following file names in epoch {epoch}:")
            pprint(fails)

    if make_cache_file is not None:
        with open(make_cache_file, "wb") as f:
            pickle.dump(sne, f)

    # Turn off aplpy logs
    log.disabled = True

    for (name, info) in list(sne.items())[start : start + count]:
        file_paths = info.file_paths
        ra = info.ra
        dec = info.dec

        successes: list[Path] = []

        try:
            fig = plot_image_apl(
                ra, dec, name=name, cmap="gray_r", filters="r", is_radio=False,
            )
            path = RESOURCES.joinpath("images", "optical", f"{name}.png")
            fig.save(path)
            fig.close()
            successes.append(path)
        except Exception:
            traceback.print_exc()
            print(f"[PARTIAL FAIL] Failed to plot source \"{name}\" (ra={ra}, dec={dec}) in optical.")

        try:
            image_file = list(file_paths)[0]
            fig = plot_image_apl(
                ra, dec, name=name, cmap="gray_r", image_file=str(image_file), is_radio=True
            )
            path = RESOURCES.joinpath("images", "radio", f"{name}.png")
            fig.save(path)
            fig.close()
            successes.append(path)
        except Exception:
            traceback.print_exc()
            print(f"[PARTIAL FAIL] Failed to plot source \"{name}\" (ra={ra}, dec={dec}) in radio.")

        if len(successes) > 0:
            output = RESOURCES.joinpath("images", "cross_matches", f"{name}.png")
            subprocess.run(["convert", "+append"] + [str(path) for path in successes] + [str(output)])
            for path in successes:
                path.unlink()
            print(f"[SUCCESS] Plotted source \"{name}\" (ra={ra}, dec={dec}).")
        else:
            print(f"[FAIL] Failed to plot source \"{name}\" (ra={ra}, dec={dec}) in both optical and radio.")

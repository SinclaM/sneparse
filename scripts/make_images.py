#!/usr/bin/env python3
from typing import Optional, Tuple
from pprint import pprint
from csv import DictReader
import os
from pathlib import Path
import traceback
import argparse
import pickle
from datetime import datetime

from tqdm import tqdm
from aplpy.core import log
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker
import matplotlib.pyplot as plt

from sneparse import RESOURCES
from sneparse.record import SneRecord, Source
from sneparse.util import unwrap, find_paths
from sneparse.imaging import plot_image_apl

if __name__ == "__main__":
    epoch = int(unwrap(os.getenv("EPOCH")))

    parser = argparse.ArgumentParser()
    parser.add_argument("start", type=int)
    parser.add_argument("count", type=int)
    parser.add_argument("--cache-file", type=str)
    parser.add_argument("--make-cache-file", type=str)
    parser.add_argument("--sne", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--tde", action=argparse.BooleanOptionalAction, default=False)

    args = parser.parse_args()

    start: int = args.start
    count: int = args.count
    cache_file: Optional[str] = args.cache_file
    make_cache_file: Optional[str] = args.make_cache_file

    engine = create_engine(URL.create(
        drivername=unwrap(os.getenv("DRIVER_NAME")),
        username  =os.getenv("TRANSIENTS_USERNAME"),
        password  =os.getenv("TRANSIENTS_PASSWORD"),
        host      =os.getenv("TRANSIENTS_HOST"),
        database  ="vlass",
        port      =int(unwrap(os.getenv("TRANSIENTS_PORT")))
    ))

    session_maker = sessionmaker(engine)

    if args.sne:
        sne: dict[SneRecord, set[Path]] = {}

        if cache_file is not None:
            with open(cache_file, "rb") as f:
                sne = pickle.load(f)
        else:
            with session_maker() as session:
                fails: list[Tuple[str, str]] = []

                # Total for tqdm to display. -2 for header and trailing newline (but it doesnt
                # have to be precise).
                total = sum(1 for _ in RESOURCES.joinpath(f"epoch{epoch}_cross_matches.csv").open()) - 2

                with RESOURCES.joinpath(f"epoch{epoch}_cross_matches.csv").open() as f:
                    for row in tqdm(DictReader(f), total=total):
                        file_paths = find_paths(session, row["file_name"], epoch)

                        if len(file_paths) == 0:
                            fails.append((row["name"], row["file_name"]))

                        record = SneRecord(
                            row["name"],
                            float(row["right_ascension"]),
                            float(row["declination"]),
                            None if row["discover_date"] == "" else datetime.fromisoformat(row["discover_date"]),
                            None if row["claimed_type"] == "" else row["claimed_type"],
                            row["source"]
                        )

                        if row["name"] not in sne:
                            sne[record] = file_paths
                        else:
                            sne[record].update(file_paths)

            if len(fails) > 0:
                print(f"Unable to find FITS files for the following (sne, file) pairs in epoch {epoch}:")
                pprint(fails)

        if make_cache_file is not None:
            with open(make_cache_file, "wb") as f:
                pickle.dump(sne, f)

        # Turn off aplpy logs
        log.disabled = True

        for (record, file_paths) in list(sne.items())[start : start + count]:
            name = record.name
            ra = unwrap(record.right_ascension).degrees
            dec = unwrap(record.declination).degrees

            success = False

            fig = plt.figure(figsize=(16, 8))
            title_date = "Unknown discovery date" if record.discover_date is None \
                            else f"Discovered {record.discover_date.date()}"

            title_claimed_type = "Unknown claimed type" if record.claimed_type is None \
                            else f"Type {record.claimed_type}"

            fig.suptitle( f"{name}        {title_date}        {title_claimed_type}", size="xx-large")

            try:
                plot_image_apl(
                    record,
                    cmap="gray_r",
                    size=340,
                    filters="r",
                    is_radio=False,
                    figure=fig,
                    subplot=[0.07, 0.05, 0.38, 0.9]
                )
                success = True
            except Exception:
                traceback.print_exc()
                print(f"[PARTIAL FAIL] Failed to plot source \"{name}\" (ra={ra}, dec={dec}) in optical.")

            try:
                image_file = list(file_paths)[0]
                plot_image_apl(
                    record,
                    cmap="gray_r",
                    size=340,
                    image_file=str(image_file),
                    is_radio=True,
                    figure=fig,
                    subplot=[0.57, 0.05, 0.38, 0.9]
                )
                success = True
            except Exception:
                traceback.print_exc()
                print(f"[PARTIAL FAIL] Failed to plot source \"{name}\" (ra={ra}, dec={dec}) in radio.")

            if success:
                plt.savefig(RESOURCES.joinpath("images", f"epoch{epoch}_cross_matches", f"{name}.png"))
                print(f"[SUCCESS] Plotted source \"{name}\" (ra={ra}, dec={dec}).")
            else:
                print(f"[FAIL] Failed to plot source \"{name}\" (ra={ra}, dec={dec}) in both optical and radio.")
            plt.close()
    if args.tde:
        tde: dict[SneRecord, set[Path]] = {}
        with session_maker() as session:
            fails: list[Tuple[str, str]] = []

            # Total for tqdm to display. -2 for header and trailing newline (but it doesnt
            # have to be precise).
            total = sum(1 for _ in RESOURCES.joinpath(f"epoch{epoch}_cross_matches_tde.csv").open()) - 2

            with RESOURCES.joinpath(f"epoch{epoch}_cross_matches_tde.csv").open() as f:
                for row in tqdm(DictReader(f), total=total):
                    file_paths = find_paths(session, row["file_name"], epoch)

                    if len(file_paths) == 0:
                        fails.append((row["name"], row["file_name"]))

                    record = SneRecord(
                        row["name"],
                        float(row["right_ascension"]),
                        float(row["declination"]),
                        None if row["discover_date"] == "" else datetime.fromisoformat(row["discover_date"]),
                        None if row["claimed_type"] == "" else row["claimed_type"],
                        Source.OAC
                    )

                    if row["name"] not in tde:
                        tde[record] = file_paths
                    else:
                        tde[record].update(file_paths)

        if len(fails) > 0:
            print(f"Unable to find FITS files for the following (tde, file) pairs in epoch {epoch}:")
            pprint(fails)

        # Turn off aplpy logs
        log.disabled = True

        for (record, file_paths) in list(tde.items()):
            name = record.name
            ra = unwrap(record.right_ascension).degrees
            dec = unwrap(record.declination).degrees

            success = False

            fig = plt.figure(figsize=(16, 8))
            title_date = "Unknown discovery date" if record.discover_date is None \
                            else f"Discovered {record.discover_date.date()}"

            title_claimed_type = "Unknown claimed type" if record.claimed_type is None \
                            else f"Type {record.claimed_type}"

            fig.suptitle( f"{name}        {title_date}        {title_claimed_type}", size="xx-large")

            try:
                plot_image_apl(
                    record,
                    cmap="gray_r",
                    size=340,
                    filters="r",
                    is_radio=False,
                    figure=fig,
                    subplot=[0.07, 0.05, 0.38, 0.9]
                )
                success = True
            except Exception:
                traceback.print_exc()
                print(f"[PARTIAL FAIL] Failed to plot source \"{name}\" (ra={ra}, dec={dec}) in optical.")

            try:
                image_file = list(file_paths)[0]
                plot_image_apl(
                    record,
                    cmap="gray_r",
                    size=340,
                    image_file=str(image_file),
                    is_radio=True,
                    figure=fig,
                    subplot=[0.57, 0.05, 0.38, 0.9]
                )
                success = True
            except Exception:
                traceback.print_exc()
                print(f"[PARTIAL FAIL] Failed to plot source \"{name}\" (ra={ra}, dec={dec}) in radio.")

            if success:
                plt.savefig(RESOURCES.joinpath("images", f"epoch{epoch}_cross_matches_tde", f"{name}.png"))
                print(f"[SUCCESS] Plotted source \"{name}\" (ra={ra}, dec={dec}).")
            else:
                print(f"[FAIL] Failed to plot source \"{name}\" (ra={ra}, dec={dec}) in both optical and radio.")
            plt.close()

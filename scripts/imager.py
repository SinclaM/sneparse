#!/usr/bin/env python3
from typing import Tuple
from csv import DictReader

from aplpy.core import log

from sneparse.definitions import ROOT_DIR
from sneparse.imaging import plot_image_astropy, plot_image_apl
 
if __name__ == "__main__":
    sne: dict[str, Tuple[float, float]] = {}
    with ROOT_DIR.joinpath("resources", "cross_matches.csv").open() as f:
        for row in DictReader(f):
            if row["name"] not in sne:
                sne[row["name"]] = (float(row["right_ascension"]), float(row["declination"]))

    # Turn off aplpy logs
    log.disabled = True

    for (name, (ra, dec)) in sne.items():
        try:
            fig = plot_image_apl(ra, dec, name=name, cmap="gray_r", filters="r")
            fig.save(ROOT_DIR.joinpath("resources", "images", "cross_matches", name))
            fig.close()
            print(f"[SUCCESS] Plotted source \"{name}\" (ra={ra}, dec={dec}).")
        except Exception as e:
            print(e)
            print(f"[FAIL] Failed to plot source \"{name}\" (ra={ra}, dec={dec}).")

#!/usr/bin/env python3
from typing import Optional
from csv import DictReader
from dataclasses import dataclass
import os
import re

from aplpy.core import log

from sneparse import RESOURCES
from sneparse.util import unwrap
from sneparse.imaging import plot_image_astropy, plot_image_apl

# Recently compiled regex's are automatically cached, so precompiling
# is only really necessary if we were to use more regex's than fit in the
# cache. But better safe than sorry.
epoch = r"(?P<epoch>.*)"
tile = r"(?P<tile>T\d\dt\d\d)"
j_info = r"(?P<j_info>J\d*[+-]\d*\.\d*\.\d*)"
version = r"(?P<version>.*)"
suffix = r"(?P<suffix>I\.iter1\.image\.pbcor\.tt0\.subim\.fits\.gz)"
VLASS_FILE_RE = re.compile(fr"VLASS{epoch}\.ql\.{tile}\.{j_info}\.{version}\.{suffix}");

VLASS_QUICKLOOK = unwrap(os.getenv("VLASS_QUICKLOOK"))
def paths_from_file_name(file_name: str) -> Optional[str]:
    match = unwrap(VLASS_FILE_RE.match(file_name))
    epoch = match.group("epoch")
    j_info = match.group("j_info")
    version = match.group("version")
    if version != "v1":
        return None
    tile = match.group("tile")
    suffix = match.group("suffix")

    dir_ = f"VLASS{epoch[0]}*.ql.{tile}.{j_info}.v*"
    file = f"{dir_}.{suffix}"

    out =  f"{VLASS_QUICKLOOK}/VLASS{epoch[0]}*{'v2' if epoch[0] == '1' else ''}/{tile}/{dir_}/{file}"
    return out

@dataclass
class CrossMatchInfo():
    file_names: list[str]
    ra: float
    dec: float
 
if __name__ == "__main__":
    sne: dict[str, CrossMatchInfo] = {}
    with RESOURCES.joinpath("cross_matches.csv").open() as f:
        for row in DictReader(f):
            file_path = paths_from_file_name(row["file_name"])
            if file_path is None:
                continue
            if row["name"] not in sne:
                sne[row["name"]] = CrossMatchInfo([file_path],
                                                  float(row["right_ascension"]),
                                                  float(row["declination"]))
            else:
                sne[row["name"]].file_names.append(file_path)

    # Turn off aplpy logs
    log.disabled = True

    for (name, info) in sne.items():
        file_names = info.file_names
        ra = info.ra
        dec = info.dec
        print(file_names[0])
        # try:
            # fig = plot_image_apl(ra, dec, name=name, cmap="gray_r", filters="r")
            # fig.save(RESOURCES.joinpath("images", "cross_matches", name))
            # fig.close()
            # print(f"[SUCCESS] Plotted source \"{name}\" (ra={ra}, dec={dec}).")
        # except Exception as e:
            # print(e)
            # print(f"[FAIL] Failed to plot source \"{name}\" (ra={ra}, dec={dec}).")

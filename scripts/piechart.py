#!/usr/bin/env python3
from pathlib import Path
import re
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt

from sneparse import RESOURCES

if __name__ == "__main__":
    df = pd.read_csv(RESOURCES.joinpath("sne.csv"))
    c = Counter(df['name'].map(lambda s: s if (r := re.search(r"[-_ ]*\d", s)) is None else s[:r.start()])
                          .tolist())
    patches, _ = plt.pie(c.values(), startangle=90)
    patches, _, _ = zip(*sorted(zip(patches, c.keys(), c.values()),
                                    key=lambda x: x[2],
                                    reverse=True))

    plt.legend(patches, c.keys(), loc='center right', fontsize=4)
    plt.savefig(Path(RESOURCES).joinpath("resources", "images", "names.png"))
    


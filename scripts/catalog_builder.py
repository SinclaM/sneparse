#!/usr/bin/env python3

from sneparse.catalog import Catalog

c = Catalog()
c.parse_dir("oac-data")

for record in c.records:
    print(record)

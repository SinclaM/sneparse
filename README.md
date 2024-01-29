# 🌌 Sneparse

Sneparse is a tool for parsing, processing, cross-matching, and imaging supernovae (SNe) and other transients
in sky surveys. This tool was developed as part of research into late-time radio-luminous SNe in epochs
of the Very Large Array Sky Survey (VLASS).

## Installation and Setup

This project requires:
* `python >= 3.11`
* `Make` (optional, used as a task runner)

To clone this repository and install the project dependencies, run:

```bash
git clone https://github.com/SinclaM/sneparse.git
cd sneparse
pip install -e .
```

If you are using anaconda, you can `conda install` all the dependencies listed in `pyproject.toml`, except
`aplpy`, which needs to be installed with `pip` (see [this issue](https://github.com/aplpy/aplpy/issues/423)).
Make sure to still run `pip install -e .` after the conda installations in order to install `sneparse` itself.

### Catalog data
Sneparse uses the [Open Astronomy Catalog](https://github.com/astrocatalogs) (OAC) and [Transient Name Server](https://www.wis-tns.org/)
(TNS) as catalogs for known SNe (and tidal disruption events). In order to cross-match blobs detected in VLASS radio
data with these catalogs, you will need to download the relevant data.

For OAC data, simply clone the `sne-*` (and/or `tde-*`) repositories from [the OAC GitHub](https://github.com/astrocatalogs) and
place them under `resources/oac-data`. The `resources` folder should be placed at the project root; it will be used
for catalog data, intermediate results, and results of the imaging pipeline.

For TNS data, use `scripts/qTNSm.sh` to download catalogs from TNS. For example, `scripts/qTNSm.sh -t u 2016`
will download all unclassified sources from 2016 into `resources/tns-data`. `scripts/qTNSm.sh` is a modified
version of the script described [here](https://www.wis-tns.org/astronotes/astronote/2021-4).

### Environment variables
This project uses a few environment variable to configure access to VLASS data and catalog databases. The
following environment variables should be set:
* `DRIVER_NAME`: the driver to use to connect to catalog databases (e.g. `postgresql+psycopg2`)
* `TRANSIENTS_HOST`: the hostname of the server holding catalog databases. This should be the CIERA
  transients host, or a server with equivalent databases.
* `TRANSIENTS_PORT`: the port to connect to on the transients server.
* `TRANSIENTS_USERNAME` and `TRANSIENTS_PASSWORD`: username and password for access to the transients server.
* `QUEST_PROJECT_DIR` (optional): an `scp` URL to a remote mirror of the project, used to quickly update
  send changes with `make put` (using `rsync`). Quest is Northwestern's HPC cluster and stores the VLASS
  quicklook data used in this project.



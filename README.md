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
* `VLASS_QUICKLOOK`: path to VLASS quicklook folder.
* `QUEST_PROJECT_DIR` (optional): an `scp` URL to a remote mirror of the project, used to quickly update
  send changes with `make put` (using `rsync`). Quest is Northwestern's HPC cluster and stores the VLASS
  quicklook data used in this project.

## Scripts
Files under `scripts` can be run directly once the project has been setup. 

* ```build_catalog_csv.py```: parses OAC and TNS sources into a csv catalog (`resources/sne.csv`).
* ```build_catalog_db.py```: parses OAC and TNS sources into the transients database (specified by the
  environment variables listed above). Two tables will be created: a "master" table (`oac_tns_all_sne`),
  which includes all parsed sources, and a "cleaned" table (`oac_tns_cleaned_sne`), which reduces duplicates
  across the catalogs.
* ```check_files.py```: runs a simple check to verify that most files on Quest are available in the `file_definiton`
  table in the transients' VLASS database.
* ```check_paths.py```: runs a simple check to verify that most paths reported in the `file_definiton` are
  available on Quest.
* ```compare_epochs.py```: makes images to compare good sources across epochs, populating `resources/images/epoch_comparisons`
  with the resulting images. Assumes cross matching and categorization have already occurred.
* ```compare_unfiltered_epochs.py```: prints sources that appear in one or more epochs but did not appear in one or more
  other epochs. For example, `scripts/compare_unfiltered_epochs.py --initial 1 2 --final 3` prints sources appearing in
  epoch 3 which did not appear in epochs 1 or 2. Assumes cross matching has already occurred.
* ```cross_match.py```: cross matches known sources (placed into a database by `build_catalog_db.py`) against VLASS blobs
  in a given epoch (requires `EPOCH` environment variable to be set to `1`, `2`, or `3`). Writes result to
  `resources/epoch{EPOCH}_cross_matches.csv`.
* ```group_driver.sh```: auxiliary script to run `plot_groups.py`.
* ```image_driver.sh```: auxiliary script to run `make_images.py`.
* ```make_images.py```: make images for cross matches sources for a given epoch (requires `EPOCH` environment variable
  to be set to `1`, `2`, or `3`). Writes resulting images to `epoch{EPOCH}_cross_matches`.
* ```piechart.py```: simple script to visualize names of parsed sources. Requires `build_catalog_csv.py` to be run first.
* ```plot_groups.py```: makes images showing nearby sources identified as a group.
* ```prepare_categories.py```: makes folder structure to prepare for image categorization.
* ```qTNSm.sh```: downloads images from TNS.
* ```query_pairs.py```: finds groups in a csv catalog (from `build_catalog_csv.py`).
* ```sort_images.py```: runs a GUI for image categorization.
* ```visualize_categories.py```: visualizes classifications for different sources.

Many of these scripts are not essential to the core pipeline. To run the pipeline, simply use the targets in the `Makefile`:

```
# Run the main pipeline for SNe
make pipeline

# Run the main pipeline for TDEs
make tde
```

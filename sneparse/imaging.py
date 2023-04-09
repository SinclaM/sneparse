"""
Adapted from 
https://outerspace.stsci.edu/display/PANSTARRS/PS1+Image+Cutout+Service#PS1ImageCutoutService-DownloadaFITSFile
"""
 
from io import StringIO
from os import system

import numpy as np
from numpy.typing import NDArray
import matplotlib.pyplot as plt
import matplotlib.lines as lines
from matplotlib.colors import LogNorm
from mpl_toolkits.axes_grid1 import make_axes_locatable
from astropy.visualization.wcsaxes.core import WCSAxesSubplot
from astropy.io import fits
from astropy.utils.data import download_file
from astropy.table import Table
from astropy.wcs import WCS
import requests
from aplpy import FITSFigure

ps1filename = "https://ps1images.stsci.edu/cgi-bin/ps1filenames.py"
fitscut = "https://ps1images.stsci.edu/cgi-bin/fitscut.cgi"
 
def locate_images(ra: float,
                  dec: float,
                  size: int = 240,
                  filters="grizy",
                  format_="fits",
                  imagetypes="stack") -> Table:
    """
    Query ps1filenames.py service for multiple positions to get a list of images
    This adds a url column to the table to retrieve the cutout.
     
    ra, dec:  positions in degrees
    size:  image size in pixels (0.25 arcsec/pixel)
    filters: string with filters to include
    format:  data format (options are "fits", "jpg", or "png")
    imagetypes:  list of any of the acceptable image types.  Default is stack;
        other common choices include warp (single-epoch images), stack.wt (weight image),
        stack.mask, stack.exp (exposure time), stack.num (number of exposures),
        warp.wt, and warp.mask.  This parameter can be a list of strings or a
        comma-separated string.
 
    Returns an astropy table with the results
    """
    if dec < -30.0:
        print( "\tThe PanSTARRS-1 survey has a nominal -30° declination limit.")
        print(f"\tA request for dec={dec} will likely fail.")

    if format_ not in ("jpg","png","fits"):
        raise ValueError("format must be one of jpg, png, fits")

    # if imagetypes is a list, convert to a comma-separated string
    if not isinstance(imagetypes,str):
        imagetypes = ",".join(imagetypes)

    # put the positions in an in-memory file object
    cbuf = StringIO()
    cbuf.write(f"{ra} {dec}")
    cbuf.seek(0)

    # use requests.post to pass in positions as a file
    r = requests.post(ps1filename,
                      data=dict(filters=filters, type=imagetypes),
                      files=dict(file=cbuf))
    r.raise_for_status()

    # Check that files have been found for the given position.
    # We check by asserting there are at least 2 lines in the response text,
    # since astropy will fail to parse it into a table if only the column names
    # are present.
    try:
        r.text.index("\n")
    except ValueError as e:
        raise Exception(f"position ra={ra}, dec={dec} cannot be found in the PanSTARRS-1 survey") from e

    tab: Table = Table.read(r.text, format="ascii")

    urlbase = f"{fitscut}?size={size}&format={format_}"
    tab["url"] = [f"{urlbase}&ra={ra}&dec={dec}&red={filename}"
                    for (filename, ra, dec) in zip(tab["filename"], tab["ra"], tab["dec"])]
    return tab

def plot_image_plt(ra: float,
                   dec: float,
                   size: int = 240,
                   filters: str = "grizy",
                   cmap: str = "gray") -> plt.Figure:
    image_file: str = download_file(locate_images(ra, dec, size, filters)["url"][0],
                                    show_progress=False)
    image_data: NDArray
    image_data, header = fits.getdata(image_file, header=True)
    image_data -= image_data[np.isfinite(image_data)].min()

    wcs = WCS(header)

    fig: plt.Figure
    ax : WCSAxesSubplot

    # fig, ax = plt.subplots(subplot_kw={"projection": wcs})
    fig, ax = plt.subplots()

    crosshair = [
        lines.Line2D([0.43 * size, 0.47 * size], [size / 2, size / 2], lw=1.5, color='red', axes=ax),
        lines.Line2D([0.53 * size, 0.57 * size], [size / 2, size / 2], lw=1.5, color='red', axes=ax),
        lines.Line2D([size / 2, size / 2], [0.43 * size, 0.47 * size], lw=1.5, color='red', axes=ax),
        lines.Line2D([size / 2, size / 2], [0.53 * size, 0.57 * size], lw=1.5, color='red', axes=ax),
    ]

    for line in crosshair:
        ax.add_line(line)

    im = ax.imshow(image_data)

    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(im, cax=cax)
    return fig

def plot_image_apl(ra: float,
               dec: float,
               size: int = 240,
               filters: str = "grizy",
               cmap: str = "gray") -> None:
    image_file: str = download_file(locate_images(ra, dec, size, filters)["url"][0],
                                    show_progress=False)
    FILE_NAME = "tmp_plot.png"

    gc = FITSFigure(image_file)
    gc.show_grayscale()

    gc.tick_labels.set_font(size='small')

    gc.save(FILE_NAME)

    system(f"qlmanage -p {FILE_NAME}")
    system(f"rm {FILE_NAME}")

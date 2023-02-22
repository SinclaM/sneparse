"""
Adapted from 
https://outerspace.stsci.edu/display/PANSTARRS/PS1+Image+Cutout+Service#PS1ImageCutoutService-DownloadaFITSFile
"""
 
from io import StringIO

import numpy as np
from numpy.typing import NDArray
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from astropy.io import fits
from astropy.utils.data import download_file
from astropy.table import Table
import requests

ps1filename = "https://ps1images.stsci.edu/cgi-bin/ps1filenames.py"
fitscut = "https://ps1images.stsci.edu/cgi-bin/fitscut.cgi"

PANSTARSS_URL_FORMAT = """https://ps1images.stsci.edu/cgi-bin/fitscut.cgi?ra={ra}&dec={dec}&size={size}\
&format=fits&red=/rings.v3.skycell/1784/059/rings.v3.skycell.1784.059.stk.{filter_}.unconv.fits"""
 
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

    tab: Table = Table.read(r.text, format="ascii")
    urlbase = f"{fitscut}?size={size}&format={format_}"
    tab["url"] = [f"{urlbase}&ra={ra}&dec={dec}&red={filename}"
                    for (filename, ra, dec) in zip(tab["filename"], tab["ra"], tab["dec"])]
    return tab

def plot_image(ra: float,
               dec: float,
               size: int = 240,
               filters: str = "grizy",
               cmap: str = "gray") -> None:
    image_file: str = download_file(locate_images(ra, dec, size, filters)["url"][0],
                                    show_progress=False)

    image_data: NDArray = fits.getdata(image_file)
    image_data -= image_data[np.isfinite(image_data)].min()

    plt.imshow(image_data, cmap=cmap, norm=LogNorm())
    plt.colorbar()
    plt.show()

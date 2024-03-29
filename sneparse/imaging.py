"""
Adapted from 
https://outerspace.stsci.edu/display/PANSTARRS/PS1+Image+Cutout+Service#PS1ImageCutoutService-DownloadaFITSFile
"""
from typing import Tuple, Any, Optional
from io import StringIO
from datetime import datetime
from csv import DictReader

import numpy as np
from numpy.typing import NDArray
import matplotlib.pyplot as plt
import matplotlib.lines as lines
import matplotlib.figure
from matplotlib.colors import LogNorm
from mpl_toolkits.axes_grid1 import make_axes_locatable
from astropy.visualization.wcsaxes.core import WCSAxesSubplot
from astropy.io import fits
from astropy.utils.data import download_file
from astropy.table import Table
from astropy.wcs import WCS
from astropy.time import Time
import requests
from aplpy import FITSFigure

from sneparse.record import SneRecord
from sneparse.coordinates import DecimalDegrees, DegreesMinutesSeconds
from sneparse.util import unwrap

ps1filename = "https://ps1images.stsci.edu/cgi-bin/ps1filenames.py"
fitscut = "https://ps1images.stsci.edu/cgi-bin/fitscut.cgi"

def locate_image_ps1(
    ra: float, dec: float, size: int = 240, filters="grizy", format_="fits", imagetypes="stack"
) -> str:
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

    # Check that files have been found for the given position.
    # We check by asserting there are at least 2 lines in the response text,
    # since astropy will fail to parse it into a table if only the column names
    # are present.
    r.text.index("\n")

    tab: Table = Table.read(r.text, format="ascii")

    urlbase = f"{fitscut}?size={size}&format={format_}"
    tab["url"] = [f"{urlbase}&ra={ra}&dec={dec}&red={filename}"
                    for (filename, ra, dec) in zip(tab["filename"], tab["ra"], tab["dec"])]
    return tab["url"][0]

def locate_image_skymapper(ra: float, dec: float, radius: float, filters: str = "r") -> str:
    size = min(2 * radius, 0.17)
    urlbase = "https://api.skymapper.nci.org.au/public/siap/dr2/query?"
    r = requests.get(f"{urlbase}POS={ra},{dec}&SIZE={size}&FORMAT=image/fits&BAND={','.join(filters)}&INTERSECT=COVERS&RESPONSEFORMAT=CSV")
    r.raise_for_status()
    reader = DictReader(StringIO(r.text))

    return next(reader)["get_image"]


class NaNImageError(Exception): ...

def ensure_image(data: NDArray) -> None:
    if np.isnan(np.nanmin(data)):
        raise NaNImageError(f"image data is all NaN")

def plot_image_astropy(ra: float,
                       dec: float,
                       size: int = 240,
                       filters: str = "grizy",
                       cmap: str = "gray",
                       image_file: Optional[str] = None) -> None:
    radius = DecimalDegrees.from_dms(DegreesMinutesSeconds(1, 0, 0, 30)).degrees

    if image_file is None:
        # Assume optical
        try:
            image_file = download_file(locate_image_ps1(ra, dec, size, filters), show_progress=False)
        except:
            image_file = download_file(locate_image_skymapper(ra, dec, radius, filters), show_progress=False)

    image_data: NDArray
    image_data, header = fits.getdata(image_file, header=True)

    ensure_image(image_data)

    # Shift data so that min is 0. Important for normalizations
    # that expect nonnegative values.
    image_data -= np.nanmin(image_data)

    # The transfrom that astropy will use to convert pixel coordinates
    # to ra and dec.
    wcs = WCS(header)

    fig: plt.Figure
    ax : WCSAxesSubplot

    fig, ax = plt.subplots(subplot_kw={"projection": wcs})


    # Add a red crosshair to the center of the image
    crosshair = [
        lines.Line2D([0.43 * size, 0.47 * size], [size / 2, size / 2], lw=1.5, color="red", axes=ax),
        lines.Line2D([0.53 * size, 0.57 * size], [size / 2, size / 2], lw=1.5, color="red", axes=ax),
        lines.Line2D([size / 2, size / 2], [0.43 * size, 0.47 * size], lw=1.5, color="red", axes=ax),
        lines.Line2D([size / 2, size / 2], [0.53 * size, 0.57 * size], lw=1.5, color="red", axes=ax),
    ]

    for line in crosshair:
        ax.add_line(line)

    im = ax.imshow(image_data, norm=LogNorm(), cmap=cmap) # type: ignore

    # Set the x and y axis labels to "ra" and "dec"
    ax.coords[0].set_axislabel("RA (J2000)")
    ax.coords[1].set_axislabel("Dec (J2000)")

    # Append a colorbar to the main plot
    divider = make_axes_locatable(ax)
    cax: WCSAxesSubplot = divider.append_axes("right", size="5%", pad=0.10)

    # Don't show any ticks on the x axis of the colorbar
    cax.coords[0].set_ticks_visible(False)
    cax.coords[0].set_ticklabel_visible(False)

    # Show ticks for the y axis of the colorbar on the right hand side,
    # and don't add a "y" label to the colorbar.
    cax.coords[1].set_ticks_position("r")
    cax.coords[1].set_ticklabel_position("r")
    cax.coords[1].set_auto_axislabel(False)

    fig.colorbar(im, cax=cax)

    fig.set_size_inches(8, 8)


def plot_image_apl(
    record: SneRecord,
    figure: Optional[matplotlib.figure.Figure] = None,
    subplot: Tuple[int, int, int] | list[float] = (1, 1, 1),
    size: int = 240,
    filters: str = "grizy",
    cmap: str = "gray",
    image_file: Optional[str] = None,
    is_radio: bool = False,
    is_non_detection = False
) -> FITSFigure:
    name = record.name
    ra = unwrap(record.right_ascension).degrees
    dec = unwrap(record.declination).degrees

    radius = DecimalDegrees.from_dms(DegreesMinutesSeconds(1, 0, 0, 30)).degrees

    is_ps1 = False
    if image_file is None:
        # Assume optical
        try:
            image_file = download_file(locate_image_ps1(ra, dec, size, filters), show_progress=False)
            is_ps1 = True
        except:
            image_file = download_file(locate_image_skymapper(ra, dec, radius, filters), show_progress=False)

    # Need wcs transfrom to translate pixel coords to ra and dec when
    # drawing crosshair.
    image_data, header = fits.getdata(image_file, header=True)
    ensure_image(image_data)

    # Create the figure from the fits data
    north = not is_radio
    fig = FITSFigure(image_file, figure=figure, subplot=subplot, north=north)
    frequency = 0.0
    if is_radio:
        frequency = fig._wcs.wcs.crval[2] * 1e-9 # GHz
        fig._wcs = fig._wcs.celestial

    fig.recenter(ra, dec, radius=radius)

    fig.tick_labels.set_font(size="small")

    # Draw the crosshair
    x, y = fig.world2pixel(ra, dec)

    gap = 1.5 if is_radio else (6 if is_ps1 else 3)
    segment = 2 * gap

    crosshair = [
        lines.Line2D([x + gap, x + gap + segment], [y, y], lw=1.5, color="red", axes=fig.ax),
        lines.Line2D([x, x], [y + gap, y + gap + segment], lw=1.5, color="red", axes=fig.ax),
    ]

    for line in crosshair:
        fig.ax.add_line(line)

    fig.add_label(0.53, 0.53, name, relative=True, color="red", horizontalalignment="left")

    if is_radio:
        observation_date = datetime.fromisoformat(header["DATE"])
        rounded = round(frequency, 2) if (floor := int(frequency)) != frequency else floor
        info = f"VLA - {rounded} GHz"
    else:
        t = Time(header["MJD-OBS"], format="mjd")
        t.format = "datetime"
        observation_date = t.value
        info = "PS1 - r-band" if is_ps1 else "SkyMapper - r-band"

    fig.add_label(
        0.05, 0.85, f"{observation_date.date().isoformat()} - {info}",
        relative=True, color="black", size="x-large", horizontalalignment="left"
    )
    fig.add_label(
        0.05, 0.9, "RADIO" if is_radio else "OPTICAL",
        relative=True, color="blue", size="xx-large", horizontalalignment="left"
    )

    if is_radio and record.discover_date is not None and observation_date < record.discover_date:
        fig.add_label(
            0.05, 0.95, "PRE-EXPLOSION", relative=True, color="red", size="xx-large", horizontalalignment="left"
        )

    if is_non_detection:
        fig.add_label(
            0.05, 0.05, "NON-DETECTION", relative=True, color="red", size="xx-large", horizontalalignment="left"
        )

    # The default `stretch="log"` is terrible for the VLASS radio data.
    # So we have to adjust the parameters to make the normalization look
    # more like ds9's output, which is more sensible.
    #
    # See p.31 of https://aplpy.readthedocs.io/_/downloads/en/stable/pdf/ for
    # the reasoning behind this specific formula.
    a = 100
    vmin = np.nanmin(image_data)
    vmax = np.nanmax(image_data)
    vmid = ((a + 1) * vmin - vmax) / a

    fig.show_colorscale(cmap=cmap, stretch="log", vmid=vmid, vmin=vmin, vmax=vmax)

    fig.add_colorbar()

    return fig

def aplpy_crosshair(ra: float, dec: float, wcs: WCS, is_radio: bool = False) -> list[NDArray[Any]]:
    # The radio image has less pixels than optical, so we manually tune the
    # desired pixel count. Not ideal but it works.
    gap = 1.5 if is_radio else 6
    segment = 2 * gap

    # The gap_length is how far from the center of the crosshair until each
    # segment starts.
    gap_length_ra = wcs.all_pix2world(gap, 0, 0)[0] - wcs.all_pix2world(0, 0, 0)[0]
    gap_length_dec = wcs.all_pix2world(0, gap, 0)[1] - wcs.all_pix2world(0, 0, 0)[1]

    # The segment length is the length of each of the 4 segments of the crosshair.
    segment_length_ra = wcs.all_pix2world(segment, 0, 0)[0] - wcs.all_pix2world(0, 0, 0)[0]
    segment_length_dec = wcs.all_pix2world(0, segment, 0)[1] - wcs.all_pix2world(0, 0, 0)[1]

    # Right
    rx1, rx2 = (ra + gap_length_ra, ra + gap_length_ra + segment_length_ra)
    ry1, ry2 = (dec, dec)

    # Up
    ux1, ux2 = (ra, ra)
    uy1, uy2 = (dec + gap_length_dec, dec + gap_length_dec + segment_length_dec)

    crosshair = [
        np.array([[rx1, rx2], [ry1, ry2]]),
        np.array([[ux1, ux2], [uy1, uy2]])
    ]

    return crosshair

def plot_group(group: list[Tuple[float, float]],
               size: int = 240,
               filters: str = "grizy",
               cmap: str = "gray") -> FITSFigure:
    ra, dec = group[0]
    radius = DecimalDegrees.from_dms(DegreesMinutesSeconds(1, 0, 0, 30)).degrees
    try:
        image_file = download_file(locate_image_ps1(ra, dec, size, filters), show_progress=False)
    except:
        image_file = download_file(locate_image_skymapper(ra, dec, radius, filters), show_progress=False)

    # Need wcs transfrom to translate pixel coords to ra and dec when
    # drawing crosshair.
    image_data, header = fits.getdata(image_file, header=True)
    ensure_image(image_data)
    wcs = WCS(header)

    # Create the figure from the fits data
    fig = FITSFigure(image_file)
    fig.show_colorscale(cmap=cmap, stretch="log", vmid=np.nanmin(image_data))

    fig.tick_labels.set_font(size="small")

    # Colors for each crosshair. Start with red ("r"), then green, blue, and
    # cyan. The 5th crosshair and beyond will fall back to cyan.
    colors = "rgbc"
    for i, (ra, dec) in enumerate(group):
        crosshair = aplpy_crosshair(ra, dec, wcs)
        fig.show_lines(crosshair, color=colors[min(i, len(colors) - 1)])

    fig.add_colorbar()

    fig._figure.set_size_inches(8, 8) # type: ignore
    return fig

from aplpy import FITSFigure
from os import system

FILE_NAME = "tmp_plot.png"

gc = FITSFigure('tutorial/fits/2MASS_k.fits')
gc.show_grayscale()

gc.tick_labels.set_font(size='small')

gc.save(FILE_NAME)

system(f"qlmanage -p {FILE_NAME}")
system(f"rm {FILE_NAME}")

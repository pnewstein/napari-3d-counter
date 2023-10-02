file = "/media/petern/f2381f8a-ab9a-4a5a-90b0-8699637b9bb3/archive/Doe/rotation/hb-ox-cas-hbo-run/ctrl/2/a3.tif"

import napari
import tifffile

viewer = napari.viewer.Viewer()
img = tifffile.imread(file)
viewer.add_image(img, channel_axis=1)

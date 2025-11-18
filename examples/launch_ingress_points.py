"""
Launch Ingress Points
=====================

Launch the Ingress Points widget on sample data
"""

import napari
from skimage.morphology import ball
from skimage.filters import gaussian
from skimage.feature import blob_dog
import numpy as np

from napari_3d_counter import CellTypeConfig, Count3D, IngressPoints

viewer = napari.Viewer()


# Make some nice sample data which consists of blured balls
# add to two image layers in the viewer
def place_ball(
    image: np.ndarray, position: tuple[int, int, int], radius=5
) -> np.ndarray:
    ball_z, ball_x, ball_y = np.where(ball(radius))
    image[ball_z + position[0], ball_x + position[1], ball_y + position[2]] = 1
    return image


green_image = np.zeros(shape=(30, 200, 200))
green_image = place_ball(green_image, (12, 100, 30))
green_image = place_ball(green_image, (7, 150, 100))
green_image = place_ball(green_image, (10, 20, 20))
green_image = gaussian(green_image, sigma=1)
viewer.add_image(green_image, colormap="green", name="Green", blending="additive")
purple_image = np.zeros(shape=(30, 200, 200))
purple_image = place_ball(purple_image, (8, 60, 35))
purple_image = place_ball(purple_image, (13, 150, 150))
purple_image = gaussian(purple_image, sigma=1)
viewer.add_image(purple_image, colormap="magenta", name="Purple", blending="additive")

# Setup the configuration for Count3D
cell_type_config = [
    CellTypeConfig(
        name="Green blobs",
        color="g",
    ),
    # CellTypeConfig has reasonable defaults, so no need to specify everything
    CellTypeConfig(name="Purple blobs", color="m"),
]

# Programmatically add the widgets to the viewer
viewer.window.add_dock_widget(
    Count3D(viewer, cell_type_config=cell_type_config)
)
viewer.window.add_dock_widget(IngressPoints(viewer))

# Do some analysis to find the cells automaticaly
points = blob_dog(green_image, 2, 3)
# Add those points to the viewer
viewer.add_points(points[:, :3], out_of_slice_display=True)

# Now Ingress Points button is ready to click

if __name__ == "__main__":
    napari.run()

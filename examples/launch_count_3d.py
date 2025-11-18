"""
Launch Count 3D
===============

Launch the count 3D plugin on some sample data
"""

import napari
from skimage.morphology import ball
from skimage.filters import gaussian
import numpy as np

from napari_3d_counter import CellTypeConfig, Count3D

viewer = napari.Viewer()


# Make some nice sample data which consists of blured balls
# add to two image layers in the viewer
def place_ball(
    image: np.ndarray, position: tuple[int, int, int], radius=5
) -> np.ndarray:
    ball_z, ball_x, ball_y = np.where(ball(radius))
    image[ball_z + position[0], ball_x + position[1], ball_y + position[2]] = 1
    return image


image = np.zeros(shape=(30, 200, 200))
image = place_ball(image, (12, 100, 30))
image = place_ball(image, (7, 150, 100))
image = place_ball(image, (10, 20, 20))
image = gaussian(image, sigma=1)
viewer.add_image(image, colormap="green", name="Green", blending="additive")
image = np.zeros(shape=(30, 200, 200))
image = place_ball(image, (8, 60, 35))
image = place_ball(image, (13, 150, 150))
image = gaussian(image, sigma=1)
viewer.add_image(image, colormap="magenta", name="Purple", blending="additive")


# Setup the configuration for Count3D
cell_type_config = [
    CellTypeConfig(
        # Name can also be changed in the GUI by changing the napari Layer name
        name="Green blobs",
        # Color can also be changed with the border color button
        color="g",
        # Keybind to switch to this type can only be set programmatically
        keybind="q",
        # Outline size controls the size of the marker. This can also be changed with the GUI point size slider
        outline_size=10,
        # out_of_slice_point_size can also be changed with the GUI point size of the `out of slice` layer
        out_of_slice_point_size=2,
        # face_color can also be changed with the GUI face color button
        face_color="#00000000",
        # face_color can also be changed with the GUI symbol drop down
        symbol="disc",
        # edge_width can only be set programmatically
        edge_width=0.05,
    ),
    # CellTypeConfig has reasonable defaults, so no need to specify everything
    CellTypeConfig(name="Purple blobs", color="m"),
]
# Programmatically add the widget to the viewer
viewer.window.add_dock_widget(
    Count3D(viewer, cell_type_config=cell_type_config)
)

# Now Count3D is ready to count!

if __name__ == "__main__":
    napari.run()

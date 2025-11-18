"""
Launch Split on Shapes
======================

Launch the Split on Shapes widget on sample data
"""

import napari
from skimage.morphology import ball
from skimage.filters import gaussian
import numpy as np

from napari_3d_counter import CellTypeConfig, Count3D, SplitOnShapes

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
viewer.add_image(
    green_image, colormap="green", name="Green", blending="additive"
)
purple_image = np.zeros(shape=(30, 200, 200))
purple_image = place_ball(purple_image, (8, 60, 35))
purple_image = place_ball(purple_image, (13, 150, 150))
purple_image = gaussian(purple_image, sigma=1)
viewer.add_image(
    purple_image, colormap="magenta", name="Purple", blending="additive"
)
# add the shapes. This would likley be done by hand in real usecases
shapes = viewer.add_shapes()
shapes.add_polygons(
    [
        [[14, 14, 11], [14, 123, 28], [14, 45, 107]],
        [[14, 170, 86], [14, 170, 185], [14, 112, 124]],
    ]
)
shapes.refresh()

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
c3d = Count3D(viewer, cell_type_config=cell_type_config)
viewer.window.add_dock_widget(c3d)
viewer.window.add_dock_widget(SplitOnShapes(viewer))

# add the points to the widget
c3d.pointer.add(np.array([17, 105, 35]))
c3d.pointer.add(np.array([12, 155, 105]))
c3d.pointer.add(np.array([15, 25, 25]))
c3d.change_state_to(c3d.cell_type_gui_and_data[-1])
c3d.pointer.add(np.array([13, 65, 40]))
c3d.pointer.add(np.array([18, 155, 155]))
# scroll to the layer with the shapes
viewer.dims.point = (13, 99, 99)
viewer.dims.point = (14, 99, 99)


# Now Split on shapes will be ready to click

if __name__ == "__main__":
    napari.run()

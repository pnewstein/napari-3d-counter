"""
Launches napari with some nice sample data for testing the gui
"""

import os
from pathlib import Path
from typing import Tuple
import sys

import napari
import numpy as np
from skimage.filters import gaussian
from skimage.morphology import ball

temp_path = Path("/tmp/napari-3d-counter")
temp_path.mkdir(exist_ok=True)
os.chdir(temp_path)


def place_ball(
    image: np.ndarray, position: Tuple[int, int, int], radius=5
) -> np.ndarray:
    ball_z, ball_x, ball_y = np.where(ball(radius))
    image[ball_z + position[0], ball_x + position[1], ball_y + position[2]] = 1
    return image


viewer = napari.viewer.Viewer()
image = np.zeros(shape=(30, 200, 200))
image = place_ball(image, (12, 100, 30))
image = place_ball(image, (7, 150, 100))
image = place_ball(image, (10, 20, 20))
image = gaussian(image, sigma=1)
viewer.add_image(image, colormap="green", name="Cell 1", blending="additive")
image = np.zeros(shape=(30, 200, 200))
image = place_ball(image, (8, 60, 35))
image = place_ball(image, (13, 150, 150))
image = gaussian(image, sigma=1)
viewer.add_image(image, colormap="magenta", name="Cell 2", blending="additive")

if len(sys.argv) == 2:
    from napari_3d_counter import Count3D, CellTypeConfig

    viewer.window.add_dock_widget(
        Count3D(viewer, [CellTypeConfig("Counter 1")])
    )

napari.run()
# start wiget
# add green cells
# add magenta cells
# add extra cell
# undo
# add extra cell
# remove it
# change color name
# save python
# Save cells
# load cells

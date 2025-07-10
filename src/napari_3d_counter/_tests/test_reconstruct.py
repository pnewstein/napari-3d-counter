"""
tests the reconstruct selected plugin
"""

from typing import List, Tuple

import numpy as np
from skimage.morphology import ball
import pytest

from napari_3d_counter import ReconstructSelected


def place_ball(
    image: np.ndarray, position: Tuple[int, int, int], number: int, radius=5
) -> np.ndarray:
    ball_z, ball_x, ball_y = np.where(ball(radius))
    image[ball_z + position[0], ball_x + position[1], ball_y + position[2]] = (
        number
    )
    return image


def make_sample_data(points: List[Tuple[int, int, int]]) -> np.ndarray:
    labels = np.zeros(shape=(30, 200, 200)).astype(int)
    for i, point in enumerate(points, start=1):
        labels = place_ball(labels, tuple(p - 5 for p in point), i)
    return labels


def test_reconstruct_selected(make_napari_viewer):
    viewer = make_napari_viewer()
    points = [(12, 100, 30), (7, 150, 100), (10, 20, 20)]
    labels = make_sample_data(points)
    viewer.add_labels(labels, name="lbls")
    rs = ReconstructSelected(viewer)
    viewer.window.add_dock_widget(rs)
    viewer.layers[-1].add(points)
    out = rs.run()
    assert out.data.sum() > 0


def test_reconstruct_selected_empty(make_napari_viewer):
    viewer = make_napari_viewer()
    points = [(12, 100, 30), (7, 150, 100), (10, 20, 20)]
    labels = make_sample_data(points)
    rs = ReconstructSelected(viewer)
    with pytest.raises(KeyError):
        out = rs.run()
    viewer.add_labels(labels, name="lbls")
    viewer.window.add_dock_widget(rs)
    viewer.layers[-2].add(points)
    out = rs.run()
    assert out.data.sum() > 0


def test_select_only_correct(make_napari_viewer):
    viewer = make_napari_viewer()
    points = [(12, 100, 30), (7, 150, 100), (10, 20, 20), (1, 2, 2)]
    labels = make_sample_data(points)
    viewer.add_labels(labels)
    rs = ReconstructSelected(viewer)
    viewer.layers[-1].add(points[:2] + [(29, 100, 100)])
    out = rs.run()
    assert out.data[tuple(np.array(points).T)].sum() == 510

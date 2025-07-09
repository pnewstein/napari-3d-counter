"""
tests the reconstruct selected plugin
"""

from typing import List, Tuple

import numpy as np
from skimage.morphology import ball

from napari_3d_counter import reconstruct_selected


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
    points = [(12, 100, 30), (7, 150, 100), (10, 20, 20)]
    labels = make_sample_data(points)
    viewer = make_napari_viewer()
    lbls = viewer.add_labels(labels, name="lbls")
    pts = viewer.add_points(points, name="pts")
    out = reconstruct_selected(lbls, pts, viewer)
    assert out.sum() > 0


def test_reconstruct_selected_empty(make_napari_viewer):
    points = []
    labels = make_sample_data(points)
    viewer = make_napari_viewer()
    lbls = viewer.add_labels(labels, name="lbls")
    pts = viewer.add_points(points, name="pts")
    out = reconstruct_selected(lbls, pts, viewer)
    assert out.sum() == 0


def test_skip_empty_points(make_napari_viewer):
    points = [(12, 100, 30), (7, 150, 100), (10, 20, 20)]
    labels = make_sample_data(points)
    viewer = make_napari_viewer()
    lbls = viewer.add_labels(labels, name="lbls")
    points = [(0, 0, 0), (1, 1, 1)]
    pts = viewer.add_points(points, name="pts")
    out = reconstruct_selected(lbls, pts, viewer)
    assert out.sum() == 0


if __name__ == "__main__":
    import napari

    test_skip_empty_points(napari.viewer.Viewer)

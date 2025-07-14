"""
tests the reconstruct selected plugin
"""

from typing import List, Tuple


from pytestqt import qtbot
import numpy as np
from skimage.morphology import ball, binary_dilation
import pytest

from napari_3d_counter import (
    ReconstructSelected,
    IngressPoints,
    get_n3d_counter,
)
import napari
from napari.layers import Image


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

    return rs.output_layer


def test_reconstruct_selected(make_napari_viewer, qtbot):
    viewer = make_napari_viewer()
    points = [(12, 100, 30), (7, 150, 100), (10, 20, 20)]
    labels = make_sample_data(points)
    viewer.add_labels(labels, name="lbls")
    rs = ReconstructSelected(viewer)
    viewer.window.add_dock_widget(rs)
    viewer.layers[-1].add(points)
    rs.run()
    # out = get_output_layer(rs)
    qtbot.waitUntil(lambda: rs.output_layer is not None)
    assert rs.output_layer.data.sum() > 0


def test_reconstruct_selected_empty(make_napari_viewer, qtbot):
    viewer = make_napari_viewer()
    points = [(12, 100, 30), (7, 150, 100), (10, 20, 20)]
    labels = make_sample_data(points)
    rs = ReconstructSelected(viewer)
    with pytest.raises(KeyError):
        rs.run()
    viewer.add_labels(labels, name="lbls")
    viewer.window.add_dock_widget(rs)
    viewer.layers[-2].add(points)
    rs.output_layer = None
    rs.run()
    qtbot.waitUntil(lambda: rs.output_layer is not None)
    assert rs.output_layer.data.sum() > 0
    scaled = viewer.add_labels(
        np.zeros((10, 10, 10)).astype(int), scale=(10, 0.1, 100), name="scaled"
    )
    click_world_coords = (10, 0.5, 10)
    rs.labels_box.setCurrentText("scaled")
    viewer.layers[rs.points_box.currentText()].add(click_world_coords)
    scaled.data[
        tuple(scaled.world_to_data(click_world_coords).astype(int))
    ] = 2
    scaled.data = binary_dilation(scaled.data)
    assert scaled.get_value(click_world_coords, world=True) != 0
    rs.output_layer = None
    rs.run()
    qtbot.waitUntil(lambda: rs.output_layer is not None)
    assert rs.output_layer.get_value(click_world_coords, world=True) != 0


def test_select_only_correct(make_napari_viewer, qtbot):
    viewer = make_napari_viewer()
    points = [(12, 100, 30), (7, 150, 100), (10, 20, 20), (1, 2, 2)]
    labels = make_sample_data(points)
    viewer.add_labels(labels)
    rs = ReconstructSelected(viewer)
    viewer.layers[-1].add(points[:2] + [(29, 100, 100)])
    rs.run()
    qtbot.waitUntil(lambda: rs.output_layer is not None)
    assert rs.output_layer.data[tuple(np.array(points).T)].sum() == 510


def test_ingress_points(make_napari_viewer):
    viewer = make_napari_viewer()
    ip = IngressPoints(viewer)
    points = viewer.add_points(scale=(2, 0.2, 5))
    click_world_coords = (10, 0.5, 10)
    points.current_size = 10
    points.add(points.world_to_data(click_world_coords))
    assert points.get_value(click_world_coords, world=True) is not None
    ip.run()
    cell_type_layer = viewer.layers[ip.cell_type_box.currentText()]
    from napari.layers import Points

    assert isinstance(cell_type_layer, Points)
    assert (
        cell_type_layer.get_value(click_world_coords, world=True) is not None
    )
    c3d = get_n3d_counter(viewer)
    c3d.undo()
    assert cell_type_layer.get_value(click_world_coords, world=True) is None

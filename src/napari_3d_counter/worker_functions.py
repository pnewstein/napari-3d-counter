"""
This module contains functions that are called as tread workers
"""

from typing import TYPE_CHECKING

from napari.qt.threading import thread_worker
from napari.layers import Points, Labels
import numpy as np


@thread_worker
def reconstruct_selected(point_layer: Points, labels_layer: Labels) -> dict:
    """
    Converts labels with hit by points into an image
    """
    name = point_layer.name
    coordinates = np.array(
        [
            np.round(
                labels_layer.world_to_data(point_layer.data_to_world(d))
            ).astype(int)
            for d in point_layer.data
        ]
    )
    if len(coordinates) == 0:
        print("No points to reconstruct")
        return {}
    labels_data = labels_layer.data
    max_coords = coordinates.max(axis=0)
    if np.any(max_coords > labels_data.shape):
        illegal_coords_mask = (coordinates > labels_data.shape).any(axis=1)
        bad_points = coordinates[illegal_coords_mask]
        print(f"skipping points out of bounds at {bad_points}")
        coordinates = coordinates[~illegal_coords_mask]
    labels = labels_layer.data[tuple(coordinates.T)]
    if TYPE_CHECKING:
        assert isinstance(labels, np.ndarray)
    if 0 in labels:
        label_mask = labels == 0
        bad_points = coordinates[label_mask]
        labels = labels[~label_mask]
        print(f"skipping points outside a label at {bad_points}")
    if TYPE_CHECKING:
        assert isinstance(labels_data, np.ndarray)
        assert isinstance(labels, np.ndarray)
    reconstruction_data = np.isin(labels_data, labels).astype(np.uint8) * 255
    return dict(
        data=reconstruction_data,
        scale=labels_layer.scale,
        translate=labels_layer.translate,
        affine=labels_layer.affine,
        name=f"{name} reconstruction",
        blending="additive",
        rendering="iso",
    )

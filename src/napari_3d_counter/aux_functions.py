"""
This module contains functions that can be used indepentetly of N3dCounter.
These functions are also used in the aux widgets

"""

from typing import TYPE_CHECKING

from napari.layers import Points, Labels, Image, Shapes
from napari import Viewer
import numpy as np
import pandas as pd


def _reconstruct_selected(point_layer: Points, labels_layer: Labels) -> dict:
    """
    this private function contains the core logic of reconstruting selected.
    It returns the empty dict as an error state. The ouput is the kwargs for add_image
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


def reconstruct_selected(
    viewer: Viewer, point_layer: Points, labels_layer: Labels
) -> Image:
    """
    Converts labels with hit by points into an image
    """
    out = viewer.add_image(**_reconstruct_selected(point_layer, labels_layer))
    assert isinstance(out, Image)
    return out


def split_on_shapes(
    point_layers: list[Points], shapes_layer: Shapes
) -> pd.DataFrame | None:
    """
    Splits up points based on which shape they are contained within
    ignore z
    """
    if not shapes_layer.data:
        print("No shapes in shapes data")
        return
    slice = shapes_layer.data[0][0, :-2]
    out: list[np.ndarray] = []
    for shape in shapes_layer.data:
        out_layer = shape
        out_layer[:, :-2] = slice
        out.append(out_layer)
    shapes_layer.data = out
    shapes_layer.refresh()
    out_series: list[pd.Series] = []
    for point_layer in point_layers:
        for point in point_layer.data:
            world_point = point_layer.data_to_world(point)
            shape_coord = tuple(list(slice) + list(world_point[-2:]))
            shape_idx = shapes_layer.get_value(shape_coord, world=True)[0]
            if shape_idx is None:
                print(f"Point at {point} missing a shape")
                return
            out_series.append(
                pd.Series(
                    {k: point[i] for i, k in enumerate(["z", "y", "x"])}
                    | {"name": point_layer.name, "shape_idx": shape_idx},
                    name=f"{point_layer.name}_{shape_idx:03}",
                )
            )
    if len(out_series) == 0:
        print("No points found")
        return
    return pd.DataFrame(out_series)

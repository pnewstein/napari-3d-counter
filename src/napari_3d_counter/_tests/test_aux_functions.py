"""
Tests aux funtions without mounting widgets
"""

import sys
from pathlib import Path

import numpy as np
import numpy as no

from napari_3d_counter import aux_functions

sys.path.append(str(Path(__file__).parent))
from test_aux import make_sample_data


shapes_data = [
    np.array(
        [
            [6.0, 3.444737, 21.686844],
            [6.0, -8.405262, 3.3921075],
            [6.0, -10.692104, -10.952629],
            [6.0, -8.197368, -12.407892],
            [6.0, -2.1684206, -13.863155],
            [6.0, 1.5736846, -13.863155],
            [6.0, 11.344737, -11.576313],
            [6.0, 14.878947, -9.289471],
            [6.0, 18.828947, -5.339471],
            [6.0, 22.363157, -0.765787],
            [6.0, 26.105263, 6.302634],
            [6.0, 27.768421, 21.06316],
            [6.0, 26.313158, 24.18158],
            [6.0, 21.947369, 28.339476],
            [6.0, 19.036842, 28.96316],
            [6.0, 9.681579, 27.923685],
        ],
    ),
    np.array(
        [
            [8.0, 113.628944, 85.926315],
            [8.0, 93.25526, 61.810528],
            [8.0, 87.01842, 52.455265],
            [8.0, 84.31579, 42.26842],
            [8.0, 84.31579, 29.171053],
            [8.0, 89.72105, 19.81579],
            [8.0, 95.12631, 16.905266],
            [8.0, 108.015785, 16.905266],
            [8.0, 112.38158, 19.192106],
            [8.0, 120.697365, 26.052633],
            [8.0, 132.54736, 38.31842],
            [8.0, 137.32895, 46.426315],
            [8.0, 151.25789, 65.96842],
            [8.0, 152.29736, 69.50263],
            [8.0, 152.92105, 78.65],
            [8.0, 156.66315, 87.58947],
            [8.0, 157.49474, 93.618416],
            [8.0, 157.28683, 106.92368],
            [8.0, 156.03947, 109.00263],
            [8.0, 153.75262, 109.210526],
            [8.0, 145.22894, 106.71579],
            [8.0, 135.25, 100.686844],
            [8.0, 124.02368, 91.539474],
        ],
    ),
]


def test_select_only_correct(make_napari_viewer):
    viewer = make_napari_viewer()
    points = [(12, 100, 30), (7, 150, 100), (10, 20, 20), (1, 2, 2)]
    labels = make_sample_data(points)
    label_layer = viewer.add_labels(labels)
    point_layer = viewer.add_points(points[:2] + [(29, 100, 100)])
    out = aux_functions.reconstruct_selected(viewer, point_layer, label_layer)
    assert out.data[tuple(np.array(points).T)].sum() == 510


def test_split_on_shapes(make_napari_viewer):
    viewer = make_napari_viewer()
    points = [(12, 100, 30), (7, 150, 100), (10, 20, 20), (1, 2, 2)]
    p_layer = viewer.add_points(points)
    s_layer = viewer.add_shapes(ndim=3)
    s_layer.add_polygons(shapes_data)
    df = aux_functions.split_on_shapes([p_layer], s_layer)
    assert df is not None
    s_layer = viewer.add_shapes(ndim=2)
    s_layer.add_polygons([d[:, -2:] for d in shapes_data])
    df = aux_functions.split_on_shapes([p_layer], s_layer)
    assert df is not None
    p_layer = viewer.add_points([[0, 0, 100]])
    df = aux_functions.split_on_shapes([p_layer], s_layer)
    assert df is None

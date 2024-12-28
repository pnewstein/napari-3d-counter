"""
Tests the code that generates python
"""

from napari_3d_counter import (
    Count3D,
    CellTypeConfig, # type: ignore
)

import numpy as np


def test_code_gen_name(make_napari_viewer):
    viewer = make_napari_viewer()
    my_widget = Count3D(viewer)
    cell_type = my_widget.cell_type_gui_and_data[0]
    cell_type.layer.name = "test name"
    python_string = repr(cell_type.get_calculated_config(1))
    config = eval(python_string)
    assert config.name == "test name"


def test_code_gen_color(make_napari_viewer):
    viewer = make_napari_viewer()
    my_widget = Count3D(viewer)
    cell_type = my_widget.cell_type_gui_and_data[0]
    cell_type.layer.current_border_color = np.array([1, 1, 1, 1])
    python_string = repr(cell_type.get_calculated_config(1))
    config = eval(python_string)
    assert config.color == "#ffffffff"


def test_config_self(make_napari_viewer):
    viewer = make_napari_viewer()
    my_widget = Count3D(viewer)
    cell_type = my_widget.cell_type_gui_and_data[0]
    cell_type.layer.name = "loop"
    python_string = repr(cell_type.get_calculated_config(1))
    config = eval(python_string)
    # attach to second viewer
    viewer = make_napari_viewer()
    my_widget = Count3D(viewer, cell_type_config=[config])
    cell_type = my_widget.cell_type_gui_and_data[0]
    assert cell_type.layer.name == "loop"


def test_print_config(make_napari_viewer):
    viewer = make_napari_viewer()
    my_widget = Count3D(viewer)
    print(my_widget.config_in_python())


def test_out_of_slice_size(make_napari_viewer):
    viewer = make_napari_viewer()
    my_widget = Count3D(viewer)
    cell_type = my_widget.cell_type_gui_and_data[0]
    ctc = cell_type.get_calculated_config(100)
    assert ctc.out_of_slice_point_size == 100



def test_size_config(make_napari_viewer):
    viewer = make_napari_viewer()
    my_widget = Count3D(viewer)
    cell_type = my_widget.cell_type_gui_and_data[0]
    cell_type.layer.add([0, 0, 0])
    assert cell_type.layer.current_size != 77
    cell_type.layer.current_size = 77
    assert cell_type.layer.current_size == 77
    assert cell_type.layer.size[0] == 77
    calculated_config = cell_type.get_calculated_config(1)
    assert isinstance(calculated_config.symbol, str)
    assert calculated_config.outline_size == 77


if __name__ == "__main__":
    import napari

    test_code_gen_color(napari.viewer.Viewer)
    viewer = napari.current_viewer()
    viewer.close_all()

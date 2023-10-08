"""
Tests the code that generates python
"""

from matplotlib.colors import to_rgba

from napari_3d_counter import Count3D, CellTypeConfig
from napari_3d_counter._widget import DEFUALT_CONFIG


def test_code_gen_name(make_napari_viewer):
    viewer = make_napari_viewer()
    my_widget = Count3D(viewer)
    cell_type = my_widget.cell_type_gui_and_data[0]
    cell_type.layer.name = "test name"
    python_string = cell_type.config_python_code()
    config = eval(python_string)
    assert config.name == "test name"

def test_code_gen_color(make_napari_viewer):
    viewer = make_napari_viewer()
    my_widget = Count3D(viewer)
    cell_type = my_widget.cell_type_gui_and_data[0]
    cell_type.layer.current_edge_color = to_rgba("#ffffffff")
    python_string = cell_type.config_python_code()
    config = eval(python_string)
    assert config.color == "#ffffffff"

def test_config_self(make_napari_viewer):
    viewer = make_napari_viewer()
    my_widget = Count3D(viewer)
    cell_type = my_widget.cell_type_gui_and_data[0]
    cell_type.layer.name = "loop"
    python_string = cell_type.config_python_code()
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

if __name__ == "__main__":
    import napari
    test_print_config(napari.viewer.Viewer)

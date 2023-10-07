from typing import List, Optional
from dataclasses import dataclass

import numpy as np

from matplotlib.colors import to_rgba_array

from napari_3d_counter import Count3D, CellTypeConfig
from napari_3d_counter._widget import DEFUALT_CONFIG


@dataclass
class Event:
    value: Optional[List[np.ndarray]] = None


# make_napari_viewer is a pytest fixture that returns a napari viewer object
# capsys is a pytest fixture that captures stdout and stderr output streams
def test_change_state(make_napari_viewer):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100, 100)))

    # create our widget, passing in the viewer
    my_widget = Count3D(viewer)

    #
    ps = my_widget.cell_type_gui_and_data[0]
    my_widget.change_state_to(ps)
    assert my_widget.pointer_type_state == ps


def test_change_color(make_napari_viewer):
    viewer = make_napari_viewer()
    my_widget = Count3D(viewer)
    default_celltype = my_widget.cell_type_gui_and_data[0]
    my_widget.new_pointer_point(Event([np.array([1, 1, 1])]))
    test_color = to_rgba_array("#12345678")
    assert sum(default_celltype.layer.edge_color[0] - test_color[0]) > 0.01
    default_celltype.layer.current_edge_color = test_color[0]
    print(test_color[0])
    assert sum(default_celltype.layer.edge_color[0] - test_color[0]) < 0.01


def test_add_point(make_napari_viewer):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100, 100)))

    # create our widget, passing in the viewer
    my_widget = Count3D(viewer)
    event = Event()
    event.value = [np.array([1, 1, 1])]
    my_widget.new_pointer_point(event)
    event.value = [np.array([2, 2, 2])]
    my_widget.new_pointer_point(event)
    default_celltype = my_widget.cell_type_gui_and_data[0]
    assert default_celltype.layer.data.shape == (2, 3)


def test_undo(make_napari_viewer):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100, 100)))

    # create our widget, passing in the viewer
    my_widget = Count3D(viewer)
    event = Event()
    event.value = [np.array([1, 1, 1])]
    my_widget.new_pointer_point(event)
    my_widget._undo()
    default_celltype = my_widget.cell_type_gui_and_data[0]
    assert len(default_celltype.layer.data) == 0


def test_undo_from_manual_add(make_napari_viewer):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    # create our widget, passing in the viewer
    my_widget = Count3D(viewer, cell_type_config=[CellTypeConfig("name")])
    assert len(my_widget.undo_stack) == 0
    viewer.layers["name"].add([1, 2, 3])
    # assert len(my_widget.undo_stack) == 1
    my_widget._undo()
    assert len(my_widget.undo_stack) == 0


def test_undo_across_states(make_napari_viewer):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100, 100)))

    # create our widget, passing in the viewer
    my_widget = Count3D(viewer)
    event = Event()
    event.value = [np.array([1, 1, 1])]
    my_widget.new_pointer_point(event)
    event.value = [np.array([2, 2, 2])]
    my_widget.new_pointer_point(event)
    my_widget.change_state_to(my_widget.cell_type_gui_and_data[1])
    my_widget.new_pointer_point(event)
    event.value = [np.array([2, 2, 2])]
    my_widget._undo()  # other state
    my_widget._undo()  # current state state
    default_celltype = my_widget.cell_type_gui_and_data[0]
    assert len(default_celltype.layer.data) == 1
    # saturate undos without errors
    my_widget._undo()
    my_widget._undo()
    my_widget._undo()


def test_name_counter(make_napari_viewer):
    viewer = make_napari_viewer()
    my_widget = Count3D(viewer)
    event = Event()
    event.value = [np.array([1, 1, 1])]
    my_widget.new_pointer_point(event)
    default_celltype = my_widget.cell_type_gui_and_data[0]
    assert default_celltype.button.text()[1] == "1"
    my_widget.new_pointer_point(event)
    assert default_celltype.button.text()[1] == "2"
    my_widget._undo()
    assert default_celltype.button.text()[1] == "1"


def test_name_counter(make_napari_viewer):
    viewer = make_napari_viewer()
    my_widget = Count3D(viewer)
    my_widget.update_out_of_slice()
    assert my_widget.out_of_slice_points.data.shape == (0, 2)


# def test_example_magic_widget(make_napari_viewer, capsys):
# viewer = make_napari_viewer()
# layer = viewer.add_image(np.random.random((100, 100)))

# # this time, our widget will be a MagicFactory or FunctionGui instance
# my_widget = example_magic_widget()

# # if we "call" this object, it'll execute our function
# my_widget(viewer.layers[0])

# # read captured output and check that it's as we expected
# captured = capsys.readouterr()
# assert captured.out == f"you have selected {layer}\n"

if __name__ == "__main__":
    import napari

    test_change_color(napari.viewer.Viewer)

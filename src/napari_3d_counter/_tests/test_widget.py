from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd
from matplotlib.colors import to_hex, to_rgba_array
import pytest

from napari_3d_counter import CellTypeConfig, Count3D
from napari_3d_counter.celltype_config import DEFAULT_COLOR_SEQUENCE
from napari_3d_counter._widget import CellTypeGuiAndData

import napari


@dataclass
class Event:
    value: Optional[List[np.ndarray]] = None
    action: Optional[str] = "added"


def total_n_points(cell_type_gui_and_data: list[CellTypeGuiAndData]):
    sum = 0
    for cell_type in cell_type_gui_and_data:
        sum = sum + cell_type.layer.data.shape[0]
    return sum


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
    default_celltype = my_widget.cell_type_gui_and_data[0]
    event.value = [np.array([1, 1, 1])]
    my_widget.new_pointer_point(event)
    print(default_celltype.layer.data.shape)
    assert default_celltype.layer.data.shape == (1, 3)
    event.value = [np.array([2, 2, 2])]
    my_widget.new_pointer_point(event)
    assert default_celltype.layer.data.shape == (2, 3)


def test_keybind_conflict(make_napari_viewer):
    viewer = make_napari_viewer()
    config = [CellTypeConfig(keybind="q"), CellTypeConfig(keybind="q")]
    # create our widget, passing in the viewer
    my_widget = Count3D(viewer, cell_type_config=config)
    viewer.window.add_dock_widget(my_widget)


def test_undo(make_napari_viewer):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100, 100)))

    # create our widget, passing in the viewer
    my_widget = Count3D(viewer)
    event = Event()
    event.value = [np.array([1, 1, 1])]
    my_widget.new_pointer_point(event)
    my_widget.undo()
    default_celltype = my_widget.cell_type_gui_and_data[0]
    assert len(default_celltype.layer.data) == 0


def test_manual_add(make_napari_viewer):
    viewer = make_napari_viewer()
    # create our widget, passing in the viewer
    my_widget = Count3D(viewer, cell_type_config=[CellTypeConfig("name")])
    viewer.layers["name"].add([1, 2, 3])
    assert viewer.layers["name"].data.shape == (1, 3)
    assert len(my_widget.undo_stack) == 1


def test_undo_from_manual_add(make_napari_viewer):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    # create our widget, passing in the viewer
    my_widget = Count3D(viewer, cell_type_config=[CellTypeConfig("name")])
    assert len(my_widget.undo_stack) == 0
    viewer.layers["name"].add([1, 2, 3])
    assert len(my_widget.undo_stack) == 1
    print("undoing")
    my_widget.undo()
    assert len(my_widget.undo_stack) == 0


def test_undo_across_states_again(make_napari_viewer):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100, 100)))
    # create our widget, passing in the viewer
    my_widget = Count3D(
        viewer,
        cell_type_config=[CellTypeConfig("name"), CellTypeConfig("two")],
    )
    event = Event()
    my_widget.change_state_to(my_widget.cell_type_gui_and_data[0])
    assert (
        total_n_points(my_widget.cell_type_gui_and_data)
        == 0
        == len(my_widget.undo_stack)
    )
    event.value = [np.array([1, 1, 1])]
    my_widget.new_pointer_point(event)
    assert (
        total_n_points(my_widget.cell_type_gui_and_data)
        == 1
        == len(my_widget.undo_stack)
    )
    my_widget.change_state_to(my_widget.cell_type_gui_and_data[1])
    event.value = [np.array([2, 2, 2])]
    my_widget.new_pointer_point(event)
    assert (
        total_n_points(my_widget.cell_type_gui_and_data)
        == 2
        == len(my_widget.undo_stack)
    )
    my_widget.change_state_to(my_widget.cell_type_gui_and_data[1])
    event.value = [np.array([1, 1, 1])]
    my_widget.new_pointer_point(event)
    assert (
        total_n_points(my_widget.cell_type_gui_and_data)
        == 3
        == len(my_widget.undo_stack)
    )
    my_widget.change_state_to(my_widget.cell_type_gui_and_data[1])
    event.value = [np.array([2, 2, 2])]
    my_widget.new_pointer_point(event)
    assert (
        total_n_points(my_widget.cell_type_gui_and_data)
        == 4
        == len(my_widget.undo_stack)
    )
    my_widget.undo()
    assert (
        total_n_points(my_widget.cell_type_gui_and_data)
        == 3
        == len(my_widget.undo_stack)
    )
    my_widget.undo()
    assert (
        total_n_points(my_widget.cell_type_gui_and_data)
        == 2
        == len(my_widget.undo_stack)
    )
    my_widget.undo()
    assert (
        total_n_points(my_widget.cell_type_gui_and_data)
        == 1
        == len(my_widget.undo_stack)
    )
    my_widget.undo()
    assert (
        total_n_points(my_widget.cell_type_gui_and_data)
        == 0
        == len(my_widget.undo_stack)
    )


def test_undo_across_states(make_napari_viewer):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100, 100)))

    # create our widget, passing in the viewer

    my_widget = Count3D(
        viewer,
        cell_type_config=[CellTypeConfig("name"), CellTypeConfig("two")],
    )
    event = Event()
    my_widget.change_state_to(my_widget.cell_type_gui_and_data[0])
    assert total_n_points(my_widget.cell_type_gui_and_data) == 0
    event.value = [np.array([1, 1, 1])]
    my_widget.new_pointer_point(event)
    assert total_n_points(my_widget.cell_type_gui_and_data) == 1
    my_widget.change_state_to(my_widget.cell_type_gui_and_data[1])
    event.value = [np.array([2, 2, 2])]
    my_widget.new_pointer_point(event)
    assert total_n_points(my_widget.cell_type_gui_and_data) == 2
    my_widget.change_state_to(my_widget.cell_type_gui_and_data[0])
    my_widget.new_pointer_point(event)
    assert total_n_points(my_widget.cell_type_gui_and_data) == 3
    event.value = [np.array([2, 2, 2])]
    my_widget.undo()  # other state
    assert total_n_points(my_widget.cell_type_gui_and_data) == 2
    my_widget.undo()  # current state state
    assert total_n_points(my_widget.cell_type_gui_and_data) == 1
    default_celltype = my_widget.cell_type_gui_and_data[0]
    my_widget.undo()
    assert total_n_points(my_widget.cell_type_gui_and_data) == 0


def test_undo_from_manual_add_across_states(make_napari_viewer):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    # create our widget, passing in the viewer
    my_widget = Count3D(
        viewer, cell_type_config=[CellTypeConfig("one"), CellTypeConfig("two")]
    )
    assert len(my_widget.undo_stack) == 0
    viewer.layers["one"].add([1, 2, 3])
    viewer.layers["two"].add([1, 2, 3])
    assert len(my_widget.undo_stack) == 2
    my_widget.undo()
    assert len(my_widget.undo_stack) == 1
    assert total_n_points(my_widget.cell_type_gui_and_data) == 1
    my_widget.undo()
    assert len(my_widget.undo_stack) == 0
    assert total_n_points(my_widget.cell_type_gui_and_data) == 0


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
    my_widget.undo()
    assert default_celltype.button.text()[1] == "1"


def test_name_counter2(make_napari_viewer):
    viewer = make_napari_viewer()
    my_widget = Count3D(viewer)
    my_widget.update_out_of_slice()
    assert my_widget.out_of_slice_points.data.shape == (0, 2)


def test_save_points_to_df_empty(make_napari_viewer):
    viewer = make_napari_viewer()
    my_widget = Count3D(viewer)
    df = my_widget.save_points_to_df()
    assert len(df.index) == 0
    assert list(df.columns) == ["cell_type", "z", "y", "x"]


def test_save_points_to_df(make_napari_viewer):
    viewer = make_napari_viewer()
    my_widget = Count3D(viewer)
    my_widget.new_pointer_point(Event([np.array([1, 1, 1])]))
    my_widget.change_state_to(my_widget.cell_type_gui_and_data[1])
    my_widget.new_pointer_point(Event([np.array([2, 2, 2])]))
    df = my_widget.save_points_to_df()
    assert len(df.index) == 2
    assert np.all(df.columns == np.array(["cell_type", "z", "y", "x"]))


def test_load_points_from_df(make_napari_viewer):
    viewer = make_napari_viewer()
    my_widget = Count3D(viewer)
    df = pd.DataFrame(
        {
            "cell_type": ["1", "1", "2", "2"],
            "z": [1, 1, 1, 1],
            "y": [3, 2, 1, 0],
            "x": [0, 1, 2, 3],
        }
    )
    my_widget.read_points_from_df(df)
    print(my_widget.cell_type_gui_and_data[-1])
    assert my_widget.cell_type_gui_and_data[-1].layer.name == "2"


def test_name_conflict(make_napari_viewer):
    viewer = make_napari_viewer()
    config = [CellTypeConfig("2")]
    my_widget = Count3D(viewer, cell_type_config=config)
    df = pd.DataFrame(
        {
            "cell_type": ["1", "1", "2", "2"],
            "z": [1, 1, 1, 1],
            "y": [3, 2, 1, 0],
            "x": [0, 1, 2, 3],
        }
    )
    my_widget.read_points_from_df(df)
    viewer.window.add_dock_widget(my_widget)
    print(my_widget.cell_type_gui_and_data[-1])
    assert my_widget.cell_type_gui_and_data[-1].layer.name == "2 [1]"


def test_color_conflict(make_napari_viewer):
    viewer = make_napari_viewer()
    config = [CellTypeConfig("2")]
    my_widget = Count3D(viewer, cell_type_config=config)
    df = pd.DataFrame(
        {
            "cell_type": ["1", "1", "2", "2"],
            "z": [1, 1, 1, 1],
            "y": [3, 2, 1, 0],
            "x": [0, 1, 2, 3],
        }
    )
    my_widget.read_points_from_df(df)
    assert (
        to_hex(
            my_widget.cell_type_gui_and_data[-1].layer.current_edge_color,
            keep_alpha=True,
        )
        == DEFAULT_COLOR_SEQUENCE[2]
    )


def test_load_save_loop(make_napari_viewer):
    viewer = make_napari_viewer()
    my_widget = Count3D(viewer, [CellTypeConfig(name="test_name")])
    my_widget.new_pointer_point(Event([np.array([1, 1, 1])]))
    df = my_widget.save_points_to_df()
    # load into a different widget
    viewer = make_napari_viewer()
    my_widget = Count3D(viewer, [])
    my_widget.read_points_from_df(df)
    cell_type = my_widget.cell_type_gui_and_data[-1]
    assert cell_type.layer.name == "test_name"
    assert cell_type.layer.data.shape[0] == 1


def test_change_symbol(make_napari_viewer):
    if napari.__version__.split(".")[:3] == ["0", "4", "19"]:
        pytest.skip("changing symbol not supported in napari 0.4.19")
    viewer = make_napari_viewer()
    my_widget = Count3D(viewer, [CellTypeConfig(name="test_name")])
    my_widget.new_pointer_point(Event([np.array([1, 2, 1])]))
    cell_type = my_widget.cell_type_gui_and_data[0]
    star = napari.layers.points._points_constants.Symbol.STAR
    cell_type.layer.current_symbol = star
    assert cell_type.layer.symbol[0] == star


def test_change_size(make_napari_viewer):
    viewer = make_napari_viewer()
    my_widget = Count3D(viewer, [CellTypeConfig(name="test_name")])
    my_widget.new_pointer_point(Event([np.array([1, 2, 1])]))
    cell_type = my_widget.cell_type_gui_and_data[0]
    cell_type.layer.current_size = 100
    assert cell_type.layer.size[0] == 100


def test_change_face_color(make_napari_viewer):
    viewer = make_napari_viewer()
    my_widget = Count3D(viewer, [CellTypeConfig(name="test_name")])
    my_widget.new_pointer_point(Event([np.array([1, 2, 1])]))
    cell_type = my_widget.cell_type_gui_and_data[0]
    color = "#00FF00"
    cell_type.layer.current_face_color = color
    assert np.all(
        cell_type.layer.face_color[0]
        == np.array(
            [
                0.0,
                1.0,
                0.0,
                1.0,
            ]
        )
    )


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
    test_undo_across_states_again(napari.viewer.Viewer)

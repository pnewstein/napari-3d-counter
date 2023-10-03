from typing import List

import numpy as np

from napari_3d_counter import Count3D
from napari_3d_counter._widget import PointerState


class Event:
    value: List[np.ndarray]


# make_napari_viewer is a pytest fixture that returns a napari viewer object
# capsys is a pytest fixture that captures stdout and stderr output streams
def test_change_state(make_napari_viewer):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100, 100)))

    # create our widget, passing in the viewer
    my_widget = Count3D(viewer)

    #
    ps = PointerState("a", "name", 0, "red")
    my_widget._change_state_to(ps)()
    assert my_widget.pointer_type_state == ps


def test_add_point(make_napari_viewer):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100, 100)))

    # create our widget, passing in the viewer
    my_widget = Count3D(viewer)
    event = Event()
    event.value = [np.array([1, 1, 1])]
    my_widget._new_point_function(event)
    event.value = [np.array([2, 2, 2])]
    my_widget._new_point_function(event)
    assert my_widget.point_layers[1].data.shape == (2, 3)


def test_undo(make_napari_viewer):
    # make viewer and add an image layer using our fixture
    viewer = make_napari_viewer()
    viewer.add_image(np.random.random((100, 100, 100)))

    # create our widget, passing in the viewer
    my_widget = Count3D(viewer)
    event = Event()
    event.value = [np.array([1, 1, 1])]
    my_widget._new_point_function(event)
    my_widget._undo()
    assert len(my_widget.point_layers[1].data) == 0


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

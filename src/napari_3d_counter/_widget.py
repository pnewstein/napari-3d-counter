"""
implements the counting interface and the reconstruction plugin
"""

from typing import Callable, Dict, List
from dataclasses import dataclass

from qtpy.QtWidgets import QVBoxLayout, QPushButton, QWidget, QLabel

import napari
from napari.utils.events import Event


@dataclass(frozen=True)
class PointerState:
    """
    Represents a counter type
    """

    keybind: str
    name: str
    state: int
    color: str


POINTER_STATES = [
    PointerState("q", "1", 1, "g"),
    PointerState("w", "2", 2, "r"),
    PointerState("e", "3", 3, "c"),
    PointerState("r", "4", 4, "m"),
]


class Count3D(QWidget):
    """
    Main interface for counting cells
    """

    def __init__(self, napari_viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = napari_viewer
        self.pointer_type_state = POINTER_STATES[0]
        self.setLayout(QVBoxLayout())
        self.pointer_type_state_label = QLabel()
        self._change_state_to(self.pointer_type_state)()
        self.layout().addWidget(self.pointer_type_state_label)
        self.undo_stack: List[int] = []
        # add out of slice markers
        self.out_of_slice_points = self.viewer.add_points(
            ndim=2, size=2, name="out of slice"
        )

        # set up state_list specific code
        self.point_layers: Dict[int, napari.layers.points.Points] = {}
        buttons: list[QPushButton] = []
        for state in POINTER_STATES:
            btn = QPushButton(f"{state.name} ({state.keybind})")
            change_state_fun = self._change_state_to(state)
            btn.clicked.connect(change_state_fun)
            self.layout().addWidget(btn)
            buttons.append(btn)
            point_layer = self.viewer.add_points(
                ndim=3,
                name=state.name,
                edge_color=state.color,
                face_color="#00000000",
                out_of_slice_display=True,
            )
            self.point_layers[state.state] = point_layer
            self.viewer.bind_key(
                key=state.keybind, func=change_state_fun, overwrite=True
            )

        def new_pointer_point(event: Event):
            """
            Handel a new point being added to the pointer
            """
            pointer_coords = event.value
            self.pointer.data = []
            current_point_layer = self.point_layers[
                self.pointer_type_state.state
            ]
            coords_2d = pointer_coords[0][1:]
            current_point_layer.add(coords=pointer_coords)
            self.out_of_slice_points.add(coords=coords_2d)
            self.undo_stack.append(self.pointer_type_state.state)
            # hack to unselect last added point
            current_point_layer.add(coords=pointer_coords)
            current_point_layer.remove_selected()

        self._new_point_function = new_pointer_point
        self.pointer = self.viewer.add_points(ndim=3, name="Selector")
        self.pointer.mode = "add"
        self.pointer.events.data.connect(new_pointer_point)
        undo_button = QPushButton("undo (u)")
        undo_button.clicked.connect(self._undo)
        self.viewer.bind_key(key="u", func=self._undo)
        self.layout().addWidget(undo_button)

    def _change_state_to(self, state: PointerState) -> Callable[[], None]:
        def out(opt=None):
            _ = opt
            self.pointer_type_state = state
            self.pointer_type_state_label.setText(state.name)

        return out

    def _undo(self, opt=None):
        """
        undo the last writen thing
        """
        _ = opt
        state = self.undo_stack.pop()
        self.point_layers[state].data = self.point_layers[state].data[:-1]
        self.out_of_slice_points.data = self.out_of_slice_points.data[:-1]


# Uses the `autogenerate: true` flag in the plugin manifest
# to indicate it should be wrapped as a magicgui to autogenerate
# a widget.
def reconstruct_selected(
    labels_layer: napari.layers.labels.Labels,
    point_layer: napari.layers.points.Points,
    viewer: napari.viewer.Viewer,
):
    """
    Reconstructs the layers in an image
    """
    name = point_layer.name
    viewer.add_image(name=f"{name} reconstruction")

"""
implements the counting interface and the reconstruction plugin
"""

from typing import Callable, List, Optional
from dataclasses import dataclass

from qtpy.QtWidgets import QVBoxLayout, QPushButton, QWidget, QLabel
import napari
from napari.utils.events import Event
import numpy as np


from .celltype_config import CellTypeConfig, PointerState, process_cell_type_config


@dataclass
class CellTypeGuiAndData:
    """
    Represents the cell type GUI and data
    """

    pointer_state: PointerState
    button: QPushButton
    layer: napari.layers.Points

    def update_button_text(self):
        """
        Updates the button with current name, and nubmer of cells
        """
        # update the button
        button_text = (
            f"[{self.layer.data.shape[0]}] {self.layer.name}"
            f"( {self.pointer_state.keybind})"
        )
        self.button.setText(button_text)


POINTER_STATES = [
    PointerState("q", "Celltype 1", 1, "g"),
    PointerState("w", "Celltype 2", 2, "r"),
    PointerState("e", "Celltype 3", 3, "c"),
    PointerState("r", "Celltype 4", 4, "m"),
]


class Count3D(QWidget):  # pylint: disable=R0902
    """
    Main interface for counting cells
    """

    def __init__(self, napari_viewer: "napari.viewer.Viewer", cell_type_config: Optional[List[CellTypeConfig]]=None):
        super().__init__()
        if cell_type_config is None:
            pointer_states = POINTER_STATES
        else:
            pointer_states = process_cell_type_config(cell_type_config)
        self.viewer = napari_viewer
        self.undo_stack: List[int] = []
        # add out of slice markers
        self.out_of_slice_points = self.viewer.add_points(
            ndim=2, size=2, name="out of slice"
        )
        # set up cell type points layers
        self.cell_type_gui_and_data = {
            state.state: self.init_celltype_gui_and_data(state)
            for state in pointer_states
        }
        # initalize the pointer points
        self.pointer = self.viewer.add_points(ndim=3, name="Selector")
        self.pointer.mode = "add"
        self.pointer.events.data.connect(self.new_pointer_point)
        # init qt gui
        self.setLayout(QVBoxLayout())
        self.pointer_type_state_label = QLabel()
        self.layout().addWidget(self.pointer_type_state_label)
        for cell_type in self.cell_type_gui_and_data.values():
            self.layout().addWidget(cell_type.button)
        # handle undo button
        undo_button = QPushButton("undo (u)")
        undo_button.clicked.connect(self._undo)
        self.viewer.bind_key(key="u", func=self._undo)
        self.layout().addWidget(undo_button)
        # initialize state to the first default
        self.pointer_type_state = pointer_states[0]
        self._change_state_to(self.pointer_type_state)()

    def new_pointer_point(self, event: Event):
        """
        Handle a new point being added to the pointer
        """
        pointer_coords = event.value
        self.pointer.data = []
        current_cell_type = self.cell_type_gui_and_data[
            self.pointer_type_state.state
        ]
        current_point_layer = current_cell_type.layer
        coords_2d = pointer_coords[0][1:]
        current_point_layer.add(coords=pointer_coords)
        self.out_of_slice_points.add(coords=coords_2d)
        # update undo stack
        self.undo_stack.append(self.pointer_type_state.state)
        # update the button
        current_cell_type.update_button_text()
        # hack to unselect last added point
        current_point_layer.add(coords=pointer_coords)
        current_point_layer.remove_selected()

    def init_celltype_gui_and_data(
        self, pointer_state: PointerState, data: Optional[np.ndarray] = None
    ) -> CellTypeGuiAndData:
        """
        Inits a celltype GUI and data by adding a layer to the viewer, and
        setting the name of the button, also binds the key
        """
        point_layer = self.viewer.add_points(
            data=data,
            ndim=3,
            name=pointer_state.name,
            edge_color=pointer_state.color,
            face_color="#00000000",
            out_of_slice_display=True,
        )
        change_state_fun = self._change_state_to(pointer_state)
        self.viewer.bind_key(
            key=pointer_state.keybind, func=change_state_fun, overwrite=True
        )
        btn = QPushButton(
            f"[{point_layer.data.shape[0]}] {pointer_state.name} ({pointer_state.keybind})"
        )
        btn.clicked.connect(change_state_fun)
        return CellTypeGuiAndData(
            pointer_state=pointer_state, button=btn, layer=point_layer
        )

    def _change_state_to(self, state: PointerState) -> Callable[[], None]:
        """
        Changes the state
        """
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
        if not self.undo_stack:
            print("No previous changes")
            return
        state = self.undo_stack.pop()
        cell_type = self.cell_type_gui_and_data[state]
        point_layer = cell_type.layer
        point_layer.data = point_layer.data[:-1]
        self.out_of_slice_points.data = self.out_of_slice_points.data[:-1]
        # update button
        cell_type.update_button_text()


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
    raise NotImplementedError()

"""
implements the counting interface and the reconstruction plugin
"""

from typing import Callable, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from functools import partial
from threading import Thread

from qtpy.QtWidgets import QVBoxLayout, QPushButton, QWidget, QLabel, QFileDialog
import napari
from napari.utils.events import Event
import numpy as np
from matplotlib.colors import to_rgba_array, to_hex


from .celltype_config import (
    CellTypeConfig,
    CellTypeConfigNotOptional,
    process_cell_type_config,
)

DEFUALT_CONFIG = [
    CellTypeConfig(keybind="q", name="Celltype 1", color="g"),
    CellTypeConfig(keybind="w", name="Celltype 2", color="r"),
    CellTypeConfig(keybind="e", name="Celltype3", color="c"),
    CellTypeConfig(keybind="r", name="Celltype4", color="m"),
]


@dataclass
class NamedPartial:
    """
    contains a functools partial and a name
    """

    func: partial
    name: str

    def __name__(self):
        return self.name

    def __call__(self, *args, **kwargs):
        return self.func.__call__(*args, **kwargs)


@dataclass
class CellTypeGuiAndData:
    """
    Represents the cell type GUI and data
    """

    # pointer_state: PointerState
    keybind: str
    button: QPushButton
    layer: napari.layers.Points

    def update_button_text(self):
        """
        Updates the button with current name, and nubmer of cells
        """
        # update the button
        if self.keybind:
            keybind_str = f" ({self.keybind})"
        else:
            keybind_str = ""
        button_text = f"[{self.layer.data.shape[0]}] {self.layer.name}" + keybind_str
        self.button.setText(button_text)

    def update_all_colors_to_current_color(self, *args):
        """
        updates all edge_colors to current_edge_color
        """
        _ = args
        current_color = to_rgba_array(self.layer.current_edge_color)
        n_edge_colors = self.layer.edge_color.shape[0]
        if n_edge_colors:
            self.layer.edge_color = np.vstack(
                [current_color] * n_edge_colors
            )

    def get_calculated_config(self) -> CellTypeConfigNotOptional:
        """
        returns the current configuration of the channel
        """
        return CellTypeConfigNotOptional(name=self.layer.name, color=to_hex(self.layer.current_edge_color, keep_alpha=True), keybind=self.keybind)

    def config_python_code(self):
        """
        returns a string containing python code, 
        which can be used to launch the plugin with
        the current config
        """
        return repr(self.get_calculated_config())


class Count3D(QWidget):  # pylint: disable=R0902
    """
    Main interface for counting cells
    """

    def __init__(
        self,
        napari_viewer: "napari.viewer.Viewer",
        cell_type_config: Optional[List[CellTypeConfig]] = None,
    ):
        super().__init__()
        if cell_type_config is None:
            cell_type_config = DEFUALT_CONFIG
        calculated_config = process_cell_type_config(cell_type_config)
        self.viewer = napari_viewer
        self.undo_stack: List[CellTypeGuiAndData] = []
        self.currently_adding_point = False
        # add out of slice markers
        self.out_of_slice_points = self.viewer.add_points(
            ndim=2, size=2, name="out of slice"
        )
        # set up cell type points layers
        self.cell_type_gui_and_data = [self.init_celltype_gui_and_data(config=config) for config in calculated_config]
        # initalize the pointer points
        self.pointer = self.viewer.add_points(ndim=3, name="Selector")
        self.pointer.mode = "add"
        self.pointer.events.data.connect(self.new_pointer_point)
        # init qt gui
        self.setLayout(QVBoxLayout())
        self.pointer_type_state_label = QLabel()
        self.layout().addWidget(self.pointer_type_state_label)
        for cell_type in self.cell_type_gui_and_data:
            self.layout().addWidget(cell_type.button)
        # handle undo button
        undo_button = QPushButton("undo (u)")
        undo_button.clicked.connect(self._undo)
        self.viewer.bind_key(key="u", func=self._undo, overwrite=True)
        self.layout().addWidget(undo_button)
        # code gen button
        code_gen_button = QPushButton("Make launch_cell_count.py")
        code_gen_button.clicked.connect(self.gen_code_gui)
        self.layout().addWidget(code_gen_button)
        # initialize state to the first default
        self.pointer_type_state = self.cell_type_gui_and_data[0]
        self.change_state_to(self.pointer_type_state)

    def update_out_of_slice(self):
        """
        Adds points from all of self.cell_type_gui_and_data
        to self.out_of_slice_points
        """
        datas = [
            cell_type.layer.data[:, 1:]
            for cell_type in self.cell_type_gui_and_data
        ]
        data = np.vstack(datas)
        _, ndims = data.shape
        assert ndims == 2
        self.out_of_slice_points.data = data

    def look_up_cell_type_from_points(
        self, points: napari.layers.Points
    ) -> CellTypeGuiAndData:
        """
        Returns the cell_type containing those points
        """
        return next(
            cell_type
            for cell_type in self.cell_type_gui_and_data
            if cell_type.layer.data is points.data
        )

    def handle_data_changed(self, event: Event):
        """
        Handle adding point specific to the layer
        """
        if self.currently_adding_point:
            return
        # add to out_of_slice_points
        self.update_out_of_slice()
        # figure out current cell type
        current_points = event.source
        current_cell_type = self.look_up_cell_type_from_points(current_points)
        # add to undo stack
        self.undo_stack.append(current_cell_type)
        # update the button
        current_cell_type.update_button_text()

    def new_pointer_point(self, event: Event):
        """
        Handle a new point being added to the pointer
        by adding to the correct sublayer
        """
        pointer_coords = event.value
        self.pointer.data = []
        current_cell_type = self.pointer_type_state
        # dispatch point to appropriate layer
        # implicitly calls self.handle_data_changed
        current_point_layer = current_cell_type.layer
        current_point_layer.add(coords=pointer_coords)
        # hack to unselect last added point
        # prevent layer specific handlers from updateing
        self.currently_adding_point = True
        # add and remove point
        current_point_layer.add(coords=pointer_coords)
        current_point_layer.remove_selected()
        self.currently_adding_point = False

    def init_celltype_gui_and_data(
        self,
        config: CellTypeConfigNotOptional,
        data: Optional[np.ndarray] = None,
    ) -> CellTypeGuiAndData:
        """
        Inits a celltype GUI and data by adding a layer to the viewer, and
        setting the name of the button, also binds the key
        """
        point_layer = self.viewer.add_points(
            data=data,
            ndim=3,
            name=config.name,
            edge_color=config.color,
            face_color="#00000000",
            out_of_slice_display=True,
        )
        point_layer.events.data.connect(self.handle_data_changed)
        btn = QPushButton()
        out = CellTypeGuiAndData(
            keybind=config.keybind, button=btn, layer=point_layer
        )
        change_state_fun = NamedPartial(
            partial(self.change_state_to, out), config.name
        )
        if config.keybind:
            try:
                self.viewer.bind_key(
                    key=config.keybind, func=change_state_fun
                )
            except ValueError:
                # probably keybind was already set
                out.keybind = ""
        btn.clicked.connect(change_state_fun)
        # update button when name changes
        point_layer.events.name.connect(out.update_button_text)
        # update color when color changes
        point_layer.events.current_edge_color.connect(
            out.update_all_colors_to_current_color
        )
        out.update_button_text()
        return out

    def change_state_to(self, state: CellTypeGuiAndData, extra=None):
        """
        Changes the state
        """
        _ = extra
        self.pointer_type_state = state
        self.pointer_type_state_label.setText(state.layer.name)

    def _undo(self, opt=None):
        """
        undo the last writen thing
        """
        _ = opt
        if not self.undo_stack:
            print("No previous changes")
            return
        cell_type = self.undo_stack.pop()
        point_layer = cell_type.layer
        point_layer.data = point_layer.data[:-1]
        self.update_out_of_slice()
        # update button
        cell_type.update_button_text()

    def config_in_python(self) -> str:
        """
        Creates a python string that when runed, 
        initatiates napari
        """
        header = (
            "import napari\n"
            "from napari_3d_counter import Count3D, CellTypeConfig\n\n"
            "viewer = napari.viewer.Viewer()\n"
            "# set up cell types\n"
            "config = [\n"
        )
        config_lines = [f"    {cell_type.config_python_code()},\n" for cell_type in self.cell_type_gui_and_data]
        footer = (
            "]\n"
            "# make a new viewer\n"
            "viewer = napari.viewer.Viewer()\n"
            "# attach plugin to viewer\n"
            "viewer.window.add_dock_widget(Count3D(viewer, cell_type_config=config))"
        )
        return "".join([header]+config_lines+[footer])

    def gen_code_gui(self, *args):
        """
        does a dialog to save generated python to a file
        """
        _ = args
        python_string = self.config_in_python()
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(self,"Save File","","All Files(*);;Text Files(*.py)",options = options)
        if file_name:
            Path(file_name).write_text(python_string)
        


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

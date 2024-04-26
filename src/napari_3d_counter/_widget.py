"""
implements the counting interface and the reconstruction plugin
"""

from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import List, Optional, Literal
from threading import Lock

import napari
import numpy as np
import pandas as pd
from matplotlib.colors import to_hex, to_rgba_array
from napari.utils.events import Event
from qtpy.QtCore import Qt  # type: ignore
from qtpy.QtWidgets import (  # pylint: disable=no-name-in-module
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .celltype_config import (
    CellTypeConfig,
    CellTypeConfigNotOptional,
    process_cell_type_config,
)

DEFUALT_CONFIG = [
    CellTypeConfig(keybind="q", name="Cell type 1", color="g"),
    CellTypeConfig(keybind="w", name="Cell type 2", color="r"),
    CellTypeConfig(keybind="e", name="Cell type 3", color="c"),
    CellTypeConfig(keybind="r", name="Cell type 4", color="m"),
]


def get_text_color(background_color: str) -> str:
    """
    returns black or white as hex string
    depending on what works better with the background
    """
    # same function as dinstinctipy
    white = "#ffffff"
    black = "#000000"
    red, green, blue, _ = to_rgba_array(background_color)[0]
    text_color = (
        white if (red * 0.299 + green * 0.587 + blue * 0.114) < 0.6 else black
    )
    return text_color


# This class is necessary because napari keybindings need a __name__
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

    def __hash__(self, *args, **kwargs):
        # hash function is necessary in some versions of napari
        return self.func.__hash__(*args, **kwargs)


@dataclass
class CellTypeGuiAndData:
    """
    Represents the cell type GUI and data
    """

    keybind: str
    button: QPushButton
    layer: napari.layers.Points
    gui_lock: Lock

    def update_button_gui(self):
        """
        Updates the button with current name, and number of cells
        """
        # do nothing if gui_lock is locked
        if self.gui_lock.locked():
            return
        # update the button
        keybind_str = f" ({self.keybind})" if self.keybind else ""
        button_text = (
            f"[{self.layer.data.shape[0]}] {self.layer.name}" + keybind_str
        )
        self.button.setText(button_text)
        color = to_hex(self.layer.current_edge_color)
        text_color = get_text_color(color)
        # hover_color is half way between text color and background color
        hover_color_rgb = (
            to_rgba_array(text_color)[0] + to_rgba_array(color)[0]
        ) / 2
        style_sheet = (
            f"QPushButton{{background-color: {color}; color: {text_color};}}"
            f"QPushButton:hover{{background-color: {to_hex(hover_color_rgb)}}}"
        )
        self.button.setStyleSheet(style_sheet)
        # updates all edge_colors to current_edge_color
        current_color = to_rgba_array(self.layer.current_edge_color)
        n_edge_colors = self.layer.edge_color.shape[0]
        if n_edge_colors:
            self.layer.edge_color = np.vstack([current_color] * n_edge_colors)

    def update_attr(
        self, attr: Literal["symbol", "size", "face_color", "edge_width"]
    ):
        """
        updates the size of the cell to the current size
        """
        current = getattr(self.layer, f"current_{attr}")
        n_points = self.layer.data.shape[0]
        setattr(self.layer, attr, np.array([current] * n_points))

    def get_calculated_config(self) -> CellTypeConfig:
        """
        returns the current configuration of the channel
        """
        return CellTypeConfig(
            name=self.layer.name,
            color=to_hex(self.layer.current_edge_color, keep_alpha=True),
            keybind=self.keybind,
        )


class Count3D(QWidget):  # pylint: disable=R0902
    """
    Main interface for counting cells
    """

    def __init__(
        self,
        napari_viewer: napari.viewer.Viewer,
        cell_type_config: Optional[List[CellTypeConfig]] = None,
    ):
        super().__init__()
        # handle configuration
        if cell_type_config is None:
            cell_type_config = DEFUALT_CONFIG
        if len(cell_type_config) == 0:
            print(
                "Cannot initialize with no cell types. Using default cell types"
            )
            cell_type_config = DEFUALT_CONFIG
        self.initial_config = process_cell_type_config(cell_type_config)
        # viewer is needed to add layers
        self.viewer = napari_viewer
        # a stack containing points with added layers
        self.undo_stack: List[CellTypeGuiAndData] = []
        # prevents unwanted animations
        self.gui_lock = Lock()
        # add out of slice markers
        self.out_of_slice_points = self.viewer.add_points(
            ndim=2,
            size=self.initial_config[0].out_of_slice_point_size,
            name="out of slice",
        )
        # set up cell type points layers
        self.cell_type_gui_and_data = [
            self.init_celltype_gui_and_data(state)
            for state in self.initial_config
        ]
        # initialize the pointer points
        self.pointer = self.viewer.add_points(
            ndim=3,
            name="Point adder",
            size=cell_type_config[0].out_of_slice_point_size,
        )
        self.pointer.mode = "add"
        # make new_pointer_point run each time data is changed
        self.pointer.events.data.connect(self.new_pointer_point)
        # initialize qt GUI
        self.setLayout(QVBoxLayout())
        # the label that says the current cell_type
        self.pointer_type_state_label = QLabel()
        self.pointer_type_state_label.setAlignment(Qt.AlignCenter)
        self.layout().addWidget(self.pointer_type_state_label)
        hline = QFrame()
        hline.setFrameShape(QFrame.HLine)
        self.layout().addWidget(hline)
        for cell_type in self.cell_type_gui_and_data:
            self.layout().addWidget(cell_type.button)
        # handle undo button
        undo_button = QPushButton("Undo (u)")
        undo_button.clicked.connect(self.undo)
        self.viewer.bind_key(key="u", func=self.undo, overwrite=True)
        self.layout().addWidget(undo_button)
        # code gen button
        code_gen_button = QPushButton("Make launch_cell_count.py")
        code_gen_button.clicked.connect(self.gen_code_gui)
        self.layout().addWidget(code_gen_button)
        # save and load buttons
        row_layout = QHBoxLayout()
        save_button = QPushButton("Save cells")
        save_button.clicked.connect(self.save_data_gui)
        row_layout.addWidget(save_button)
        save_button = QPushButton("Load cells")
        save_button.clicked.connect(self.load_data_gui)
        row_layout.addWidget(save_button)
        self.layout().addLayout(row_layout)

        # initialize state to the first default
        self.pointer_type_state = self.cell_type_gui_and_data[0]
        self.change_state_to(self.pointer_type_state)
        self.update_gui()

    def update_out_of_slice(self):
        """
        Adds points from all of self.cell_type_gui_and_data
        to self.out_of_slice_points
        """
        datas = [
            cell_type.layer.data[:, 1:]  # make 2d by taking last 2 coords
            for cell_type in self.cell_type_gui_and_data
        ]
        data = np.vstack(datas)
        _, ndims = data.shape
        assert ndims == 2
        self.out_of_slice_points.data = data

    def handle_data_changed(self, event: Event):
        """
        Handle adding point specific to the layer
        """
        # try:
        # event.value[0]
        # except IndexError:
        # # received an empty event
        # return
        if self.gui_lock.locked():
            return
        if event.action == "added":
            return
        # add to out_of_slice_points
        self.update_out_of_slice()
        # figure out current cell type
        current_points = event.source
        current_cell_type = next(
            cell_type
            for cell_type in self.cell_type_gui_and_data
            if cell_type.layer.data is current_points.data
        )
        # add to undo stack
        self.undo_stack.append(current_cell_type)
        # update the button
        current_cell_type.update_button_gui()

    def new_pointer_point(self, event: Event):
        """
        Handle a new point being added to the pointer
        by adding to the correct sub-layer
        """
        if event.action == "adding":
            return
        if self.gui_lock.locked():
            return
        pointer_coords = event.value
        assert self.gui_lock.acquire(blocking=False)
        self.pointer.data = []
        self.gui_lock.release()
        current_cell_type = self.pointer_type_state
        # dispatch point to appropriate layer
        # implicitly calls self.handle_data_changed
        current_point_layer = current_cell_type.layer
        # import pudb; pudb.set_trace()
        current_point_layer.add(coords=pointer_coords)
        # hack to unselect last added point
        # prevent layer specific handlers from updating
        # add and remove point
        assert self.gui_lock.acquire(blocking=False)
        current_point_layer.add(coords=pointer_coords)
        current_point_layer.remove_selected()
        self.gui_lock.release()
        self.update_out_of_slice()

    def update_gui(self):
        """
        Updates button color and button text
        """
        for cell_type in self.cell_type_gui_and_data:
            cell_type.update_button_gui()
        self.update_pointer_state_label()

    def init_celltype_gui_and_data(
        self,
        config: CellTypeConfigNotOptional,
        data: Optional[np.ndarray] = None,
    ) -> CellTypeGuiAndData:
        """
        Inits a cell type GUI and data by adding a layer to the viewer, and
        setting the name of the button, also binds the key
        """
        point_layer = self.viewer.add_points(
            data=data,
            ndim=3,
            name=config.name,
            edge_color=config.color,
            size=config.outline_size,
            out_of_slice_display=True,
            symbol=config.symbol,
            face_color=config.face_color,
            edge_width=config.edge_width,
        )
        point_layer.events.data.connect(self.handle_data_changed)
        btn = QPushButton()
        out = CellTypeGuiAndData(
            keybind=config.keybind,
            button=btn,
            layer=point_layer,
            gui_lock=self.gui_lock,
        )
        # set up event handler that changes state to this
        change_state_fun = NamedPartial(
            partial(self.change_state_to, out), config.name
        )
        if config.keybind:
            try:
                self.viewer.bind_key(key=config.keybind, func=change_state_fun)
            except ValueError:
                # probably key bind was already set
                out.keybind = ""
        btn.clicked.connect(change_state_fun)
        # update GUI when name changes
        point_layer.events.name.connect(self.update_gui)
        # update GUI when color changes
        point_layer.events.current_edge_color.connect(self.update_gui)
        # Update rest of the points when face_color, size, symbol, edge_width changes
        point_layer.events.current_face_color.connect(
            partial(out.update_attr, "face_color")
        )
        point_layer.events.current_size.connect(
            partial(out.update_attr, "size")
        )
        point_layer.events.current_edge_width.connect(
            partial(out.update_attr, "edge_width")
        )
        def update_symbol():
            if napari.__version__.split(".")[:3] == ["0", "4", "19"]:
                # see https://github.com/napari/napari/issues/6865
                print("Updating exising symbols is not supported in napari 0.4.19\n"
                      "This feature is availible in napari 0.4.18")
            else:
                out.update_attr("symbol")
        point_layer.events.current_symbol.connect(update_symbol)
        return out

    def change_state_to(self, state: CellTypeGuiAndData, *args, **kwargs):
        """
        Changes the state
        """
        # handler for qt events
        _ = args
        _ = kwargs
        self.pointer_type_state = state
        # no need to update the whole GUI
        self.update_pointer_state_label()

    def update_pointer_state_label(self):
        """
        Updates the color and text of the pointer_state_label
        """
        self.pointer_type_state_label.setText(
            self.pointer_type_state.layer.name
        )
        color = to_hex(self.pointer_type_state.layer.current_edge_color)
        text_color = get_text_color(color)
        style_sheet = (
            f"background-color: {color}; color: {text_color}; font-size: 20px"
        )
        self.pointer_type_state_label.setStyleSheet(style_sheet)

    def undo(self, *args, **kwargs):
        """
        undo the last written cell
        """
        # handler for qt events
        _ = args
        _ = kwargs
        if not self.undo_stack:
            print("No previous changes")
            return
        cell_type = self.undo_stack.pop()
        point_layer = cell_type.layer
        assert self.gui_lock.acquire(blocking=True)
        point_layer.data = point_layer.data[:-1]
        self.gui_lock.release()
        self.update_out_of_slice()
        # update button
        cell_type.update_button_gui()

    def config_in_python(self) -> str:
        """
        Creates a python string that when run,
        initiates napari
        """
        header = (
            "import napari\n"
            "from napari_3d_counter import Count3D, CellTypeConfig\n\n"
            "viewer = napari.viewer.Viewer()\n"
            "# set up cell types\n"
            "config = [\n"
        )
        config_lines = [
            f"    {repr(cell_type.get_calculated_config())},\n"
            for cell_type in self.cell_type_gui_and_data
        ]
        footer = (
            "]\n"
            "# make a new viewer\n"
            "viewer = napari.viewer.Viewer()\n"
            "# attach plugin to viewer\n"
            "viewer.window.add_dock_widget(Count3D(viewer, cell_type_config=config))"
        )
        return "".join([header] + config_lines + [footer])

    def gen_code_gui(self, *args, **kwargs):
        """
        does a dialog to save generated python to a file
        """
        # handles qt events
        _ = args
        _ = kwargs
        python_string = self.config_in_python()
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "launch_cell_count.py",
            "Python File(*.py);;File(*)",
            options=options,
        )
        if file_name:
            Path(file_name).write_text(python_string, "utf-8")

    def save_data_gui(self, *args, **kwargs):
        """
        does a dialog to save counts to csv
        """
        # handles qt events
        _ = args
        _ = kwargs
        data = self.save_points_to_df()
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "points.csv",
            "CSV Files(*.csv);;File(*)",
            options=options,
        )
        if file_name:
            data.to_csv(file_name, index=False)

    def load_data_gui(self, *args, **kwargs):
        """
        does a dialog to load counts from csv
        """
        # handles qt events
        _ = args
        _ = kwargs
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Save File",
            "points.csv",
            "CSV Files(*.csv);;File(*)",
            options=options,
        )
        if file_name:
            data = pd.read_csv(file_name)
            self.read_points_from_df(data)

    def save_points_to_df(self) -> pd.DataFrame:
        """
        Saves all points a data frame with the columns
            cell_type("str"), z(float), x(float), y(float)
        """
        partial_dfs: List[pd.DataFrame] = []
        for cell_type in self.cell_type_gui_and_data:
            partial_df = pd.DataFrame(
                cell_type.layer.data, columns=["z", "y", "x"]
            )
            partial_df.insert(0, "cell_type", cell_type.layer.name)
            partial_dfs.append(partial_df)
        out = pd.concat(partial_dfs)
        return out

    def read_points_from_df(self, data: pd.DataFrame):
        """
        reads all points a data frame with the columns
            cell_type("str"), z(float), x(float), y(float)
        """
        layer_names = np.unique(data["cell_type"])
        self.initial_config = process_cell_type_config(
            [ct.get_calculated_config() for ct in self.cell_type_gui_and_data]
            + [CellTypeConfig(name=name) for name in layer_names]
        )
        for config, layer_name in zip(
            self.initial_config[-len(layer_names) :], layer_names
        ):
            points = data.loc[data["cell_type"] == layer_name, ["z", "y", "x"]]
            cell_type = self.init_celltype_gui_and_data(config, data=points)
            self.cell_type_gui_and_data.append(cell_type)
            # put button right below the last one
            layout_index = self.layout().indexOf(
                self.cell_type_gui_and_data[-2].button
            )
            self.layout().insertWidget(layout_index + 1, cell_type.button)
        self.update_out_of_slice()
        self.update_gui()


# Uses the `autogenerate: true` flag in the plugin manifest
# to indicate it should be wrapped as a magicgui to autogenerate
# a widget.
def reconstruct_selected(
    labels_layer: napari.layers.labels.Labels,
    point_layer: napari.layers.points.Points,
    viewer: napari.viewer.Viewer,
) -> np.ndarray:
    """
    Reconstructs the layers in an image
    """
    name = point_layer.name
    reconstruction_data = np.zeros(labels_layer.data.shape).astype(np.int8)
    for point in point_layer.data:
        xcoord, ycoord, zcoord = point.astype(int)
        neuron_label = labels_layer.data[xcoord, ycoord, zcoord]
        if neuron_label == 0:
            print(
                f"skipping a point outside a lable at {[xcoord, ycoord, zcoord]}"
            )
            continue
        reconstruction_data[labels_layer.data == neuron_label] = 1
    viewer.add_image(
        reconstruction_data,
        name=f"{name} reconstruction",
        blending="additive",
        rendering="iso",
    )
    return reconstruction_data

"""
implements the counting interface and the reconstruction plugin
"""

from typing import Callable, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from functools import partial

from qtpy.QtWidgets import (
    QVBoxLayout,
    QPushButton,
    QWidget,
    QLabel,
    QFileDialog,
    QHBoxLayout,
)
import napari
from napari.utils.events import Event
import numpy as np
import pandas as pd
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


def get_text_color(background_color: str) -> str:
    """
    returns black or white as hex string 
    depending on what works better with the backround
    """
    # same function as dinstinctipy
    red, green, blue, _ = to_rgba_array(background_color)[0]
    return "#ffffff" if (red * 0.299 + green * 0.587 + blue * 0.114) < 0.6 else "#000000"


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

    def update_button_gui(self):
        """
        Updates the button with current name, and nubmer of cells
        """
        # update the button
        if self.keybind:
            keybind_str = f" ({self.keybind})"
        else:
            keybind_str = ""
        button_text = (
            f"[{self.layer.data.shape[0]}] {self.layer.name}" + keybind_str
        )
        self.button.setText(button_text)
        color = to_hex(self.layer.current_edge_color)
        style_sheet = f"background-color: {color}; color: {get_text_color(color)}"
        self.button.setStyleSheet(style_sheet)
        # updates all edge_colors to current_edge_color
        current_color = to_rgba_array(self.layer.current_edge_color)
        n_edge_colors = self.layer.edge_color.shape[0]
        if n_edge_colors:
            self.layer.edge_color = np.vstack([current_color] * n_edge_colors)

    def get_calculated_config(self) -> CellTypeConfig:
        """
        returns the current configuration of the channel
        """
        return CellTypeConfig(
            name=self.layer.name,
            color=to_hex(self.layer.current_edge_color, keep_alpha=True),
            keybind=self.keybind,
        )

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
        if len(cell_type_config) == 0:
            print(
                "Cannot initialize with no cell types. Using default cell types"
            )
            cell_type_config = DEFUALT_CONFIG
        self.initial_config = process_cell_type_config(cell_type_config)
        self.viewer = napari_viewer
        self.undo_stack: List[CellTypeGuiAndData] = []
        self.currently_adding_point = False
        # add out of slice markers
        self.out_of_slice_points = self.viewer.add_points(
            ndim=2, size=2, name="out of slice"
        )
        # set up cell type points layers
        self.cell_type_gui_and_data = [
            self.init_celltype_gui_and_data(state)
            for state in self.initial_config
        ]
        # initalize the pointer points
        self.pointer = self.viewer.add_points(ndim=3, name="Point adder")
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
        # save and load
        row_layout = QHBoxLayout()
        save_button = QPushButton("save cells")
        save_button.clicked.connect(self.save_data_gui)
        row_layout.addWidget(save_button)
        save_button = QPushButton("load cells")
        save_button.clicked.connect(self.load_data_gui)
        row_layout.addWidget(save_button)
        self.layout().addLayout(row_layout)

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
        current_cell_type.update_button_gui()

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
                self.viewer.bind_key(key=config.keybind, func=change_state_fun)
            except ValueError:
                # probably keybind was already set
                out.keybind = ""
        btn.clicked.connect(change_state_fun)
        # update button when name changes
        point_layer.events.name.connect(out.update_button_gui)
        # update color when color changes
        point_layer.events.current_edge_color.connect(
            self.update_gui
        )
        out.update_button_gui()
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
        cell_type.update_button_gui()

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
        config_lines = [
            f"    {cell_type.config_python_code()},\n"
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

    def gen_code_gui(self, *args):
        """
        does a dialog to save generated python to a file
        """
        _ = args
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
            Path(file_name).write_text(python_string)

    def save_data_gui(self, *args):
        """
        does a dialog to save counts to csv
        """
        _ = args
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

    def load_data_gui(self, *args):
        """
        does a dialog to load counts from csv
        """
        _ = args
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
                cell_type.layer.data, columns=["z", "x", "y"]
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
            points = data.loc[data["cell_type"] == layer_name, ["z", "x", "y"]]
            cell_type = self.init_celltype_gui_and_data(config, data=points)
            self.cell_type_gui_and_data.append(cell_type)
            # put button right below the last one
            layout_index = self.layout().indexOf(
                self.cell_type_gui_and_data[-2].button
            )
            self.layout().insertWidget(layout_index + 1, cell_type.button)
        self.update_out_of_slice()

    def update_gui(self, *args, **kwargs):
        """
        Updates button color and button text
        """
        _ = args
        _ = kwargs
        for cell_type in self.cell_type_gui_and_data:
            cell_type.update_button_gui()



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

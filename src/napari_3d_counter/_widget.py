"""
implements the counting interface and the reconstruction plugin
"""

from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import List, Optional, Literal
from threading import Lock
from typing import TYPE_CHECKING


import napari
from napari.layers import Points, Labels, Image, Shapes
from napari.utils._proxies import PublicOnlyProxy
import numpy as np
import pandas as pd
from napari.utils.events import Event
from napari.utils.color import ColorValue
from napari.qt.threading import create_worker
from qtpy.QtCore import Qt  # type: ignore
from qtpy.QtWidgets import (  # pylint: disable=no-name-in-module
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
)

from .celltype_config import (
    CellTypeConfig,
    CellTypeConfigNotOptional,
    process_cell_type_config,
    to_hex,
)
from .aux_functions import _reconstruct_selected, split_on_shapes

DEFUALT_CONFIG = [
    CellTypeConfig(keybind="q", name="Cell type 1", color="g"),
    CellTypeConfig(keybind="w", name="Cell type 2", color="r"),
    CellTypeConfig(keybind="e", name="Cell type 3", color="c"),
    CellTypeConfig(keybind="r", name="Cell type 4", color="m"),
]


def _create_summary_table(data: pd.DataFrame) -> pd.DataFrame:
    """
    creates a summary table with columns "CellType", "Shape", "count"
    """
    out = data.groupby(["name", "shape_idx"]).count()["x"].reset_index()
    out.columns = ["CellType", "Shape", "count"]
    return out


def get_n3d_counter(viewer: "napari.Viewer") -> "Count3D":
    """
    Gets Count3D if it exists else adds it as a dock widget
    """
    # napari 0.6.2 only
    try:
        c3d = next(
            w
            for w in viewer.window.dock_widgets.values()
            if isinstance(w, Count3D)
        )
    except StopIteration:
        _, c3d = viewer.window.add_plugin_dock_widget(
            "napari-3d-counter", "Count 3D"
        )
    return c3d


def get_text_color(background_color: str) -> str:
    """
    returns black or white as hex string
    depending on what works better with the background
    """
    # same function as dinstinctipy
    white = "#ffffff"
    black = "#000000"
    red, green, blue, _ = ColorValue(background_color)
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
    layer: Points
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
        color = to_hex(ColorValue(self.layer.current_border_color)[:-1])
        text_color = get_text_color(color)
        # hover_color is half way between text color and background color
        hover_color_rgb = (ColorValue(text_color) + ColorValue(color))[:-1] / 2
        style_sheet = (
            f"QPushButton{{background-color: {color}; color: {text_color};}}"
            f"QPushButton:hover{{background-color: {to_hex(hover_color_rgb)}}}"
        )
        self.button.setStyleSheet(style_sheet)
        # updates all border_colors to current_border_color
        current_color = ColorValue(self.layer.current_border_color)
        n_border_colors = self.layer.border_color.shape[0]
        if n_border_colors:
            self.layer.border_color = np.vstack(
                [current_color] * n_border_colors
            )

    def update_attr(
        self, attr: Literal["symbol", "size", "face_color", "border_width"]
    ):
        """
        updates the size of the cell to the current size
        """
        current = getattr(self.layer, f"current_{attr}")
        n_points = self.layer.data.shape[0]
        if isinstance(current, PublicOnlyProxy):
            current = current.value
        setattr(self.layer, attr, np.array([current] * n_points))

    def get_calculated_config(
        self, out_of_slice_points_size: float
    ) -> CellTypeConfig:
        """
        returns the current configuration of the channel
        """

        # sometimes current size is a numpy array of 1
        current_size = self.layer.current_size
        if isinstance(current_size, np.ndarray):
            current_size = current_size.ravel()[0]
        # sometimes edge_width is a numpy array of 1
        edge_width = self.layer.current_border_width
        if isinstance(edge_width, np.ndarray):
            edge_width = edge_width.ravel()[0]

        return CellTypeConfig(
            name=self.layer.name,
            out_of_slice_point_size=out_of_slice_points_size,
            color=to_hex(ColorValue(self.layer.current_border_color)),
            keybind=self.keybind,
            symbol=self.layer.current_symbol.value,  # type: ignore
            outline_size=current_size,
            face_color=self.layer.current_face_color,
            edge_width=edge_width,
        )


class Count3D(QWidget):  # pylint: disable=R0902
    """
    Main interface for counting cells
    """

    def __init__(
        self,
        napari_viewer: napari.Viewer,
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
        """initial because it doesn't take into account gui changes"""
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

        def update_out_of_slice_size():
            current = self.out_of_slice_points.current_size
            n_points = self.out_of_slice_points.data.shape[0]
            self.out_of_slice_points.size = np.array([current] * n_points)

        self.out_of_slice_points.events.current_size.connect(
            update_out_of_slice_size
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
        self.viewer.bind_key(key_bind="u", func=self.undo, overwrite=True)
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
        self.pointer.data = np.array([])
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
            border_color=config.color,
            size=config.outline_size,
            out_of_slice_display=True,
            symbol=config.symbol,
            face_color=config.face_color,
            border_width=config.edge_width,
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
                self.viewer.bind_key(
                    key_bind=config.keybind, func=change_state_fun
                )
            except ValueError:
                # probably key bind was already set
                out.keybind = ""
        btn.clicked.connect(change_state_fun)
        # update GUI when name changes
        point_layer.events.name.connect(self.update_gui)
        # update GUI when color changes
        point_layer.events.current_border_color.connect(self.update_gui)
        # Update rest of the points when face_color, size, symbol, border_width changes
        point_layer.events.current_face_color.connect(
            partial(out.update_attr, "face_color")
        )
        point_layer.events.current_size.connect(
            partial(out.update_attr, "size")
        )
        point_layer.events.current_symbol.connect(
            partial(out.update_attr, "symbol")
        )
        point_layer.events.current_border_width.connect(
            partial(out.update_attr, "border_width")
        )

        def update_symbol():
            if napari.__version__.split(".")[:3] == ["0", "4", "19"]:
                # see https://github.com/napari/napari/issues/6865
                print(
                    "Updating exising symbols is not supported in napari 0.4.19\n"
                    "This feature is availible in napari 0.4.18"
                )
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
        color = to_hex(
            ColorValue(self.pointer_type_state.layer.current_border_color)[:-1]
        )
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
            "# set up cell types\n"
            "config = [\n"
        )
        out_of_slice_points_size = self.out_of_slice_points.current_size
        config_lines = [
            f"    {repr(cell_type.get_calculated_config(out_of_slice_points_size))},\n"
            for cell_type in self.cell_type_gui_and_data
        ]
        footer = (
            "]\n"
            "# make a new viewer\n"
            "viewer = napari.Viewer()\n"
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
        # if layer name is used and empty move over the data to that one
        layers = {
            ct.layer.name: ct.layer for ct in self.cell_type_gui_and_data
        }
        duplicate_layers = layer_names[
            np.isin(layer_names, list(layers.keys()))
        ]
        for layer_name in duplicate_layers:
            if len(layers[layer_name].data) == 0:
                # remove that layer from layer_names to add
                layer_names = layer_names[layer_names != layer_name]
                # tranfer the layer over
                points = data.loc[
                    data["cell_type"] == layer_name, ["z", "y", "x"]
                ]
                layers[layer_name].data = points
        self.initial_config = process_cell_type_config(
            [
                ct.get_calculated_config(self.out_of_slice_points.current_size)
                for ct in self.cell_type_gui_and_data
            ]
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


def reset_box(box: QComboBox, values: list[str]):
    """
    resets a combo box to a new set of values
    """
    old_value = box.currentText()
    box.clear()
    # avoid repeat labels
    box.addItems(list(dict.fromkeys(values)))
    if old_value in values:
        box.setCurrentText(old_value)


class ReconstructSelected(QWidget):
    """
    Interface for reconstructing labels into an image based on cell counts
    """

    def __init__(
        self,
        napari_viewer: napari.Viewer,
    ):
        super().__init__()
        self.viewer = napari_viewer
        # initialize qt GUI
        self.setLayout(QVBoxLayout())
        self.points_box: QComboBox = QComboBox()
        self.layout().addWidget(self.points_box)
        self.labels_box: QComboBox = QComboBox()
        self.layout().addWidget(self.labels_box)
        self.run_button = QPushButton("Reconstruct Selected")
        self.run_button.clicked.connect(self.run)
        self.layout().addWidget(self.run_button)
        self.resetting_lock = Lock()
        # viewer callbacks
        napari_viewer.layers.events.inserted.connect(self.reset_boxes)
        napari_viewer.layers.events.removed.connect(self.reset_boxes)
        self.reset_boxes(None)
        self.output_layer: Image | None = None

    def reset_boxes(self, event):
        """
        A callback when the layers are changed. make sure that all of the boxes
        have valid layer names and that the run button is only enabled
        """
        _ = event
        if self.resetting_lock.locked():
            return
        assert self.resetting_lock.acquire(blocking=False)
        c3d = get_n3d_counter(self.viewer)
        self.resetting_lock.release()
        reset_box(
            self.points_box,
            [l.layer.name for l in c3d.cell_type_gui_and_data],
        )
        reset_box(
            self.labels_box,
            [l.name for l in self.viewer.layers if isinstance(l, Labels)],
        )
        if bool(
            self.points_box.currentText() and self.labels_box.currentText()
        ):
            self.run_button.setDisabled(False)
        else:
            self.run_button.setDisabled(True)

    def process_output(self, reconstruct_selected_out: dict):
        """
        A callback for after processing worker completes
        resets button state, adds the image layer and updates the widget object
        to reflect the new layer
        """
        self.run_button.setEnabled(True)
        self.run_button.setChecked(False)
        if not reconstruct_selected_out:
            return
        out = self.viewer.add_image(**reconstruct_selected_out)
        assert isinstance(out, Image)
        self.output_layer = out

    def run(self, *args, **kwargs):
        """
        callback for run button
        Starts a reconstruct selected worker
        """
        _ = args
        _ = kwargs
        point_layer = self.viewer.layers[self.points_box.currentText()]
        labels_layer = self.viewer.layers[self.labels_box.currentText()]
        self.run_button.setChecked(True)
        self.run_button.setEnabled(False)
        worker = create_worker(
            _reconstruct_selected, point_layer, labels_layer
        )
        worker.returned.connect(self.process_output)
        worker.start()


class IngressPoints(QWidget):
    """
    Interface for ingressing points
    """

    def __init__(
        self,
        napari_viewer: napari.Viewer,
    ):
        super().__init__()
        self.viewer = napari_viewer
        # initialize qt GUI
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(QLabel("from:"))
        self.points_box: QComboBox = QComboBox()
        self.layout().addWidget(self.points_box)
        self.layout().addWidget(QLabel("to:"))
        self.cell_type_box: QComboBox = QComboBox()
        self.layout().addWidget(self.cell_type_box)
        self.run_button = QPushButton("Ingress Points")
        self.run_button.clicked.connect(self.run)
        # needed to keep it pushed while long running task runs in worker thread
        self.run_button.setCheckable(True)
        self.layout().addWidget(self.run_button)
        self.resetting_lock = Lock()
        # viewer callbacks
        napari_viewer.layers.events.inserted.connect(self.reset_boxes)
        napari_viewer.layers.events.removed.connect(self.reset_boxes)
        self.reset_boxes(None)

    def reset_boxes(self, event):
        """
        A callback when the layers are changed. make sure that all of the boxes
        have valid layer names and that the run button is only enabled
        """
        _ = event
        if self.resetting_lock.locked():
            return
        assert self.resetting_lock.acquire(blocking=False)
        c3d = get_n3d_counter(self.viewer)
        self.resetting_lock.release()
        possible_celltype_boxes = [
            l.layer.name for l in c3d.cell_type_gui_and_data
        ]
        n3d_counter_names = possible_celltype_boxes + [
            c3d.out_of_slice_points.name,
            c3d.pointer.name,
        ]
        reset_box(
            self.cell_type_box,
            possible_celltype_boxes,
        )
        reset_box(
            self.points_box,
            [
                l.name
                for l in self.viewer.layers
                if isinstance(l, Points) and l.name not in n3d_counter_names
            ],
        )
        if bool(
            self.points_box.currentText() and self.cell_type_box.currentText()
        ):
            self.run_button.setDisabled(False)
        else:
            self.run_button.setDisabled(True)

    def run(self, *args, **kwargs):
        """
        Callback for run button
        Main function to ingress points
        """
        _ = args
        _ = kwargs
        point_layer = self.viewer.layers[self.points_box.currentText()]
        cell_type_layer = self.viewer.layers[self.cell_type_box.currentText()]
        if TYPE_CHECKING:
            assert isinstance(cell_type_layer, Points)
        coordinates = np.array(
            [
                cell_type_layer.world_to_data(point_layer.data_to_world(d))
                for d in point_layer.data
            ]
        )
        [cell_type_layer.add(c) for c in coordinates]


class SplitOnShapes(QWidget):
    """
    Interface for spliting cell counts by what shape they are in
    """

    def __init__(
        self,
        napari_viewer: napari.Viewer,
    ):
        super().__init__()
        self.viewer = napari_viewer
        # initialize qt GUI
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(QLabel("Shapes layer:"))
        self.shapes_box: QComboBox = QComboBox()
        self.layout().addWidget(self.shapes_box)
        self.tbl = QTableWidget()
        self.tbl.setSelectionBehavior(self.tbl.SelectItems)
        self.tbl.setSelectionMode(self.tbl.ExtendedSelection)
        self.layout().addWidget(self.tbl)
        self.run_button = QPushButton("Split on Shapes")
        self.run_button.clicked.connect(self.run)
        # needed to keep it pushed while long running task runs in worker thread
        self.run_button.setCheckable(True)
        self.layout().addWidget(self.run_button)
        row_layout = QHBoxLayout()
        save_summary_button = QPushButton("Save Summary")
        save_summary_button.clicked.connect(self.save_summary)
        row_layout.addWidget(save_summary_button)
        save_points = QPushButton("Save cells")
        save_points.clicked.connect(self.save_points)
        row_layout.addWidget(save_points)
        self.layout().addLayout(row_layout)
        self.resetting_lock = Lock()
        self.df: pd.DataFrame | None = None
        # viewer callbacks
        napari_viewer.layers.events.inserted.connect(self.reset_boxes)
        napari_viewer.layers.events.removed.connect(self.reset_boxes)
        self.reset_boxes(None)
        self.update_table(None)
        self.run_button.setEnabled(False)

    def reset_boxes(self, event):
        """
        A callback when the layers are changed. make sure that all of the boxes
        have valid layer names and that the run button is only enabled
        """
        _ = event
        if self.resetting_lock.locked():
            return
        assert self.resetting_lock.acquire(blocking=False)
        self.resetting_lock.release()
        reset_box(
            self.shapes_box,
            [l.name for l in self.viewer.layers if isinstance(l, Shapes)],
        )
        if self.shapes_box.currentText():
            self.run_button.setDisabled(False)
        else:
            self.run_button.setDisabled(True)

    def save_summary(self):
        """
        Launches a GUI to save the summary file
        """
        df = self.df
        if df is None:
            print('Error: run "Split on Shapes" firt')
            return
        summary = _create_summary_table(df)
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "summary.csv",
            "CSV Files(*.csv);;File(*)",
            options=options,
        )
        if file_name:
            summary.to_csv(file_name, index=False)

    def _get_points_df(self) -> pd.DataFrame | None:
        """
        Converts the internal df to one that can be read by Count 3D
        """
        if self.df is None:
            print('Error: run "Split on Shapes" firt')
            return
        out = pd.DataFrame(self.df[["z", "y", "x"]])
        out.insert(0, "cell_type", out.index)
        out.index = range(len(out))
        return out

    def save_points(self):
        """
        Launches a GUI to save points in a way that can be read by Count 3D
        such that each shape * cell type becomes an individual cell type
        """
        points_df = self.get_points_df()
        if points_df is None:
            return
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "shape_segmented_points.csv",
            "CSV Files(*.csv);;File(*)",
            options=options,
        )
        if file_name:
            points_df.to_csv(file_name, index=False)

    def update_table(self, data: pd.DataFrame | None):
        """
        Callback for aux_functions split_on_shapes
        Updates the GUI table from a pandas DataFrame. self.df is also updated to be update_table.
        """
        self.df = data
        if data is None:
            data = pd.DataFrame(
                np.nan, columns=["CellType", "Shape", "count"], index=range(0)
            )
        else:
            data = _create_summary_table(data)
        self.tbl.setRowCount(len(data))
        self.tbl.setColumnCount(len(data.columns))
        self.tbl.setHorizontalHeaderLabels(data.columns.astype(str).tolist())
        for row in range(len(data)):
            for col in range(len(data.columns)):
                val = str(data.iat[row, col])
                self.tbl.setItem(row, col, QTableWidgetItem(val))
        self.tbl.setSortingEnabled(True)
        self.tbl.resizeColumnsToContents()
        self.run_button.setEnabled(True)
        self.run_button.setChecked(False)

    def run(self, *args, **kwargs):
        """
        Callback for run buttion
        starts a worker for split_on_shapes
        """
        _ = args
        _ = kwargs
        shapes_layer = self.viewer.layers[self.shapes_box.currentText()]
        c3d = get_n3d_counter(self.viewer)
        celltypes = [l.layer for l in c3d.cell_type_gui_and_data]
        self.run_button.setChecked(True)
        self.run_button.setEnabled(False)
        worker = create_worker(split_on_shapes, celltypes, shapes_layer)
        worker.returned.connect(self.update_table)
        worker.start()

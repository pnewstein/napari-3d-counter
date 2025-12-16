"""
Contains the plugin to read csv files
"""

from typing import Union, Sequence, Callable, List, Optional
from warnings import warn

from napari.types import LayerData
import napari
import pandas as pd
import numpy as np
from ._widget import CellTypeConfig, Count3D

PathLike = str
PathOrPaths = Union[PathLike, Sequence[PathLike]]
ReaderFunction = Callable[[PathOrPaths], List[LayerData]]


def get_reader(path: "PathOrPaths") -> Optional["ReaderFunction"]:
    # If we recognize the format, we return the actual reader function
    if isinstance(path, str) and path.endswith(".csv"):
        with open(path, "r") as file:
            first_line = file.readline()
        if first_line == "cell_type,z,y,x\n":
            return csv_file_reader
    warn(
        "Invalid CSV file. Use one created by the Save Cells button in Count3D"
    )
    return None


def csv_file_reader(path: "PathOrPaths") -> List[tuple[None]]:
    data = pd.read_csv(path)
    labels = np.unique(data["cell_type"])
    viewer = napari.current_viewer()
    if viewer is None:
        raise RuntimeError("Could not access viewer")
    try:
        c3d = next(
            w
            for w in viewer.window.dock_widgets.values()
            if isinstance(w, Count3D)
        )
    except StopIteration:
        c3d = Count3D(viewer, [CellTypeConfig(name=n) for n in labels])
        viewer.window.add_dock_widget(c3d)
    # add all of the points
    c3d.read_points_from_df(data)
    return [(None,)]

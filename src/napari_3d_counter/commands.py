"""
register commands for the command pallette
"""

from typing import TYPE_CHECKING

import napari
from ._widget import get_n3d_counter


def save(viewer: "napari.Viewer"):
    c3d = get_n3d_counter(viewer)
    c3d.save_data_gui()


def load(viewer: "napari.Viewer"):
    c3d = get_n3d_counter(viewer)
    c3d.load_data_gui()


def next_cell_type(viewer: "napari.Viewer"):
    c3d = get_n3d_counter(viewer)
    current_index = c3d.cell_type_gui_and_data.index(c3d.pointer_type_state)
    next_index = (current_index + 1) % len(c3d.cell_type_gui_and_data)
    c3d.change_state_to(c3d.cell_type_gui_and_data[next_index])


def prev_cell_type(viewer: "napari.Viewer"):
    c3d = get_n3d_counter(viewer)
    current_index = c3d.cell_type_gui_and_data.index(c3d.pointer_type_state)
    next_index = (current_index - 1) % len(c3d.cell_type_gui_and_data)
    c3d.change_state_to(c3d.cell_type_gui_and_data[next_index])

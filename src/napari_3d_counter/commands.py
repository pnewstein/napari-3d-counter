"""
register commands for the command pallette
"""

from . import Count3D
import napari


def get_n3d_counter(viewer: "napari.Viewer") -> Count3D:
    """
    Gets Count3D if it exists else adds it as a dock widget
    """
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

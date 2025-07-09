"""
Tests the regestered command
"""

from napari_3d_counter import commands as cmd


def test_get_n3d_counter(make_napari_viewer):
    viewer = make_napari_viewer()
    c3d = cmd.get_n3d_counter(viewer)
    c3d2 = cmd.get_n3d_counter(viewer)
    assert c3d is c3d2


def test_next_cell_type(make_napari_viewer):
    viewer = make_napari_viewer()
    c3d = cmd.get_n3d_counter(viewer)
    assert len(c3d.cell_type_gui_and_data) == 4
    assert c3d.pointer_type_state == c3d.cell_type_gui_and_data[0]
    cmd.next_cell_type(viewer)
    assert c3d.pointer_type_state == c3d.cell_type_gui_and_data[1]
    cmd.next_cell_type(viewer)
    assert c3d.pointer_type_state == c3d.cell_type_gui_and_data[2]
    cmd.next_cell_type(viewer)
    assert c3d.pointer_type_state == c3d.cell_type_gui_and_data[3]
    cmd.next_cell_type(viewer)
    assert c3d.pointer_type_state == c3d.cell_type_gui_and_data[0]


def test_prev_cell_type(make_napari_viewer):
    viewer = make_napari_viewer()
    c3d = cmd.get_n3d_counter(viewer)
    assert len(c3d.cell_type_gui_and_data) == 4
    assert c3d.pointer_type_state == c3d.cell_type_gui_and_data[0]
    cmd.prev_cell_type(viewer)
    assert c3d.pointer_type_state == c3d.cell_type_gui_and_data[3]
    cmd.prev_cell_type(viewer)
    assert c3d.pointer_type_state == c3d.cell_type_gui_and_data[2]
    cmd.prev_cell_type(viewer)
    assert c3d.pointer_type_state == c3d.cell_type_gui_and_data[1]
    cmd.prev_cell_type(viewer)
    assert c3d.pointer_type_state == c3d.cell_type_gui_and_data[0]

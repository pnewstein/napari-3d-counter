"""
tests configuration of celltypes through python
"""

import pytest

from napari_3d_counter import celltype_config as cc
from napari_3d_counter import Count3D


def test_fewer_colors():
    ctc = [cc.CellTypeConfig()] * 3
    out = cc.process_cell_type_config(ctc)
    assert [c.color for c in out] == cc.DEFAULT_COLOR_SEQUENCE[:3]
    print(out)


def test_more_colors():
    ctc = [cc.CellTypeConfig()] * (len(cc.DEFAULT_COLOR_SEQUENCE) + 1)
    out = cc.process_cell_type_config(ctc)
    assert [c.color for c in out] == cc.DEFAULT_COLOR_SEQUENCE + [
        cc.DEFAULT_COLOR_SEQUENCE[-1]
    ]


def test_specified_default():
    requests = [None, cc.DEFAULT_COLOR_SEQUENCE[0], None]
    out = cc.fill_in_defaults(requests, cc.DEFAULT_COLOR_SEQUENCE)
    assert out == [
        cc.DEFAULT_COLOR_SEQUENCE[1],
        cc.DEFAULT_COLOR_SEQUENCE[0],
        cc.DEFAULT_COLOR_SEQUENCE[2],
    ]


def test_name_conflict():
    ctc = [
        cc.CellTypeConfig("Cell1"),
        cc.CellTypeConfig(
            "Cell1",
        ),
    ]
    out = cc.process_cell_type_config(ctc)
    print(out)
    assert out[-1].name == "Cell1 [1]"


def test_process_cell_type_config():
    ctc = [
        cc.CellTypeConfig(),
        cc.CellTypeConfig(
            "Cell1",
            cc.DEFAULT_COLOR_SEQUENCE[0],
            cc.DEFAULT_KEYMAP_SEQUENCE[0],
        ),
    ]
    out = cc.process_cell_type_config(ctc)
    expected = [
        cc.CellTypeConfigNotOptional(
            keybind=cc.DEFAULT_KEYMAP_SEQUENCE[1],
            name="Celltype 1",
            color=cc.DEFAULT_COLOR_SEQUENCE[1],
            outline_size=cc.DEFAULT_OUTLINE_SIZE,
            out_of_slice_point_size=cc.DEFAULT_OUT_OF_SLICE_SIZE,
            face_color=cc.DEFAULT_FACE_COLOR,
            symbol=cc.DEFAULT_SYMBOL,
            edge_width=cc.DEFAULT_EDGE_WIDTH,
        ),
        cc.CellTypeConfigNotOptional(
            keybind=cc.DEFAULT_KEYMAP_SEQUENCE[0],
            name="Cell1",
            color=cc.DEFAULT_COLOR_SEQUENCE[0],
            outline_size=cc.DEFAULT_OUTLINE_SIZE,
            out_of_slice_point_size=cc.DEFAULT_OUT_OF_SLICE_SIZE,
            face_color=cc.DEFAULT_FACE_COLOR,
            symbol=cc.DEFAULT_SYMBOL,
            edge_width=cc.DEFAULT_EDGE_WIDTH,
        ),
    ]
    assert out == expected


def test_mismatch():
    ctc = [
        cc.CellTypeConfig(out_of_slice_point_size=100),
        cc.CellTypeConfig(out_of_slice_point_size=10),
    ]
    with pytest.raises(ValueError):
        cc.process_cell_type_config(ctc)


@pytest.fixture
def viewer(make_napari_viewer):
    return make_napari_viewer()


def test_seting_name(viewer):
    test_feat = "test_name"
    ctc = [cc.CellTypeConfig(name=test_feat)]
    widget = Count3D(viewer, ctc)
    layer = widget.cell_type_gui_and_data[0].layer
    assert layer.name == test_feat


def test_seting_color(viewer):
    test_feat = "#12345678"
    ctc = [cc.CellTypeConfig(color=test_feat)]
    widget = Count3D(viewer, ctc)
    layer = widget.cell_type_gui_and_data[0].layer
    assert layer.current_edge_color == test_feat


def test_seting_outline_size(viewer):
    test_feat = 100
    ctc = [cc.CellTypeConfig(outline_size=test_feat)]
    widget = Count3D(viewer, ctc)
    layer = widget.cell_type_gui_and_data[0].layer
    assert layer.current_size == test_feat


def test_seting_face_color(viewer):
    test_feat = "#12345678"
    ctc = [cc.CellTypeConfig(face_color=test_feat)]
    widget = Count3D(viewer, ctc)
    layer = widget.cell_type_gui_and_data[0].layer
    assert layer.current_face_color == test_feat


def test_seting_symbol(viewer):
    test_feat = "x"
    ctc = [cc.CellTypeConfig(symbol=test_feat)]
    widget = Count3D(viewer, ctc)
    layer = widget.cell_type_gui_and_data[0].layer
    assert layer.current_symbol == test_feat


def test_seting_edge_width(viewer):
    test_feat = 0.8
    ctc = [cc.CellTypeConfig(edge_width=test_feat)]
    widget = Count3D(viewer, ctc)
    layer = widget.cell_type_gui_and_data[0].layer
    assert layer.current_edge_width == test_feat


if __name__ == "__main__":
    test_mismatch()

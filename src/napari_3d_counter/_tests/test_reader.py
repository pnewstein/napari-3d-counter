import napari
from napari_3d_counter._widget import get_n3d_counter
import pytest

from pathlib import Path

HERE = Path(__file__).parent


def test_launch_count_3d(make_napari_viewer):
    viewer: napari.Viewer = make_napari_viewer()
    viewer.open(HERE / "test_point.csv", plugin="napari-3d-counter")
    c3d = get_n3d_counter(viewer)
    df = c3d.save_points_to_df()
    assert len(df) == 3



def test_ignores_bad_csv(make_napari_viewer):
    viewer: napari.Viewer = make_napari_viewer()
    with pytest.raises(ValueError):
        viewer.open(HERE / "bad.csv", plugin="napari-3d-counter")


@pytest.mark.skip(reason="wait for #24")
def test_chooses_right_viewer_first(make_napari_viewer):
    v1 = make_napari_viewer()
    v2 = make_napari_viewer()
    v1.open(HERE / "test_point.csv", plugin="napari-3d-counter")
    c3d1 = get_n3d_counter(v1)
    df1 = c3d1.save_points_to_df()
    assert len(df1) == 3
    c3d2 = get_n3d_counter(v2)
    df2 = c3d2.save_points_to_df()
    assert len(df2) == 0


def test_attach_to_current_c3d(make_napari_viewer):
    viewer: napari.Viewer = make_napari_viewer()
    c3d = get_n3d_counter(viewer)
    df = c3d.save_points_to_df()
    assert len(df) == 0
    viewer.open(HERE / "test_point.csv", plugin="napari-3d-counter")
    df = c3d.save_points_to_df()
    assert len(df) == 3


def test_empty_csv(make_napari_viewer):
    viewer: napari.Viewer = make_napari_viewer()
    viewer.open(HERE / "test_empty.csv", plugin="napari-3d-counter")
    c3d = get_n3d_counter(viewer)
    df = c3d.save_points_to_df()
    assert len(df) == 0

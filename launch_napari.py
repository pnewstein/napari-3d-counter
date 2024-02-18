import napari

viewer = napari.viewer.Viewer()

from napari_3d_counter import CellTypeConfig, Count3D

cell_type_config = [
    CellTypeConfig(name="cq+eve+", color="g"),
    CellTypeConfig(name="cq+eve-", color="c"),
    CellTypeConfig(name="cq-eve+", color="r"),
]
viewer.window.add_dock_widget(
    Count3D(viewer, cell_type_config=cell_type_config)
)
# viewer.add_image(img, channel_axis=1)
napari.run()

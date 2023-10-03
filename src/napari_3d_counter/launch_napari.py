import napari
import napari_3d_counter

viewer = napari.viewer.Viewer()
viewer.window.add_dock_widget(napari_3d_counter.Count3D(viewer))
# viewer.add_image(img, channel_axis=1)

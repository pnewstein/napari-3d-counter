# Napari-3D-Counter

[![License GNU GPL v3.0](https://img.shields.io/pypi/l/napari-3d-counter.svg?color=green)](https://github.com/pnewstein/napari-3d-counter/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-3d-counter.svg?color=green)](https://pypi.org/project/napari-3d-counter)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-3d-counter.svg?color=green)](https://python.org)
[![tests](https://github.com/pnewstein/napari-3d-counter/workflows/tests/badge.svg)](https://github.com/pnewstein/napari-3d-counter/actions)
[![codecov](https://codecov.io/gh/pnewstein/napari-3d-counter/branch/main/graph/badge.svg)](https://codecov.io/gh/pnewstein/napari-3d-counter)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/napari-3d-counter)](https://napari-hub.org/plugins/napari-3d-counter)

A plugin for manually counting objects in 3D images

![small](https://github.com/pnewstein/napari-3d-counter/assets/30813691/9d524c31-f23b-4b34-bcb6-ec3bb415cdae)

----------------------------------

This [napari] plugin was generated with [Cookiecutter] using [@napari]'s [cookiecutter-napari-plugin] template.

## Prerequisites

It is recommended to use conda to install Napari-3D-Counter and napari.
Installation instructions for the miniconda distribution of conda can be found here: 

[https://www.anaconda.com/docs/getting-started/miniconda/install](https://www.anaconda.com/docs/getting-started/miniconda/install)



## Installation


You can install `napari-3d-counter` via conda
    
    conda create -n n3dc-env -c conda-forge -y napari napari-3d-counter pyqt
    conda activate n3dc-env


or pip

    pip install napari-3d-counter


##  Count3D Usage

1. First launch napari with the `napari` command.
1. Count3D can be launched from the plugin menu of napari, or through the
   command palette (Ctrl+Shift+P). Select Count3D.

This will spawn several [Points Layers](https://napari.org/stable/howtos/layers/points.html):

##### Point adder

This layer acts as the interface for napari-3d-counter. Any points added to
this layer are dispatched into the appropriate data layer labeled by the GUI.
*Any other actions to this layer has no effects*

##### Cell Type N

These are the data layers. The points actually live in these layers,
and you can edit the style or delete individual points here.

##### out of slice

This contains the x and y of all points in all layers. This may be
useful to keep track of what regions of the data have been annotated.

### Adding a cell

You can add a cell of the currently selected cell type by clicking on the
viewer. The counter on the current cell type's button (on the right side of the
screen) will be incremented.

<details>

<summary>Troubleshooting</summary>

- Ensure that `Point adder` layer is selected
- Ensure that `Add points` tool is selected
- Click on the viewer where you would like the point to be added

</details>


https://github.com/pnewstein/napari-3d-counter/assets/30813691/745d495e-1d18-43dd-aa5e-e9ecd835cdae


### Changing cell type

You can change the currently selected cell type by clicking on that cell type's
button. This change will be reflected in the GUI. Additionally, the keyboard
shortcut for that cell type can be used. Keyboard shortcuts are listed on the
button, and are "q", "w", "e", "r", "t", "y" by default


https://github.com/pnewstein/napari-3d-counter/assets/30813691/844d04ce-2795-4226-a98b-d5fe5a0b131e


### Undo last added cell

The undo button (shortcut u) will remove last added cell, regardless of
cell type


https://github.com/pnewstein/napari-3d-counter/assets/30813691/c04ca5e3-9f48-4dd5-89e5-a9866b353e03


### Remove a particular cell

To remove a particular cell, change to the layer containing the cell you would
like to remove. Then select the `select points` tool to select the points to
delete, then use `Delete selected points` to delete those points

This change will be reflected in the counts.

> *Important*
> Ensure that the corect napari cell type layer is selected


https://github.com/pnewstein/napari-3d-counter/assets/30813691/d0787cba-9b23-46d5-9cd3-21a4ad73460a



### Change appearance of a cell type

Changes to the name or edge color of a points layer will be reflected in the
previously added points, as well as the GUI. Features that are editable in this way include:
    - face color
    - edge color
    - symbol
    - size

> *Important*
> Ensure that the corect napari cell type layer is selected

https://github.com/pnewstein/napari-3d-counter/assets/30813691/6c495270-d4c4-473e-9091-8d2e0f8e2764


### Save configuration

Use the `Make launch_cell_count.py` button to create a python script that will
launch napari with 3DCounter added to the dock and current cell type appearances
already loaded


https://github.com/pnewstein/napari-3d-counter/assets/30813691/3448652d-3064-4900-8bbe-e88d75667108


### Save cells

Use the "Save cells" button to save the cell coordinates for all layers into a
csv file


https://github.com/pnewstein/napari-3d-counter/assets/30813691/38b30f2a-cc83-46c2-8b19-4d44715c07c5


### Load cells

Use the "Load cells" button to load the cells from a csv file into new layers


https://github.com/pnewstein/napari-3d-counter/assets/30813691/7df74688-85b1-4b61-aa51-dab179763832


### Launch with saved configuration

To run Count3D with custom configuration, paste the following code into your napari ipython console

```python
from napari_3d_counter import Count3D, CellTypeConfig

cell_type_config = [
    # The first cell type is called "cq+eve+" and should be green
    CellTypeConfig(
        name="cq+eve+",
        color="g"
    ),
    # The first cell type is called "cq+eve-" and should be cyan
    CellTypeConfig(
        name="cq+eve-",
        color="c"
    ),
    # The first cell type is called "cq-eve+" and should be red
    CellTypeConfig(
        name="cq-eve+",
        color="r"
    ),
]
# Launch the plugin with configuration
viewer.window.add_dock_widget(Count3D(viewer, cell_type_config=cell_type_config))
```

##  Auxiliary plugins


### Ingress Points

![Ingress Points](https://github.com/user-attachments/assets/2b0dc92b-ae14-40e0-8670-0d99f36b3468)

This plugin takes a points layer and adds the points to the selected cell type
layer. This can be useful if you want to manually count cells after cell identification.

### Split on Shapes

![Split on Shapes](https://github.com/user-attachments/assets/0d3c12fc-1347-4226-a9b9-9e34dd50577a)

This plugin can be used to subset a cell type into several groups based on their
x-y location. Simply draw a shape that surrounds your cells (perhaps in a
segment) and run this plugin to get a list of cells of each type in each shape.

### Reconstruct Selected

![Reconstruct Selected](https://github.com/user-attachments/assets/2f629b5a-d976-4add-8c5b-af4fc7e45729)

One use case of Napari 3D Counter is to visualize a subset of labeled cells.
For example, automated process label your cells of interest as well as a set of
off-target cells, and you would like to visualize only your cells of interest.
This can be accomplished by using Napari 3D Counter to count your cells of
interest, and some other process to create labels (perhaps
[nsbatwm](https://github.com/haesleinhuepf/napari-segment-blobs-and-things-with-membranes))
and using Reconstruct Selected to create a new image layer of those labels
which have been counted as a particular cell type.

## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.

## License

Distributed under the terms of the [GNU GPL v3.0] license,
"napari-3d-counter" is free and open source software

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[@napari]: https://github.com/napari
[MIT]: http://opensource.org/licenses/MIT
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[GNU GPL v3.0]: http://www.gnu.org/licenses/gpl-3.0.txt
[GNU LGPL v3.0]: http://www.gnu.org/licenses/lgpl-3.0.txt
[Apache Software License 2.0]: http://www.apache.org/licenses/LICENSE-2.0
[Mozilla Public License 2.0]: https://www.mozilla.org/media/MPL/2.0/index.txt
[cookiecutter-napari-plugin]: https://github.com/napari/cookiecutter-napari-plugin

[file an issue]: https://github.com/pnewstein/napari-3d-counter/issues

[napari]: https://github.com/napari/napari
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/

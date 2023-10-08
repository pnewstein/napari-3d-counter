# napari-3d-counter

[![License GNU GPL v3.0](https://img.shields.io/pypi/l/napari-3d-counter.svg?color=green)](https://github.com/pnewstein/napari-3d-counter/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-3d-counter.svg?color=green)](https://pypi.org/project/napari-3d-counter)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-3d-counter.svg?color=green)](https://python.org)
[![tests](https://github.com/pnewstein/napari-3d-counter/workflows/tests/badge.svg)](https://github.com/pnewstein/napari-3d-counter/actions)
[![codecov](https://codecov.io/gh/pnewstein/napari-3d-counter/branch/main/graph/badge.svg)](https://codecov.io/gh/pnewstein/napari-3d-counter)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/napari-3d-counter)](https://napari-hub.org/plugins/napari-3d-counter)

A simple plugin for counting objects in 3D images

----------------------------------

This [napari] plugin was generated with [Cookiecutter] using [@napari]'s [cookiecutter-napari-plugin] template.

<!--
Don't miss the full getting started guide to set up your new package:
https://github.com/napari/cookiecutter-napari-plugin#getting-started

and review the napari docs for plugin developers:
https://napari.org/stable/plugins/index.html
-->

## Installation

You cannot install `napari-3d-counter` via [pip]:

    pip install napari-3d-counter


Doesn't work yet


To install latest development version :

    pip install git+https://github.com/pnewstein/napari-3d-counter.git


##  Count3D Usage

Count3D can be launched from the plugin menu

### Adding a cell

You can add a cell of the currently selected cell type by clicking on the viewer.

- Ensure that `Point adder` layer is selected
- Ensure that `Add points` tool is selected
- Click on the viewer where you would like the point to be added

The counter on the current cell type's button will be incremented

### Changing cell type

You can change the currently selected cell type by clicking on that cell type's
button. This change will be reflected in the GUI. Additionally, the keyboard
shortcut for that cell type can be used. Keyboard shortcuts are listed on the
button, and are "q", "w", "e", "r", "t", "y" by default

### Undo last added cell

The undo button (shortcut u) will remove last added cell, regardless of
cell type

### Remove a particular cell

To remove a particular cell. Change to the layer containing the cell you would
like to remove. Then select the `select points` tool to select the points to
delete, then use `Delete selected points` to delete those points

This change will be reflected in the counts.


### Change appearance of a cell type

Changes to the name or edge color of a points layer will be reflected in the
previously added points, as well as the GUI.

### Save configuration

Use the `Make launch_cell_count.py` button to create a python script that will
launch napari with 3DCounter added to the dock and current cell type appearances
already loaded

### Save cells

Use the "Save cells" button to save the cell coordinates for all layers into a
csv file

### Load cells

Use the "Load cells" button to load the cells from a csv file into new layers

### Launch with saved configuration

To run Count3D with custom configuration, paste the following code into your napari ipython console

```python
from napari_3d_counter import Count3D, CellTypeConfig

cell_type_config = [
    # The first celltype is called "cq+eve+" and should be green
    CellTypeConfig(
        name="cq+eve+",
        color="g"
    ),
    # The first celltype is called "cq+eve-" and should be cyan
    CellTypeConfig(
        name="cq+eve-",
        color="c"
    ),
    # The first celltype is called "cq-eve+" and should be red
    CellTypeConfig(
        name="cq-eve+",
        color="r"
    ),
]
# Launch the plugin with configuration
viewer.window.add_dock_widget(Count3D(viewer, cell_type_config=cell_type_config))
```

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

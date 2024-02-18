"""
Contains code for specifying style: keyboard shortcut, color, name
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

from matplotlib.colors import to_hex

MatplotlibColor = Union[
    Tuple[float, float, float], Tuple[float, float, float, float], str
]

DEFAULT_KEYMAP_SEQUENCE = ["q", "w", "e", "r", "t", "y", ""]
DEFAULT_COLOR_SEQUENCE = [
    "#ffff00ff",  # y
    "#ff0000ff",  # r
    "#00ffffff",  # c
    "#0000ffff",  # b
    "#ff00ffff",  # m
    "#00ff00ff",  # g
    "#ffffffff",  # w
]
DEFAULT_OUTLINE_SIZE = 10
DEFAULT_OUT_OF_SLICE_SIZE = 2
DEFAULT_FACE_COLOR = "#ffffff00"
DEFAULT_SYMBOL = "o"
DEFAULT_EDGE_WIDTH = 0.05


@dataclass(frozen=True)
class CellTypeConfig:  # pylint: disable=too-many-instance-attributes
    """
    Data type for specifying configuration of celltype states
    """

    name: Optional[str] = None
    "The name to be displayed in the points layer"
    color: Optional[MatplotlibColor] = None
    "The edgecolor of the points"
    keybind: Optional[str] = None
    "the keyboard binding to switch to this celltype"
    outline_size: Optional[float] = None
    "The size of the circle around the cell"
    out_of_slice_point_size: Optional[int] = None
    "The size of the out of slice point"
    face_color: Optional[MatplotlibColor] = None
    "The filled in color of the point"
    symbol: Optional[str] = None
    "the symbol to use for the points"
    edge_width: Optional[float] = None
    "the width of the outline of the point"


@dataclass(frozen=True)
class CellTypeConfigNotOptional:  # pylint: disable=too-many-instance-attributes
    """
    Data type for specifying configuration of celltype states
    """

    name: str
    "The name to be displayed in the points layer"
    color: str
    "The edgecolor of the points as a hex color"
    keybind: str
    "the keyboard binding to switch to this celltype"
    outline_size: float
    "The size of the circle around the cell"
    out_of_slice_point_size: float
    "The size of the out of slice point"
    face_color: MatplotlibColor
    "The filled in color of the point"
    symbol: str
    "the symbol to use for the points"
    edge_width: float
    "the width of the outline of the point"


def fill_in_defaults(
    requests: List[Optional[str]], defaults: List[str]
) -> List[str]:
    """
    Fills in defaults from a list by looking up a unique defalt to use
    """
    used_defaults = set(defaults).intersection(requests)
    # discard used defaults
    default_list = [d for d in defaults if d not in used_defaults]
    # ensure that we will never run out of defauts
    default_list = default_list + ([default_list[-1]] * len(requests))
    # fill in Nones with a next unique default
    out: List[str] = []
    for request in requests:
        if request is None:
            out.append(default_list.pop(0))
        else:
            out.append(request)
    return out


def resolve_color(color: MatplotlibColor) -> str:
    """
    resolves matplotlib color
    """
    return to_hex(color, keep_alpha=True)


def process_cell_type_config(
    cell_type_configs: List[CellTypeConfig],
) -> List[CellTypeConfigNotOptional]:
    """
    Applies reasonable defaults to a some CellTypeConfigs to make some PointerStates
    """
    n_celltype = len(cell_type_configs)
    request_color_list = [
        None if c.color is None else resolve_color(c.color)
        for c in cell_type_configs
    ]
    colors = fill_in_defaults(request_color_list, DEFAULT_COLOR_SEQUENCE)
    keymaps = fill_in_defaults(
        [c.keybind for c in cell_type_configs], DEFAULT_KEYMAP_SEQUENCE
    )
    numbers = list(range(n_celltype))
    default_names = [f"Celltype {n+1}" for n in numbers]
    names: list[str] = []
    for default_name, cell_type_config in zip(
        default_names, cell_type_configs
    ):
        if cell_type_config.name is None:
            names.append(default_name)
        else:
            names.append(cell_type_config.name)
    # prevent name conflicts:
    unique_names: list[str] = []
    for name in names:
        if name not in unique_names:
            unique_names.append(name)
            continue
        name_int = 1
        while f"{name} [{name_int}]" in unique_names:
            name_int += 1
        unique_names.append(f"{name} [{name_int}]")
    outline_sizes = [
        DEFAULT_OUTLINE_SIZE if c.outline_size is None else c.outline_size
        for c in cell_type_configs
    ]
    out_of_slice_sizes = [
        (
            DEFAULT_OUT_OF_SLICE_SIZE
            if c.out_of_slice_point_size is None
            else c.out_of_slice_point_size
        )
        for c in cell_type_configs
    ]
    symbols = [
        DEFAULT_SYMBOL if c.symbol is None else c.symbol
        for c in cell_type_configs
    ]
    face_colors = [
        DEFAULT_FACE_COLOR if c.face_color is None else c.face_color
        for c in cell_type_configs
    ]
    edge_widths = [
        DEFAULT_EDGE_WIDTH if c.edge_width is None else c.edge_width
        for c in cell_type_configs
    ]
    # ensure that all out_of_slice_sizes are the same
    if any(s != out_of_slice_sizes[0] for s in out_of_slice_sizes):
        raise ValueError("All out of slice points sizes must be the same")
    return [
        CellTypeConfigNotOptional(
            keybind=keybind,
            name=name,
            color=color,
            outline_size=outline_size,
            out_of_slice_point_size=out_of_slice_size,
            symbol=symbol,
            face_color=face_color,
            edge_width=edge_width,
        )
        for keybind, name, color, outline_size, out_of_slice_size, symbol, face_color, edge_width in zip(
            keymaps,
            unique_names,
            colors,
            outline_sizes,
            out_of_slice_sizes,
            symbols,
            face_colors,
            edge_widths,
        )
    ]

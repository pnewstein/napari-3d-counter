"""
Contains code for specifying style: keyboard shortcut, color, name
"""

from dataclasses import dataclass
from typing import Optional, Union, Tuple, List

from matplotlib.colors import to_hex

MatplotlibColor = Union[Tuple[float, float, float], Tuple[float, float, float, float], str, None]

DEFAULT_KEYMAP_SEQUENCE = ["q", "w", "e", "r", "t", "y", ""]
DEFAULT_COLOR_SEQUENCE = [
    "#ffff00ff", # y
    "#ff0000ff", # r
    "#00ffffff", # c
    "#0000ffff", # b
    "#ff00ffff", # m
    "#00ff00ff", # g
    "#ffffffff", # w
]

@dataclass(frozen=True)
class PointerState:
    """
    Represents a counter type
    """

    keybind: str
    name: str
    state: int
    color: str


@dataclass(frozen=True)
class CellTypeConfig:
    """
    Data type for specifying configuration of celltype states
    """

    name: Optional[str] = None
    "The name to be displayed in the points layer"
    color: MatplotlibColor = None
    "The edgecolor of the points"
    keybind:  Optional[str] = None
    "the keyboard binding to switch to this celltype"

def fill_in_defaults(requests: List[Optional[str]], defaults: list[str]) -> list[str]:
    """
    Fills in defaults from a list by looking up a unique defalt to use
    """
    used_defaults = set(defaults).intersection(requests)
    # discard used defaults
    default_list = [d for d in defaults if d not in used_defaults]
    # ensure that we will never run out of defauts
    default_list = default_list + ([default_list[-1]] * len(requests))
    # fill in Nones with a next unique default
    out: list[str] = []
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


def process_cell_type_config(cell_type_configs: List[CellTypeConfig]) -> List[PointerState]:
    """
    Applies reasonable defaults to a some CellTypeConfigs to make some PointerStates
    """
    n_celltype = len(cell_type_configs)
    request_color_list = [None if c.color is None else resolve_color(c.color) for c in cell_type_configs]
    colors = fill_in_defaults(request_color_list, DEFAULT_COLOR_SEQUENCE)
    keymaps = fill_in_defaults([c.keybind for c in cell_type_configs], DEFAULT_KEYMAP_SEQUENCE)
    numbers = list(range(n_celltype))
    default_names = [f"Celltype {n+1}" for n in numbers]
    names: list[str] = []
    for (default_name, cell_type_config) in zip(default_names, cell_type_configs):
        if cell_type_config.name is None:
            names.append(default_name)
        else:
            names.append(cell_type_config.name)
    return [
        PointerState(keybind=keybind, name=name, state=state, color=color)
        for keybind, name, state, color in
        zip(keymaps, names, numbers, colors)
    ]

"""
A napari plugin for counting cells
"""

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

from ._widget import (
    Count3D,
    ReconstructSelected,
    get_n3d_counter,
    IngressPoints,
    SplitOnShapes,
)
from .celltype_config import CellTypeConfig

__all__ = (
    "Count3D",
    "ReconstructSelected",
    "CellTypeConfig",
    "get_n3d_counter",
    "IngressPoints",
    "SplitOnShapes",
)

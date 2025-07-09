"""
A napari plugin for counting cells
"""

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

from ._widget import Count3D, reconstruct_selected
from .celltype_config import CellTypeConfig
from .commands import get_n3d_counter

__all__ = (
    "Count3D",
    "reconstruct_selected",
    "CellTypeConfig",
    "get_n3d_counter",
)

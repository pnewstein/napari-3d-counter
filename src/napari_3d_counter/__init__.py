"""
A napari plugin for counting cells
"""

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

from ._widget import Count3D, reconstruct_selected
from .celltype_config import CellTypeConfig

__all__ = ("Count3D", "reconstruct_selected")

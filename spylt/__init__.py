"""Top-level package for spylt."""
import sys

if sys.version_info < (3, 10):
    # compatibility for python <3.10
    import importlib_metadata as metadata
else:
    from importlib import metadata

from spylt.core import SpyllingFigure
from spylt.recover import recover, recover_data, recover_fun, recover_rcParams
from spylt.wrappers import SpyllingContext, spylling

__all__ = [
    SpyllingFigure,
    SpyllingContext,
    spylling,
    recover,
    recover_data,
    recover_fun,
    recover_rcParams,
]

__version__ = metadata.version("spylt")

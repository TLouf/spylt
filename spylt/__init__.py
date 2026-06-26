"""Top-level package for spylt."""

import sys

if sys.version_info < (3, 10):
    # compatibility for python <3.10
    import importlib_metadata as metadata
else:
    from importlib import metadata

from .core import SpyllingFigure
from .recover import recover, recover_data, recover_fun, recover_rcParams
from .wrappers import SpyllingContext, spylling

__version__ = metadata.version("spylt")

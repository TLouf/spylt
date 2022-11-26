from __future__ import annotations

import importlib
import pickle
import zipfile
from pathlib import Path
from types import FunctionType
from typing import Any

import matplotlib


def recover(path: str | Path) -> tuple[FunctionType, dict[str, Any]]:
    """
    Recover the necessary data and metadata to regenerate a
    :py:class:`spylt.SpyllingFigure` saved at `path`.

    Parameters
    ----------
    path
        Path where to find the metadata to recover.

    Returns
    -------
    fun
        Function that generated the figure to recover.
    data
        Dictionary to feed `fun` to regenerate the figure.

    Examples
    --------

    You can regenerate the exact same figure:

    >>> fun, data_dict = spylt.recover("figure")
    >>> fun(**data_dict)

    You can also inspect the function's definition to then tweak its definition:

    >>> import inspect
    >>> print(inspect.getsource(fun))

    and / or change the value of a parameter before replotting. Let's say the colormap
    was an argument of `fun` and we wish to change it to "viridis":

    >>> fun, data_dict = spylt.recover("figure")
    >>> data_dict["cmap"] = "viridis"
    >>> fun(**data_dict)
    """
    path = _extract_if_zip(path)
    data = recover_data(path)
    fun = recover_fun(path)
    recover_rcParams(path)
    return fun, data


def recover_fun(path: str | Path) -> FunctionType:
    """
    Recover the function necessary to regenerate a :py:class:`spylt.SpyllingFigure`
    saved at `path`.

    Parameters
    ----------
    path
        Path where to find the metadata to recover.

    Returns
    -------
    fun
        Function that generated the plot to recover.
    """
    # only works if path is child of current directory, TODO: implement for any path?
    path = _extract_if_zip(path)
    py_files = list(path.glob("**/*.py"))
    global module
    if len(py_files) == 1:
        p = py_files[0]
        # function name and module name are necessarily the same
        if path.is_absolute():
            p = p.relative_to(path.parent)
        module_name = ".".join(p.with_suffix("").parts)
        module = importlib.import_module(module_name)
        fun = getattr(module, p.stem)
    elif len(py_files) == 2:
        # One file with a module, another that just imports function which has a name
        # different from the module's, and which is the file's stem.
        file_sizes = [p.stat().st_size for p in py_files]
        # The module contains the function so it's necessarily a bigger file.
        module_idx = int(file_sizes[0] < file_sizes[1])
        p = py_files[module_idx]
        if path.is_absolute():
            p = p.relative_to(path.parent)
        module_name = ".".join(p.with_suffix("").parts)
        module = importlib.import_module(module_name)
        fun = getattr(module, py_files[1 - module_idx].stem)
    else:
        raise ValueError(
            "The backup seems to be corrupted, there are at least three .py files."
        )
    return fun


def recover_data(path: str | Path) -> dict[str, Any]:
    """
    Recover the data necessary to regenerate a :py:class:`spylt.SpyllingFigure` saved at
    `path`.

    Parameters
    ----------
    path
        Path where to find the metadata to recover.

    Returns
    -------
    data
        Dictionary to feed `fun` to regenerate the plot.
    """
    path = _extract_if_zip(path)
    data = {}
    for p in path.glob("*.pickle"):
        with open(p, "rb") as f:
            data[p.stem] = pickle.load(f)

    return data


def recover_rcParams(path: str | Path) -> matplotlib.RcParams:
    """
    Recover the rcParams that were set when a :py:class:`spylt.SpyllingFigure` was saved
    at `path`.

    Parameters
    ----------
    path
        Path where to find the metadata to recover.

    Returns
    -------
    rcParams
        The matplotlib's rcParams that were set when the figure was saved.
    """
    path = _extract_if_zip(path)
    saved_rcParams = matplotlib.rc_params_from_file(
        path / "matplotlibrc", use_default_template=False
    )
    matplotlib.rcParams.update(saved_rcParams)
    return matplotlib.rcParams


def _extract_if_zip(path: str | Path) -> Path:
    path = Path(path)

    if not path.is_dir() and path.suffix == ".zip":
        with zipfile.ZipFile(path, "r") as zip:
            zip.extractall(path.stem)
        path = path.with_suffix("")
    return path

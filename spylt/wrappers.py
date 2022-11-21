import inspect
from collections.abc import Iterable
from contextlib import contextmanager
from functools import partial, wraps
from importlib import import_module
from typing import Any

import matplotlib.pyplot as plt

from spylt._typing import PlotGenType
from spylt.core import SpyllingFigure


@contextmanager
def SpyllingContext(
    plot_generator: PlotGenType | None = None,
    data: dict[str, Any] | None = None,
    as_dir: bool = True,
    zipped: bool = False,
    excluded_args: Iterable | None = None,
    excluded_types: Iterable | None = None,
    save_env: bool = False,
    verbose: bool = False,
):
    """Context within which generated figures are turned it into a SpyllingFigure.

    Parameters
    ----------
    as_dir
        Whether to save the backup in a child directory, named after the figure
        file's name.
    zipped
        Whether to save the backup in a zipped directory, named after the figure
        file's name. If as_dir is True too, only a zip will be saved.
    excluded_args
        Iterable of argument names not to save even if they are present in `data`.
    excluded_types
        Iterable of argument types not to save even if they are present in `data`.
    save_env
        Whether to save a file listing the packages installed in the virtual environment
        (`requirements.txt` for `pip`, `environment.yml` for `conda`).
    verbose
        Whether to print for every file saved to disk.

    Examples
    --------

    >>> with SpyllingContext(verbose=True):
    ...     # Code that creates your figure.
    """
    kwargs = {
        "plot_generator": plot_generator,
        "data": data,
        "as_dir": as_dir,
        "zipped": zipped,
        "excluded_args": excluded_args,
        "excluded_types": excluded_types,
        "save_env": save_env,
        "verbose": verbose,
    }
    func = plt.figure
    owner = import_module(func.__module__)
    qname = func.__qualname__
    while "." in qname:
        parent, qname = qname.split(".", 1)
        owner = getattr(owner, parent)
    # partial sets default, but if user calls func with explicit kwarg, it will
    # override this default (which is a good thing).
    setattr(owner, func.__name__, partial(func, FigureClass=SpyllingFigure, **kwargs))
    yield
    setattr(owner, func.__name__, func)


def spylling(
    as_dir: bool = True,
    zipped: bool = False,
    excluded_args: Iterable | None = None,
    excluded_types: Iterable | None = None,
    save_env: bool = False,
    verbose: bool = False,
):
    """Decorator to wrap functions generating a figure to turn it into a SpyllingFigure.

    The :py:class:`spylt.SpyllingFigure` instantiated within the decorated function
    will be passed the function as `plot_generator`, and its arguments and keyword
    arguments as `data`.

    Parameters
    ----------
    as_dir
        Whether to save the backup in a child directory, named after the figure
        file's name.
    zipped
        Whether to save the backup in a zipped directory, named after the figure
        file's name. If as_dir is True too, only a zip will be saved.
    excluded_args
        Iterable of argument names not to save even if they are present in `data`.
    excluded_types
        Iterable of argument types not to save even if they are present in `data`.
    save_env
        Whether to save a file listing the packages installed in the virtual environment
        (`requirements.txt` for `pip`, `environment.yml` for `conda`).
    verbose
        Whether to print for every file saved to disk.

    Examples
    --------
    A function plotting figures can be directly decorated to always be spylling:

    >>> @spylling(verbose=True)
    ... def plot(dataset, scatter_size=6, cmap='plasma'):
    ...    # Function that creates your figure
    ...    return ax
    >>> ax = plot(dataset, scatter_size=10)
    >>> ax.get_figure().savefig('fig.pdf')
    Saved figure: fig
    Saving backup data to ./fig
    Saved plot.py
    Saved matplotlibrc
    Saved dataset.pickle
    Saved scatter_size.pickle
    Saved cmap.pickle


    or you can generate a new decorated function when calling it:

    >>> def plot(dataset, scatter_size=6, cmap='plasma'):
    ...    # Function that creates your figure
    ...    return ax
    >>> ax = spylling(plot)(dataset, scatter_size=10)
    >>> ax.get_figure().savefig('fig.pdf')
    Saved figure: fig
    Saving backup data to ./fig
    Saved plot.py
    Saved matplotlibrc
    Saved dataset.pickle
    Saved scatter_size.pickle
    Saved cmap.pickle
    """

    def decorator_plot(func):
        @wraps(func)
        def wrapper_plot(*args, **kwargs):
            data = {
                param_name: param.default
                for param_name, param in inspect.signature(func).parameters.items()
            }
            all_arg_names = list(data.keys())
            for i, a in enumerate(args):
                data[all_arg_names[i]] = a
            data.update(kwargs)

            with SpyllingContext(
                plot_generator=func,
                data=data,
                as_dir=as_dir,
                zipped=zipped,
                excluded_args=excluded_args,
                excluded_types=excluded_types,
                save_env=save_env,
                verbose=verbose,
            ):
                return func(*args, **kwargs)

        return wrapper_plot

    return decorator_plot

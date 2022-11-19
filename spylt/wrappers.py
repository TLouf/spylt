import inspect
from contextlib import contextmanager
from functools import partial, wraps
from importlib import import_module

import matplotlib.pyplot as plt

from spylt.core import SpyllingFigure


@contextmanager
def Spylling(**kwargs):
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
    as_dir=False,
    zipped=False,
    excluded_types=None,
    excluded_args=None,
    verbose=False,
    save_env=True,
):
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

            with Spylling(
                plot_func=func,
                data=data,
                as_dir=as_dir,
                zipped=zipped,
                save_env=save_env,
                excluded_types=excluded_types,
                excluded_args=excluded_args,
                verbose=verbose,
            ):
                return func(*args, **kwargs)

        return wrapper_plot

    return decorator_plot

import inspect
import string
import sys
from types import ModuleType

import matplotlib.pyplot as plt
from matplotlib.testing.decorators import _image_directories, _raise_on_image_difference

from spylt import SpyllingFigure, spylling

# TODO: cleanup


def get_attr(spylling_figure, attr):
    attr_fmt = f"_{SpyllingFigure.__name__}__{{}}"
    return getattr(spylling_figure, attr_fmt.format(attr))


def plot():
    lines = plt.plot([1, 2])
    return lines[0].axes.get_figure()


def figure():
    return plt.figure()


def subplots():
    fig, _ = plt.subplots()
    return fig


def subplot_mosaic():
    fig, _ = plt.subplot_mosaic("A")
    return fig


def subplot2grid():
    ax = plt.subplot2grid((1, 1), (0, 0))
    return ax.get_figure()


def paramed_plot(y, c="g", ls="--", **kwargs):
    fig, ax = plt.subplots()
    ax.plot(y, c=c, ls=ls, **kwargs)
    return ax


def spylling_figure(**kwargs):
    return plt.figure(FigureClass=SpyllingFigure, **kwargs)


def recover_plot_fun(x, fig_test=None, **kwargs):
    if fig_test is None:
        fig_test = plt.figure(FigureClass=SpyllingFigure, **kwargs)
    fig_test.subplots().plot(x)
    return fig_test


class Plot:
    def figure(self):
        return plt.figure()


class SpyllingPlot:
    @spylling()
    def figure(self):
        return plt.figure()


def check_figures_equal(
    *, extensions=("png", "pdf", "svg"), tol=0, data=None, plot_fun=None
):
    """
    Decorator for test cases that generate and compare two figures.

    Adapted from matplotlib's implementation.

    The decorated function must take two keyword arguments, *fig_test*
    and *fig_ref*, and draw the test and reference images on them.
    After the function returns, the figures are saved and compared.

    This decorator should be preferred over `image_comparison` when possible in
    order to keep the size of the test suite from ballooning.

    Parameters
    ----------
    extensions : list, default: ["png", "pdf", "svg"]
        The extensions to test.
    tol : float
        The RMS threshold above which the test is considered failed.

    Raises
    ------
    RuntimeError
        If any new figures are created (and not subsequently closed) inside
        the test function.

    Examples
    --------
    Check that calling `.Axes.plot` with a single argument plots it against
    ``[0, 1, 2, ...]``::

        @check_figures_equal()
        def test_plot(fig_test, fig_ref):
            fig_test.subplots().plot([1, 3, 5])
            fig_ref.subplots().plot([0, 1, 2], [1, 3, 5])

    """
    ALLOWED_CHARS = set(string.digits + string.ascii_letters + "_-[]()")
    KEYWORD_ONLY = inspect.Parameter.KEYWORD_ONLY

    def decorator(func):
        import pytest

        _, result_dir = _image_directories(func)
        old_sig = inspect.signature(func)

        if not {"fig_test", "fig_ref"}.issubset(old_sig.parameters):
            raise ValueError(
                "The decorated function must have at least the "
                "parameters 'fig_ref' and 'fig_test', but your "
                f"function has the signature {old_sig}"
            )

        @pytest.mark.parametrize("ext", extensions)
        def wrapper(*args, ext, request, **kwargs):
            if "ext" in old_sig.parameters:
                kwargs["ext"] = ext
            if "request" in old_sig.parameters:
                kwargs["request"] = request

            file_name = "".join(c for c in request.node.name if c in ALLOWED_CHARS)
            try:
                fig_test = plt.figure("test")  # , FigureClass=SpyllingFigure)
                fig_ref = plt.figure(
                    "reference",
                    FigureClass=SpyllingFigure,
                    data=data,
                    plot_fun=plot_fun,
                )
                # Keep track of number of open figures, to make sure test
                # doesn't create any new ones
                n_figs = len(plt.get_fignums())
                func(*args, fig_test=fig_test, fig_ref=fig_ref, **kwargs)
                if len(plt.get_fignums()) > n_figs:
                    raise RuntimeError(
                        "Number of open figures changed during "
                        "test. Make sure you are plotting to "
                        "fig_test or fig_ref, or if this is "
                        "deliberate explicitly close the "
                        "new figure(s) inside the test."
                    )
                test_image_path = result_dir / (file_name + "." + ext)
                ref_image_path = result_dir / (file_name + "-expected." + ext)
                fig_test.savefig(test_image_path)
                fig_ref.savefig(ref_image_path)
                _raise_on_image_difference(ref_image_path, test_image_path, tol=tol)
            except Exception as e:  # TODO: remove
                raise e
            finally:
                plt.close(fig_test)
                plt.close(fig_ref)

        parameters = [
            param
            for param in old_sig.parameters.values()
            if param.name not in {"fig_test", "fig_ref"}
        ]
        if "ext" not in old_sig.parameters:
            parameters += [inspect.Parameter("ext", KEYWORD_ONLY)]
        if "request" not in old_sig.parameters:
            parameters += [inspect.Parameter("request", KEYWORD_ONLY)]
        new_sig = old_sig.replace(parameters=parameters)
        wrapper.__signature__ = new_sig

        # reach a bit into pytest internals to hoist the marks from
        # our wrapped function
        new_marks = getattr(func, "pytestmark", []) + wrapper.pytestmark
        wrapper.pytestmark = new_marks

        return wrapper

    return decorator


def fake_figure():
    pass


fake_module = ModuleType("fake_figure")
sys.modules[fake_module.__name__] = fake_module
fake_module.__file__ = __file__
fake_module.fake_figure = fake_figure
fake_module.fake_figure.__module__ = fake_module.__name__

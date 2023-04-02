from inspect import getsource
from textwrap import dedent

import matplotlib.pyplot as plt
import pytest

import spylt
import spylt._testing as tm

x = [0, 1, 2]


@pytest.mark.parametrize("plot_fun", [tm.figure, tm.fake_module.fake_figure])
def test_plot_fun_in_module(tmp_path, plot_fun):
    fig = tm.spylling_figure(plot_fun=plot_fun)
    path = tmp_path / "fig.png"
    fig.savefig(path)
    expected = getsource(plot_fun)
    assert getsource(spylt.recover_fun(path)) == expected


def test_plot_method_in_module(tmp_path):
    plot_fun = tm.SpyllingPlot().figure
    # Too convoluted to do it the "core way", passing the method to the method itself...
    # will never happen in practice.
    # fig = tm.spylling_figure(plot_fun=plot_fun)
    # fig = spylt.spylling()(plot_fun)()
    fig = plot_fun()
    path = tmp_path / "fig.png"
    fig.savefig(path)
    expected = "\n".join(getsource(plot_fun).splitlines()[1:]).replace("(self)", "()")
    recovered_fun = spylt.recover_fun(path)
    assert dedent(getsource(recovered_fun)).strip() == dedent(expected)


def test_plot_fun_in_main(tmp_path, plot_fun_in_main):
    path = tmp_path / "fig.png"
    expected = getsource(tm.spylling_figure)
    assert getsource(spylt.recover_fun(path)) == expected


def test_plot_fun_in_interactive(tmp_path, plot_fun_in_interactive):
    path = tmp_path / "fig.png"
    expected = getsource(tm.spylling_figure)
    assert getsource(spylt.recover_fun(path)) == expected


def test_data(tmp_path):
    expected_data = {"a": 1}
    fig = tm.recover_plot_fun(x, data=expected_data)
    path = tmp_path / "fig.png"
    fig.savefig(path)
    assert spylt.recover_data(path) == expected_data


def test_rcParams(tmp_path):
    ls = "--"
    plt.rcParams["lines.linestyle"] = ls
    fig = tm.recover_plot_fun(x)
    path = tmp_path / "fig.png"
    fig.savefig(path)
    plt.rcParams["lines.linestyle"] = "-"
    spylt.recover_rcParams(path)
    assert plt.rcParams["lines.linestyle"] == ls


@tm.check_figures_equal(extensions=["png"], data={"x": x}, plot_fun=tm.recover_plot_fun)
def test_replot_identical(tmp_path, fig_test, fig_ref):
    fig_ref.subplots().plot(x)
    fig_ref.savefig(tmp_path / "fig.png")

    fun, data_dict = spylt.recover(tmp_path / "fig")
    fig_test = fun(**data_dict, fig_test=fig_test)

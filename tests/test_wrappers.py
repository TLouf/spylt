import spylt._testing as tm
from spylt import SpyllingContext, SpyllingFigure, spylling

FIG_GEN_FUNCTS = (tm.plot, tm.figure, tm.subplots, tm.subplot_mosaic, tm.subplot2grid)


def test_decorator_passes_metadata():
    y = [1, 2]
    c = "b"
    dec_kwargs = {
        "as_dir": False,
        "zipped": True,
        "excluded_args": {"y"},
        "excluded_types": (str,),
        "save_env": True,
        "verbose": True,
    }
    fig = spylling(**dec_kwargs)(tm.paramed_plot)(y, c=c).get_figure()

    fig_fun = tm.get_attr(fig, "plot_fun")
    assert fig_fun == tm.paramed_plot

    assert tm.get_attr(fig, "plot_module") == tm

    fig_data = tm.get_attr(fig, "data")
    assert fig_data == {"y": y, "c": c, "ls": "--"}

    for key, value in dec_kwargs.items():
        assert tm.get_attr(fig, key) == value


def test_context_passes_metadata():
    y = [1, 2]
    c = "r"
    context_kwargs = {
        "plot_fun": tm.paramed_plot,
        "data": {"y": y, "c": c},
        "as_dir": False,
        "zipped": True,
        "excluded_args": {"y"},
        "excluded_types": (str,),
        "save_env": True,
        "verbose": True,
    }
    with SpyllingContext(**context_kwargs):
        fig = tm.paramed_plot(y, c=c).get_figure()

    for key, value in context_kwargs.items():
        assert tm.get_attr(fig, key) == value

    fig_fun = tm.get_attr(fig, "plot_fun")
    assert fig_fun == tm.paramed_plot

    fig_data = tm.get_attr(fig, "data")
    assert fig_data == {"y": y, "c": c}

    assert tm.get_attr(fig, "plot_module") == tm


def test_decorator_fig_gen():
    for fun in FIG_GEN_FUNCTS:
        fig = spylling()(fun)()
        assert isinstance(fig, SpyllingFigure)


def test_context_fig_gen():
    for fun in FIG_GEN_FUNCTS:
        with SpyllingContext():
            fig = fun()
        assert isinstance(fig, SpyllingFigure)

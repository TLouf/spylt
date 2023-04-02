import matplotlib.pyplot as plt

from spylt import SpyllingFigure


def get_attr(spylling_figure, attr):
    attr_fmt = f"_{SpyllingFigure.__name__}__{{}}"
    return getattr(spylling_figure, attr_fmt.format(attr))


def plot(c: str = "r"):
    _ = plt.plot([1, 2], c=c)
    return plt.gcf()


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

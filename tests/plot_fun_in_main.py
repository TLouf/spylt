import sys

import matplotlib.pyplot as plt

from spylt import SpyllingFigure


def spylling_figure(**kwargs):
    return plt.figure(FigureClass=SpyllingFigure, **kwargs)


if __name__ == "__main__":
    path = sys.argv[1]
    fig = spylling_figure(plot_fun=spylling_figure)
    print(hasattr(spylling_figure, "__self__"))
    fig.savefig(path)

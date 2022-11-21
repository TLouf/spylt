# spylt
![](https://img.shields.io/pypi/pyversions/spylt)
[![](https://img.shields.io/pypi/v/spylt.svg)](https://pypi.python.org/pypi/spylt)


Simple utility to back up the data necessary to reproduce a matplotlib figure.

Please bear in mind that `spylt` should only be seen as a failsafe, it does not replace good practices such as version control, testing code and saving intermediary results.

## Installation

The simplest is to install with `pip`

```
pip install spylt
```

To install from source, first clone from the repository (or your own fork if you wish to open a pull request), and then use [`poetry`](https://python-poetry.org/docs/) to install

```
git clone https://github.com/TLouf/spylt.git
cd spylt
poetry install
```

## Usage
There are three ways to utilise `spylt`'s functionality, presented in the following from more to less recommended:

- decorating the plotting function with `@spylling`
    ```python
    from spylt import spylling

    @spylling(verbose=True)
    def plot(dataset, scatter_size=6, cmap='plasma'):
        """Function that creates your figure"""
        ...
        return ax
    ```
    This method is aware of the defined function and its arguments, and can thus save both the function definition and the value of all its args and kwargs without you specifying anything:

    ```python
    >>> ax = plot(dataset, scatter_size=10)
    >>> ax.get_figure().savefig('fig.pdf')
    Saved figure: fig
    Saving backup data to ./fig
    Saved plot.py
    Saved matplotlibrc
    Saved dataset.pickle
    Saved scatter_size.pickle
    Saved cmap.pickle
    ```

    The `savefig` call can be made outside or inside the `plot` function, everything will be backed up as long as it is done on a figure instantiated in `plot` (via `plt.figure`, `plt.subplots`, `plt.subplot_mosaic`, etc)


- plotting within a context defined by `SpyllingContext`
    ```python
    from spylt import SpyllingContext

    with SpyllingContext(verbose=True):
        """Code that creates your figure"""
        ...
    ```

- instantiating the `SpyllingFigure` class
    ```python
    from spylt import SpyllingFigure

    fig, ax = plt.subplots(*args, FigureClass=SpyllingFigure, verbose=True)
    ...
    ```

    In the two previous cases, you'll have to specify what data you want to save, and possibly the function definition:
    ```python
    >>> fig.savefig('fig.pdf', plot_generator=plot, data={'dataset': dataset})
    Saved figure: fig
    Saving backup data to ./fig
    Saved plot.py
    Saved matplotlibrc
    Saved dataset.pickle
    ```

## How's that package called again?

If it can help you remember the name of the package in the figure, it comes from the idea of spilling data to disk, stylised as `spylt` which is reminiscent of both `python` and `matplotlib.pyplot` (`plt`).

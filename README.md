# spylt
![](https://img.shields.io/pypi/pyversions/spylt)
[![](https://img.shields.io/pypi/v/spylt.svg)](https://pypi.python.org/pypi/spylt)


`spylt` is a simple utility to back up the data necessary to reproduce a matplotlib
figure. Ever came back after weeks, months (years?) to a figure that you need to
slightly adjust, only to find out that you have no idea where you buried that piece of
code or that dataset that you need to generate this plot? That's a situation in which
having used `spylt` would have helped. It provides a decorator for your plotting
functions that adds the functionality that upon saving the figure, a copy of all the
following metadata can be saved:

- The function or even the function's module code, as a `.py` file.
- The values of all of the function's arguments, as
  [`pickle`](https://docs.python.org/3/library/pickle.html) files.
- The virtual environment definition, that is `pip`'s `requirements.txt` or `conda`'s
  `environment.yml`.
- A `matplotlibrc` file, which can be useful in case you've modified
  [`rcParams`](https://matplotlib.org/stable/tutorials/introductory/customizing.html) at
  runtime.
- Other things? Please make your suggestions in [the issue
  tracker](https://github.com/TLouf/spylt/issues)!

Please bear in mind that `spylt` should only be seen as a failsafe, it does not replace
good practices such as version control, saving intermediary results and figure metadata.

<!-- follows_intro DO NOT REMOVE install_follows -->

## Installation

The simplest is to install with `pip`:

```
pip install spylt
```

To install the latest development version from source (requires `pip >= 19.0`):
```
pip install git+https://github.com/TLouf/spylt.git
```

To install an editable version for development, first clone from the repository (or your
own fork), and then use [`poetry`](https://python-poetry.org/docs/) to install:

```
git clone https://github.com/TLouf/spylt.git
cd spylt
poetry install
```

## Usage
There are three ways to utilise `spylt`'s functionality, presented in the following from
more to less recommended:

- decorating the plotting function with `@spylling`
    ```python
    from spylt import spylling

    @spylling(verbose=True)
    def plot(dataset, scatter_size=6, cmap='plasma'):
        """Function that creates your figure"""
        ...
        return ax
    ```
    This method is aware of the defined function and its arguments, and can thus save
    both the function definition and the value of all its args and kwargs without you
    specifying anything:

    ```python
    >>> ax = plot(dataset, scatter_size=10)
    >>> ax.get_figure().savefig('fig.pdf')
    Saved figure: fig.pdf
    Saving backup data to:
    └── fig
        ├── plot.py
        ├── scatter_size.pickle
        ├── dataset.pickle
        ├── cmap.pickle
        └── matplotlibrc
    ```

    The `savefig` call can be made outside or inside the `plot` function, everything
    will be backed up as long as it is done on a figure instantiated in `plot` (via
    `plt.figure`, `plt.subplots`, `plt.subplot_mosaic`, etc).


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

    In the two previous cases, you'll have to specify what data you want to save, and
    possibly the function definition:
    ```python
    >>> fig.savefig('fig.pdf', plot_fun=plot, data={'dataset': dataset})
    Saved figure: fig.pdf
    Saving backup data to:
    └── fig
        ├── plot.py
        ├── dataset.pickle
        └── matplotlibrc
    ```

## How's that package called again?

If it can help you remember the name of the package in the future, it comes from the
idea of spilling data to disk, stylised as `spylt` to be reminiscent of
`matplotlib.pyplot`.

import inspect
import io
import os
import pickle
import subprocess
import sys
import zipfile
from collections.abc import Iterable
from importlib import import_module
from pathlib import Path
from typing import Any

from matplotlib.pyplot import Figure, rcParams

from spylt._typing import PlotGenType


class SpyllingFigure(Figure):
    """Figure subclass that will backup data to disk on save.

    Parameters
    ----------
    *args
        :py:class:`matplotlib.figure.Figure` init arguments.
    plot_generator
        Function, method or module used to generate the figure.
    data
        Dictionary containing all the data objects necessary to reproduce the figure
        with `plot_generator`.
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
    **kwargs
        :py:class:`matplotlib.figure.Figure` init keyword arguments.
    """

    def __init__(
        self,
        *args,
        plot_generator: PlotGenType | None = None,
        data: dict[str, Any] | None = None,
        as_dir: bool = True,
        zipped: bool = False,
        excluded_args: Iterable | None = None,
        excluded_types: Iterable | None = None,
        save_env: bool = False,
        verbose: bool = False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        module = getattr(plot_generator, "__module__", None)
        # If we can get a module and it's not __main__ from an interactive session:
        if module is not None:
            module = import_module(module)
            if hasattr(module, "__file__"):
                plot_generator = module
        self.__plot_generator = plot_generator
        self.__data = data
        self.__as_dir = as_dir
        self.__zipped = zipped
        self.__save_env = save_env
        self.__verbose = verbose
        self.__verbose_print = print if self.__verbose else lambda *a, **k: None
        if excluded_types is None:
            excluded_types = ()
        self.__excluded_types = tuple(excluded_types)
        if excluded_args is None:
            excluded_args = set()
        self.__excluded_args = set(excluded_args)
        self.__buffers = {}

    def savefig(self, *args, **kwargs):
        # savefig first to limit possibility of a bug from our side to impede saving.
        super().savefig(*args, **kwargs)

        plot_generator = self.__plot_generator
        data = self.__data or {}
        self.__buffers = {}

        fig_path = Path(args[0]).absolute()
        self.__verbose_print(f"Saved figure: {fig_path.name}")

        savedir_path = fig_path.parent
        if self.__as_dir or self.__zipped:
            savedir_path = savedir_path / fig_path.stem
            if self.__zipped:
                savedir_path = savedir_path.with_suffix(".zip")
            else:
                savedir_path.mkdir(parents=True, exist_ok=True)

        self.__verbose_print(f"Saving backup data to {savedir_path}")
        # Save requirements at init to save time? Problematic case: user inits in
        # notebook, does their stuff and then installs a package, the requirements from
        # init would be wrong. Could be an option given to the user though.
        if self.__save_env:
            try:
                requirements = subprocess.check_output(
                    [sys.executable, "-m", "pip", "freeze"], text=True
                )
                self.__save_text(requirements, savedir_path / "requirements.txt")
            except subprocess.CalledProcessError:
                pass

            if "CONDA_PREFIX" in os.environ:
                try:
                    environment = subprocess.check_output(
                        ["conda", "env", "export"], text=True
                    )
                    self.__save_text(environment, savedir_path / "environment.yml")
                except subprocess.CalledProcessError:
                    pass

        if plot_generator is not None:
            if plot_generator.__name__ == "__main__":
                with open(plot_generator.__file__) as f:
                    source = f.read()
            else:
                source = inspect.getsource(plot_generator)
            self.__save_text(source, savedir_path / f"{plot_generator.__name__}.py")

        rcParams_str = "\n".join(
            [
                line
                if line.startswith("axes.prop_cycle")
                else line.replace("[", "").replace("'", "").replace("]", "")
                for line in str(rcParams).replace("#", "").splitlines()
            ]
        ).replace("savefig.bbox: None", "savefig.bbox: standard")
        self.__save_text(rcParams_str, savedir_path / "matplotlibrc")

        # Is it worth implementing class specific save formats (for common ones)? Like
        # DataFrames to csv or parquet, which have the advantage of not being
        # Python-specific. Or give the user option to select the save method for
        # specific classes / data objects?
        args_to_save = set(data.keys()) - self.__excluded_args
        for arg in args_to_save:
            value = data[arg]
            if not isinstance(value, self.__excluded_types):
                self.__save_pickle(value, savedir_path / f"{arg}.pickle")

        if self.__zipped:
            with zipfile.ZipFile(savedir_path.with_suffix(".zip"), "w") as zip:
                for file_name, buffer in self.__buffers.items():
                    zip.writestr(file_name, buffer.getvalue())

        self.__buffers.clear()

    savefig.__doc__ = "\n".join(
        [
            (
                "This extended version also backs up the data needed to reproduce this "
                "figure."
            ),
            Figure.savefig.__doc__ or "",
        ]
    )

    def __save_text(self, text, path):
        if self.__zipped:
            buffer = io.StringIO()
            buffer.write(text)
            self.__buffers[path.name] = buffer

        else:
            with open(path, "w") as f:
                f.write(text)

        self.__verbose_print(f"Saved {path.name}")

    def __save_pickle(self, obj, path):
        if self.__zipped:
            buffer = io.BytesIO()
            pickle.dump(obj, buffer)
            self.__buffers[path.name] = buffer

        else:
            with open(path, "wb") as f:
                pickle.dump(obj, f)

        self.__verbose_print(f"Saved {path.name}")


# TODO: recover from previous spylling, save whole module when possible?

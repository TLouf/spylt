from __future__ import annotations

import inspect
import io
import os
import pickle
import subprocess
import sys
import zipfile
from collections.abc import Iterable
from importlib import import_module
from itertools import accumulate
from operator import truediv
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
    plot_fun
        Function or method used to generate the figure.
    data
        Dictionary containing all the data objects necessary to reproduce the figure
        with `plot_fun`.
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
        plot_fun: PlotGenType | None = None,
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
        self.__plot_fun = plot_fun
        self.__plot_module = None
        module_name = getattr(plot_fun, "__module__", None)
        # If we can get a module and it's not __main__ from an interactive session:
        if module_name is not None:
            module = import_module(module_name)
            if hasattr(module, "__file__"):
                self.__plot_module = module
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

        fname = args[0]
        if not isinstance(fname, (str, Path)):
            if hasattr(fname, "name"):
                # For file-like objects
                fname = fname.name
            else:
                # For buffers, if figure is saved to buffer the user probably does not
                # want to backup the data to disk.
                return

        fig_path = Path(fname)
        self.__verbose_print(f"Saved figure: {fig_path.name}")

        data = self.__data or {}
        self.__buffers = {}

        savedir_path = fig_path.parent
        if self.__as_dir or self.__zipped:
            savedir_path = savedir_path / fig_path.stem
            if self.__zipped:
                savedir_path = savedir_path.with_suffix(".zip")
            else:
                savedir_path.mkdir(parents=True, exist_ok=True)

        self.__verbose_print(f"Saving backup data to:\n└── {savedir_path}")
        savedir_path = savedir_path.absolute()
        # Save requirements at init to save time? Problematic case: user inits in
        # notebook, does their stuff and then installs a package, the requirements from
        # init would be wrong. Could be an option given to the user though.
        if self.__save_env:
            try:
                requirements = subprocess.check_output(
                    [sys.executable, "-m", "pip", "freeze"], text=True
                )
                self.__save_text(requirements, savedir_path, "requirements.txt")
            except subprocess.CalledProcessError:
                pass

            if "CONDA_PREFIX" in os.environ:
                try:
                    environment = subprocess.check_output(
                        ["conda", "env", "export"], text=True
                    )
                    self.__save_text(environment, savedir_path, "environment.yml")
                except subprocess.CalledProcessError:
                    pass

        plot_module = self.__plot_module
        plot_fun = self.__plot_fun
        if plot_module is not None:
            fun_name = plot_fun.__name__
            module_name = plot_module.__name__
            if module_name == "__main__":
                with open(plot_module.__file__) as f:
                    source = f.read()
            else:
                source = inspect.getsource(plot_module)
            structure = module_name.split(".")
            structure[0] = Path(structure[0])
            rel_path = list(accumulate(structure, func=truediv))[-1]
            self.__save_text(source, savedir_path, rel_path.with_suffix(".py"))

            # If the function and the module don't have the same name, we also save a
            # python file with the name of the function so as to retain this information
            # for recovery.
            if fun_name != module_name:
                content = f"from {module_name} import {fun_name}"
                self.__save_text(content, savedir_path, f"{fun_name}.py")
            # Else, during recovery when we see only one file, we know that we simply
            # have to import from that file the function with the same name.

        elif plot_fun is not None:
            # Just save one file with function definition.
            plot_fun_source = inspect.getsource(plot_fun)
            self.__save_text(plot_fun_source, savedir_path, f"{plot_fun.__name__}.py")

        # Is it worth implementing class specific save formats (for common ones)? Like
        # DataFrames to csv or parquet, which have the advantage of not being
        # Python-specific. Or give the user option to select the save method for
        # specific classes / data objects?
        args_to_save = set(data.keys()) - self.__excluded_args
        for arg in args_to_save:
            value = data[arg]
            if not isinstance(value, self.__excluded_types):
                self.__save_pickle(value, savedir_path, f"{arg}.pickle")

        if self.__zipped:
            with zipfile.ZipFile(savedir_path.with_suffix(".zip"), "w") as zip:
                for file_name, buffer in self.__buffers.items():
                    zip.writestr(file_name, buffer.getvalue())

        self.__buffers.clear()

        rcParams_lines = str(rcParams).replace("#", "").splitlines()
        output_lines = []
        for line in rcParams_lines:
            if line.startswith("axes.prop_cycle"):
                output_lines.append(line)
            elif line == "savefig.bbox: None":
                output_lines.append("savefig.bbox: standard")
            elif not line.startswith("backend"):
                output_lines.append(
                    line.replace("[", "").replace("'", "").replace("]", "")
                )
        rcParams_str = "\n".join(output_lines)
        self.__save_text(rcParams_str, savedir_path, "matplotlibrc", last=True)

    savefig.__doc__ = "\n".join(
        [
            (
                "This extended version also backs up the data needed to reproduce this "
                "figure."
            ),
            Figure.savefig.__doc__ or "",
        ]
    )

    def __save_text(
        self,
        text: str,
        savedir_path: Path,
        rel_file_path: Path | str,
        last: bool = False,
    ):
        path = savedir_path / rel_file_path
        if self.__zipped:
            buffer = io.StringIO()
            buffer.write(text)
            self.__buffers[path.name] = buffer

        else:
            path.parent.mkdir(exist_ok=True, parents=True)
            with open(path, "w") as f:
                f.write(text)

        if self.__verbose:
            _print_structure(rel_file_path, last=last)

    def __save_pickle(self, obj: Any, savedir_path: Path, rel_file_path: Path | str):
        path = savedir_path / rel_file_path
        if self.__zipped:
            buffer = io.BytesIO()
            pickle.dump(obj, buffer)
            self.__buffers[path.name] = buffer

        else:
            path.parent.mkdir(exist_ok=True, parents=True)
            with open(path, "wb") as f:
                pickle.dump(obj, f)

        if self.__verbose:
            _print_structure(rel_file_path)


def _print_structure(rel_file_path, last=False):
    branch = "└──" if last else "├──"
    rel_path_parts = Path(rel_file_path).parts
    str_struct = "\n".join(
        f"{'    ' * (i + 1)}{branch} {part}"
        if i == 0
        else f"    {'|' * (not last)}{'    ' * i}└── {part}"
        for i, part in enumerate(rel_path_parts)
    )
    print(str_struct)

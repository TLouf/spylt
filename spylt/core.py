import inspect
import io
import os
import pickle
import subprocess
import sys
import zipfile
from pathlib import Path

from matplotlib.pyplot import Figure, rcParams


class SpyllingFigure(Figure):
    def __init__(
        self,
        *args,
        plot_func=None,
        data=None,
        as_dir=False,
        zipped=False,
        save_env=True,
        excluded_types=None,
        excluded_args=None,
        verbose=False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.__plot_func = plot_func
        self.__data = data
        self.__as_dir = as_dir
        self.__zipped = zipped
        self.__save_env = save_env
        self.__verbose = verbose
        self.__verbose_print = print if self.__verbose else lambda *a, **k: None
        if excluded_types is None:
            excluded_types = []
        self.__excluded_types = tuple(excluded_types)
        if excluded_args is None:
            excluded_args = []
        self.__excluded_args = set(excluded_args)
        self.__buffers = {}

    def savefig(self, *args, plot_func=None, data=None, **kwargs):
        # savefig first to limit possibility of a bug from our side to impede saving.
        super().savefig(*args, **kwargs)

        plot_func = plot_func or self.__plot_func
        data = data or self.__data or {}
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

        if plot_func is not None:
            plot_func_def = inspect.getsource(plot_func)
            self.__save_text(plot_func_def, savedir_path / f"{plot_func.__name__}.py")

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
        # DataFrames to csv or parquet, which have the advanatge of not being
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

        self.__buffers = {}

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

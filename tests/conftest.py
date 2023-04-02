import subprocess
from pathlib import Path

import pytest

import spylt

# from matplotlib.testing.conftest import (
#     mpl_test_settings,
#     pytest_configure,
#     pytest_unconfigure,
# )


@pytest.fixture
def plot_fun_in_main(tmp_path):
    fig_path = tmp_path / "fig.png"
    fig_path = fig_path.absolute()
    tests_path = Path(spylt.__path__[0]).parent / "tests"
    subprocess.run(["python", str(tests_path / "plot_fun_in_main.py"), str(fig_path)])


@pytest.fixture
def plot_fun_in_interactive(tmp_path):
    fig_path = tmp_path / "fig.png"
    fig_path = fig_path.absolute()
    tests_path = Path(spylt.__path__[0]).parent / "tests"
    with open(tests_path / "plot_fun_in_main.py") as f:
        code = f.read().replace("sys.argv[1]", f"'{fig_path}'")
    subprocess.run(["ipython", "-c", code])

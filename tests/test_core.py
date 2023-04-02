import zipfile
from io import BytesIO
from pathlib import Path

import pytest

import spylt._testing as tm


@pytest.mark.parametrize("fname", ["fig.png", Path("fig.png")])
def test_savefig_fnames(tmp_path, fname):
    fig = tm.spylling_figure()
    fig.savefig(tmp_path / fname)
    assert (tmp_path / "fig.png").exists()
    out_dir = tmp_path / "fig"
    assert out_dir.exists()
    assert set(out_dir.iterdir()) == {out_dir / "matplotlibrc"}


def test_savefig_filelike(tmp_path):
    fig = tm.spylling_figure()
    with open(tmp_path / "fig.png", "wb") as f:
        fig.savefig(f)
    assert (tmp_path / "fig.png").exists()
    out_dir = tmp_path / "fig"
    assert out_dir.exists()
    assert set(out_dir.iterdir()) == {out_dir / "matplotlibrc"}


def test_savefig_buffer():
    fig = tm.spylling_figure()
    buf = BytesIO()
    fig.savefig(buf)


def test_plot_fun_in_module(tmp_path):
    fig = tm.spylling_figure(plot_fun=tm.figure)
    assert tm.get_attr(fig, "plot_fun") == tm.figure
    assert tm.get_attr(fig, "plot_module") == tm

    fig.savefig(tmp_path / "fig.png")
    out_dir = tmp_path / "fig"
    module_path = out_dir / "spylt" / "_testing.py"
    assert set(out_dir.glob("**/*")) == {
        out_dir / "matplotlibrc",
        module_path.parent,
        out_dir / "figure.py",
        module_path,
    }


def test_plot_fun_in_module_sharing_name(tmp_path):
    fig = tm.spylling_figure(plot_fun=tm.fake_module.fake_figure)
    assert tm.get_attr(fig, "plot_fun") == tm.fake_module.fake_figure
    assert tm.get_attr(fig, "plot_module") == tm.fake_module

    fig.savefig(tmp_path / "fig.png")
    out_dir = tmp_path / "fig"
    module_path = out_dir / "fake_figure.py"
    assert set(out_dir.glob("**/*")) == {out_dir / "matplotlibrc", module_path}


def test_plot_fun_as_method(tmp_path):
    fig = tm.spylling_figure(plot_fun=tm.Plot.figure)
    assert tm.get_attr(fig, "plot_fun") == tm.Plot.figure
    assert tm.get_attr(fig, "plot_module") == tm

    fig.savefig(tmp_path / "fig.png")
    out_dir = tmp_path / "fig"
    module_path = out_dir / "spylt" / "_testing.py"
    assert set(out_dir.glob("**/*")) == {
        out_dir / "matplotlibrc",
        module_path.parent,
        out_dir / "figure.py",
        module_path,
    }


def test_plot_fun_in_main(tmp_path, plot_fun_in_main):
    out_dir = tmp_path / "fig"
    assert set(out_dir.glob("**/*")) == {
        out_dir / "matplotlibrc",
        out_dir / "spylling_figure.py",
    }


def test_plot_fun_in_interactive(tmp_path, plot_fun_in_interactive):
    out_dir = tmp_path / "fig"
    assert set(out_dir.glob("**/*")) == {
        out_dir / "matplotlibrc",
        out_dir / "spylling_figure.py",
    }


def test_data_save(tmp_path):
    fig = tm.spylling_figure(data={"arg": 1})
    fig.savefig(tmp_path / "fig.png")
    out_dir = tmp_path / "fig"
    assert set(out_dir.iterdir()) == {out_dir / "matplotlibrc", out_dir / "arg.pickle"}


def test_not_asdir(tmp_path):
    fig = tm.spylling_figure(as_dir=False)
    fig.savefig(tmp_path / "fig.png")
    out_dir = tmp_path
    assert set(out_dir.iterdir()) == {out_dir / "matplotlibrc", out_dir / "fig.png"}


def test_zipped(tmp_path):
    # Add data to make sure `__save_pickle` also works correctly when zipped is True.
    fig = tm.spylling_figure(zipped=True, data={"arg": 1})
    fig.savefig(tmp_path / "fig.png")
    out_fpath = tmp_path / "fig.zip"
    assert out_fpath.exists()
    with zipfile.ZipFile(out_fpath) as zip:
        assert set(zip.namelist()) == {"arg.pickle", "matplotlibrc"}


def test_excluded_args(tmp_path):
    fig = tm.spylling_figure(data={"arg": 1}, excluded_args=["arg"])
    fig.savefig(tmp_path / "fig.png")
    out_dir = tmp_path / "fig"
    assert set(out_dir.iterdir()) == {out_dir / "matplotlibrc"}


def test_excluded_types(tmp_path):
    fig = tm.spylling_figure(data={"arg": 1}, excluded_types=[int])
    fig.savefig(tmp_path / "fig.png")
    out_dir = tmp_path / "fig"
    assert set(out_dir.iterdir()) == {out_dir / "matplotlibrc"}


def test_env_save(tmp_path):
    fig = tm.spylling_figure(save_env=True)
    fig.savefig(tmp_path / "fig.png")
    out_dir = tmp_path / "fig"
    assert set(out_dir.iterdir()) == {
        out_dir / "matplotlibrc",
        out_dir / "requirements.txt",
    }

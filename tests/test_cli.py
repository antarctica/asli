import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


from asli.cli import _parse_args, _top_level_parser, cli


def test_get_cli_lsm_args():
    # test -e flag
    with patch("sys.argv", ["_", "download", "-e"]):
        args = _parse_args(_top_level_parser())

        assert args.e is True
        assert args.area_dict is None

    # test area and border parsing
    test_border = 7.0
    with patch(
        "sys.argv",
        ["_", "download", "--area", "1", "2", "3", "4", "--border", str(test_border)],
    ):
        args = _parse_args(_top_level_parser())

        assert args.area_dict == {"north": 1, "west": 2, "south": 3, "east": 4}
        assert args.border == test_border

    # test that -e overrides --area
    with patch("sys.argv", ["_", "download", "--area", "1", "2", "3", "4", "-e"]):
        args = _parse_args(_top_level_parser())

        assert args.e is True
        assert args.area_dict is None


class TestCliCalc(unittest.TestCase):
    def setUp(self):
        self.lsm_file = str(Path("tests", "fixtures", "test_lsm.nc"))
        self.msl_file = str(Path("tests", "fixtures", "test_era5_msl.nc"))
        self.temp_filename = tempfile.NamedTemporaryFile(delete=False).name

    def tearDown(self):
        os.remove(self.temp_filename)

    def test_cli_calc(self):
        # first without output
        with patch("sys.argv", ["_", "calc", "--mask", self.lsm_file, self.msl_file]):
            cli()

        # then with output
        with patch(
            "sys.argv",
            [
                "_",
                "calc",
                "--output",
                self.temp_filename,
                "--mask",
                self.lsm_file,
                self.msl_file,
            ],
        ):
            cli()


class TestCliPlot(unittest.TestCase):
    def setUp(self):
        self.lsm_file = str(Path("tests", "fixtures", "test_lsm.nc"))
        self.msl_file = str(Path("tests", "fixtures", "test_era5_msl.nc"))
        self.csv_file = str(Path("tests", "fixtures", "test_csv.csv"))

    def tearDown(self):
        pass

    def test_cli_plot_all(self):
        with patch("sys.argv", ["_", "plot", "--mask", self.lsm_file, self.msl_file]):
            cli()

    def test_cli_plot_year(self):
        with patch(
            "sys.argv",
            ["_", "plot", "--year", "2024", "--mask", self.lsm_file, self.msl_file],
        ):
            cli()

    def test_cli_plot_month(self):
        with patch(
            "sys.argv",
            [
                "_",
                "plot",
                "--year",
                "2024",
                "--month",
                "4",
                "--mask",
                self.lsm_file,
                self.msl_file,
            ],
        ):
            cli()

    def test_cli_plot_lines(self):
        with patch(
            "sys.argv",
            [
                "_",
                "plot",
                "--line",
                "--line-column",
                "ActCenPres",
                "--line-column",
                "Lat",
                "--input",
                self.csv_file,
                "--mask",
                self.lsm_file,
                self.msl_file,
            ],
        ):
            cli()

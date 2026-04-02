from pathlib import Path
import unittest

import matplotlib

from asli import ASLICalculator, Plotter


class TestPlotting(unittest.TestCase):
    def setUp(self):
        self.lsm_file = str(Path("tests", "fixtures", "test_lsm.nc"))
        self.msl_file = str(Path("tests", "fixtures", "test_era5_msl.nc"))
        self.csv_file = str(Path("tests", "fixtures", "test_csv.csv"))

        a = ASLICalculator(mask_filename=self.lsm_file, msl_pattern=self.msl_file)
        a.read_mask_data()
        a.read_msl_data()

        a.import_from_csv(self.csv_file)

        self.a = a
        self.plotter = Plotter(self.a)

    def tearDown(self):
        return super().tearDown()

    def test_plot_all(self):
        fig, ax = self.plotter.plot_all()

        assert isinstance(fig, matplotlib.figure.Figure)
        assert isinstance(ax, matplotlib.axes.Axes)

    def test_plot_year(self):
        fig, ax = self.plotter.plot_year(year=2024)

        assert isinstance(fig, matplotlib.figure.Figure)
        assert isinstance(ax, matplotlib.axes.Axes)

    def test_plot_month(self):
        fig, ax = self.plotter.plot_month(year=2024, month=4)

        assert isinstance(fig, matplotlib.figure.Figure)
        assert isinstance(ax, matplotlib.axes.Axes)

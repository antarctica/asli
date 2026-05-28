"""Helper functions for plotting ASLI data"""

import math

import cartopy.crs as ccrs
import pandas as pd
import matplotlib
import matplotlib.figure
import numpy as np
import xarray as xr

from .asli import ASLICalculator
from .params import ASL_REGION


LINE_PLOT_COLUMNS = ("ActCenPres", "SectPres", "RelCenPres", "longitude", "latitude")
LINE_PLOT_ALIASES = {
    "actcenpres": "ActCenPres",
    "actual_central_pressure": "ActCenPres",
    "sectpres": "SectPres",
    "sector_pressure": "SectPres",
    "relcenpres": "RelCenPres",
    "relative_central_pressure": "RelCenPres",
    "lon": "longitude",
    "long": "longitude",
    "longitude": "longitude",
    "lat": "latitude",
    "latitude": "latitude",
}
LINE_PLOT_LABELS = {
    "ActCenPres": "Actual central pressure (hPa)",
    "SectPres": "Sector pressure (hPa)",
    "RelCenPres": "Relative central pressure (hPa)",
    "longitude": "Longitude (degrees east)",
    "latitude": "Latitude (degrees north)",
}


class Plotter:
    def __init__(
        self,
        aslicalculator: ASLICalculator,
    ):
        """Plot monthly pressure contour plots with points marked as crosses."""

        self.da = aslicalculator.masked_msl_data
        self.df = aslicalculator.minima_df

    @staticmethod
    def draw_regional_box(
        ax: matplotlib.axes.Axes,
        region: dict,
    ):
        """
        Draw box around a region on a map.

        Args:
            ax (matplotlib.axes.Axes): axes object on which to plot box.
            region (dict): keys west,east,south,north containing numeric values of the extent in latitude and longitude.
        """

        transform = ccrs.PlateCarree()

        ax.plot(
            [region["west"], region["west"]],
            [region["south"], region["north"]],
            "k-",
            transform=transform,
            linewidth=1,
        )
        ax.plot(
            [region["east"], region["east"]],
            [region["south"], region["north"]],
            "k-",
            transform=transform,
            linewidth=1,
        )

        for i in range(int(region["west"]), int(region["east"])):
            ax.plot(
                [i, i + 1],
                [region["south"], region["south"]],
                "k-",
                transform=transform,
                linewidth=1,
            )
            ax.plot(
                [i, i + 1],
                [region["north"], region["north"]],
                "k-",
                transform=transform,
                linewidth=1,
            )

    def plot_month(
        self,
        year: int,
        month: int,
        ax: matplotlib.axes.Axes = None,
        width: float = 20,
        height: float = 15,
        cmap: str = "Reds",
        colorbar: bool = False,
        border: int = 10,
        regionbox: dict = ASL_REGION,
        coastlines: bool = False,
        point_color: str = "k",
        point_cmap: str = "gray",
        coastline_resolution: str = "110m",
        min: float = None,
        max: float = None,
        levels: int = 20,
    ):
        """
        Core plotting function. Plot a single month of pressure fields and minima from self.da and self.df.

        Args:
            year (int): Year to plot from self.da
            month (int): Month to plot from self.da
            ax (matplotlib.axes.Axes, optional): axes object to use for plot, if not supplied, one will be created. Primarily used for multi-plot figures/subplots.
            cmap (str, optional): matplotlib-valid colormap string for contour plots. Defaults to "Reds".
            border (int, optional): border around each plot. Defaults to 10.
            regionbox (dict, optional): plot a black box around region. Defaults to asli.params.ASL_REGION.
            coastlines (bool, optional): show coastlines. Defaults to False.
            point_color (str, optional): used when one point per month, colour of marker, must be matplotlib-valid color string. Defaults to "k".
            point_cmap (str, optional): used when multiple points per month. must be matplotlib-valid colormap. Defaults to "gray".
            coastline_resolution (str, optional): resolution for coastlines as taken by cartopy.mpl.geoaxes.GeoAxes.coastlines, default: "110m"
            min (float, optional): minimum value in colormap, if not provided, will be calculated. Primarily used for multi-plot figures.
            max (float, optional): maximum value in colormap, if not provided, will be calculated. Primarily used for multi-plot figures.
            levels (int, optional): Number of levels in contour plot.

        Returns:
            fig (matplotlib.figure.Figure): figure object
            ax (matplotib.axes.Axes): axis object
        """
        # If no axes provided, create a new standalone figure
        if ax is None:
            fig = matplotlib.figure.Figure(figsize=(width, height))
            ax = fig.add_subplot(
                projection=ccrs.Stereographic(
                    central_longitude=0.0, central_latitude=-90.0
                )
            )

        else:
            fig = ax.get_figure()

        # get correct time slice from da
        da_2D = self.da.sel(valid_time=f"{year}-{month:02}-01")

        # get spatial extent of da
        da_2D = da_2D.sel(
            latitude=slice(regionbox["north"] + border, regionbox["south"] - border),
            longitude=slice(regionbox["west"] - border, regionbox["east"] + border),
        )

        # set extent of plot
        if regionbox:
            ax.set_extent(
                [
                    regionbox["west"] - border,
                    regionbox["east"] + border,
                    regionbox["south"] - border,
                    regionbox["north"] + border,
                ],
                ccrs.PlateCarree(),
            )

        if min is None:
            min = np.nanmin(da_2D.values)

        if max is None:
            max = np.nanmax(da_2D.values)

        # add filled contour plot
        co = da_2D.plot.contourf(
            x="longitude",
            y="latitude",
            ax=ax,
            cmap=cmap,
            transform=ccrs.PlateCarree(),
            add_colorbar=False,
            levels=np.linspace(min, max, levels),
        )

        if colorbar:
            fig.colorbar(co, ax=ax, label="Mean Sea Level Pressure (hPa)")

        if coastlines:
            ax.coastlines(resolution=coastline_resolution)

        ## mark pressure minima
        time = pd.to_datetime(da_2D.valid_time.values)
        ax.set_title(time.strftime("%Y-%m"))
        df_single_date = self.df[self.df["time"] == time.strftime("%Y-%m-%d")]
        df_single_date.reset_index(inplace=True)
        num_points = len(df_single_date)
        if num_points > 1:
            # for more than one point, color them in sequence using a colormap
            point_colormap = matplotlib.colormaps[point_cmap].resampled(num_points)
            point_color_list = point_colormap(np.linspace(0, 1, num_points))
        else:
            # for a single point, use single color
            point_color_list = [point_color]
        for i in range(num_points):
            ax.plot(
                df_single_date["longitude"][i],
                df_single_date["latitude"][i],
                color=point_color_list[i],
                marker="x",
                transform=ccrs.PlateCarree(),
            )

        if regionbox:
            self.draw_regional_box(ax, regionbox)

        return fig, ax

    def _line_plot_column(self, column: str) -> str:
        """Resolve line plot column names and common aliases."""

        resolved = LINE_PLOT_ALIASES.get(column.lower(), column)
        if resolved not in self.df.columns:
            valid = ", ".join(LINE_PLOT_COLUMNS)
            raise ValueError(f"Column {column!r} not found. Expected one of: {valid}.")
        return resolved

    def plot_line(
        self,
        column: str = "ActCenPres",
        ax: matplotlib.axes.Axes = None,
        width: float = 10,
        height: float = 4,
        marker: str = "o",
        color: str = None,
    ):
        """
        Plot one calculated ASLI value as a time-series line plot.

        Args:
            column (str): Data column or alias to plot. Common choices are
                ActCenPres, SectPres, RelCenPres, longitude, and latitude.
            ax (matplotlib.axes.Axes, optional): axes object to use for plot.
            width (float, optional): figure width when ax is not supplied.
            height (float, optional): figure height when ax is not supplied.
            marker (str, optional): matplotlib marker style.
            color (str, optional): matplotlib line color.

        Returns:
            fig (matplotlib.figure.Figure): figure object
            ax (matplotlib.axes.Axes): axis object
        """

        column = self._line_plot_column(column)
        plot_df = self.df.copy()
        plot_df["time"] = pd.to_datetime(plot_df["time"])
        plot_df.sort_values("time", inplace=True)

        if ax is None:
            fig = matplotlib.figure.Figure(figsize=(width, height))
            ax = fig.add_subplot()
        else:
            fig = ax.get_figure()

        plot_kwargs = {"marker": marker}
        if color is not None:
            plot_kwargs["color"] = color
        ax.plot(plot_df["time"], plot_df[column], **plot_kwargs)
        ax.set_xlabel("Time")
        ax.set_ylabel(LINE_PLOT_LABELS.get(column, column))
        ax.set_title(LINE_PLOT_LABELS.get(column, column))
        fig.autofmt_xdate()

        return fig, ax

    def plot_lines(
        self,
        columns: list[str] = None,
        n_cols: int = 1,
        width: float = None,
        height: float = None,
        marker: str = "o",
    ):
        """
        Plot multiple calculated ASLI values as stacked time-series line plots.

        Args:
            columns (list[str], optional): Data columns or aliases to plot.
                Defaults to ActCenPres, SectPres, RelCenPres, longitude, and latitude.
            n_cols (int, optional): Number of subplot columns. Defaults to 1.
            width (float, optional): Figure width. Defaults from n_cols.
            height (float, optional): Figure height. Defaults from row count.
            marker (str, optional): matplotlib marker style.

        Returns:
            fig (matplotlib.figure.Figure): figure object
            axes (list[matplotlib.axes.Axes]): line plot axes
        """

        columns = list(columns) if columns is not None else list(LINE_PLOT_COLUMNS)
        columns = [self._line_plot_column(column) for column in columns]
        n_rows = math.ceil(len(columns) / n_cols)
        fig = matplotlib.figure.Figure(
            figsize=(width or n_cols * 10, height or n_rows * 3)
        )

        axes = []
        for i, column in enumerate(columns):
            ax = fig.add_subplot(n_rows, n_cols, i + 1)
            self.plot_line(column=column, ax=ax, marker=marker)
            axes.append(ax)

        fig.tight_layout()

        return fig, axes

    def plot_da(self, da: xr.DataArray, n_cols: int = 3, *args, **kwargs):
        """Plot all the months in the given DataArray, da.

        Args:
            da (xr.DataArray): DataArray to plot.
            n_cols (int): number of columns in which to arrange the plots.
            *args: positional arguments passed to plot_month
            **kwargs: keyword arguments passed to plot_month

        Returns:
            fig (matplotlib.figure.Figure): figure object
            ax (matplotib.axes.Axes): axis object
        """

        # get the min and max values of the range to set consistent color scales
        min = np.nanmin(da.values)
        max = np.nanmax(da.values)

        # if colorbar=True in call to this function, enable for first plot, but disable for the rest
        colorbar = kwargs.pop("colorbar") if kwargs.get("colorbar") else False

        n_months = len(da.valid_time)
        n_rows = math.ceil(n_months / n_cols)
        width = kwargs.get("width", n_cols * 5)
        height = kwargs.get("height", n_rows * 5)

        fig = matplotlib.figure.Figure(figsize=(width, height))

        for i in range(n_months):
            ax = fig.add_subplot(
                n_rows,
                n_cols,
                i + 1,
                projection=ccrs.Stereographic(
                    central_longitude=0.0, central_latitude=-90.0
                ),
            )

            fig, ax = self.plot_month(
                year=int(da.isel(valid_time=i).valid_time.dt.year.values),
                month=int(da.isel(valid_time=i).valid_time.dt.month.values),
                ax=ax,
                width=width,
                height=height,
                min=min,
                max=max,
                colorbar=True if i == 0 and colorbar else False,  # noqa  # if colorbar=True in call to this function, enable for first plot, but disable for the rest
                *args,
                **kwargs,
            )

        return fig, ax

    def plot_year(self, year: int, *args, **kwargs):
        """Plot a single calendar year from the DataArray self.da.

        Args:
            year (int): The year to plot.
            *args: positional arguments passed to plot_month
            **kwargs: keyword arguments passed to plot_month

        Returns:
            fig (matplotlib.figure.Figure): figure object
            ax (matplotib.axes.Axes): axis object
        """
        da_year = self.da.sel(valid_time=slice(f"{year}-01-01", f"{year}-12-01"))

        return self.plot_da(da_year, *args, **kwargs)

    def plot_all(self, *args, **kwargs):
        """Plot all months from the DataArray self.da.

        Args:
            *args: positional arguments passed to plot_month
            **kwargs: keyword arguments passed to plot_month

        Returns:
            fig (matplotlib.figure.Figure): figure object
            ax (matplotib.axes.Axes): axis object
        """
        return self.plot_da(self.da, *args, **kwargs)

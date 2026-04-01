"""Helper functions for plotting ASLI data"""

import cartopy.crs as ccrs
import pandas as pd
import matplotlib
import matplotlib.figure
import numpy as np

from .asli import ASLICalculator
from .params import ASL_REGION


class Plotter:
    def __init__(
        self,
        aslicalculator: ASLICalculator,
    ):
        """Plot monthly pressure contour plots with points marked as crosses."""

        self.da = aslicalculator.masked_msl_data
        self.df = aslicalculator.asl_df

    @staticmethod
    def draw_regional_box(
        ax: matplotlib.axes.Axes,
        region: dict,
        transform: ccrs.Projection = ccrs.PlateCarree(),
    ):
        """
        Draw box around a region on a map

        Args:
            ax
            region (dict): keys west,east,south,north containing numeric values of the extent in latitude and longitude.
        """

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
            year (int)
            month (int)
            ax
            cmap (str, optional): matplotlib-valid colormap string for contour plots. Defaults to "Reds".
            border (int, optional): border around each plot. Defaults to 10.
            regionbox (dict, optional): plot a black box around region. Defaults to asli.params.ASL_REGION.
            coastlines (bool, optional): show coastlines. Defaults to False.
            point_color (str, optional): used when one point per month, colour of marker, must be matplotlib-valid color string. Defaults to "k".
            point_cmap (str, optional): used when multiple points per month. must be matplotlib-valid colormap. Defaults to "gray".
            coastline_resolution (str, optional): resolution for coastlines as taken by cartopy.mpl.geoaxes.GeoAxes.coastlines, default: "110m"
            min (float, optional)
            max
            levels (int, optional)

        Returns:
            fig
            ax
        """
        # If no axes provided, create a new standalone figure
        if ax is None:
            fig = matplotlib.figure.Figure(figsize=(20, 15))
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

    def plot_year(self, year: int, *args, **kwargs):
        # get the min and max values of the range to set consistent color scales
        da_year = self.da.sel(valid_time=slice(f"{year}-01-01", f"{year}-12-01"))
        min = np.nanmin(da_year.values)
        max = np.nanmax(da_year.values)

        # if colorbar=True in call to this function, enable for first plot, but disable for the rest
        colorbar = kwargs.pop("colorbar") if kwargs.get("colorbar") else False

        fig = matplotlib.figure.Figure(figsize=(20, 15))

        for month in range(1, 13):
            ax = fig.add_subplot(
                3,
                4,
                month,
                projection=ccrs.Stereographic(
                    central_longitude=0.0, central_latitude=-90.0
                ),
            )

            fig, ax = self.plot_month(
                year=year,
                month=month,
                ax=ax,
                min=min,
                max=max,
                colorbar=True
                if month == 1 and colorbar
                else False,  # if colorbar=True in call to this function, enable for first plot, but disable for the rest
                *args,
                **kwargs,
            )

        return fig, ax

    def plot_all(self, *args, **kwargs):
        pass

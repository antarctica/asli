"""Perform calculations of the Amundsen Sea Low Index"""

import datetime
import logging
from pathlib import Path
from typing import Mapping, Union
import warnings

import joblib
import pandas as pd
import skimage
from tqdm import tqdm
import xarray as xr

from .params import ASL_REGION, CALCULATION_VERSION, SOFTWARE_VERSION, MASK_THRESHOLD
from .plot import plot_lows
from .utils import tqdm_joblib, configure_s3_bucket

logger = logging.getLogger(__name__)

__all__ = ["ASLICalculator"]


def asl_sector_mean(
    da: xr.DataArray, mask: xr.DataArray, asl_region: Mapping[str, float] = ASL_REGION
) -> xr.DataArray:
    """
    Mean of data array `da`, masked by land-sea mask `mask` within bounded region `asl_region`.
    `asl_region` defaults to Amundsen Sea bounds defined in this package as `ASL_REGION`.
    """

    return (
        da.where(mask < MASK_THRESHOLD)
        .sel(
            latitude=slice(asl_region["north"], asl_region["south"]),
            longitude=slice(asl_region["west"], asl_region["east"]),
        )
        .mean()
        .values
    )


def get_lows(
    da: xr.DataArray,
    mask: xr.DataArray,
    minima: int = 1,
) -> pd.DataFrame:
    """
    Finds local minima in data array da, ignoring land from land-sea mask, mask.

    Args:
        da (xr.DataArray): data array containing mean sea level pressure fields.
        mask (xr.DataArray): data array containing land-sea mask.
        minima (int): Max number of minima to locate in pressure field per time step. Default: 1

    Returns:
        pd.DataFrame: containing columns 'time','longitude','latitude','actual_central_pressure','sector_pressure','relative_central_pressure'
    """

    lons, lats = da.longitude.values, da.latitude.values

    sector_mean_pres = asl_sector_mean(da, mask)
    threshold = sector_mean_pres

    # Converting to datetime and dropping hourly data, not required
    datetime_values = pd.to_datetime(da.valid_time.values)
    time_str = datetime_values.strftime("%Y-%m-%d")

    # ensure that expver value of mask doesn't impact masking
    mask = mask.reset_coords("expver", drop=True)

    # fill land in with highest value to limit lows being found here
    da_max = da.max().values
    da = da.where(mask < MASK_THRESHOLD).fillna(da_max)

    invert_data = (da * -1.0).values  # search for peaks rather than minima

    if threshold is None:
        threshold_abs = invert_data.mean()
    else:
        threshold_abs = (
            threshold * -1
        )  # define threshold cut-off for peaks (inverted lows)

    minima_yx = skimage.feature.peak_local_max(
        invert_data,  # input data
        min_distance=5,  # peaks are separated by at least min_distance
        num_peaks=minima,  # maximum number of peaks
        exclude_border=False,  # excludes peaks from within min_distance pixels of the border
        threshold_abs=threshold_abs,  # minimum intensity of peaks
    )

    minima_lat, minima_lon, pressure = [], [], []
    for minima in minima_yx:
        minima_lat.append(lats[minima[0]])
        minima_lon.append(lons[minima[1]])
        pressure.append(da.values[minima[0], minima[1]])

    df = pd.DataFrame()
    df["latitude"] = minima_lat
    df["longitude"] = minima_lon
    df["actual_central_pressure"] = pressure
    df["sector_pressure"] = sector_mean_pres
    df["time"] = time_str

    if hasattr(da, "expver"):
        if da.expver.values == "0001":
            df["DataSource"] = "ERA5"
        elif da.expver.values == "0005":
            df["DataSource"] = "ERA5T"
        else:
            df["DataSource"] = str(da.expver.values)
    else:
        logger.warning(
            f"Cannot determine DataSource for {time_str}. Setting DataSource to UNKNOWN for this row."
        )
        df["DataSource"] = "UNKNOWN"
        logger.debug(da)

    ### Add relative central pressure (Hosking et al. 2013)
    df["relative_central_pressure"] = (
        df["actual_central_pressure"] - df["sector_pressure"]
    )

    ### re-order columns
    df = df[
        [
            "time",
            "longitude",
            "latitude",
            "actual_central_pressure",
            "sector_pressure",
            "relative_central_pressure",
            "DataSource",
        ]
    ]

    ### clean-up DataFrame
    df = df.reset_index(drop=True)

    return df


def _get_lows_by_time(
    da: xr.DataArray, slice_by: str, t: int, mask: xr.DataArray, minima: int
):
    if slice_by == "season":
        da_t = da.isel(season=t)
    elif slice_by == "valid_time":
        da_t = da.isel(valid_time=t)

    return get_lows(da_t, mask, minima=minima)


def define_minima_per_time_in_region(
    df: pd.DataFrame,
    region: Mapping[str, float] = ASL_REGION,
    output_all_minima: bool = False,
) -> pd.DataFrame:
    """
    From a dataframe of multiple minima per time period, selects the lowest minimum within each time period,
    contained within bounding box: region (defaults to ASL_REGION)
    """
    ### select only those points within ASL box
    df2 = df[
        (df["longitude"] > region["west"])
        & (df["longitude"] < region["east"])
        & (df["latitude"] > region["south"])
        & (df["latitude"] < region["north"])
    ]

    if not output_all_minima:
        df2 = df2.loc[df2.groupby("time")["actual_central_pressure"].idxmin()]

    df2 = df2.reset_index(drop=True)

    return df2


def slice_region(
    da: xr.DataArray, region: Mapping[str, float] = ASL_REGION, border: int = 8
):
    """
    Select region from within data array, with surrounding border.
    """
    da = da.sel(
        latitude=slice(region["north"] + border, region["south"] - border),
        longitude=slice(region["west"] - border, region["east"] + border),
    )
    return da


def season_mean(ds, calendar="standard"):
    # # Make a DataArray with the number of days in each month, size = len(time)
    # month_length = ds.time.dt.days_in_month

    # # Calculate the weights by grouping by 'time.season'
    # weights = (
    #     month_length.groupby("time.season") / month_length.groupby("time.season").sum()
    # )

    # # Test that the sum of the weights for each season is 1.0
    # np.testing.assert_allclose(weights.groupby("time.season").sum().values, np.ones(4))

    # # Calculate the weighted average
    # return (ds * weights).groupby("time.season").sum(dim="time")

    return ds.resample(time="QS-Mar").mean("time")


class ASLICalculator:
    """
    Object to handle calculations of the Amundsen Sea Low Index
    """

    def __init__(
        self,
        mask_filename: str = "era5_lsm.nc",
        msl_pattern: str = "./data/era5/monthly/era5_mean_sea_level_pressure_monthly_*.nc",
        s3_config_dir: str = Path.home(),
        s3_config_filename: str = ".s3cfg",
    ) -> None:
        self.mask_filename = mask_filename
        self.msl_pattern = msl_pattern

        self.s3_config_dir = s3_config_dir
        self.s3_config_filename = s3_config_filename

        self.land_sea_mask = None
        self.raw_msl_data = None
        self.masked_msl_data = None
        self.sliced_msl = None
        self.sliced_masked_msl = None
        self.asl_df = None

    def read_mask_data(self):
        """
        Reads in the Land-Sea mask file from <mask_filename>
        """
        # Check is the path is an s3 bucket
        if self.mask_filename.startswith("s3://"):
            # Using utility function to set up s3 connection with the config file
            # Passing s3 connection and specifying file bucket
            import s3fs  # noqa
            # import zarr #noqa

            s3_lsm_bucket = s3fs.S3Map(
                self.mask_filename,
                s3=configure_s3_bucket(self.s3_config_dir, self.s3_config_filename),
            )

            # Using open_zarr to read in files, ie. we are expecting .zarr NOT .nc
            self.land_sea_mask = xr.open_zarr(
                s3_lsm_bucket, consolidated=True
            ).lsm.squeeze()
        else:
            self.land_sea_mask = xr.open_dataset(self.mask_filename).lsm.squeeze()

    def read_msl_data(self, include_era5t: bool = False):
        """
        Reads in the MSL (mean sea level pressure) files from <msl_pattern>.
        msl_pattern should be a file path a pattern as taken by xarray.open_mfdataset()
        eg monthly/era5_mean_sea_level_pressure_monthly_*.nc

        Args:
            include_era5t(bool): Controls whether ERA5T initial release data is included. (Default: False)
        """

        if self.land_sea_mask is None:
            logger.error("Must read in land-sea mask before mean sea level data.")
            return

        if self.msl_pattern.startswith("s3://"):
            import s3fs  # noqa
            # import zarr #noqa

            s3_msl_bucket = s3fs.S3Map(
                self.msl_pattern,
                s3=configure_s3_bucket(self.s3_config_dir, self.s3_config_filename),
            )

            # Using open_zarr to read in files, ie. we are expecting .zarr NOT .nc
            self.raw_msl_data = xr.open_zarr(s3_msl_bucket, consolidated=True).msl
        else:
            self.raw_msl_data = xr.open_mfdataset(self.msl_pattern).msl

        # expver coordinate indicates whether data is initial or final release
        # expver=0001 - final, expver=0005 initial
        if hasattr(self.raw_msl_data, "expver") and not include_era5t:
            months = []
            for month in self.raw_msl_data:
                if month.expver.values == "0001":
                    months.append(month)
            self.raw_msl_data = xr.concat(months, dim="valid_time")

        self.masked_msl_data = self.raw_msl_data.where(
            self.land_sea_mask.values < MASK_THRESHOLD
        )

        ### slice area around ASL region
        sliced_msl = slice_region(self.raw_msl_data)
        self.sliced_masked_msl = slice_region(self.masked_msl_data)

        # change units
        sliced_msl = sliced_msl / 100.0
        self.sliced_msl = sliced_msl.assign_attrs(units="hPa")

    def read_data(self, include_era5t: bool = False):
        """
        Convenience method for reading in both mask and msl data files.

        Args:
            include_era5t(bool): Controls whether ERA5T intial release data is included. (Default: False)
        """
        self.read_mask_data()
        self.read_msl_data(include_era5t)

    def calculate(self, n_jobs: int = 1, num_minima: int = 1) -> pd.DataFrame:
        """
        From loaded mean sea level pressure data and land-sea mask, runs the calculation of minima.

        Args:
            n_jobs (int, optional): Number of processes to use for parallel calculation. Defaults to 1.
            minima (int, optimal): Max number of minima to locate in pressure field per time step. Default: 1.

        Returns:
            pd.DataFrame: dataframe containing locations of pressure minima, mean pressure.
        """

        if self.sliced_msl is None:
            raise Exception(
                f"self.sliced_msl is {self.sliced_msl}, have you run .read_data()?"
            )

        if "season" in self.sliced_msl.dims:
            ntime = 4
            slice_by = "season"
        if "valid_time" in self.sliced_msl.dims:
            ntime = self.sliced_msl.valid_time.shape[0]
            slice_by = "valid_time"

        with tqdm_joblib(tqdm(total=ntime)) as progress_bar:  # noqa
            lows_per_time = joblib.Parallel(n_jobs=n_jobs)(
                joblib.delayed(_get_lows_by_time)(
                    self.sliced_msl,
                    slice_by,
                    t,
                    self.land_sea_mask,
                    num_minima,
                )
                for t in range(ntime)
            )

        self.all_lows_dfs = pd.concat(lows_per_time, ignore_index=True)

        self.asl_df = define_minima_per_time_in_region(self.all_lows_dfs)
        return self.asl_df

    def to_csv(self, filepath: str) -> None:
        """Writes out ASLICalculator.asl_df as a CSV file with header.

        Args:
            filepath (str): filepath to write out to.
        """

        # TODO handle source data, time_averaging and writing out all lows
        # if (len(self.all_lows_dfs.time.unique()) < 200):
        #     if '-TESTING' not in version_id:
        #         version_id = version_id+'-TESTING'

        # if header == 'asli':
        #     fname = indata+'/asli_'+time_averaging+'_v'+version_id+'.csv'
        # if header == 'all_lows':
        #     fname = indata+'/all_lows_'+time_averaging+'_v'+version_id+'.csv'

        # Set up jinja
        from jinja2 import Environment, PackageLoader, select_autoescape

        env = Environment(loader=PackageLoader("asli"), autoescape=select_autoescape())
        template = env.get_template("asli_data.csv.template")

        header = template.render(
            calculation_version=CALCULATION_VERSION,
            software_version=SOFTWARE_VERSION,
            date_created=datetime.datetime.now().strftime("%Y%m%d"),
            time_coverage_start=self.asl_df["time"].min(),
            time_coverage_end=self.asl_df["time"].max(),
        )

        logger.info(f"Writing csv to {filepath}")
        with open(filepath, "w") as f:
            f.writelines(header)
            self.asl_df.to_csv(f, index=False, header=None)

    def import_from_csv(
        self, filepath: Union[str, Path], header: int = 33, force: bool = False
    ):
        """
        Import a csv file exported from the .export_df method, for example to plot data from a previous session.

        Args:
            filepath (str|Path, required): Path to csv file containing ASL dataframe.
            header (int, optional): number of header rows in csv. Default: 28
            force (bool, optional): Overwrite existing calculations in this object. Defaults to False.
        """
        if self.asl_df is not None and not force:
            warnings.warn(
                "Calculation dataframe has existing values, set force=True to overwrite with import."
            )
            return

        logger.info(f"Importing ASL values from {filepath}")

        # If we are reading from s3 we will need to call our configuration file
        if str(filepath).startswith("s3://"):
            s3 = configure_s3_bucket(self.s3_config_dir, self.s3_config_filename)

            self.asl_df = pd.read_csv(
                s3.open(filepath, mode="rb"),
                header=header,
            )
        else:
            self.asl_df = pd.read_csv(filepath, header=header)

        self.asl_df.rename(
            columns={
                "time (mo)": "time",
                "longitude (degree)": "longitude",
                "latitude (degree)": "latitude",
                "actual_central_pressure (hPA)": "ActCenPres",
                "sector_pressure (hPA)": "SectPres",
                "relative_central_pressure (hPA) [b]": "RelCenPres",
            },
            inplace=True,
        )

    def plot_region_all(self, **kwargs):
        """Plots mean sea level pressure fields for the Amundsen Sea with identified low pressure and bounding box."""

        if self.asl_df is None:
            raise Warning(
                f"ASL calculation dataframe is {self.as_df}, can not plot. \
                          Try running .calculate() first."
            )
        plot_lows(self.masked_msl_data, self.asl_df, regionbox=ASL_REGION, **kwargs)

    def plot_region_year(self, year: int, **kwargs):
        """As for plot_region_all but selects only year

        Args:
            year (int): year to plot
        """
        if self.asl_df is None:
            raise Warning(
                f"ASL calculation dataframe is {self.as_df}, can not plot. \
                          Try running .calculate() first."
            )

        da = self.masked_msl_data.sel(
            valid_time=slice(str(year) + "0101", str(year) + "1201")
        )

        df = self.asl_df[
            (self.asl_df.time >= str(year) + "-01-01")
            & (self.asl_df.time <= str(year) + "-12-01")
        ]

        return plot_lows(da, df, regionbox=ASL_REGION, **kwargs)

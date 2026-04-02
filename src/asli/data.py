"""Download and organise data for ASLI calculations"""

import logging
from pathlib import Path

import cdsapi

from .params import ASL_REGION, DEFAULT_START_YEAR, DEFAULT_END_YEAR

logger = logging.getLogger(__name__)

__all__ = ["CDSDownloader", "get_era5_monthly", "get_land_sea_mask"]


class CDSDownloader:
    """
    Handles downloading of data from Climate Data Store

    Args:
        data_dir (str): Directory in which to place downloaded data.
        request_params (dict): Dictionary of request parameters to pass to cdsapi
        output_filename (str): name of files when downloaded, relative to data_dir.
        area (dict): Dictionary with keys "north", "south", "east" and "west" defining the area bounds of the downloaded data.
    """

    def __init__(
        self, data_dir: str, request_params: dict, output_filename: str, area: dict
    ):
        self.data_dir = data_dir
        self.request_params = request_params
        self.output_path = Path(self.data_dir, output_filename)

        if area:
            logger.info(f"Downloading with bounding area: {area}")
            self.request_params.update(
                {"area": [area["north"], area["west"], area["south"], area["east"]]}
            )
        else:
            logger.info(
                "No bounding area specified, downloading with no bounding area, i.e. whole earth."
            )

    def download(self):
        """Runs the download from Climate Data Store"""
        logger.debug(f"request_params: {self.request_params}")
        c = cdsapi.Client()
        c.retrieve(
            "reanalysis-era5-single-levels-monthly-means",
            self.request_params,
            self.output_path,
        )


def get_era5_monthly(
    data_dir: str,
    vars: list = ["msl"],
    start_year: int = DEFAULT_START_YEAR,
    end_year: int = DEFAULT_END_YEAR,
    area: dict = ASL_REGION,
    border: float = None,
) -> None:
    """
    Download the ERA5 monthly averaged variables from the Climate Data Store (CDS).
    Uses the CDS API beta and therefore requires CDS account and API key.
    Please see the CDS API documentation: https://cds-beta.climate.copernicus.eu/how-to-api
    If running for the first time, may require agreement to CDS Terms of Use per dataset at https://cds-beta.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-monthly-means?tab=download

    Downloads may queue for a considerable time depending on the CDS.
    Request progress can be tracked through your CDS account at: https://cds-beta.climate.copernicus.eu/requests

    Args:
        data_dir(str): path of data directory
        vars (Sequence[str]): list of strings specifying variables to download. Can be one or more of "msl" (default), "tas", "uas", \
            "vas" corresponding to "mean_sea_level_pressure", "2m_temperature", "10m_u_component_of_wind", and "10m_v_component_of_wind, respectively.
        start_year(int): earliest year of data to download. (Default: 1953)
        start_year(int): latest year of data to download. (Default: current year)
        area(dict): either dictionary containing keys 'north', 'south', 'east', 'west' bounding coordinates of area to download (default) or None.
    """

    variables = [
        "10m_u_component_of_wind" if "uas" in vars else None,
        "10m_v_component_of_wind" if "vas" in vars else None,
        "2m_temperature" if "tas" in vars else None,
        "mean_sea_level_pressure" if "msl" in vars else None,
    ]
    variables = [e for e in variables if e is not None]  # remove None values

    request_params = {
        "format": "netcdf",
        "product_type": "monthly_averaged_reanalysis",
        "variable": variables,
        "year": list(map(str, list(range(start_year, end_year + 1, 1)))),
        "month": [
            "01",
            "02",
            "03",
            "04",
            "05",
            "06",
            "07",
            "08",
            "09",
            "10",
            "11",
            "12",
        ],
        "time": "00:00",
    }

    # make the data subdirectory if needed
    era5_monthly_dir = Path("era5", "monthly")
    Path(data_dir, era5_monthly_dir).mkdir(parents=True, exist_ok=True)

    data_downloader = CDSDownloader(
        data_dir,
        request_params=request_params,
        output_filename=str(
            Path(
                era5_monthly_dir,
                f"era5_{'_'.join(variables)}_monthly_{start_year}-{end_year}.nc",
            )
        ),
        area=_get_request_area(area, border),
    )
    data_downloader.download()


def get_land_sea_mask(
    data_dir: str,
    filename: str = "era5_lsm.nc",
    area: dict = ASL_REGION,
    border: float = None,
):
    """
    Download the ERA5 land-sea mask from the Climate Data Store (CDS).
    Uses the CDS API and therefore requires CDS account and API key.
    Please see the CDS API documentation: https://cds.climate.copernicus.eu/api-how-to
    If running for the first time, may require agreement to CDS T&Cs per dataset. See output for details.

    Downloads may queue for a considerable time depending on the CDS.
    Request progress can be tracked through your CDS account at: https://cds.climate.copernicus.eu/cdsapp#!/yourrequests

    Args:
        data_dir(str): path of data directory
        filename (str): name to give downloaded mask file, relative to data_dir (Default: era5_lsm.nc)
        area(dict): either dictionary containing keys 'north', 'south', 'east', 'west' bounding coordinates of area to download (default) or None.
    """

    request_params = {
        "format": "netcdf",
        "product_type": "monthly_averaged_reanalysis",
        "variable": "land_sea_mask",
        "year": "2023",
        "month": "12",
        "time": "00:00",
    }

    data_downloader = CDSDownloader(
        data_dir,
        request_params=request_params,
        output_filename=filename,
        area=_get_request_area(area, border),
    )
    data_downloader.download()


def _get_request_area(area: dict, border: float) -> dict:
    """Takes a rectangular area and a border width, returning an area dictionary with additional surrounding border.

    Args:
        area (dict): Dictionary with keys "north", "south", "east" and "west" defining the area bounds of the downloaded data.
        border (float): Width of border to add around area.

    Returns:
        dict: Dictionary with keys "north", "south", "east" and "west" defining the area bounds of the downloaded data.
    """

    if area:
        logger.info(
            f"Area of N:{area['north']}, W:{area['west']}, S:{area['south']}, E:{area['east']} specified."
        )
        if border is None:
            request_area = area
        else:
            logger.info(f"Border of {border} specified.")
            request_area = {
                "north": area["north"] + border,
                "south": area["south"] - border,
                "east": area["east"] + border,
                "west": area["west"] - border,
            }
        logger.info(
            f"Requesting: N:{area['north']}, W:{area['west']}, S:{area['south']}, E:{area['east']}."
        )
        return request_area
    else:
        return None

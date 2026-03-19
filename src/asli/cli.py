import argparse
import logging
import os
from pathlib import Path

import matplotlib.pyplot as plt

from .asli import ASLICalculator
from .data import get_land_sea_mask, get_era5_monthly
from .params import ASL_REGION, DEFAULT_START_YEAR, DEFAULT_END_YEAR

logger = logging.getLogger(__name__)


def _cli_common_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Parse command-line args common to calculation and plotting."""
    parser.add_argument(
        "-d",
        "--datadir",
        nargs="?",
        type=str,
        default="./data",
        help="Path to directory in which to put downloaded data. (Default: ./data)",
    )
    parser.add_argument(
        "-m",
        "--mask",
        nargs="?",
        type=str,
        default="era5_lsm.nc",
        help="Land-sea mask file path relative to <datadir>. (Default: era5_lsm.nc)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file path for file, relative to <datadir>.",
    )
    parser.add_argument(
        "msl_files",
        nargs="*",
        type=str,
        help="Path or glob pattern relative to <datadir> for file(s) containing mean sea level pressure.",
    )  # msl files/pattern

    return parser


def _cli_plot(args):
    """Command-line interface to ASLI plotting."""

    a = ASLICalculator(args.datadir, args.mask, args.msl_files[0])
    a.read_mask_data()
    a.read_msl_data()
    # Perform the calculation if no input file is provided
    if args.input:
        a.import_from_csv(args.input)
    else:
        a.calculate()
    # Plot all if no specific year is provided
    if args.year:
        a.plot_region_year(args.year)
    else:
        a.plot_region_all()
    if args.output:
        plt.savefig(os.path.join(args.datadir, args.output))


def _cli_calc(args):
    """Command-line interface to ASL calculation."""

    a = ASLICalculator(args.datadir, args.mask, args.msl_files[0])
    a.read_mask_data()
    a.read_msl_data(include_era5t=args.era5t)
    a.calculate(args.numjobs, num_minima=args.minima)

    if args.output:
        a.to_csv(args.output)


def _cli_get_era5_monthly(args):
    """
    CLI for get_era5_monthly, designed to be used via package entrypoint
    """

    vars = list(filter(None, args.vars.split(",")))
    logger.info(f"variables to download: {', '.join(vars)}")

    get_era5_monthly(
        data_dir=Path(args.datadir),
        vars=vars,
        start_year=args.start,
        end_year=args.end,
        area=args.area_dict,
    )


def _cli_get_land_sea_mask(args):
    """
    CLI for get_land_sea_mask, designed to be used via package entrypoint
    """

    get_land_sea_mask(
        data_dir=Path(args.datadir),
        filename=args.filename,
        area=args.area_dict,
        border=args.border,
    )


def _cli_data_common_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Adds options that are common to the data download CLIs"""

    parser.add_argument(
        "-d",
        "--datadir",
        default="./data",
        help="Path to directory in which to put downloaded data. (Default: ./data)",
    )
    parser.add_argument(
        "-e",
        action="store_true",
        help="Download entire earth. i.e. don't restrict to bounds specified using '-a'.",
    )
    parser.add_argument(
        "-a",
        "--area",
        type=float,
        nargs=4,
        default=[
            ASL_REGION["north"],
            ASL_REGION["west"],
            ASL_REGION["south"],
            ASL_REGION["east"],
        ],
        help=f"Bounding coordinates for data download: N W S E. Optional. Overridden by '-e' option. \
                            (Default: bounds of Amundsen Sea: North: {ASL_REGION['north']}, West: {ASL_REGION['west']}, South: {ASL_REGION['south']}, East: {ASL_REGION['east']})",
    )
    parser.add_argument(
        "-b",
        "--border",
        type=float,
        nargs="?",
        default=0.0,
        help="Additional border around <area> to download in degrees",
    )

    return parser


def cli():
    """Main entrypoint for the CLI. Handles command line arguments and executes the corresponding function."""

    parser = argparse.ArgumentParser(prog="asli")
    subparsers = parser.add_subparsers()

    calc_parser = subparsers.add_parser(
        "calc",
        help="Calculates the Amundsen Sea Low from mean sea level pressure fields.",
    )
    calc_parser.set_defaults(func=_cli_calc)
    calc_parser = _cli_common_args(calc_parser)
    calc_parser.add_argument(
        "-e",
        "--era5t",
        action="store_true",
        help="When present, this flag enables the inclusion of ERA5T initial release data as well as finalised ERA5 data.",
    )
    calc_parser.add_argument(
        "-n",
        "--numjobs",
        nargs="?",
        type=int,
        default=1,
        help="Number of processes used by joblib in parallel calculation.",
    )
    calc_parser.add_argument(
        "-M",
        "--minima",
        type=int,
        nargs="?",
        default=1,
        help="Max number of minima to locate in pressure field per time step.",
    )

    plot_parser = subparsers.add_parser(
        "plot", help="Plot Amundsen sea low with mean sea level pressure fields."
    )
    plot_parser.set_defaults(func=_cli_plot)
    plot_parser = _cli_common_args(plot_parser)
    plot_parser.add_argument(
        "-i",
        "--input",
        nargs="?",
        type=str,
        help="Input CSV file, relative to <datadir>.",
    )
    plot_parser.add_argument(
        "-y",
        "--year",
        nargs="?",
        type=int,
        help="When present, plot only the year specified",
    )

    lsm_parser = subparsers.add_parser(
        "lsm",
        help="Downloads the ERA5 land-sea mask from the Climate Data Store (CDS). \
                                Uses the CDS API and therefore requires CDS account and API key. \
                                Please see the CDS API documentation: https://cds.climate.copernicus.eu/api-how-to \
                                If running for the first time, may require agreement to CDS T&Cs per dataset. See output for details. \
                                \n \
                                Downloads may queue for a considerable time depending on the CDS. \
                                Request progress can be tracked through your CDS account at: https://cds.climate.copernicus.eu/cdsapp#!/yourrequests",
    )
    lsm_parser.set_defaults(func=_cli_get_land_sea_mask)
    lsm_parser = _cli_data_common_args(lsm_parser)
    lsm_parser.add_argument(
        "-f",
        "--filename",
        default="era5_lsm.nc",
        help="Filename for data once downloaded. (Default: era5_lsm.nc)",
    )

    era5_parser = subparsers.add_parser(
        "data",
        help="Downloads the ERA5 monthly averaged data from the Climate Data Store (CDS). \
                                Uses the CDS API and therefore requires CDS account and API key. \
                                Please see the CDS API documentation: https://cds.climate.copernicus.eu/api-how-to \
                                If running for the first time, may require agreement to CDS T&Cs per dataset. See output for details. \
                                \n \
                                Downloads may queue for a considerable time depending on the CDS. \
                                Request progress can be tracked through your CDS account at: https://cds.climate.copernicus.eu/cdsapp#!/yourrequests",
    )
    era5_parser.set_defaults(func=_cli_get_era5_monthly)
    era5_parser = _cli_data_common_args(era5_parser)
    era5_parser.add_argument(
        "-v",
        "--vars",
        nargs="?",
        default="msl,",
        help="comma-separated list of strings specifying variables to download. Can be one or more of 'msl' (default), 'tas', 'uas', \
                        'vas' corresponding to 'mean_sea_level_pressure', '2m_temperature', '10m_u_component_of_wind', and '10m_v_component_of_wind', respectively.",
    )
    era5_parser.add_argument(
        "-s",
        "--start",
        default=DEFAULT_START_YEAR,
        type=int,
        help=f"Earliest year to download. (Default: {DEFAULT_START_YEAR})",
    )
    era5_parser.add_argument(
        "-n",
        "--end",
        default=DEFAULT_END_YEAR,
        type=int,
        help=f"Latest year to download. (Default: {DEFAULT_END_YEAR})",
    )

    args = parser.parse_args()

    if args.func is _cli_get_era5_monthly or _cli_get_land_sea_mask:
        if args.e is True:
            logger.info("'-e' flag specified. Will download whole Earth.")
            args.area_dict = None
        else:
            args.area_dict = {
                "north": args.area[0],
                "west": args.area[1],
                "south": args.area[2],
                "east": args.area[3],
            }

    args.func(args)

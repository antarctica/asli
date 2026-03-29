import argparse
import logging
from pathlib import Path

import matplotlib.pyplot as plt

from .asli import ASLICalculator
from .data import get_land_sea_mask, get_era5_monthly
from .params import ASL_REGION, DEFAULT_START_YEAR, DEFAULT_END_YEAR

logger = logging.getLogger(__name__)


def _cli_common_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Parse command-line args common to calculation and plotting."""
    parser.add_argument(
        "-m",
        "--mask",
        nargs="?",
        type=str,
        default="./data/era5_lsm.nc",
        help="Land-sea mask file path. (Default: ./data/era5_lsm.nc)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file path for file.",
    )
    parser.add_argument(
        "msl_files",
        nargs="*",
        type=str,
        help="Path or glob pattern for file(s) containing mean sea level pressure.",
    )  # msl files/pattern

    return parser


def _cli_plot(args):
    """Command-line interface to ASLI plotting."""

    a = ASLICalculator(args.mask, args.msl_files[0])
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
        plt.savefig(args.output)


def _cli_calc(args):
    """Command-line interface to ASL calculation."""

    if not args.output:
        logger.warning("No output file specified. Running calculations without output.")

    a = ASLICalculator(args.mask, args.msl_files[0])
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


def _cli_download(args):
    """Interface for download operation. If --lsm flag is true, download land-sea mask; else download era5 variables."""

    if args.lsm:
        _cli_get_land_sea_mask(args)
    else:
        _cli_get_era5_monthly(args)


def _parse_args(parser: argparse.ArgumentParser):
    """Parse command line arguments using argparse. Structured as this function for ease of testing."""
    args = parser.parse_args()

    # for download function, set the area dict based on options
    if args.func is _cli_download:
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

    return args


def _top_level_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="asli",
        description="Command line interface to download source data, calculate and plot pressure minima using asli.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # subcommand for downloading data
    download_parser = subparsers.add_parser(
        "download",
        help="Download ERA5 or land-sea mask data from the Climate Data Store.",
        description="Downloads the ERA5 monthly averaged data or land-sea mask from the Climate Data Store (CDS). \
                    Uses the CDS API and therefore requires CDS account and API key. \
                    Please see the CDS API documentation: https://cds.climate.copernicus.eu/how-to-api \
                    If running for the first time, may require agreement to CDS T&Cs per dataset. See output for details. \
                    \n \
                    Downloads may queue for a considerable time depending on the CDS. \
                    Request progress can be tracked through your CDS account at: https://cds.climate.copernicus.eu/requests",
    )
    download_parser.set_defaults(func=_cli_download)
    download_parser.add_argument(
        "-d",
        "--datadir",
        default="./data",
        help="Path to directory in which to put downloaded data. (Default: ./data)",
    )
    download_parser.add_argument(
        "-e",
        action="store_true",
        help="Download entire earth. i.e. don't restrict to bounds specified using '-a'.",
    )
    download_parser.add_argument(
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
    download_parser.add_argument(
        "-b",
        "--border",
        type=float,
        nargs="?",
        default=0.0,
        help="Additional border around <area> to download in degrees",
    )
    download_parser.add_argument(
        "--lsm",
        action="store_true",
        help="Download the land-sea mask, instead of the era5 variables. If this flag is present, vars, start, end will be ignored.",
    )
    download_parser.add_argument(
        "-v",
        "--vars",
        nargs="?",
        default="msl,",
        help="comma-separated list of strings specifying variables to download. Can be one or more of 'msl' (default), 'tas', 'uas', \
                        'vas' corresponding to 'mean_sea_level_pressure', '2m_temperature', '10m_u_component_of_wind', and '10m_v_component_of_wind', respectively.",
    )
    download_parser.add_argument(
        "-s",
        "--start",
        default=DEFAULT_START_YEAR,
        type=int,
        help=f"Earliest year to download. (Default: {DEFAULT_START_YEAR})",
    )
    download_parser.add_argument(
        "-n",
        "--end",
        default=DEFAULT_END_YEAR,
        type=int,
        help=f"Latest year to download. (Default: {DEFAULT_END_YEAR})",
    )

    # subcommand for running calculations
    calc_parser = subparsers.add_parser(
        "calc",
        help="Calculates the pressure minima index from mean sea level pressure fields.",
        description="",
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

    # subcommand for plotting
    plot_parser = subparsers.add_parser(
        "plot",
        help="Plot pressure minima with mean sea level pressure fields.",
        description="Takes an input CSV file containing pressure minima (output from calc subcommand) and mean sea level pressure field data and plots the output to file.",
    )
    plot_parser.set_defaults(func=_cli_plot)
    plot_parser = _cli_common_args(plot_parser)
    plot_parser.add_argument(
        "-i",
        "--input",
        nargs="?",
        type=str,
        help="Path to input CSV file.",
    )
    plot_parser.add_argument(
        "-y",
        "--year",
        nargs="?",
        type=int,
        help="When present, plot only the year specified",
    )

    return parser


def cli():
    """Main entrypoint for the CLI. Handles command line arguments and executes the corresponding function."""

    parser = _top_level_parser()

    # parse the command line arguments
    args = _parse_args(parser)

    # call the function specified, with the arguments supplied
    args.func(args)

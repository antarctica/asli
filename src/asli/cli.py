import argparse
import logging
from pathlib import Path


from .asli import ASLICalculator
from .data import get_land_sea_mask, get_era5_monthly
from .params import ASL_REGION, DEFAULT_START_YEAR, DEFAULT_END_YEAR
from .plot import Plotter

logger = logging.getLogger(__name__)


def _cli_common_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Parse command-line args common to calculation and plotting."""
    parser.add_argument(
        "-m",
        "--mask",
        nargs="?",
        type=str,
        default="./data/era5_lsm.nc",
        help="Land-sea mask file path. Default: %(default)s",
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

    # warn against missing input and output commands before anything else happens
    if not args.input:
        logger.warning("No input file specified. Calculating pressure minima.")

    if not args.output:
        logger.warning("No output file specified. Running plots without output.")

    if args.month and not args.year:
        logger.error(
            f"--month option specified (value: {args.month}) but no value for -y/--year, if using month, year must be present also."
        )

    a = ASLICalculator(args.mask, args.msl_files[0])
    a.read_mask_data()
    a.read_msl_data()

    # Perform the calculation if no input file is provided
    if args.input:
        a.import_from_csv(args.input)
    else:
        a.calculate()

    # Plot all if no specific year is provided
    plotter = Plotter(a)
    if args.line:
        logger.info(f"Plotting ASLI line plots from {args.msl_files}.")
        fig, _ = plotter.plot_lines(columns=args.line_columns)
    elif args.month and args.year:
        logger.info(f"Plotting for {args.year}-{args.month} from {args.msl_files}.")
        fig, _ = plotter.plot_month(year=args.year, month=args.month, colorbar=True)
    elif args.year:
        logger.info(f"Plotting for {args.year} from {args.msl_files}.")
        fig, _ = plotter.plot_year(args.year, colorbar=True)
    else:
        logger.info(f"Plotting for full range from {args.msl_files}.")
        fig, _ = plotter.plot_all(colorbar=True)

    if args.output:
        logger.info(f"Saving plot to {args.output}")
        fig.savefig(f"{args.output}")


def _cli_calc(args):
    """Command-line interface to ASLI calculation."""

    if not args.output:
        logger.warning("No output file specified. Running calculations without output.")

    a = ASLICalculator(args.mask, args.msl_files[0])
    a.read_mask_data()
    a.read_msl_data(include_era5t=args.era5t)
    a.calculate(n_jobs=args.numjobs, num_minima=args.minima)

    if args.output:
        a.to_csv(
            args.output, header=args.no_header, custom_header_template=args.template
        )


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


def _validate_year(value):
    """Checks if the year is a 4-digit integer."""
    ivalue = int(value)
    if not (1959 <= ivalue <= 3000):
        raise argparse.ArgumentTypeError(f"{value} is not a valid year")
    return ivalue


def _validate_month(value):
    """Checks if the month is between 1 and 12."""
    ivalue = int(value)
    if not (1 <= ivalue <= 12):
        raise argparse.ArgumentTypeError(f"{value} is not a valid month (1-12)")
    return ivalue


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
        help="Path to directory in which to put downloaded data. (Default: %(default)s)",
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
        help="Bounding coordinates for data download: N W S E. Optional. Overridden by '-e' option. \
                            (Default: bounds of Amundsen Sea: %(default)s)",
    )
    download_parser.add_argument(
        "-b",
        "--border",
        type=float,
        nargs="?",
        default=0.0,
        help="Additional border around <area> to download in degrees. Default: %(default)s",
    )
    download_parser.add_argument(
        "--lsm",
        action="store_true",
        help="Download the land-sea mask, instead of the era5 variables. If this flag is present, vars, start, end will be ignored.",
    )
    download_parser.add_argument(
        "-f",
        "--filename",
        default="era5_lsm.nc",
        help="Filename for land sea mask file once downloaded. Not applicable unless --lsm option present. (Default: %(default)s)",
    )
    download_parser.add_argument(
        "-v",
        "--vars",
        nargs="?",
        default="msl,",
        help="comma-separated list of strings specifying variables to download. Can be one or more of 'msl' (default), 'tas', 'uas', \
                        'vas' corresponding to 'mean_sea_level_pressure', '2m_temperature', '10m_u_component_of_wind', and '10m_v_component_of_wind', respectively. \
                            Default: %(default)s",
    )
    download_parser.add_argument(
        "-s",
        "--start",
        default=DEFAULT_START_YEAR,
        type=_validate_year,
        help="Earliest year to download. (Default: %(default)s)",
    )
    download_parser.add_argument(
        "-n",
        "--end",
        default=DEFAULT_END_YEAR,
        type=_validate_year,
        help="Latest year to download. (Default: %(default)s)",
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
        help="Number of processes used by joblib in parallel calculation. Default: %(default)s",
    )
    calc_parser.add_argument(
        "-M",
        "--minima",
        type=int,
        nargs="?",
        default=1,
        help="Max number of minima to locate in pressure field per time step. Default: %(default)s",
    )
    calc_parser.add_argument(
        "-x",
        "--no-header",
        action="store_false",
        help="When present, this flag disables the header in the CSV output.",
    )
    calc_parser.add_argument(
        "-t",
        "--template",
        nargs="?",
        type=str,
        help="Path to a custom jinja2 CSV header template file, containing the variables:  calculation_version, software_version, date_created, time_coverage_start, time_coverage_end.",
    )

    # subcommand for plotting
    plot_parser = subparsers.add_parser(
        "plot",
        help="Plot pressure minima with mean sea level pressure fields. Output to png supported.",
        description="Takes an input CSV file containing pressure minima (output from calc subcommand) and mean sea level pressure field data and plots the output to png.",
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
        type=_validate_year,
        help="When present, plot only the year specified",
    )
    plot_parser.add_argument(
        "--month",
        nargs="?",
        type=_validate_month,
        help="When present, plot only the month specified. Requires --year to be present.",
    )
    plot_parser.add_argument(
        "--line",
        action="store_true",
        help="Plot calculated ASLI values as time-series lines instead of pressure maps.",
    )
    plot_parser.add_argument(
        "--line-column",
        dest="line_columns",
        action="append",
        help="Column or alias to include with --line. May be repeated.",
    )

    return parser


def cli():
    """Main entrypoint for the CLI. Handles command line arguments and executes the corresponding function."""

    parser = _top_level_parser()

    # parse the command line arguments
    args = _parse_args(parser)

    # call the function specified, with the arguments supplied
    args.func(args)


if __name__ == "__main__":
    cli()

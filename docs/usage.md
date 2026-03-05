# Usage

## Installation

We advise installing this package and its dependencies in a python virtual environment using a tool such as [venv](https://docs.python.org/3/library/venv.html) or [conda](https://conda.io/projects/conda/en/latest/user-guide/getting-started.html#managing-python) (other virtual environment managers are available).

Install the package from GitHub using pip:

```sh
pip install git+https://github.com/scotthosking/amundsen-sea-low-index
```

## Overview

The process of running calculations is split into three steps:

1. Download mean sea level pressure and land-sea mask data,
1. Run the calculations of the location and level of the pressure minimum for each month of the time period,
1. Create the output CSV, optionally including plotting.

There are two interfaces provided, a [command-line interface](#command-line-interface) and a [python interface](#python-interface).

Whilst the default behaviour is to download and run the calculations for the bounding box defining the Amundsen Sea (north: -60°, south: -80°, east: 298°, west: 170°); the package will work for any rectangular area.

## Command-line interface

### Downloading data `asli_data_lsm` and `asli_data_era5`
Command-line utilities are provided as a convenient way to download the datasets required for this analysis.

+ `asli_data_lsm` downloads land-sea mask ERA5 data.
+ `asli_data_era5` downloads certain variables from ERA5, by default `mean_sea_level_pressure`.

The `--help` flags can be used to find out more information, e.g.

```sh
asli_data_lsm --help
```

### Running calculations `asli_calc`
A command-line utility is also provided for performing the basic calculations, with a similar help flag:

```sh
asli_calc --help
```

### Plotting `asli_plot`

```sh
asli_plot --help

usage: asli_plot [-h] [-i [INPUT]] [-y [YEAR]] [-d [DATADIR]] [-m [MASK]] [-o OUTPUT] [msl_files ...]

Plot Amundsen sea low with mean sea level pressure fields.

positional arguments:
  msl_files             Path or glob pattern relative to <datadir> for file(s) containing mean sea level
                        pressure.

options:
  -h, --help            show this help message and exit
  -i, --input [INPUT]   Input CSV file, relative to <datadir>.
  -y, --year [YEAR]     When present, plot only the year specified
  -d, --datadir [DATADIR]
                        Path to directory in which to put downloaded data. (Default: ./data)
  -m, --mask [MASK]     Land-sea mask file path relative to <datadir>. (Default: era5_lsm.nc)
  -o, --output OUTPUT   Output file path for file, relative to <datadir>.
```

## Python interface
Alternatively, using the python interface:

### Downloading data

```py
from asli.data import get_land_sea_mask, get_era5_monthly

help(get_land_sea_mask)
...

help(get_era5_monthly)
...
```

### Running calculations

Import the package and create an instance of the `ASLICalculator` class, initialising with the locations of the land-sea mask and mean sea level pressure data:

```py
import asli
a = asli.ASLICalculator(data_dir="./data/",
                   mask_filename="era5_lsm.nc",
                   msl_pattern="era5/monthly/era5_mean_sea_level_pressure_monthly_1988.nc"
                   )
```

then read in the data and perform the calculation:

```py
a.read_mask_data()
a.read_msl_data()
a.calculate()
```

### Outputting data as a csv file and plotting
Once the calculations are done, we can write out the dataframe to a csv file, providing the filename:

```py
a.to_csv('asl.csv')
```

Basic plots of the pressure fields and lows can be made using the `plot_region_all()` and `plot_region_year()` methods.

```py
a.plot_region_all()
```

Optionally, calculations already saved to file can be read back in to a new `ASLCalculator` object with its `import_from_csv()` method, for instance in a new session, for plotting. Note that to plot from a new object, the `read_mask_data()` and `read_msl_data()` (or just `read_data()`) methods will need to be run first, for example:

```py
import asli
b = asli.ASLICalculator(data_dir="./data/",
                   mask_filename="era5_lsm.nc",
                   msl_pattern="era5/monthly/era5_mean_sea_level_pressure_monthly_1988.nc"
                   )
b.read_data()
b.import_from_csv('asl.csv')
b.plot_region_all()
```

## Working with Zarr and Object Storage
The `asli` package also supports Zarr data import from s3 storage through the python interface. The method remains the same, but you will need to install the [s3] optional dependencies.

```sh
pip install git+https://github.com/scotthosking/amundsen-sea-low-index[s3]
```

Additionally you will need to provide the location of your s3 config file, to the `ASLICalculator` class:

```py
from pathlib import Path

a = asli.ASLICalculator(data_dir="s3://asli",
                   mask_filename="zarr-lsm",
                   msl_pattern="zarr-msl",
                   s3_config_dir = Path.home(), # Default location
                   s3_config_filename = ".s3cfg" # Default location
                   )
```

Below is an example of an s3 config file, `~/.s3cfg`. This example is adapted from the [JASMIN documentation on using object storage](https://help.jasmin.ac.uk/docs/short-term-project-storage/using-the-jasmin-object-store/#using-s3cmd). Other object store providers can be used, but the config at a minimum should contain the `[default]` header and provide `access key`, `host_base`, `host_bucket` and `secret_key`.

```txt
[default]
access_key = <access key>
host_base = my-os-tenancy-o.s3-ext.jc.rl.ac.uk
host_bucket = my-os-tenancy-o.s3-ext.jc.rl.ac.uk
secret_key = <secret key>
use_https = True
signature_v2 = False
```

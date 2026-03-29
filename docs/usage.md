# Usage

## Installation

We advise installing this package and its dependencies in a python virtual environment using a tool such as [venv](https://docs.python.org/3/library/venv.html) or [conda](https://conda.io/projects/conda/en/latest/user-guide/getting-started.html#managing-python) (other virtual environment managers are available).

Install the latest version of the package from PyPI using pip:

```sh
pip install asli
```

or from GitHub:

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

Below we show the basic usage of the command-line interface (CLI), for more in-depth information run `asli --help` or the [CLI reference](cli.md).

### Downloading data `asli download`
Command-line utilities are provided as a convenient way to download the datasets required for this analysis.

+ `asli download` downloads certain variables from ERA5, by default `mean_sea_level_pressure`.
+ `asli download --lsm` downloads land-sea mask ERA5 data.

The `--help` flags can be used to find out more information, e.g.

```sh
asli download --help
```

To download the land-sea mask for the Amundsen Sea region to the directory `./data`, run:

```sh
asli download --lsm
```

To download the ERA5 mean sea level pressure data from 1959 (the start of ERA5) to the current year, also to the directory `./data`, run:

```sh
asli download
```

Much of the download behaviour can be customised using flags for the temporal and spatial range as well as to download other variables from the ERA5 monthly averaged dataset. For more in-depth information run `asli --help` or the [CLI reference](cli.md).


### Running calculations `asli calc`
To run the calculations of the locations of each montlhy pressure minimum, using the default options, run:

```sh
asli calc era5/monthly/era5_mean_sea_level_pressure_monthly_1959-2026.nc
```

Additional options at the command line can control:

+ the number of cores used for the parallel computation of the pressure minima,
+ whether or not to include ERA5T non-finalised ERA5 data for recent months,
+ the location of the output file.

### Plotting `asli plot`



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

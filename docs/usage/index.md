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

There are two interfaces provided, a [command-line interface](cli.md) and a [python interface](python.md).

Whilst the default behaviour is to download and run the calculations for the bounding box defining the Amundsen Sea (north: -60°, south: -80°, east: 298°, west: 170°); the package will work for any rectangular area.

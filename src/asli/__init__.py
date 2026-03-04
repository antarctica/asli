"""Amundsen Sea Low detection from mean sea level pressure fields."""

# Import the asli class here for nicer namespace
from .asli import ASLICalculator #noqa

from . import data, plot, utils #noqa

from .params import CALCULATION_VERSION, ASL_REGION, SOFTWARE_VERSION #noqa

import logging
import os
logging.basicConfig(level=os.environ.get('ASLI_LOGLEVEL', 'INFO').upper())

"""
Parameters used by all modules
"""

from datetime import datetime
import importlib.metadata
from types import MappingProxyType

SOFTWARE_VERSION = importlib.metadata.version("bas-asli")

# Version of the calculation method (*NOT* the package version)
CALCULATION_VERSION = "3.20240813"

# Bounds of the Amundsen Sea region
ASL_REGION = MappingProxyType(
    {"west": 170.0, "east": 298.0, "south": -80.0, "north": -60.0}
)

# Threshold for land-sea mask percentage land per pixel
MASK_THRESHOLD = 0.5

# download degault params
DEFAULT_START_YEAR = 1959
DEFAULT_END_YEAR = datetime.now().year

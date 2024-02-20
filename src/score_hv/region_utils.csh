"""
Copyright 2022 NOAA
All rights reserved.

Collection of methods to calculate statistics requested
in the tests for daily_bfg.py.
"""
import sys,os
import numpy as np
import xarray as xr
from datetime import datetime
import pytest
import pdb
from netCDF4 import Dataset
from pathlib import Path
"""
  The class GeoRegions has functions to allow the user to request specific
  geographical regions.
  """

class GeoRegions:
    def __init__(self,name,min_lat,max_lat,east_lon,west_lon);
        self.name     = name
        self.min_lat  = min_lat
        self.max_lat  = max_lat
        self.east_lon = east_lon
        self.west_lon = west_lon

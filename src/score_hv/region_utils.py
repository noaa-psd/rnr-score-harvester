"""
Copyright 2024 NOAA
All rights reserved.

Collection of methods to work with user requested
geographic regions.
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

DEFAULT_MAX_LAT = 90.0
DEFAULT_MIN_LAT = -90.0
DEFAULT_EAST_LON = 0.0
DEFAULT_WEST_LON = 360.0

class GeoRegions:
    def __init__(self):
        """
          Parameters:
          - new_name: Name of the new region.
          - new_min_lat: Minimum latitude of the new region.
          - new_max_lat: Maximum latitude of the new region.
          - new_east_lon: Eastern longitude of the new region.
          - new_west_lon: Western longitude of the new region.
        """
        self.name=[]
        self.min_lat=[]
        self.max_lat=[]
        self.east_lon=[]
        self.west_lon=[]

    def add_user_region(self, new_name, new_min_lat, new_max_lat, \
                        new_east_lon, new_west_lon):
        """
          Calculate a new region based on specified parameters.

          Parameters:
          - new_name: Name of the new region.
          - new_min_lat: Minimum latitude of the new region.
          - new_max_lat: Maximum latitude of the new region.
          - new_east_lon: Eastern longitude of the new region.
          - new_west_lon: Western longitude of the new region.
        """

        if not isinstance(new_name, str):
           msg = f'name must be a string - name {new_name}'
           raise ValueError(msg)

        self.name.append(new_name)
        self.min_lat.append(new_min_lat)
        self.max_lat.append(new_max_lat)
        self.east_lon.append(new_east_lon)
        self.west_lon.append(new_west_lon)

    def get_user_region(self):
        user_regions = []
        for i in range(len(self.name)):
            region_info = {
                'name': self.name[i],
                'min_lat': self.min_lat[i],
                'max_lat': self.max_lat[i],
                'east_lon': self.east_lon[i],
                'west_lon': self.west_lon[i],
            }
        return user_regions 

        

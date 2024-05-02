"""
Copyright 2024 NOAA
All rights reserved.

Collection of methods to work with user requested
geographic regions.
"""
import sys,os
import numpy as np
import xarray as xr
import math
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
    def __init__(self,latitudes,longitudes):
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
        self.latitudes=latitudes
        self.longitudes=longitudes

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
        
        if new_min_lat > new_max_lat:  
           msg = f'minimum latitude must be less than maximum latitude ' \
                 f'min_lat: {new_min_lat}, max_lat: {new_max_lat}'  
           raise ValueError(msg)
         
        if new_min_lat < -90. or new_min_lat > 90.:
           msg = f'minimum latitude must be greater than -90. and less than 90. '\
                 f'min_lat: {new_min_lat}'
           raise ValueError(msg)

        if new_max_lat > 90.0  or new_max_lat < -90.:
           msg = f'maximum latitude must be greater than -90. and less than 90. '\
                 f'max_lat: {new_max_lat}'
           raise ValueError(msg)        
         
        if new_east_lon < 0.0 or new_east_lon > 360.:
           msg = f'east longitude must be greater than 0.0 and less than 360. ' \
                 f'east_lon: {new_east_lon}'
           raise ValueError(msg)
        
        if new_west_lon > 360.0 or  new_west_lon < 0.0:
           msg = f'west longitude must be less than 360.0 and greater than 0.0 ' \
                 f'west_lon: {new_west_lon}'
           raise ValueError(msg)

        self.name.append(new_name)
        self.min_lat.append(new_min_lat)
        self.max_lat.append(new_max_lat)
        self.east_lon.append(new_east_lon)
        self.west_lon.append(new_west_lon)

    def get_region_coordinates(self):
        latitudes = self.latitudes
        longitudes = self.longitudes
        num_lon = len(longitudes)
        num_lat = len(latitudes)
        region_indices = []
        for i in range(len(self.name)):
            min_lat = self.min_lat[i]
            max_lat = self.max_lat[i]
            east_lon = self.east_lon[i]
            west_lon = self.west_lon[i]
            # Find latitude indices within the region
            latitude_indices=[index for index, lat in enumerate(latitudes) if min_lat <= lat <= max_lat]
            """
              The if statement tests to make sure the list,latitude_indices, is not empty.  
              if the list is empty it returns false.  If it is not empty it returns true.
              """
            if latitude_indices:
               lat_start_index = latitude_indices[0]
               lat_end_index = latitude_indices[-1]
            else:
               msg=f"No latitude values found within the specified range of {min_lat} and {max_lat}."
               raise KeyError(msg)
 
            """Find longitude indices within the region. We need to include values of east and west
               that include the prime meridian.
               """
            ieast = (east_lon * num_lon)/360
            jwest = (west_lon * num_lon)/360
            east_index = math.floor(ieast)
            west_index = math.floor(jwest)
            if east_index > west_index:
               temp = east_index
               east_index = west_index
               west_index = temp 
            region_indices.append((lat_start_index, lat_end_index, east_index, west_index))
        
        return region_indices


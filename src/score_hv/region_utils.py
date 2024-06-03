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

"""
  Here we define default latitude and longitude range tuples.
  min lat is -90 and max lat is 90. Tuple is (min_lat,max_lat)
  NOTE: Our longitude on the BFG files goes from 0 to 360 degrees east, circular.
  east_lon = 360 and west lon = 0. Tuple is (east_lon, west_lon)
  """
DEFAULT_LATITUDE_RANGE  = (-90, 90) 
DEFAULT_LONGITUDE_RANGE = (360, 0)

class GeoRegionsCatalog:
    def __init__(self):
        """
          Here we initalize the region class. 
          The variable unmasked_regions is set to all. Meaning, there is
          no masking of land, ocean or ice.  This varaible is set in the
          method check_region_validity in this script below. 
          """
        self.name = []
        self.latitude_tuples = []
        self.longitude_tuples = []

    def test_user_latitudes(self,latitude_range):
        """
          This method tests to make sure the latitude values 
          entered by the user are within the bounds of -90 to 90.
          Also, if the user has not entered latitude values then 
          the default values assigned.
          """
        min_lat, max_lat = latitude_range
        if min_lat < -90 or min_lat > 90:
           msg = f'minimum latitude must be greater than -90. and less than 90. '\
                 f'min_lat: {min_lat}'
           raise ValueError(msg)

        if max_lat < -90 or max_lat > 90:
           msg = f'maximum latitude must be greater than -90 and less than 90. ' \
                 f'max_lat: {max_lat}'
           raise ValueError(msg)

        if min_lat > max_lat:
           msg = f'minimum latitude must be less than maximum latitude ' \
                f'min_lat: {min_lat}, max_lat: {max_lat}'  
           raise ValueError(msg)

    def test_user_longitudes(self,longitude_range):

        east_lon,west_lon = longitude_range
        if east_lon < 0 or east_lon > 360:
           msg = f'east longitude must be greater than 0 and less than 360 '\
                 f'east_lon: {east_lon}'
           raise ValueError(msg)

        if west_lon < 0 or west_lon > 360:
           msg = f'west longitude must be greater than 0 and less than 360 '\
                 f'west_lon: {west_lon}'
           raise ValueError(msg)

    def check_region_validity(self,dictionary):
        """
          Parameters:
          dictionary - The dictionary should contain the following keys.
                       name - name of the region.
                       latitude_range - a tuple of min and max latitude values
                       longitude_range - a tuple of east and west longitude values.
          If the dictionay is empty we exit with a message.             
          If either the latitude or the longitude keys are missing we supply
          a default.

          This method will check to see if the user wants to apply a mask.
          The variable unmasked_regions is set to the area that the user 
          wants to keep.  It is initialized to 'all', meaning that the 
          user does not want to mask out any areas.
          """
        if not dictionary:
            msg = f'The dictionary passed in to check_region_validity is empty'
            raise ValueError(msg)

        print("in check region validity")

        for region_name ,subvalue in dictionary.items():
            """
             Here we test to see if user is missing either the longitude or
             the latitude tuple values by iterating through the dictionary.  
             If either one is missing then we supply the default values.
             If unmasked_regions is either 'land','ocean' or 'ice' then there 
             will not be latitude or longitute region tuples. 
             """
            if "longitude_range" not in subvalue:
                print("missing longitude values. Using defaults of east longitude = 360 and west longitude  = 0")
                longitude_range = DEFAULT_LONGITUDE_RANGE
            else: 
                longitude_range = subvalue.get("longitude_range")
            self.test_user_longitudes(longitude_range)

            if "latitude_range" not in subvalue:    
                print("Latitude range is missing. Using defaults of minimum latitude = -90, maximum latitude = 90")
                latitude_range = DEFAULT_LATITUDE_RANGE 
            else:
                latitude_range = subvalue.get("latitude_range")
            self.test_user_latitudes(latitude_range)
            print("all passed")
            
            self.name.append(region_name)
            self.latitude_tuples.append(latitude_range)
            self.longitude_tuples.append(longitude_range)

    def get_region_coordinates(self,latitude_values,longitude_values):
        """
          This method calculates the indices in the latitude values and
          longitude values that are passed in from the calling function. 
          The latitude and longitude tuples values assigned in the 
          method, add_user_region, above are used to determine the 
          indices.
          Parameters:
          - latitude_values:  These are the array of latitude values from 
            the bfg files opened with xarray.
          - longitude values:  These are the array of longitude values from 
            the bfg files opened with xarray.
          - returns: The lat_indices and lon_indices.  These lists 
            return the start and end indices as tuples. 
            """

        num_lon = len(longitude_values)
        num_lat = len(latitude_values)
        step_size = longitude_values[num_lon-1]/num_lon
        region_indices = {}

        for ireg in range(len(self.name)):
            # Find latitude indices within the region.
            name = self.name[ireg]
            min_lat,max_lat = self.latitude_tuples[ireg]
            latitude_indices = [index for index, lat in enumerate(latitude_values) if min_lat <= lat <= max_lat]
            if latitude_indices:
               lat_start_index = latitude_indices[0]
               lat_end_index = latitude_indices[-1]
            else:
               msg=f"No latitude values were found within the specified range of {min_lat} and {max_lat}."
               raise KeyError(msg)

            """Find longitue indices within the region.
               We have two cases to consider here. 
               Ranges that do not cross the Prime Meridian and ranges that do cross the 
               prime meridian. Our longitude array is 0 to 360 degrees east circular.
                  """
            east_lon,west_lon = self.longitude_tuples[ireg]
            if east_lon <= west_lon:
                #region crosses the prime meridian.
                lon_start_index = int(east_lon / step_size)
                lon_end_index = int(west_lon / step_size)
            else:
                lon_start_index = int(west_lon / step_size) 
                lon_end_index = int(east_lon / step_size)
           
            region_indices[name] = (lat_start_index,lat_end_index,lon_start_index,lon_end_index)
        return region_indices 


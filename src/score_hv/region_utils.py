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
  Here we define default latitude and longitude ranges.
  min lat is -90 and max lat is 90. 
  NOTE: Our longitude on the BFG files goes from 0 to 360 degrees east, circular.
  west long is 0 and east_long is 360. 
  """
NORTH_LAT = 90
SOUTH_LAT = -90
WEST_LONG = 0
EAST_LONG = 360

class GeoRegionsCatalog:
    def __init__(self,dataset):
        """
          Here we initalize the region class as a dictionary.
          Parameter: datset - This is a dataset that has been 
                              opened with xarray.
          """
        self.name = []
        self.north_lat = []
        self.south_lat = []
        self.west_long = []
        self.east_long = []
        self.region_indices = []
        self.latitude_values = dataset['grid_yt'].values
        self.longitude_values = dataset['grid_xt'].values

    def test_user_latitudes(self,north_lat,south_lat):
        """
          This method tests to make sure the latitude values 
          entered by the user are within the bounds of -90 to 90.
          """
        if south_lat < -90 or north_lat > 90:
           msg = f'southern latitude must be greater than -90. and less than 90. '\
                 f'south_lat: {south_lat}'
           raise ValueError(msg)

        if north_lat < -90 or north_lat > 90:
           msg = f'northern latitude must be greater than -90 and less than 90. ' \
                 f'north_lat: {north_lat}'
           raise ValueError(msg)

        if south_lat > north_lat:
           msg = f'southern latitude must be less than northern latitude ' \
                f'south_lat: {south_lat}, north_lat: {north_lat}'  
           raise ValueError(msg)
    
    def test_user_longitudes(self,west_long,east_long):
        """
          This method tests to make sure the longitude values 
          entered by the user are within the bounds of 0 to 360.
          """
        if east_long < 0 or east_long > 360:
           msg = f'east longitude must be greater than 0 and less than 360 '\
                 f'east_long: {east_long}'
           raise ValueError(msg)

        if west_long < 0 or west_long > 360:
           msg = f'west longitude must be greater than 0 and less than 360 '\
                 f'west_long: {west_lon}'
           raise ValueError(msg)


    def add_user_region(self,dictionary):
        """
          Parameters:
          dictionary - The dictionary should contain the following keys.
                       name - name of the region.
                       north_lat - northern most latitude.
                       south_lat - southern most latitude.
                       west_long - westmost longitude.  
                       east_long - eastmost longitude.
          If the dictionay is empty we exit with a message.             
          If the region name key word is missing then we exit with a message.             
          If either the latitude or the longitude keys are missing we supply
          a default.
        """
        if not dictionary:
            msg = f'The dictionary passed in to add_user_region is empty'
            raise ValueError(msg)
        
        for region_name, input_dictionary in dictionary.items():
            if not region_name:
               msg = 'No region name was given. Please enter a name for your region.'
               raise ValueError(msg)
            self.name.append(region_name) 

            required_keywords = {'north_lat','south_lat','west_long','east_long'}
            missing_keys = required_keywords - set(input_dictionary.keys())
            if "north_lat" in missing_keys:
               print("north_lat is missing. Using the default of north latitude = 90")
               north_lat = NORTH_LAT
            else:
               north_lat = input_dictionary.get("north_lat")

            if "south_lat" in missing_keys:
                print("south_lat is missing. Using the default of south latitude = -90")
                south_lat = SOUTH_LAT 
            else:
                south_lat = input_dictionary.get("south_lat")

            if "west_long" in missing_keys:
                print("west_long is missing. Using the default of west longitude = 0")
                west_long = WEST_LONG
            else: 
                west_long = input_dictionary.get("west_long")

            if "east_long" in missing_keys:
                print("east_long is missing. Using the default of east longitude = 360")
                east_long = EAST_LONG
            else: 
                east_long = input_dictionary.get("east_long")
           
            self.test_user_latitudes(north_lat,south_lat)
            self.north_lat.append(north_lat)
            self.south_lat.append(south_lat)

            self.test_user_longitudes(west_long,east_long)
            self.west_long.append(west_long)
            self.east_long.append(east_long)
            
    def get_region_indices(self,region_index):
        """
          This method calculates the indices in the latitude values and
          longitude values that are passed in from the calling function. 
          The latitude and longitude values assigned in the 
          method, add_user_region, above are used to determine the 
          indices.
          Parameters:
          - returns: The lat_indices and lon_indices.  These lists 
            return the start and end indices as tuples. 
            """
        num_long = len(self.longitude_values)
        num_lat = len(self.latitude_values)
        step_size = self.longitude_values[num_long-1]/num_long
        
        # Find latitude indices within the region.
        name = self.name[region_index]
        
        north_lat = self.north_lat[region_index]
        south_lat = self.south_lat[region_index]
        latitude_indices = [index for index, lat in enumerate(self.latitude_values) if south_lat <= lat <= north_lat ]
        if latitude_indices:
           lat_start_index = latitude_indices[0]
           lat_end_index = latitude_indices[-1]
        else:
           msg=f"No latitude values were found within the specified range of {south_lat} and {max_lat}."
           raise KeyError(msg)

       
        """Find longitue indices within the region.
           We have two cases to consider here. 
           Ranges that do not cross the Prime Meridian and ranges that do cross the 
           prime meridian. Our longitude array is 0 to 360 degrees east circular.
           """
        east_long = self.east_long[region_index]
        west_long = self.west_long[region_index]
        if east_long <= west_long:
           #region crosses the prime meridian. So we need to get two separate regions.
           long1_start_index = int(west_long/step_size)
           long1_end_index = num_long - 1
           long2_start_index = 0
           long2_end_index = int(east_long/step_size)
        else:
           long1_start_index = int(west_long / step_size) 
           long1_end_index = int(east_long / step_size)
           long2_start_index = -999
           long2_end_index = -999
        return (lat_start_index,lat_end_index,long1_start_index,long1_end_index,long2_start_index,long2_end_index) 

    def get_region_data(self,region_index,data):
        """ The data.isel is a xarray method that selects a range of indices
            along the grid_yt and grid_xt dimension.
            """
        lat_start_index,lat_end_index,long1_start_index,long1_end_index,long2_start_index, \
        long2_end_index = self.get_region_indices(region_index)
         
        # Check dimensions of the specific variable in the dataset
        var_dims = data.dims
        if 'time' in var_dims:
            if long2_start_index != -999:
               print("crosses")
               region1_data = data.isel(time=slice(None),
                                                   grid_yt=slice(lat_start_index, lat_end_index + 1),
                                                   grid_xt=slice(long1_start_index, long1_end_index))

               region2_data = data.isel(time=slice(None),
                                                   grid_yt=slice(lat_start_index, lat_end_index + 1),
                                                   grid_xt=slice(long2_start_index, long2_end_index))
               region_data = xr.concat([region1_data,region2_data],dim='grid_xt')
               
            else:
               print("does not cross")
               region_data = data.isel(time=slice(None),
                                                   grid_yt=slice(lat_start_index, lat_end_index + 1),
                                                   grid_xt=slice(long1_start_index, long1_end_index))                
        else:
            if long2_start_index != -999:
               region1_data = data.isel(grid_yt=slice(lat_start_index, lat_end_index + 1),
                                                   grid_xt=slice(long1_start_index,long1_end_index)) 

               region2_data = data.isel(grid_yt=slice(lat_start_index, lat_end_index + 1),
                                                   grid_xt=slice(long2_start_index,long2_end_index)) 
           
               region_data = xr.concat([region1_data,region2_data],dim='grid_xt')
            else:
               region_data = data.isel(grid_yt=slice(lat_start_index, lat_end_index + 1),
                                                   grid_xt=slice(long1_start_index,long1_end_index))        
        return(region_data)

         

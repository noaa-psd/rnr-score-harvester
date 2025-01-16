#!/usr/bin/env python

import os
import sys
import ast
import xarray as xr
import numpy as np
import cftime
import copy
from pathlib import Path
from netCDF4 import MFDataset
from datetime import datetime as dt
from collections import namedtuple
from dataclasses import dataclass
from dataclasses import field
from score_hv.config_base  import ConfigInterface
from score_hv.stats_utils  import VarStatsCatalog  
from score_hv.region_utils import GeoRegionsCatalog
from score_hv.mask_utils import MaskCatalog
from score_hv.variable_utils import VarUtilsCatalog


HARVESTER_NAME = 'daily_bfg'
VALID_STATISTICS = ('mean', 'variance', 'minimum', 'maximum')
VALID_REGION_BOUND_KEYS = ('min_lat', 'max_lat', 'west_lon', 'east_lon')
DEFAULT_REGION = {'global': {'north_lat': 90.0, 'south_lat': -90.0, 'west_long': 0.0, 'east_long': 360.0}}
"""
  VALID_VARIABLES are the variables of interest that come from the background forecast data.
"""
VALID_VARIABLES  = (
                    'icetk', # sea ice thickness (m)
                    'lhtfl_ave',# surface latent heat flux (W/m**2)
                    'shtfl_ave', # surface sensible heat flux (W/m**2)
                    'dlwrf_ave', # surface downward longwave flux (W/m**2)
                    'dswrf_ave', # averaged surface downward shortwave flux (W/m**2)
                    'ulwrf_ave', # surface upward longwave flux (W/m**2)
                    'uswrf_ave', # averaged surface upward shortwave flux (W/m**2)
                    'netrf_avetoa',#top of atmosphere net radiative flux (SW and LW) (W/m**2)
                    'netef_ave',#surface energy balance (W/m**2)
                    'nsst', # near sea surface temperature(K), using tref over the ocean only.
                    'prate_ave', # surface precip rate (mm weq. s^-1)
                    'pressfc', # surface pressure (Pa)
                    'snowc_ave', # snow cover -GFS lsm
                    'snod', # surface snow depth (m)
                    'soilm', # total column soil moisture content (mm weq.)
                    'soilt4', # soil temperature unknown layer 4 (K)
                    'sst', # sea surface temperature(K),using tmpsfc over the ocean only.
                    'tg3', # deep soil temperature (K)
                    'tmp2m', # 2m (surface air) temperature (K)
                    'tsnowp', #accumulated surface snow (kg/m**2)
                    'ulwrf_avetoa', # top of atmos upward longwave flux (W m^-2)
                    'weasd', # surface snow water equivalent (kg/m**2)
                    )

HarvestedData = namedtuple('HarvestedData', ['filenames',
                                             'statistic',
                                             'variable',
                                             'value',
                                             'units',
                                             'mediantime',
                                             'longname',
                                             'surface_mask',
                                             'regions'])
def get_gridcell_area_data_path():
    return os.path.join(Path(__file__).parent.parent.resolve(),
                        'data', 'gridcell-area' + 
                        '_noaa-ufs-gefsv13replay-pds' + 
                        '_bfg_control_1536x768_20231116.nc')

def get_median_cftime(xr_dataset):
    """the xr_dataset is a netcdf bfg_xr_dataset.  Where time stamps represent
       end points for the time period.
       """
    temporal_endpoints = np.array([cftime.date2num(time, \
                                   'hours since 1951-01-01 00:00:00') \
                                   for time in xr_dataset['time']])
    num_times = len(temporal_endpoints)
    if  num_times > 1:
        """ can estimate the time step only if there're more than 1
            timestamps
            """
        temporal_midpoints = temporal_endpoints - np.gradient(temporal_endpoints)/2.

        median_cftime = cftime.num2date(np.median(temporal_midpoints), \
                                            'hours since 1951-01-01 00:00:00')
    else:
        median_cftime = cftime.num2date(np.median(temporal_endpoints), \
                                         'hours since 1951-01-01 00:00:00')
    return(median_cftime) 

def calculate_temporal_mean(masked_variable,fraction_data,variable_data,normalized_weights):
    """
       special variable list: ['icetk','nsst','snod','soilm','soilt4','sst','tg3','tsnowp','weasd']
       Parameters:
                masked_variable - masked_variable:
                                  True if the variable name is in the special variable list. 
                                  These variable
                                  are automatically masked before any calculations are done.
                                  True if the user has requested a mask.
                                  False if the user did not request a mask and the variable name
                                  is not as defined above.
                fraction_data - The fraction data is either the land fraction(lfrac) or the 
                                ice fraction(icec).  The fraction data will come in as 
                                as region if the user has requested a reqion and/or masked if the user
                                has requested a mask, or if it is one of the special variables listed above.
                                The fraction data type is <class 'xarray.core.dataarray.DataArray'>
                variable_data - The variable data.
                                The variable data type is <class 'xarray.core.dataarray.DataArray'>
                weights - The area weigths.
                          The area weights type is <class 'xarray.core.dataarray.DataArray'>    
      return: The temporal mean of the region_variable_data as calculated from 
      """
    if masked_variable:  
       weighted_data_sum = ( fraction_data * variable_data * normalized_weights).sum(dim='time', skipna=True)
       normalized_weights_sum = ( fraction_data * normalized_weights).sum(dim='time',skipna=True)
       normalized_weights_sum = normalized_weights_sum.where(normalized_weights_sum != 0, np.nan)
    else: 
       """
         The fraction data is not used if the user has not requested a mask or if the 
         variable is not in the special variable list.  This is because the land fraction
         data has 0 over the ocean.
         """
       weighted_data_sum = ( variable_data * normalized_weights).sum(dim='time', skipna=True)
       normalized_weights_sum = normalized_weights.sum(dim='time',skipna=True)

    value = (weighted_data_sum / normalized_weights_sum).where(normalized_weights_sum != 0, np.nan)
    return(value)

@dataclass
class DailyBFGConfig(ConfigInterface):

    config_data: dict = field(default_factory=dict)

    def __post_init__(self):
        self.set_config()

    def set_config(self):
        """ function to set configuration variables from given dictionary
        """
        self.harvest_filenames=self.config_data.get('filenames')
        self.set_stats()
        self.set_variables()
        self.set_surface_mask()
        self.set_regions()

    def set_variables(self):
        """
        set the variables specified by the config dict
        """
        
        self.variables = self.config_data.get('variable')
        for var in self.variables:
            if var not in VALID_VARIABLES:
                msg = ("'%s' is not a supported "
                       "variable to harvest from the background forecast data. "
                       "Please reconfigure the input dictionary using only the "
                       "following variables: %r" % (var, VALID_VARIABLES))
                raise KeyError(msg)
     
    def get_stats(self):
        ''' return list of all stat types based on harvest_config '''
        return self.stats
   
    def get_masks(self):
        return self.surface_mask

    def set_surface_mask(self):
        self.surface_mask = self.config_data.get('surface_mask')
    
    def get_regions(self):
        ''' return list of regions based on harvest config'''
        return self.regions

    def set_regions(self):
        self.regions = self.config_data.get('regions')
        if self.regions is None:   
           self.regions =  DEFAULT_REGION
           print("Setting a default global region ",self.regions)

    def set_stats(self):
        """
        set the statistics specified by the config dict
        """
        self.stats = self.config_data.get('statistic')
        for stat in self.stats:
            if stat not in VALID_STATISTICS:
                msg = ("'%s' is not a supported statistic to harvest from "
                       "daily mean background forecast data. "
                       "Please reconfigure the input dictionary using only the "
                       "following statistics: %r" % (stat, VALID_STATISTICS))
                raise KeyError(msg)
    
    def get_variables(self):
        ''' return list of all variable types based on harvest_config'''
        return self.variables

@dataclass
class DailyBFGHv(object):
    """ Harvester dataclass used to parse daily mean statistics from 
        background forecast data
    
        Parameters:
        -----------
        config: DailyBFGConfig object containing information used to determine
                which variable to parse the log file
        Methods:
        --------
        get_data: parse descriptive statistics from log files based on input
                  config file
                  returns a list of tuples containing specific data
    """
    config: DailyBFGConfig = field(default_factory=DailyBFGConfig)
     
    def get_data(self):
        """ Harvests requested statistics and variables from background 
            forecast data and returns harvested_data, a list of HarvestData 
            tuples
        
            The below routine extracts timestamps from the input data (forecast 
            files), which are expected to represent the temporal endpoints of 
            the (e.g., 3 hour) forecast window. To calculate the temporal 
            midpoint representative of the whole list of input forecast files,
            the routine estimates the time step using a finite difference
            calculation of the timestamps. Shifting the timestamps by minus
            half of the time step gives the temporal midpoints, which are
            then used to determine the multi-file temporal midpoint.
        """
        harvested_data = list()
       
        xr_dataset = xr.open_mfdataset(self.config.harvest_filenames, 
                                       combine='nested', 
                                       concat_dim='time',
                                       decode_times=True)
        var_utils_catalog = VarUtilsCatalog(xr_dataset)
        num_times = xr_dataset.sizes['time']
        gridcell_area_data = xr.open_dataset(get_gridcell_area_data_path())
        gridcell_area_weights = gridcell_area_data['area']
        """
          For consistancy in the calculations we make the global area weights a
          three dimensionsal data.  The calculations fail at times unless this is
          done.
          """
        global_area_weights = gridcell_area_weights.expand_dims(dim='time', axis=0)
        global_area_weights = xr.concat([global_area_weights] * num_times, dim='time')
        global_area_weights = global_area_weights.assign_coords(time=xr_dataset['time']) 

        median_cftime = get_median_cftime(xr_dataset)
       
        """
          We will always have a least one region so we can initialize the region catalog.
          The regions were gathered in the get_regions method above in the DailyBFGConfig 
          class and are defined in self.config.regions dictionary. 
          """
        regions_catalog = GeoRegionsCatalog(xr_dataset)
        regions_catalog.add_user_region(self.config.regions)
        regions_copy = copy.deepcopy(self.config.regions)

        """
          Get the statistics requested by the user.  
          Instantiate the stats class in stats_util.py.
          Initialize the temporal_means list.  The
          temporal_means are calculated in the stats_util.py
          class and returned.
          """
        stats_list = self.config.get_stats()
        var_stats_catalog = VarStatsCatalog(stats_list,self.config.regions)
      
       
        """
          Initialize the mask class in case we need it. 
          Most all of the mask utilities will need the
          soil type variable. We can store it in the mask
          class. 
          """
        global_soil_type_data = var_utils_catalog.get_soil_type_data()
        mask_instance = MaskCatalog()

        for i, variable in enumerate(self.config.get_variables()):
            """ 
              The first nested loop iterates through each requesed variable.
              """
            namelist=self.config.get_variables()
            var_name=namelist[i]
            global_variable_data,longname,units = var_utils_catalog.extract_variable_info(var_name)
            global_fraction_data = var_utils_catalog.get_fraction_data(var_name) 
            """
              The temporal means is a list which will hold the 
              temporal means calculated in this function.
              The temporal means are passed into the stats_util 
              class in order to calculate the statistics requested
              by the user.
              """
            temporal_means = []
            var_stats_catalog.clear_requested_statistics()
            for iregion in range(len(self.config.regions)): #There is always at least one region.
                region_name = list(self.config.regions.keys())[iregion]
                print(region_name)
                variable_data = regions_catalog.get_region_data(iregion,global_variable_data)
                region_lat = variable_data.grid_yt
                region_lon = variable_data.grid_xt
                # Use the variable_data region as a template for weights,fraction_data, and soil_type_data.
                weights = global_area_weights.sel(grid_yt=region_lat, grid_xt=region_lon)
                fraction_data = global_fraction_data.sel(grid_yt=region_lat, grid_xt=region_lon)
                soil_type_data = global_soil_type_data.sel(grid_yt=region_lat, grid_xt=region_lon) 
                initial_mask_variable = mask_instance.check_variable_to_mask(var_name)
                if initial_mask_variable:
                   is_masked = True
                   masked_variable,masked_fraction,masked_weights = \
                          mask_instance.initial_mask_variable(var_name,variable_data,fraction_data, \
                          weights,soil_type_data)
                   
                   weight_sum = weights.sum(dim=['grid_yt', 'grid_xt'], skipna=True)
                   normalized_weights = xr.where(weight_sum!=0,weights/weight_sum,np.nan)
                   value = calculate_temporal_mean(is_masked,masked_fraction,masked_variable,masked_weights)
                   temporal_means.append(value)
                   var_stats_catalog.calculate_requested_statistics(masked_weights,value,region_name)

                elif self.config.surface_mask != None:
                   is_masked = True
                   mask_instance.check_surface_mask(self.config.surface_mask)
                   for mask in self.config.surface_mask:
                       masked_variable,masked_fraction,masked_weights = \
                            mask_instance.user_mask(mask,variable_data,fraction_data,weights,soil_type_data) 
                       weight_sum = masked_weights.sum(dim=['grid_yt', 'grid_xt'], skipna=True)
                       normalized_weights = xr.where(weight_sum != 0, masked_weights / weight_sum, np.nan)
                       value = calculate_temporal_mean(is_masked,masked_fraction,masked_variable,masked_weights)
                       temporal_means.append(value)
                       var_stats_catalog.calculate_requested_statistics(masked_weights,value,region_name)
                else:
                   is_masked = False
                   mask = 'None'
                   weight_sum = weights.sum(dim=['grid_yt', 'grid_xt'], skipna=True)
                   normalized_weights = xr.where(weight_sum!=0,weights/weight_sum,np.nan)
                   value = calculate_temporal_mean(is_masked,fraction_data,variable_data,normalized_weights)
                   temporal_means.append(value)
                   var_stats_catalog.calculate_requested_statistics(weights,value,region_name)

               # updated_region = var_stats_catalog.regions.get(region_name)
               # print("updated region ",region_name,"  ",updated_region)

            for iregion in range(len(self.config.regions)):
                region_name = list(self.config.regions.keys())[iregion]
                for j, statistic in enumerate(self.config.get_stats()):
                    """ The j loop iterates through each requested 
                        statistic and region.
                        """
                    if statistic == 'mean':
                       value = self.config.regions[region_name]['mean']
                       print(variable,"  ",value)                
                    elif statistic == 'variance':
                       value = self.config.regions[region_name]['variance']         
                                         
                    elif statistic == 'maximum':
                       value = self.config.regions[region_name]['maximum']
                    
                    elif statistic == 'minimum':
                       value = self.config.regions[region_name]['minimum']
                    
                    harvested_data.append(HarvestedData(
                                          self.config.harvest_filenames,
                                          statistic, 
                                          variable,
                                          np.float32(value),
                                          units,
                                          dt.fromisoformat(median_cftime.isoformat()),
                                          longname,
                                          self.config.surface_mask,
                                          regions_copy))
 
      
        gridcell_area_data.close()
        xr_dataset.close()
        return harvested_data

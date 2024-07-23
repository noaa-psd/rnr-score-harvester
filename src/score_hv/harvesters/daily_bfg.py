#!/usr/bin/env python

import os
import sys
import ast
import xarray as xr
import numpy as np
import cftime
from pathlib import Path
from netCDF4 import MFDataset
from datetime import datetime as dt
from collections import namedtuple
from dataclasses import dataclass
from dataclasses import field
from score_hv.config_base  import ConfigInterface
from score_hv.stats_utils  import VarStatsCatalog  
from score_hv.region_utils import GeoRegionsCatalog

HARVESTER_NAME = 'daily_bfg'
VALID_STATISTICS = ('mean', 'variance', 'minimum', 'maximum')
VALID_REGION_BOUND_KEYS = ('min_lat', 'max_lat', 'east_lon', 'west_lon')
DEFAULT_REGION = {'global': {'latitude_range': (-90.0, 90.0), 'longitude_range': (360.0, 0.0)}}

"""Variables of interest that come from the background forecast data.
Commented out variables can be uncommented to generate gridcell weighted
statistics but are in development and are currently not fully supported.
"""
VALID_VARIABLES  = (
                    #'icetk', # sea ice thickness (m)
                    'lhtfl_ave',# surface latent heat flux (W/m**2)
                    'shtfl_ave', # surface sensible heat flux (W/m**2)
                    'dlwrf_ave', # surface downward longwave flux (W/m**2)
                    'dswrf_ave', # averaged surface downward shortwave flux (W/m**2)
                    'ulwrf_ave', # surface upward longwave flux (W/m**2)
                    'uswrf_ave', # averaged surface upward shortwave flux (W/m**2)
                    'netrf_avetoa',#top of atmosphere net radiative flux (SW and LW) (W/m**2)
                    'netef_ave',#surface energy balance (W/m**2)
                    'prateb_ave', # surface precip rate (mm weq. s^-1)
                    #'pressfc', # surface pressure (Pa)
                    #'snod', # surface snow depth (m)
                    #'soil4', # liquid soil moisture at layer-4 (?)
                    #'soilm', # total column soil moisture content (mm weq.)
                    #'soilt4', # soil temperature unknown layer 4 (K)
                    #'tg3', # deep soil temperature (K)
                    'tmp2m', # 2m (surface air) temperature (K)
                    #'tmpsfc', # surface temperature (K)
                    'ulwrf_avetoa', # top of atmos upward longwave flux (W m^-2)
                    #'weasd', # surface snow water equivalent (mm weq.)
                    )

HarvestedData = namedtuple('HarvestedData', ['filenames',
                                             'statistic',
                                             'variable',
                                             'value',
                                             'units',
                                             'mediantime',
                                             'longname',
                                             'regions'])
def get_gridcell_area_data_path():
    return os.path.join(Path(__file__).parent.parent.parent.parent.resolve(),
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

def check_array_dimensions(region_variable,region_weights):
    """
      This method makes sure the dimensions numbers of grid_ny
      and grid_ny are the same after subsetting the region_variable and 
      region weights into the region requested by the user.  
      If they are not the same we need to exit the program.  
      The calculation of the statistics will fail. The time dimensin
      for the weights will be 1.  The time dimension for the region
      variable will equal the number of input bfg netcdf files read in.
      The time dimension inequality is handled later in the code.
      """
    variable_dims = region_variable.dims
    weight_dims = region_weights.dims
    
    try:
        assert variable_dims[1] == weight_dims[1]
    except AssertionError:
        msg = f'Assertion failed: The number of latitudes in the weights array {weight_dims[1]}' \
              f'is not equal to the number of latitudes the variable array {variable.dims[1]}'        
        raise ValueError(msg) 

    try:
        assert variable_dims[2] == weight_dims[2]
    except AssertionError:
        msg = f'Assertion failed: The number of longitudes in the weights array {weight_dims[2]}' \
              f'is not equal to the number of longitudes the variable array {variable.dims[2]}'        
        raise ValueError(msg) 

def calculate_surface_energy_balance(xr_dataset):
    """
       This method calculates the derived variable netef_ave. 
       The required fields are:
       dswrf_ave : averaged surface downward shortwave flux
       dlwrf_ave : surface downward longwave flux
       ulwrf_ave : surface upward longwave flux
       uswrf_ave : averaged surface upward shortwave flux
       shtfl_ave : surface sensible heat flux
       lhtfl_ave : surface latent heat flux
       netef_ave = dswrf_ave + dlwrf_ave - ulwrf_ave - uswrf_ave - shtfl_ave - lhtfl_ave
       """
    dswrf=xr_dataset['dswrf_ave']
    dlwrf=xr_dataset['dlwrf_ave']
    ulwrf=xr_dataset['ulwrf_ave']
    uswrf=xr_dataset['uswrf_ave']
    shtfl=xr_dataset['shtfl_ave']
    lhtfl=xr_dataset['lhtfl_ave']
    netef_ave_data=dswrf + dlwrf - ulwrf - uswrf - shtfl - lhtfl
    return(netef_ave_data)

def calculate_toa_radative_flux(xr_dataset):
    """
       This method calculates the derived variable netef_ave.
       The variable name netrf_avetoa referes to the top of the
       atmosphere (TOA) net radiative energy flux.
       The required fields are:
       dswrf_avetoa:averaged surface downward shortwave flux
       uswrf_avetoa:averaged surface upward shortwave flux
       ulwrf_avetoa:surface upward longwave flux
       netrf_avetoa = dswrf_avetoa - uswrf_avetoa - ulwrf_avetoa
       """
    dswrf=xr_dataset['dswrf_avetoa']
    uswrf=xr_dataset['uswrf_avetoa']
    ulwrf=xr_dataset['ulwrf_avetoa']
    netrf_avetoa=dswrf - uswrf - ulwrf
    return(netrf_avetoa)

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
                which  variable to parse the log file
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
        latitudes = xr_dataset['grid_yt']
        longitudes = xr_dataset['grid_xt']
        gridcell_area_data = xr.open_dataset(get_gridcell_area_data_path())
        gridcell_area_weights = (gridcell_area_data.variables['area'])
        """
          This sum is needed for the calculation of the weighted sum of the regional
          variable data.
          """
        sum_global_weights = gridcell_area_data['area'].sum()
        median_cftime = get_median_cftime(xr_dataset)
        """
          We have a least one region so we can instantiate the region catalog.
          The regions were gathered in the get_regions method above in the DailyBFGConfig class.
          and are defined in self.config.regions dictionary.
          """
        regions_catalog = GeoRegionsCatalog(xr_dataset)
        regions_catalog.add_user_region(self.config.regions)


        for i, variable in enumerate(self.config.get_variables()):
            """ The first nested loop iterates through each requested variable.
               """
            namelist=self.config.get_variables()
            var_name=namelist[i]
            if var_name == "netef_ave":
                 variable_data=calculate_surface_energy_balance(xr_dataset)
                 longname="surface energy balance"
                 units="W/m**2"
            elif var_name == "netrf_avetoa":
                 variable_data=calculate_toa_radative_flux(xr_dataset)
                 longname="Top of atmosphere net radiative flux"
                 units="W/m**2"
            else:     
                 variable_data=xr_dataset[variable]
                 if 'long_name' in variable_data.attrs:
                     longname=variable_data.attrs['long_name']
                 else:
                     longname="None"
                 if 'units' in variable_data.attrs:
                     units=variable_data.attrs['units']
                 else:
                     units="None"
            """
              Get the statistics requested by the user.  
              Instantiate the stats class in stats_util.py.
              Initialize the temporal_means list.  The
              temporal_means are calculated in the stats_util.py
              class and returned.
              """
            stats_list = self.config.get_stats()
            var_stats_instance = VarStatsCatalog(stats_list)
            """
              The temporal means is a list which will hold the 
              temporal means calculated in this function.
              The temporal means are passed into the stats_util 
              class in order to calculate the statistics requested
              by the user.
              """
            temporal_means = []
            for iregion in range(len(self.config.regions)):
                region_variable_data = regions_catalog.get_region_data(iregion, \
                                                                       variable_data)
                region_weights = regions_catalog.get_region_data(iregion,gridcell_area_data)
                """
                  region_weights is an xarray Dataset.  The following line converts the
                  xarray Dataset to a singe xarray DataArray.
                  """
                region_weights = region_weights.to_array()
                check_array_dimensions(region_variable_data,region_weights)
                sum_region_weights = region_weights.sum()
                """
                  The line region_solid_angle calculates the sum of weights for a region, 
                  adjusted by the ratio of the region's weights to the 
                  sum of global weights, and then scaled by the 
                  solid angle of a sphere (which is 4 * np.pi)
                  The sum_global_weights is calculated above. 
                  """
                region_solid_angle = (sum_region_weights / sum_global_weights) * 4 * np.pi
                
                """
                  Calculate the solid angle for each weight in the region.
                  Make sure the calculated region solid angle matches the sum of 
                  the individual weights' solid angles. If it does not we need to 
                  exit with an error.
                  """
                region_solid_angle_sum_of_weights = (region_weights / sum_global_weights) * 4 * np.pi
                if not np.isclose(region_solid_angle, region_solid_angle_sum_of_weights.sum()):
                   raise ValueError(f"The region solid angle {region_solid_angle}" 
                                    f"does not match the sum of the weights" 
                                    f"{region_solid_angle_sum_of_weights.sum()}.")
                # Normalizes the weights based on the solid angle sum.  
                normalized_weights = region_solid_angle_sum_of_weights / region_solid_angle_sum_of_weights.sum() 
                
                # Calculate the temporal mean of the region variable data, skipping NaN values
                region_data_temporal_mean = region_variable_data.mean(dim='time', skipna=True)
                # Mask any invalid values (NaN or Inf) in the temporal mean
                value = np.ma.masked_invalid(region_data_temporal_mean)
                temporal_means.append(value)
                """
                   Here we pass the normalized_weights and the temporal_mean into the 
                   stats class.  
                   Note: we need to "squeeze" the normalized_weights down to just 
                         the numnx and numny value to get rid of the time dimension. 
                         This is done because the temporal_means array does not have the 
                         time dimension. The stats class will give an error when calculating
                         the weighted mean and the variance of the data if the dimensions
                         of the normalized weights and temporal mean are different.
                   """
                if normalized_weights.shape[0] == 1:
                   normalized_weights = normalized_weights.squeeze(axis=0)
                   
                var_stats_instance.calculate_requested_statistics(normalized_weights,value)

            for j, statistic in enumerate(self.config.get_stats()):
                """ The second nested loop iterates through each requested 
                    statistic and regions if the user has requested geographical
                    regions..
                    """
                if statistic == 'mean':
                    value = var_stats_instance.weighted_averages 

                elif statistic == 'variance':
                    value = var_stats_instance.variances

                elif statistic == 'maximum':
                    value = var_stats_instance.maximum
                    
                elif statistic == 'minimum':
                    value = var_stats_instance.minimum

                harvested_data.append(HarvestedData(
                                      self.config.harvest_filenames,
                                       statistic, 
                                       variable,
                                       np.float32(value),
                                       units,
                                       dt.fromisoformat(median_cftime.isoformat()),
                                       longname,
                                       self.config.regions))
       
        gridcell_area_data.close()
        xr_dataset.close()
        return harvested_data

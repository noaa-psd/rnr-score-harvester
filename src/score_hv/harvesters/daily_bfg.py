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
from score_hv.mask_utils import MaskCatalog

HARVESTER_NAME = 'daily_bfg'
VALID_STATISTICS = ('mean', 'variance', 'minimum', 'maximum')
VALID_REGION_BOUND_KEYS = ('min_lat', 'max_lat', 'west_lon', 'east_lon')
DEFAULT_REGION = {'global': {'north_lat': 90.0, 'south_lat': -90.0, 'west_long': 0.0, 'east_long': 360.0}}
"""
  The following variables are automatically masked when they
  are read in.
  Soil variables are soil4,soilm,soilt4 and tg3.
  This mask is different than the user requested mask.
  """  
VARIABLES_TO_MASK = ['soill4', 'soilm', 'soilt4', 'tg3']
VALID_MASKS = ['land','ocean','sea', 'ice']
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
                    'prate_ave', # surface precip rate (mm weq. s^-1)
                    'prateb_ave',# bucket surface precipitation rate
                    #'pressfc', # surface pressure (Pa)
                    #'snod', # surface snow depth (m)
                    'soill4', # liquid soil moisture at layer-4 (?)
                    'soilm', # total column soil moisture content (mm weq.)
                    'soilt4', # soil temperature unknown layer 4 (K)
                    'tg3', # deep soil temperature (K)
                    'tmp2m', # 2m (surface air) temperature (K)
                    'tmpsfc', # surface temperature (K)
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

def check_variable_exists(var_name,dataset_variable_names):
    """
      Checks if a field exists in the xarray dataset. If
      the variable does not exist we exit with a message giving
      the missing variable name.
      Parameters:
      var_name: The name of the variable to check for.
      dataset_variable_names: A list of variables names that are 
                              in the input dataset.
      """
    if var_name not in dataset_variable_names:
        raise KeyError(f"Missing required field in the dataset: {var_name}")
        sys.exit(1)

def calculate_surface_energy_balance(xr_dataset,dataset_variable_names):
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
       Parameter:
       xr_dataset - The entire bfg data set given by the user in the harvested
                    data list.
       Return - The calculated surface energy balance variable.             
       """
    required_variables = ['dswrf_ave', 'dlwrf_ave', 'ulwrf_ave', 'uswrf_ave', 'shtfl_ave', 'lhtfl_ave']   
    for var_name in required_variables:
        check_variable_exists(var_name,dataset_variable_names) 

    dswrf=xr_dataset['dswrf_ave']
    dlwrf=xr_dataset['dlwrf_ave']
    ulwrf=xr_dataset['ulwrf_ave']
    uswrf=xr_dataset['uswrf_ave']
    shtfl=xr_dataset['shtfl_ave']
    lhtfl=xr_dataset['lhtfl_ave']
    netef_ave_data = dswrf + dlwrf - ulwrf - uswrf - shtfl - lhtfl
    return(netef_ave_data)

def calculate_toa_radative_flux(xr_dataset,dataset_variable_names):
    """
       This method calculates the derived variable netef_ave.
       The variable name netrf_avetoa referes to the top of the
       atmosphere (TOA) net radiative energy flux.
       The required fields are:
       dswrf_avetoa:averaged surface downward shortwave flux
       uswrf_avetoa:averaged surface upward shortwave flux
       ulwrf_avetoa:surface upward longwave flux
       netrf_avetoa = dswrf_avetoa - uswrf_avetoa - ulwrf_avetoa
       Parameter:
       xr_dataset - The entire bfg data set given by the user in the harvested
                    data list.
       Return - The calculated the top of atmosphere radiative energy flux.         
       """
    required_variables = ['dswrf_avetoa', 'uswrf_avetoa', 'ulwrf_avetoa']
    for var_name in required_variables:
        check_variable_exists(var_name,dataset_variable_names)

    dswrf=xr_dataset['dswrf_avetoa']
    uswrf=xr_dataset['uswrf_avetoa']
    ulwrf=xr_dataset['ulwrf_avetoa']
    netrf_avetoa=dswrf - uswrf - ulwrf
    return(netrf_avetoa)


def check_array_dimensions(region_variable,region_weights):
    """
      This method makes sure the dimensions numbers of grid_ny
      and grid_ny are the same after subsetting the region_variable and 
      region weights into the region requested by the user.  
      If they are not the same we need to exit the program.  
      The calculation of the statistics will fail. 
      Parameters:
      region_variable - The variable data from the bfg data files
                        that corresponds to the region requested bye
                        the user.
      region_weights - The weights from the weight files that corresponds to 
                       the region requested by the user.
      Return - nothing is returned.                 
      """
    vardims = region_variable.dims
    for dim in vardims:
        if dim in region_variable.coords and dim in region_weights.coords:
           var_coord_values = region_variable.coords[dim].size
           weight_coord_values = region_weights.coords[dim].size
           try:
                assert var_coord_values == weight_coord_values
           except AssertionError:
                msg = (f"Mismatch in coordinate sizes for dimension '{dim}':\n"
                       f"region_variable '{dim}' size: {var_coord_values}\n"
                       f"region_weights '{dim}' size: {weight_coord_values}")
                raise ValueError(msg)           


def calculate_and_normalize_solid_angle(sum_global_weights,region_weights):
    """
       This method calculates the solid angle for the regional weights
       and normalizes them.
       Parameters:
       sum_global_weights - The sum_of_global_weights is is the sum of the 
                            variable "area" in the gridcell area data file.
       region_weights - The region weights are the weights the 
                        gridcell_area data file that corresponds to the region
                        requested by the user. The region weights come in as
                         an xarray Dataset. 
       Return - The normalized weights based on the solid angle is returned.                 
       """
    region_weights = region_weights.to_array()
    sum_region_weights = region_weights.sum()
    """
       The line region_solid_angle calculates the sum of weights for a region, 
       adjusted by the ratio of the region's weights to the 
       sum of global weights, and then scaled by the 
       solid angle of a sphere (which is 4 * np.pi)
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
                           f"does not match the sum of the weights") 
     
    # Normalize the weights based on the solid angle sum.  
    normalized_weights = region_solid_angle_sum_of_weights / region_solid_angle_sum_of_weights.sum()    
    return(normalized_weights) 


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
                       "variablee to harvest from the background forecast data. "
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
        if self.surface_mask != None: 
           for mask in self.surface_mask:
               if mask not in VALID_MASKS:
                  msg = f'The mask: {mask} is not a supported mask. ' \
                        f'Valid masks are: "land, ocean ,sea, ice.'  
                  raise ValueError(msg)
    
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
        # Get the list of variable names in the dataset
        dataset_variable_names = list(xr_dataset.data_vars.keys())
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
          Get the statistics requested by the user.  
          Instantiate the stats class in stats_util.py.
          Initialize the temporal_means list.  The
          temporal_means are calculated in the stats_util.py
          class and returned.
          """
        stats_list = self.config.get_stats()
        var_stats_instance = VarStatsCatalog(stats_list)

        """
          We will always have a least one region so we can instantiate the region catalog.
          The regions were gathered in the get_regions method above in the DailyBFGConfig class.
          and are defined in self.config.regions dictionary.
          """
        regions_catalog = GeoRegionsCatalog(xr_dataset)
        regions_catalog.add_user_region(self.config.regions)

        """
          Here we initialize the MaskCatalog class.
          mask_instance = MaskCatalog().  The sotyp variable
          on the dataset is used to distinguish between 
          land,ocean and ice. 
          ocean = sotyp has vaues of 0
          sea   = sotyp has values of 0
          ice   = sotyp has values of 16
          land  = sotyp has values between ocean and ice.
          """
        soil_type = 'sotyp'  
        check_variable_exists(soil_type,dataset_variable_names) 
        soil_type_variable = xr_dataset['sotyp']  
        mask_instance = MaskCatalog(self.config.surface_mask,soil_type_variable)
        
        for i, variable in enumerate(self.config.get_variables()):
            """ 
              The first nested loop iterates through each requesed variable.
              """
            namelist=self.config.get_variables()
            var_name=namelist[i]
            if var_name == "netef_ave":
                 variable_data = calculate_surface_energy_balance(xr_dataset,dataset_variable_names)
                 longname = "surface energy balance"
                 units = "W/m**2"
            elif var_name == "netrf_avetoa":
                 variable_data = calculate_toa_radative_flux(xr_dataset,dataset_variable_names)
                 longname ="Top of atmosphere net radiative flux"
                 units = "W/m**2"
            else: 
                 check_variable_exists(var_name,dataset_variable_names)
                 variable_data = xr_dataset[variable]
                 if var_name in VARIABLES_TO_MASK:
                    variable_data = mask_instance.initial_mask_of_variable(var_name,variable_data)
                    
                 variable_data = mask_instance.replace_bad_values_with_nan(variable_data)
                 if 'long_name' in variable_data.attrs:
                     longname=variable_data.attrs['long_name']
                 else:
                     longname="None"
                 if 'units' in variable_data.attrs:
                     units=variable_data.attrs['units']
                 else:
                     units="None"
              
            """
              The temporal means is a list which will hold the 
              temporal means calculated in this function.
              The temporal means are passed into the stats_util 
              class in order to calculate the statistics requested
              by the user.
              """
            temporal_means = []
            var_stats_instance.clear_requested_statistics()
            for iregion in range(len(self.config.regions)):
                region_variable_data = regions_catalog.get_region_data(iregion,variable_data)
                region_weights = regions_catalog.get_region_data(iregion,gridcell_area_data)
                check_array_dimensions(region_variable_data,region_weights)
                normalized_weights = calculate_and_normalize_solid_angle(sum_global_weights,region_weights)
                
                if self.config.surface_mask != None:
                   """
                     Subset the soil_type_variable into the region requested by the user.
                     """
                   region_mask = regions_catalog.get_region_data(iregion,soil_type_variable)
                   check_array_dimensions(region_variable_data,region_mask)
                   """
                     Delete the values in the region_mask that are not wanted by the user.
                     """
                   masked_array = mask_instance.user_mask_array(region_mask)
                   masked_array_firsttime = masked_array.isel(time=0)
                   """
                      Adding the drop=False keeps the original xarray.DataArray structure. That is 
                      it keeps the original dimension names and metadata. Where the dimension names 
                      are time,grid_yt,grid_xt.
                      NOTE:region_variable_data is of type xarray.core.dataarray.DataArray
                           landmasks_array is of type xarray.core.dataarray.DataArray.
                           normalized_weights is of type xarray.core.dataarray.DataArray
                      """
                   region_variable_data = region_variable_data.where(masked_array, drop=False)
                   normalized_weights = normalized_weights.where(masked_array_firsttime,drop=False)

                # Compute the mean over the time dimension. 
                value = region_variable_data.mean(dim='time',skipna=True)
                temporal_means.append(value)
                normalized_weights = normalized_weights.squeeze(axis=0)
                """
                   Here we pass the normalized_weights and the temporal_mean into the 
                   stats class.  
                   Note: we had to "squeeze" the normalized_weights down to just 
                         the numnx and numny value to get rid of the time dimension. 
                         This is done because the temporal_means array does not have the 
                         time dimension. The stats class will give an error when calculating
                         the weighted mean and the variance of the data if the dimensions
                         of the normalized weights and temporal mean are different.
                   """
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
                                       self.config.surface_mask,
                                       self.config.regions))
       
        gridcell_area_data.close()
        xr_dataset.close()
        return harvested_data

#!/usr/bin/env python
import os
import sys
import ast
import xarray as xr
import numpy as np
import cftime
import netCDF4
from pathlib import Path
from datetime import datetime as dt
from collections import namedtuple
from dataclasses import dataclass
from dataclasses import field
from score_hv.config_base  import ConfigInterface
from score_hv.stats_utils  import var_statsCatalog
from score_hv.region_utils import GeoRegionsCatalog


HARVESTER_NAME = 'daily_bfg'
VALID_STATISTICS = ('mean', 'variance', 'minimum', 'maximum')
VALID_MASKS = ('land', 'ocean', 'ice')
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
                    'soill4', # liquid soil moisture at layer-4 (?)
                    'soilm', # total column soil moisture content (mm weq.)
                    'soilt4', # soil temperature unknown layer 4 (K)
                    'tg3', # deep soil temperature (K)
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
                                             'surface_mask',
                                             'region'])
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

def check_weights(area_weights,total_original_elements,total_regional_elements):
    """
      This method checks the sum of the weights to make sure the sum
      meets a certain threshold.
      """
    sumweights = area_weights.sum()
    ratio = total_regional_elements / total_original_elements 
    total_solid_angle = ratio * 4 * np.pi 
    try:
      assert sumweights >= 0.999 * total_solid_angle  
      assert sumweights <= 1.001 * total_solid_angle

    except AssertionError as err:
      msg = (f'{gridcell_area_weights}\n'
               f'(gridcell area weights) sum does not equal {total_solid_angle} steradians; '  
               'cannot calculate accurate global/regional weighted statistics')
      raise AssertionError(msg) from err 
    
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
        if self.surface_mask != None: 
           for mask in self.surface_mask:
               if mask not in VALID_MASKS:
                  msg = f'The mask: {mask} is not a supported mask. ' \
                        f'Valid masks are: "land, ocean , ice.'  
                  raise ValueError(msg)

    def get_regions(self):
        ''' return list of regions based on harvest config'''
        return self.regions

    def set_regions(self):
        self.regions = self.config_data.get('region')
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
        if self.config.surface_mask != None:
           land_mask = xr_dataset['land']

        gridcell_area_data=xr.open_dataset(get_gridcell_area_data_path())
        gridcell_area_weights=(gridcell_area_data.variables['area'])
        num_lat = len(latitudes.values)
        num_lon = len(longitudes.values)
        total_original_elements = num_lat * num_lon
        total_regional_elements = total_original_elements
        check_weights(gridcell_area_weights,total_original_elements,total_regional_elements) 
        median_cftime = get_median_cftime(xr_dataset)
        """
          We have a least one region so we can instantiate the region catalog.
          The regions were gathered in the get_regions method above in the DailyBFGConfig class.
          and are defined in self.config.regions dictionary.
          """
        user_regions = self.config.regions
        print(user_regions)
        regions_catalog = GeoRegionsCatalog()
        regions_catalog.check_region_validity(self.config.regions)

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
                 print("before config surface mask ",self.config.surface_mask)
                 if self.config.surface_mask != None:
                     print("in surface mask ",self.config.surface_mask)
                     """
                       The user has requested a mask. Here we keep only the 
                       type of data that the user wants. On the bfg Netcdf file
                       the land mask has: 
                                         0 for ocean
                                         1 for land
                                         2 for ice.
                        The xarray where method in the line below will keep the data 
                        where the land_mask is True and replace the values where it is
                        false with the missing value in the meta data of the bfg file.
                        The "other = value_to_use - This makes sure that the data set fill
                        value or missing value is used where the mask is false.
                        """
                     unmasked_data = xr_dataset[variable]  
                     missing_value = unmasked_data.encoding.get('missing_value',None)
                     fill_value = xr_dataset[variable].attrs.get('_FillValue', None)
                     if missing_value is not None:
                        value_to_use = missing_value 
                     elif fill_value is not None:
                        value_to_use = fill_value
                     else:
                        value_to_use = np.nan
                     if 'land' in self.config.surface_mask:
                        variable_data = xr_dataset[variable].where(land_mask == 1, other=value_to_use)
                        sys.exit(0)
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
            var_stats_instance = var_statsCatalog(stats_list)
            """
              The temporal means is a list which will hold the 
              temporal means calculated in this function.
              The temporal means are passed into the stats_util 
              class in order to calculate the statistics requested
              by the user.
              """
            temporal_means = []
            region_index_values = regions_catalog.get_region_coordinates(latitudes,longitudes)
            print(region_index_values)
            sys.exit(0)
            for name, indices  in region_index_values.items():
                lat_start_index, lat_end_index, east_index, west_index = indices 
                """ The variable_data.isel is a xarray method that selects a range of indices
                    along the grid_yt and grid_xt dimension.
                    """
                var_data = variable_data.isel(time=slice(None), \
                                            grid_yt=slice(lat_start_index,lat_end_index+1), \
                                            grid_xt=slice(east_index,west_index))
                
                weights=gridcell_area_data['area'].isel(grid_yt=slice(lat_start_index,lat_end_index + 1), \
                                                        grid_xt=slice(east_index, west_index))
                value  = np.ma.masked_invalid(var_data.mean(dim='time',skipna=True))
                temporal_means.append(value)
                var_stats_instance.calculate_requested_statistics(var_data,weights,value)
            
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
                                       user_regions))
       
        gridcell_area_data.close()
        xr_dataset.close()
        return harvested_data

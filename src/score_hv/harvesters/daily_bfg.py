#!/usr/bin/env python

import os
import sys
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
from score_hv.stats_utils  import var_stats
from score_hv.innov_netcdf import DEFAULT_REGIONS


HARVESTER_NAME = 'daily_bfg'
VALID_STATISTICS = ('mean', 'variance', 'minimum', 'maximum')
VALID_REGIONS    = ('equatorial', 'global' ,'north_hemis', 'tropics', 'south_hemis')


"""Variables of interest that come from the background forecast data.
Commented out variables can be uncommented to generate gridcell weighted
statistics but are in development and are currently not fully supported.
"""
VALID_VARIABLES  = (
                    #'icetk', # sea ice thickness (m)
                    #'lhtfl_ave', # surface latent heat flux (W m^-2)
                    #'netrf_avetoa',#top of atmoshere net radiative flux (SW and LW) (W/m**2)
                    #'netR',#surface energy balance (W/m**2)
                    'prateb_ave', # surface precip rate (mm weq. s^-1)
                    #'prateb_ave', # bucket surface precip rate (mm weq. s^-1)
                    #'pressfc', # surface pressure (Pa)
                    #'snod', # surface snow depth (m)
                    #'soil4', # liquid soil moisture at layer-4 (?)
                    #'soilm', # total column soil moisture content (mm weq.)
                    #'soilt4', # soil temperature unknown layer 4 (K)
                    #'tg3', # deep soil temperature (K)
                    #'tmp2m', # 2m (surface air) temperature (K)
                    #'tmpsfc', # surface temperature (K)
                    #'weasd', # surface snow water equivalent (mm weq.)
                    )

HarvestedData = namedtuple('HarvestedData', ['filenames',
                                             'statistic',
                                             'variable',
                                             'value',
                                             'units',
                                             'mediantime',
                                             'longname',
                                             'region'])

"""
  Create an instance of the var_stats class so
  so we can use it to calculate statistics. This
  class is defined in src/score_hv.
  """
var_stats_instance = var_stats()

def get_gridcell_area_data_path():
    return os.path.join(Path(__file__).parent.parent.parent.parent.resolve(),
                        'data', 'gridcell-area' + 
                        '_noaa-ufs-gefsv13replay-pds' + 
                        '_bfg_control_1536x768_20231116.nc')
@dataclass
class DailyBFGConfig(ConfigInterface):

    config_data: dict = field(default_factory=dict)

    def __post_init__(self):
        self.set_config()

    def set_config(self):
        """ function to set configuration variables from given dictionary
        """
        self.harvest_filenames = self.config_data.get('filenames')
        self.set_stats()
        self.set_variables()
        self.set_region()

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
    
    def get_region(self):
        ''' return list of regions based on harvest config'''
        return self.config.region

    def set_region(self):
        self.region = self.config_data.get('region')
        print("in ",self.region)
        
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
        harvested_data    = list()
        
        xr_dataset = xr.open_mfdataset(self.config.harvest_filenames, 
                                       combine='nested', 
                                       concat_dim='time',
                                       decode_times=True)

        gridcell_area_data    = xr.open_dataset(get_gridcell_area_data_path())
        gridcell_area_weights = (gridcell_area_data.variables['area'])
        sumweights            = gridcell_area_weights.sum()
        assert sumweights >= 0.999 * 4. * np.pi
        assert sumweights <= 1.001 * 4. * np.pi

        """
          Get the user requested regions.
          """
        num_regions = 0  
        if 'region' in HarvestedData._fields:
            theregions  = self.config.region 
            num_regions = len(theregions)
            print(theregions)
            lat_values  = xr_dataset['grid_yt'].values
            lon_values  = xr_dataset['grid_xt'].values
      
        temporal_endpoints = np.array([cftime.date2num(time,
            'hours since 1951-01-01 00:00:00') for time in xr_dataset['time']])
        
        if len(self.config.harvest_filenames) > 1:
            """ can estimate the time step only if there're more than 1 
                timestamps
            """
            temporal_midpoints = temporal_endpoints - np.gradient(temporal_endpoints)/2.
        
            median_cftime = cftime.num2date(np.median(temporal_midpoints),
                                            'hours since 1951-01-01 00:00:00')
        else:
            median_cftime = cftime.num2date(np.median(temporal_endpoints),
                                            'hours since 1951-01-01 00:00:00')

        for i, variable in enumerate(self.config.get_variables()):
            """ The first nested loop iterates through each requested variable.
               """
            variable_data  = xr_dataset[variable]
            var_mean       = np.ma.masked_invalid(variable_data.mean(dim='time',skipna=True))
            temporal_means = var_mean                                             
            if 'long_name' in variable_data.attrs:
                longname = variable_data.attrs['long_name']
            else:
                longname = "None"
            if 'units' in variable_data.attrs:
                units = variable_data.attrs['units']
            else:
                units = "None"
            
            if num_regions > 0 :
                """Iterate through the DEFAULT_REGIONS list
                   """
                for iregion in range(0,num_regions):
                    user_region_name = theregions[iregion]
                    for region in DEFAULT_REGIONS:
                        if region.name == user_region_name:
                           print(user_region_name)
                           minlat = region.min_lat
                           maxlat = region.max_lat
                           minlon = region.min_lon
                           maxlon = region.max_lon
                           print(minlat,minlon)
                           # Define the latitude and longitude masks
                           lat_mask = (minlat <= lat_values) & (lat_values <= maxlat)
                           lon_mask = (minlon <= lon_values) & (lon_values <= maxlon)
                           temporal_means_region        = temporal_means[lat_mask, :][:, lon_mask]
                           gridcell_area_weights_region = gridcell_area_weights[lat_mask,:][:,lon_mask]
                           expected_value,sumweights    = np.ma.average(temporal_means_region,
                                                          weights=gridcell_area_weights_region,
                                                          returned=True)
                           print(expected_value)
                           
            sys.exit(0) 
            for j, statistic in enumerate(self.config.get_stats()):
                """ The second nested loop iterates through each requested 
                    statistic
                """
                if statistic == 'mean':
                   value = expected_value

                elif statistic == 'variance':
                   value = -expected_value**2 + np.ma.sum(
                                                temporal_means**2 * 
                                                (gridcell_area_weights / 
                                                gridcell_area_weights.sum()))
                elif statistic == 'maximum':
                    value= np.ma.max(temporal_means)
                    num_vars  = len(required_vars)  

                elif statistic == 'minimum':
                    value = np.ma.min(temporal_means)
                
                harvested_data.append(HarvestedData(
                                    self.config.harvest_filenames,
                                    statistic, 
                                    variable,
                                    np.float32(value),
                                    units,
                                    dt.fromisoformat(median_cftime.isoformat()),
                                    longname))
        
        gridcell_area_data.close()
        xr_dataset.close()
        return harvested_data

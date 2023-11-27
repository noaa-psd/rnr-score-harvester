#!/usr/bin/env python

import os
import sys

import numpy as np
from netCDF4 import MFDataset
import xarray as xr
from datetime import datetime as dt
import cftime
from collections import namedtuple
from dataclasses import dataclass
from dataclasses import field

from score_hv.config_base import ConfigInterface

GRID_CELL_AREA_DATA = './normalized_area_weights.nc'

HARVESTER_NAME   = 'global_bucket_precip_ave'
VALID_STATISTICS = ('mean', 'std')
VALID_VARIABLES  = ('prateb_ave', 'soilm', 'tmp2m', 'soill4', 'soilt4')

HarvestedData = namedtuple('HarvestedData', ['filenames',
                                             'statistic',
                                             'variable',
                                             'value',
                                             'units',
                                             'mediantime',
                                             'longname'])
@dataclass
class GlobalBucketPrecipRateConfig(ConfigInterface):

    config_data: dict = field(default_factory=dict)

    def __post_init__(self):
        self.set_config()

    def set_config(self):
        """ function to set configuration variables from given dictionary
        """
        self.harvest_filenames = self.config_data.get('filenames')
        self.set_stats()
        self.set_variables()

    def set_variables(self):
        """
        set the variables specified by the config dict
        """
        
        self.variables = self.config_data.get('variable')
        for var in self.variables:
            if var not in VALID_VARIABLES:
                msg = ("'%s' is not a supported global bucket precip average "
                       "variable to harvest from the background forecast data. "
                       "Please reconfigure the input dictionary using only the "
                       "following variables: %r" % (var, VALID_VARIABLES))
                raise KeyError(msg)
    
    def get_stats(self):
        ''' return list of all stat types based on harvest_config '''
        return self.stats

    def set_stats(self):
        """
        set the statistics specified by the config dict
        """
        self.stats = self.config_data.get('statistic')
        for stat in self.stats:
            if stat not in VALID_STATISTICS:
                msg = ("'%s' is not a supported statistic to harvest for global bucket precipitation. "
                       "Please reconfigure the input dictionary using only the "
                       "following statistics: %r" % (stat, VALID_STATISTICS))
                raise KeyError(msg)

    def get_variables(self):
        ''' return list of all variable types based on harvest_config'''
        return self.variables

@dataclass
class GlobalBucketPrecipRateHv(object):
    """ Harvester dataclass used to parse precip stored in 
        background forecast data
    
        Parameters:
        -----------
        config: precipConfig object containing information used to determine
                which variable to parse the log file
        Methods:
        --------
        get_data: parse descriptive statistics from log files based on input
                  config file
    
                  returns a list of tuples containing specific data
    """
    config: GlobalBucketPrecipRateConfig = field(
                                default_factory=GlobalBucketPrecipRateConfig)
    
    def get_data(self):
        """ Harvests requested statistics and variables from background 
            forecast data returns harvested_data, a list of HarvestData tuples
        
            The below routine extracts timestamps from the input data (forecast 
            files), which are expected to represent the temporal endpoints of 
            the (e.g., 3 hour) forecast window. To calculate the temporal 
            midpoint representative of the whole list of input forecast files,
            the routine estimates the time step using a finite difference
            calculation of the timestamps. Shifting the timestamps by minus
            half of the time step gives the temporal midpoints, which are
            then used to determine the multi-file temporal midpoint.
        """
        harvested_data  = list()
        datetimes       = list() #List for holding the date and time of the file
        
        xr_dataset = xr.open_mfdataset(self.config.harvest_filenames, 
                                       combine='nested', 
                                       concat_dim='time',
                                       decode_times=True)

        # Get the current working directory
        current_directory = os.getcwd()
        grid_cell_file    = os.path.join(current_directory,GRID_CELL_AREA_DATA)
        grid_cell_area_data = xr.open_dataset(grid_cell_file)
        grid_cell_weights   = (grid_cell_area_data.variables['area'] /
                             grid_cell_area_data.variables['area'].sum())
        
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
            """ The first nested loop iterates through each requested variable
            """
            field_data = xr_dataset[variable]
            temporal_means = field_data.mean(dim='time', skipna=True)
            if 'long_name' in field_data.attrs:
                longname = field_data.attrs['long_name']
            else:
                longname = "None"
            if 'units' in field_data.attrs:
                units = field_data.attrs['units']
            else:
                units = "None"
            for j, statistic in enumerate(self.config.get_stats()):
                """ The second nested loop iterates through each requested 
                    statistic
                """
                if statistic == 'mean':
                    value = np.ma.sum(np.ma.masked_invalid(
                                temporal_means * grid_cell_weights))
                if statistic == 'std':
                    value = np.ma.std(np.ma.masked_invalid(temporal_means.values))
                harvested_data.append(HarvestedData(
                                      self.config.harvest_filenames,
                                      statistic, 
                                      variable,
                                      np.float32(value),
                                      units,
                                      dt.fromisoformat(median_cftime.isoformat()),
                                      longname))
        
        grid_cell_area_data.close()
        xr_dataset.close()
        return harvested_data

import os,sys
import numpy as np
import netCDF4 as nc 
import xarray as xr
import datetime
import cftime
from collections          import namedtuple
from netCDF4              import Dataset
from dataclasses          import dataclass
from dataclasses          import field
from score_hv.config_base import ConfigInterface

HARVESTER_NAME   = 'global_bucket_evap_ave'
VALID_STATISTICS = ('var_mean','global_mean')
VALID_VARIABLES  = ('lhtfl_ave')

HarvestedData = namedtuple('HarvestedData', ['filenames',
                                             'statistic',
                                             'variable',
                                             'value',
                                             'units',
                                             'mediantime',
                                             'longname'])
@dataclass
class GlobalBucketEvapRateConfig(ConfigInterface):

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
                msg = ("'%s' is not a supported global bucket evaporation average "
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
                msg = ("'%s' is not a supported statistic to harvest for global bucket evaporation. "
                       "Please reconfigure the input dictionary using only the "
                       "following statistics: %r" % (stat, VALID_STATISTICS))
                raise KeyError(msg)

    def get_variables(self):
        ''' return list of all variable types based on harvest_config'''
        return self.variables

@dataclass

@dataclass
class GlobalBucketEvapRateHv(object):
    """ Harvester dataclass used to parse,lhtfl,evaporation stored in 
        background forecast data
    
        Parameters:
        -----------
        evaporation config: Config object containing information used to determine
                which variable to parse the log file
        Methods:
        --------
        get_data: parse descriptive statistics from log files based on input
                  config file
    
                  returns a list of tuples containing specific data
    """
    config: GlobalBucketEvapRateConfig = field(
                                default_factory=GlobalBucketEvapRateConfig)
    
    def get_data(self):
        """ Harvests requested statistics and variables from  background forecast data
            returns harvested_data, a list of HarvestData tuples

            The routine below extracts timestamps from the input data (forecast
            files), which are expected to represent the temporal endpoints of
            the (e.g., 3 hour) forecast window. To calculate the temporal
            midpoint representative of the whole list of input forecast files,
            the routine estimates the time step using a finite difference
            calculation of the timestamps. Shifting the timestamps by minus
            half of the time step gives the temporal midpoints, which are
            then used to determine the multi-file temporal midpoint.
        """
        harvested_data = list()
        evaporation   = [] 
        mean_values   = []
        filenames     = self.config.harvest_filenames
        datetimes     = list() #List for holding the date and time of the file
        xr_dataset    = xr.open_mfdataset(filenames,combine='nested',concat_dim='time',decode_times=True)
        temporal_endpoints = np.array([cftime.date2num(time,'hours since 1951-01-01 00:00:00') 
        for time in xr_dataset['time']])

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
            varname      = self.config.variables[i]
            print(varname)
            thevar       = xr_dataset[varname]
            dims         = thevar.shape
            ntimes       = dims[0]
            evaporation  = thevar.values
            if 'long_name' in thevar.attrs:
                    longname = thevar.attrs['long_name']
            else:
                    longname = "None"
            if 'units' in thevar.attrs:
                    units = thevar.attrs['units']
            else:
                    units = "None"
            for j, statistic in enumerate(self.config.get_stats()):
                """ The second nested loop iterates through each requested 
                    statistic
                """
                statistic = self.config.stats[j]
                if statistic == 'var_mean':
                   """This part of the code calculates the mean of the 
                      variable for each of the date and times in the data set.
                      The xarray function mean handles missing or masked values."""
                   thetimes = xr_dataset['time'].values
                   mean_values_by_time = []
                   for itime in thetimes:
                       itime_data = xr_dataset.sel(time=itime)
                       mean_for_time_period = np.float32(itime_data[varname].mean().values.item())
                       mean_values_by_time.append(mean_for_time_period)
                       value = mean_for_time_period
                       harvested_data.append(HarvestedData(filenames, statistic, variable,
                                                   value,units,median_cftime,longname))
                elif statistic == 'global_mean': 
                       """Now calculate the mean for the entire dataset. 
                          The list, mean_variable_by_time,holds the mean values of the variable 
                          for each date and time."""
                       evap_mean_value = np.mean(mean_values_by_time)
                       value           = evap_mean_value
                       harvested_data.append(HarvestedData(filenames, statistic, variable,
                                                   value,units,median_cftime,longname))
                else:
                       print("Statistic is unknown")
        return harvested_data

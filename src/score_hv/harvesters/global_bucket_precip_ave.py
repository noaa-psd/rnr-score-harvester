import os,sys

from collections import namedtuple
from dataclasses import dataclass
from dataclasses import field
import numpy as np
import netCDF4 as nc 
import xarray as xr
import glob


from score_hv.config_base import ConfigInterface

HARVESTER_NAME   = 'global_bucket_precip_ave'
VALID_STATISTICS = ('mean')
VALID_VARIABLES  = ('prateb_ave')

HarvestedData = namedtuple('HarvestedData', ['filenames',
                                             'statistic',
                                             'variable',
                                             'value',
                                             'units'])
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


@dataclass
class GlobalBucketPrecipRateHv(object):
    """ Harvester dataclass used to parse precip stored in 
        background forecast data
    
        Parameters:
        -----------
        config: TemperatureConfig object containing information used to determine
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
        """ Harvests prateb_ave from background forecast data
            returns harvested_data, a list of HarvestData tuples
        """
        harvested_data = list()
       
        mean_values = []
        filenames   = self.config.harvest_filenames
        #Open the requested file names
        for infile in filenames:
            nc_file = nc.Dataset(infile, 'r')
        #Open the requested file names
        for i, variable in enumerate(self.config.get_variables()):
            """ The first nested loop iterates through each requested variable
            """
            for j, statistic in enumerate(self.config.get_stats()):
                """ The second nested loop iterates through each requested 
                    statistic
                """
                var_name    = variable
                for infile in filenames:
                    nc_file            = nc.Dataset(infile, 'r')
                    requested_var      = nc_file.variables[var_name][:]
                    units              = nc_file.variables[var_name].units if hasattr(nc_file.variables[var_name], 'units') else None
                    mean_values.append(np.mean(requested_var)) 
                    nc_file.close()
                value = np.mean(mean_values)
                print(value)
                harvested_data.append(HarvestedData(filenames, statistic, variable,
                                                   value,units))
                
                                                    
        return harvested_data


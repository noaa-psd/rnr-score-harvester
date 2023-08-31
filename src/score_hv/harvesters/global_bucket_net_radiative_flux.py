import os,sys
import numpy as np
import netCDF4 as nc 
import xarray as xr
import glob
from collections          import namedtuple
from netCDF4              import Dataset
from dataclasses          import dataclass
from dataclasses          import field
from score_hv.config_base import ConfigInterface

HARVESTER_NAME   = 'global_bucket_net_radiative_flux'
VALID_STATISTICS = ('mean')
VALID_VARIABLES  = ('dswrf_avetoa','ulwrf_avetoa','uswrf_avetoa')

HarvestedData = namedtuple('HarvestedData', ['filenames',
                                             'statistic',
                                             'variables',
                                             'value',
                                             'units'])
@dataclass
class GlobalBucketNetRadiativeFluxConfig(ConfigInterface):

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
        
        self.variables = self.config_data.get('variables')
        for var in self.variables:
            if var not in VALID_VARIABLES:
                msg = ("'%s' is not a supported global bucket net radiative flux "
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
                msg = ("'%s' is not a supported statistic to harvest for global bucket net radiative flux. "
                       "Please reconfigure the input dictionary using only the "
                       "following statistics: %r" % (stat, VALID_STATISTICS))
                raise KeyError(msg)

    def get_variables(self):
        ''' return list of all variable types based on harvest_config'''
        return self.variables

@dataclass

@dataclass
class GlobalBucketNetRadiativeFluxHv(object):
    """ Harvester dataclass used to parse precip stored in 
        background forecast data
    
        Parameters:
        -----------
        config: NetRadiativeFluxConfig object containing information used to determine
                which variable to parse the log file
        Methods:
        --------
        get_data: parse descriptive statistics from log files based on input
                  config file
    
                  returns a list of tuples containing specific data
    """
    config: GlobalBucketNetRadiativeFluxConfig = field(
                                default_factory=GlobalBucketNetRadiativeFluxConfig)
    
    def get_data(self):
        """ Harvests requested statistics and variables from background forecast data
            returns harvested_data, a list of HarvestData tuples
        """
        harvested_data = list()
        """Arrays for each of the three variables needed to calculate
           the top of the atmosphere net radiative flux"""
        mean_dswrf  = []
        mean_ulwrf  = []
        mean_uswrf  = []
        datasets    = []
        filenames   = self.config.harvest_filenames
        for file_path in filenames:
            dataset = xr.open_dataset(file_path)
            datasets.append(dataset) 
        for i, variable in enumerate(self.config.get_variables()):
            """ The first nested loop iterates through each requested variable
            """
            varname      = self.config.variables[i]
            thevar       = dataset[varname]
            if 'units' in thevar.attrs:
                units    = thevar.attrs['units']
            else:
                units    = "None"
            if i == 0:
                print("a zero")
            dswrf_avetoa = dataset['dswrf_avetoa']
            ulwrf_avetoa = dataset['ulwrf_avetoa']
            uswrf_avetoa = dataset['uswrf_avetoa']
            mean_dswrf.append(np.ma.mean(dswrf_avetoa))
            mean_ulwrf.append(np.ma.mean(ulwrf_avetoa))
            mean_uswrf.append(np.ma.mean(uswrf_avetoa))
            for j, statistic in enumerate(self.config.get_stats()):
                """ The second nested loop iterates through each requested 
                    statistic
                """
                global_dswrf_mean  = np.ma.mean(mean_dswrf)
                global_ulwrf_mean  = np.ma.mean(mean_ulwrf)
                global_uswrf_mean  = np.ma.mean(mean_uswrf)
                net_radiative_flux = "{:.5f}".format(global_dswrf_mean - global_ulwrf_mean - global_uswrf_mean)
                print(net_radiative_flux)
                value = 0
                harvested_data.append(HarvestedData(filenames, statistic, variable,
                                                   value,units))
        return harvested_data



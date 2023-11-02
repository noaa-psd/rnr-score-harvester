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
HARVESTER_NAME   = 'global_bucket_net_radiative_flux'
VALID_STATISTICS = ('mean')
VALID_VARIABLES  = ('dswrf_avetoa','ulwrf_avetoa','uswrf_avetoa','net_radiative_flux')

HarvestedData = namedtuple('HarvestedData', ['filenames',
                                             'statistic',
                                             'variables',
                                             'value',
                                             'units',
                                             'median_time',
                                             'longname'])
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
        dswrf       = []
        ulwrf       = []
        uswrf       = []
        mean_dswrf  = []
        mean_ulwrf  = []
        mean_uswrf  = []
        datetimes   = [] #List for holding the date and time of the file
        filenames   = self.config.harvest_filenames
        xr_dataset  = xr.open_mfdataset(filenames,combine='nested',concat_dim='time',decode_times=True)
        temporal_endpoints = np.array([cftime.date2num(time,
            'hours since 1951-01-01 00:00:00') for time in xr_dataset['time']])

        if len(self.config.harvest_filenames) > 1:
            """ can estimate the time step only if there're more than 1
                timestamps
            """
            temporal_midpoints = temporal_endpoints - np.gradient(temporal_endpoints)/2.
            median_time = cftime.num2date(np.median(temporal_midpoints),
                                            'hours since 1951-01-01 00:00:00')
        else:
            median_time = cftime.num2date(np.median(temporal_endpoints),
                                            'hours since 1951-01-01 00:00:00')
        for i, variable in enumerate(self.config.get_variables()):
            """ The first nested loop iterates through each requested variable
            """
            varname    = self.config.variables[i]
            if i == 0:
                thevar = xr_dataset[varname]
                """The variables for this harvester all have the same units.  
                So we only need to get the units for the first variable.
                We calculate the global mean with the np.isfinite. This skips 
                any masked values"""
                """Since the global mean top of the atmosphere net radiative
                   flux is a derived variable we hard code the long name"""
                longname = "TOA net radiative flux"
                if 'units' in thevar.attrs:
                    units = thevar.attrs['units']
                else:
                    units = "None"
                dswrf   = thevar.values 
            elif i == 1:
                thevar  = xr_dataset[varname]
                ulwrf   = thevar.values
            elif i == 2:    
                thevar  = xr_dataset[varname]
                uswrf   = thevar.values
            for j, statistic in enumerate(self.config.get_stats()):
                """ The second nested loop iterates through each requested 
                    statistic
                """
                if i == 0:
                    mean_dswrf = dswrf[np.isfinite(dswrf)].mean()
                    value = mean_dswrf 
                elif i == 1:
                    mean_ulwrf = ulwrf[np.isfinite(ulwrf)].mean()
                    value = mean_ulwrf
                elif i == 2:
                    mean_uswrf = uswrf[np.isfinite(uswrf)].mean()
                    value = mean_uswrf
                elif i == 3:
                    net_radiative_flux = mean_dswrf - mean_ulwrf - mean_uswrf
                    value = net_radiative_flux

                harvested_data.append(HarvestedData(filenames, statistic, variable,
                                                   value,units,median_time,longname))


        return harvested_data



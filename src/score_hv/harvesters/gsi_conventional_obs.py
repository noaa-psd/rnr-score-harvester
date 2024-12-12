"""methods to extract information from the Gridpoint Statistical Interpolation (GSI) analysis output (fit files), including innovation statistics for
conventional observations
"""

import os
import warnings
from collections import namedtuple
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime

from score_hv.config_base import ConfigInterface

HARVESTER_NAME = 'gsi_conventional_obs'

VALID_VARIABLES = (
    'fit_psfc_data', # fit of surface pressure data (mb)
    'fit_u_data', # fit of u wind data (m/s),
    'fit_v_data', # fit of v wind data (m/s),
    'fit_t_data', # fit of temperature data (K)
    'fit_q_data', # fit of moisture data (% of qsaturation guess)
)

VALID_STATISTICS = (
    'count', # number of obs summed under obs types and vertical layers
    'bias', # bias of obs departure for each outer loop (it)
    'rms', # root mean squre error of obs departure for each outer loop (it)
    'cpen', # obs part of penalty (cost function)
    'qcpen' # nonlinear qc penalty
)

HarvestedData = namedtuple(
    'HarvestedData',
    ['datetime', # datetime.datetime object (date and a time)
     'ensemble_member',
     'plevs_top', # pressures at the tops of the layers (for multi-level data)
     'plevs_bot', # pressure at the bottoms of the layers (for multi-level data)
     'plevs_units',
     'variable',
     'statistic',
     'values',
     'units',
     'longname',
     'iteration', # GSI outer loop number
     'usage', # used (asm), read in but not assimilated (mon) or rejected (rej)
     'type', # prepbufr obs type    
    ]
)

def get_longname(variable):
    
    longnames = {'fit_psfc_data': 'fit of surface pressure data',
                 'fit_u_data': 'fit of u wind data',
                 'fit_v_data': 'fit of v wind data',
                 'fit_t_data': 'fit of temperature data',
                 'fit_q_data': r'fit of moisture data (% of qsaturation guess)'}
    
    return longnames[variable]
    
def get_units(statistic, variable):
    
    units = {'fit_psfc_data': 'mb',
             'fit_u_data': 'm/s',
             'fit_v_data': 'm/s',
             'fit_t_data': 'K',
             'fit_q_data': r'%'}
             
    if statistic == 'count':
        units[variable] = None
    
    return units[variable]

@dataclass
class GSIConvObsConfig(ConfigInterface):
    
    config_data: dict = field(default_factory=dict)
    
    def __post_init__(self):
        self.set_config()
        
    def set_config(self):
        """ function to set configuration variables from given dictionary
        """
        self.harvest_filename = self.config_data.get('filename')
        self.set_variables()
        self.set_statistics()
    
    def set_variables(self):
        self.vars_to_harvest = self.config_data.get('variables')
        if self.vars_to_harvest == None:
            self.vars_to_harvest = list()
        
        for var in self.vars_to_harvest:
            if var not in VALID_VARIABLES:
                msg = (f"{var} is not a supported variable "
                       "to harvest from the GSI analysis fort.201, fort.205 "
                       "and fort.213 fit files. "
                       "Please reconfigure the input dictionary using only the "
                       f"following variables: {VALID_VARIABLES}")
                raise KeyError(msg)
    
    def set_statistics(self):
        self.stats_to_harvest = self.config_data.get('statistics')
        if self.stats_to_harvest == None:
            self.stats_to_harvest = list()
            
        for stat in self.stats_to_harvest:
            if stat not in VALID_STATISTICS:
                msg = (f"{stat} is not a supported statistic "
                       "to harvest from the GSI analysis fort.201, fort.205 "
                       "and fort.213 fit files. "
                       "Please reconfigure the input dictionary using only the "
                       f"following statistics: {VALID_STATISTICS}")
                raise KeyError(msg)
                
@dataclass
class GSIConvObsHv(object):
    
    config: GSIConvObsConfig = field(default_factory = GSIConvObsConfig)
    
    def get_data(self):
        """Read the fit file (from the GSI analysis output)"
        
        returns a list of HarvestedData tuples
        """
        self.plevs_top = dict()
        self.plevs_bot = dict()
        
        # get the datetime from the input file name
        try: # format is gsistats.YYYYMMDDHH_control
            self.datetime = datetime.strptime(
                self.config.harvest_filename.split('.')[-1].split('_')[0],
                '%Y%m%d%H')
            self.ensemble_member = self.config.harvest_filename.split('.')[-1].split('_')[1]
            
        except ValueError as err:
            if self.config.harvest_filename[-5:] == 'z.txt':
                # assume format from NASA
                self.datetime = datetime.strptime(
                    self.config.harvest_filename.split('.')[-2],
                    '%Y%m%d_%Hz'
                )
                self.ensemble_member = 'control'
            else:
                raise ValueError(f'{self.config.harvest_filename} is not a '
                 'supported GSI fit file name: cannot return datetime') from err
        
        with open(self.config.harvest_filename, encoding="utf-8") as f:
            self.lines = list(f)
            
        self.parse_fit_file()
        
        harvested_data = list()
        for var in self.config.vars_to_harvest:
            
            longname = get_longname(var)
            
            for stat in self.config.stats_to_harvest:
                
                units = get_units(stat, var)
                
                harvested_data.append(
                    HarvestedData(
                        self.datetime,
                        self.ensemble_member,
                        list(),
                        list(),
                        'GET_PLEV_UNITS',
                        var,
                        stat,
                        self.values,
                        units,
                        longname,
                        'GET_GSI_STAGE',
                        'GET_USAGE',
                        'GET_OBS_TYPE'
                    ))
        
        return harvested_data 
        
    def parse_fit_file(self):
        """ parse lines of fit file and extract statistics
        """
        self.values = self.lines
                
def test(gsistats_test_file):
    test_datetime = datetime.strptime(
        gsistats_test_file.split('.')[-1].split('_')[0], '%Y%m%d%H')
    import ipdb
    ipdb.set_trace()
    print(test_datetime)
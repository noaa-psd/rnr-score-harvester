#!/usr/bin/env python

""" Collection of methods to faciliate retrieval of increment
    descriptive statistics from logs
"""

import os

from collections import namedtuple
from dataclasses import dataclass
from dataclasses import field

from score_hv.config_base import ConfigInterface

HRVSTER_NAME = 'inc_logs'
VALID_STATISTICS = ('mean', 'RMS')
VALID_VARIABLES = ['pt_inc', 's_inc', 'u_inc', 'v_inc', 'SSH', 'Salinity',
                   'Temperature', 'Speed of Currents', 'o3mr_inc', 'sphum_inc',
                   'T_inc', 'delp_inc', 'delz_inc']

HarvestedData = namedtuple('HarvestedData', ['logfile',
                                             'statistic',
                                             'variable',
                                             'value', 
                                             'units'])
N_TUPLE_ENTRIES = 5                                             

@dataclass
class LogIncCfg(ConfigInterface):
    """ Dataclass to hold and provide configuration information pertaining to
        how the harvester should read increment log files
    
        Parameters:
        -----------
        config_data: dict - contains configuration data parsed from either an
                            input yaml file or input dict
        
    """
    config_data: dict = field(default_factory=dict)
    
    def __post_init__(self):
        self.set_config()
    
    def set_config(self):
        """ function to set configuration variables from given dictionary
        """ 
        try:
            self.harvest_filename = self.config_data.get('filename')
        except Exception as err:
            msg = '%s key missing' % key
            raise KeyError(msg) from err
        
        self.set_stats()
        self.set_variables()
    
    def set_variables(self):
        """
        set the variables specified by the config dict
        """
        try:
            self.variables = self.config_data.get('variable')
            for var in self.variables:
                if var not in VALID_VARIABLES:
                    msg = f'Invalid variable, must be one of \'{VALID_VARIABLES}\''
                    raise KeyError(msg)
        except Exception as err:
            msg = f'\'variables\' key missing, must be one of ' \
                f'({VALID_VARIABLES}) - err: {err}'
            raise KeyError(msg) from err

    def set_stats(self):
        """
        set the statistics specified by the config dict
        """
        try:
            self.stats = self.config_data.get('statistic')
            for stat in self.stats:
                if stat not in VALID_STATISTICS:
                    msg = f'Invalid statistic, must be one of \'{VALID_STATISTICS}\''
                    raise KeyError(msg)
        except Exception as err:
            msg = f'\'statistics\' key missing, must be one of ' \
                f'({VALID_STATISTICS}) - err: {err}'
            raise KeyError(msg) from err
    
    def get_stats(self):
        ''' return list of all stat types based on harvest_config '''
        return self.stats
        
    def get_variables(self):
        ''' return list of all variable types based on harvest_config'''
        return self.variables
        
@dataclass
class LogIncHv(object):
    """ Harvester dataclass used to parse increment descriptive
        statistics stored in log files
    
        Parameters:
        -----------
        config: IncCfg object containing information used to determine
                which variable to parse the log file
        Methods:
        --------
        get_data: parse descriptive statistics from log files based on input
                  config file
    
                  returns a list of tuples containing specific data
    """
    config: LogIncCfg = field(default_factory=LogIncCfg)
    
    def get_data(self):
        """ Harvests ocean increment descriptive statistics.
            Input file is a log text file.
        
            returns harvested_data, a list of HarvestData tuples
        """
        harvested_data = []        
        # read in file
        # find section for statistics
        # read values
        
        with open(self.config.harvest_filename) as log_file:
            lines = log_file.readlines()
        
        for i, line in enumerate(lines):
            """ The outer most loop iterates through each line
            """                
            for j, variable in enumerate(self.config.get_variables()):
                """ The first nested loop iterates through each requested variable
                """
                for k, statistic in enumerate(self.config.get_stats()):
                    """ The second nested loop iterates through each requested statistic
                    """
                    if line.split(',')[1][1:] == variable:
                        """ harvest data
                        """
                        if statistic == VALID_STATISTICS[0]:
                            """ harvest mean
                            """ 
                            harvest_tuple = HarvestedData(
                                self.config.harvest_filename,
                                statistic,
                                variable,
                                float(line.split(',')[-2]), # value
                                'unspecified', # units
                                )
                        elif statistic == VALID_STATISTICS[1]:
                            """ harvest RMS
                            """
                            harvest_tuple = HarvestedData(
                                self.config.harvest_filename,
                                statistic,
                                variable,
                                float(line.split(',')[-1]), # value
                                'unspecified', # units
                                )
                        else:
                            harvest_tuple = ()
                        
                        if len(harvest_tuple) == N_TUPLE_ENTRIES:
                            harvested_data.append(harvest_tuple)
    
        return harvested_data
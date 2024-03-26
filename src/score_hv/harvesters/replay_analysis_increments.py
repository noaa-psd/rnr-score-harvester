"""Collection of methods to facilitate retrieval of the replay analysis
increments (from the fv3_increment6.nc files)
"""

import os
from pathlib import Path
from collections import namedtuple
from dataclasses import dataclass, field

from netCDF4 import Dataset
import numpy as np

from score_hv.config_base import ConfigInterface
from score_hv import stats_utils

HARVESTER_NAME = 'replay_analysis_increments'
VALID_STATISTICS = ('mean', 'variance', 'minimum', 'maximum')

"""Variables of interest that come from the analysis increment data.
Commented out variables can be uncommented to generate gridcell weighted
statistics but are in development and are currently not fully supported.
"""
VALID_VARIABLES  = (# Analysis increments for FV3 prognostic variables:
                    'delp_inc', # vertical difference in hydrostatic pressure,
                                # proportional to mass
                    'u_inc', # mean westerly (horizontal x-direction) wind
                    'v_inc', # mean southerly (horizontal y-direction) wind
                    'delz_inc', # geometric layer height
                    
                    # other analysis increments:
                    'o3mr_inc', # ozone mixing ratio
                    'sphum_inc', # specific humidity
                    'T_inc', # temperature
                    )

HarvestedData = namedtuple('HarvestedData', ['filename',
                                             'cycletime',
                                             'statistic',
                                             'variable',
                                             'values',
                                             'levels',
                                             'units',
                                             'longname'])

def get_longname(variable):
    """Define descriptions for VALID_VARIABLES
    """
    variables = {'delp_inc': 'Analysis increment of the vertical difference in '
                           'hydrostatic pressure, proportional to mass',
                 'u_inc': 'Analysis increment of the D-grid face-mean '
                          'horizontal x-direction wind',
                 'v_inc': 'Analysis increment of the D-grid face-mean ' 
                          'horizontal y-direction wind',
                 'delz_inc': 'Analysis increment of the geometric layer height',
                 'o3mr_inc': 'Analysis increment of the ozone mixing ratio',
                 'sphum_inc': 'Analysis increment of the specific humidity',
                 'T_inc': 'Analysis increment of the temperature'}
                 
    for key, value in variables.items():
        if variable == key:
            description = value
    
    return description
    
def get_units(variable):
    """Define units for VALID_VARIABLES
    """
    #TODO: figure out units for the analysis increments and return them below
    return "None"

#TODO: move get_gridcell_area_data_path() to utils file
def get_gridcell_area_data_path():
    return os.path.join(Path(__file__).parent.parent.parent.parent.resolve(),
                        'data', 'gridcell-area' + 
                        '_noaa-ufs-gefsv13replay-pds' + 
                        '_bfg_control_1536x768_20231116.nc')
@dataclass
class IncrementsConfig(ConfigInterface):

    config_data: dict = field(default_factory=dict)

    def __post_init__(self):
        self.set_config()

    def set_config(self):
        """function to set configuration variables from given dictionary
        """
        self.harvest_filename = self.config_data.get('filename')
        self.set_stats()
        self.set_variables()

    def set_variables(self):
        """set the variables specified by the config dict
        """
        
        self.variables = self.config_data.get('variable')
        for var in self.variables:
            if var not in VALID_VARIABLES:
                msg = (f"{var} is not a supported "
                       "variable to harvest from the replay analysis " 
                       "increments (fv3_increment6.nc). "
                       "Please reconfigure the input dictionary using only the "
                       f"following variables: {VALID_VARIABLES}")
                raise KeyError(msg)

    def set_stats(self):
        """set the statistics specified by the config dict
        """
        self.stats = self.config_data.get('statistic')
        for stat in self.stats:
            if stat not in VALID_STATISTICS:
                msg = ("{stat} is not a supported statistic to harvest from "
                       "the replay analysis increments (fv3_increment6.nc). "
                       "Please reconfigure the input dictionary using only the "
                       f"following statistics: {VALID_STATISTICS}")
                raise KeyError(msg)

@dataclass
class IncrementsHv(object):
    """Harvester dataclass used to parse daily mean statistics from the replay 
    analysis increments
    
    Parameters:
    -----------
    config: IncrementsConfig object containing information used to determine
            which variable to harvest
    Methods:
    --------
    get_data: calculate descriptive statistics from analysis increments 
              based on input config file
    
    returns a list of tuples containing specific data
    """
    config: IncrementsConfig = field(default_factory=IncrementsConfig)
    
    def get_data(self):
        """Harvests requested statistics and variables from replay analysis 
        increments and returns harvested_data, a list of HarvestData tuples
        """
        
        harvested_data = list()
        
        rootgrp = Dataset(self.config.harvest_filename)
        
        gridcell_area_data = Dataset(get_gridcell_area_data_path())
        gridcell_area_weights = gridcell_area_data.variables['area']
        
        for i, variable in enumerate(self.config.get_variables()):
            """ The first nested loop iterates through each requested variable
            """
            variable_data = rootgrp.variables[variable]
            
            if 'long_name' in variable_data.ncattrs():
                longname = variable_data.long_name
            elif 'longname' in variable_data.ncattrs():
                longname = variable_data.longname
            else:
                longname = get_longname(variable)
            if 'units' in variable_data.ncattrs():
                units = variable_data.units
            else:
                units = get_units(variable)
            
            expected_values = list()
            levels = list()
            for level_idx in range(variable_data.shape[0]):
                """Calculate statistics for each vertical level
                """
                expected_value = stats_utils.area_weighted_mean(
                                                    variable_data[level_idx],
                                                    gridcell_area_weights[:])
                
                expected_values.append(expected_value)
                levels.append(rootgrp.variables['lev'][:][level_idx])
                
            for j, statistic in enumerate(self.config.get_stats()):
                """ The second nested loop iterates through each requested 
                    statistic
                """
                if statistic == 'mean':
                    values = expected_values
                elif statistic == 'variance':
                    for 
            
                harvested_data.append(HarvestedData(
                                        self.config.harvest_filename,
                                        'NEED_CYCLETIME',
                                        statistic, 
                                        variable,
                                        values,
                                        levels,
                                        units,
                                        longname))
            
        return harvested_data
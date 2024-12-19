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
     'subtype', # prepbufr obs subtype
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
        self.results = dict()
        for var in self.config.vars_to_harvest:
            self.results[var] = {
                'plevs_top': list(),
                'plevs_bot': list(),
                'plevs_units': list(),
            }
            for stat in self.config.stats_to_harvest:
                self.results[var][stat] = dict()
                
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
                
                for row_idx, value in enumerate(
                                    self.results[var][stat][stat]['values']):
                
                    harvested_data.append(
                        HarvestedData(
                            self.datetime,
                            self.ensemble_member,
                            self.results[var]['plevs_top'],
                            self.results[var]['plevs_bot'],
                            self.results[var]['plevs_units'],
                            var,
                            stat,
                            value,
                            units,
                            longname,
                            int(self.results[
                                var][
                                    stat][
                                        'it'][
                                            'values'][
                                                row_idx]),
                            self.results[var][stat]['use']['values'][row_idx],
                            self.results[var][stat]['typ']['values'][row_idx],
                            self.results[var][stat]['styp']['values'][row_idx],
                        )
                    )
        
        return harvested_data 
    
    def parse_fit_file(self):
        """ parse lines of fit file and extract statistics
        """
        read_fit_ps = False
        
        for line_number, line in enumerate(self.lines):
            line_parts = line.split()
            if 'fit_psfc_data' in self.config.vars_to_harvest and len(line_parts) > 2:
                """extract fit of surface pressure data statistics
                """
                if line_parts[0] == 'pressure' and line_parts[1] == 'levels':
                    read_fit_ps = True
                    self.results['fit_psfc_data']['plevs_units'].append(
                        line_parts[2][1:-2]
                    )
                    self.results['fit_psfc_data']['plevs_top'].append(
                        [float(line_parts[3])]
                    )
                    self.results['fit_psfc_data']['plevs_bot'].append(
                        [float(line_parts[4])]
                    )

                elif read_fit_ps and line_parts[0] == 'o-g' and line_parts[1] == 'it':
                    for stat in self.config.stats_to_harvest:
                        for col, part in enumerate(line_parts):
                            if part=='it' or part=='obs' or part=='use' or part=='typ' or part=='styp' or part==stat: 
                                # store column index and column name
                                
                                if part in self.results[
                                    'fit_psfc_data'][
                                        stat].keys():
                                    """data entries exist, update only the
                                    column indicies
                                    """
                                    self.results[
                                        'fit_psfc_data'][
                                            stat][
                                                part][
                                                    'column_index'] = col
                                else:
                                    """no results added yet, create empty list
                                    to store values
                                    """
                                    self.results[
                                        'fit_psfc_data'][
                                            stat][
                                                part] = {'column_index': col,
                                                         'values': list()}
                                                                         
                elif read_fit_ps and line_parts[0] == 'o-g' and line_parts[2] == 'ps':
                   
                   for stat in self.config.stats_to_harvest:
                       for column_name, column_values in self.results['fit_psfc_data'][stat].items():
                           column_index = self.results[
                               'fit_psfc_data'][
                                   stat][
                                       column_name][
                                           'column_index']
                           if column_name == 'count':
                               return_value = [int(line_parts[column_index])]
                           elif column_name == stat:  
                               return_value = [float(line_parts[column_index])]
                           else:
                               return_value = line_parts[column_index]
                           
                           self.results[
                               'fit_psfc_data'][
                                   stat][column_name][
                                       'values'].append(return_value)
                        
                elif read_fit_ps and line_parts[0] == 'o-g' and line_parts[3] == 'all':
                    # stats for all surface pressure observation types
                    for stat in self.config.stats_to_harvest:
                        self.results[
                            'fit_psfc_data'][
                                stat][
                                    'it'][
                                        'values'].append(
                                            line_parts[1])
                        self.results[
                            'fit_psfc_data'][
                                stat][
                                    'use'][
                                        'values'].append(
                                            line_parts[2])
                        self.results[
                            'fit_psfc_data'][
                                stat][
                                    'typ'][
                                        'values'].append(
                                            line_parts[3])
                                            
                        self.results[
                            'fit_psfc_data'][
                                stat][
                                    'styp'][
                                        'values'].append(None)
                        
                        for column_name, column_values in self.results['fit_psfc_data'][stat].items():
                            if column_name == stat:
                                column_index = self.results[
                                    'fit_psfc_data'][
                                        stat][
                                            column_name][
                                                'column_index'] - 2 # this is a
                                            # weird corner case where the row is
                                            # formatted differently for all
                                            # observations than for stats by
                                            # observtion type
                                if column_name == 'count':
                                    return_value = [int(
                                                     line_parts[column_index])]
                                else:
                                    return_value = [float(
                                                      line_parts[column_index])]
                                
                                self.results[
                                    'fit_psfc_data'][
                                        stat][column_name][
                                            'values'].append(return_value)
                
                elif line_parts[0] == 'current' and line_parts[1] == 'vfit':
                    read_fit_ps = False
                
def test(gsistats_test_file):
    test_datetime = datetime.strptime(
        gsistats_test_file.split('.')[-1].split('_')[0], '%Y%m%d%H')
    import ipdb
    ipdb.set_trace()
    print(test_datetime)
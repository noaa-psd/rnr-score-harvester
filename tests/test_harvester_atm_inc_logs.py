#!/usr/bin/env python

""" Unit tests for atmosphere increment descriptive statistics harvester
"""

import pathlib
import os
from datetime import datetime

import numpy as np

from score_hv import hv_registry
from score_hv.harvester_base import harvest
from score_hv.yaml_utils import YamlLoader

PYTEST_CALLING_DIR = pathlib.Path(__file__).parent.resolve()
LOG_HARVESTER_ATM__VALID = 'calc_atm_inc.out'

DATA_DIR = 'data'
CONFIGS_DIR = 'configs'

TEST_DATA_PATH = os.path.join(PYTEST_CALLING_DIR, DATA_DIR)
FILE_PATH_ATM_INC_LOGS = os.path.join(TEST_DATA_PATH,
                                      LOG_HARVESTER_ATM__VALID)
                 
VALID_CONFIG_DICT = {'harvester_name': hv_registry.INC_LOGS,
                     'filename' : FILE_PATH_ATM_INC_LOGS,
                     'cycletime': datetime(2019,3,21,0),
                     'statistic': ['mean', 'RMS'],
                     'variable': ['o3mr_inc', 'sphum_inc', 'T_inc', 'u_inc', 'v_inc',
                                  'delp_inc', 'delz_inc']}

def test_inc_harvester_get_data():
    data1 = harvest(VALID_CONFIG_DICT)  
    assert type(data1) is list
    assert len(data1) > 0
        
def test_ozone_mixing_ratio_inc(varname='o3mr_inc'):
    for i, variable in enumerate(VALID_CONFIG_DICT['variable']):
        if variable == varname:
            variable_rank = i
    assert VALID_CONFIG_DICT['variable'][variable_rank]==varname
    
    n_stats = len(VALID_CONFIG_DICT['statistic'])
    
    valid_idxs_in_tuple = np.arange(n_stats) + variable_rank * n_stats
    
    stats_harvested = list()
    pt_tuple_subset = list()
    data1 = harvest(VALID_CONFIG_DICT)
    for i, harvested_data_tuple in enumerate(data1):
        if np.isin(i, valid_idxs_in_tuple): # pt_inc data
            assert harvested_data_tuple.statistic in VALID_CONFIG_DICT['statistic']
            stats_harvested.append(harvested_data_tuple.statistic)
            assert harvested_data_tuple.variable == VALID_CONFIG_DICT['variable'][variable_rank]
            
            pt_tuple_subset.append(harvested_data_tuple)
    
    for i, valid_statistic in enumerate(VALID_CONFIG_DICT['statistic']):
        assert valid_statistic == stats_harvested[i]
        assert valid_statistic == 'mean' or valid_statistic == 'RMS'
        
        if valid_statistic == 'mean':
            assert pt_tuple_subset[i].value == -0.120E-07
        elif valid_statistic == 'RMS': # RMS
            assert pt_tuple_subset[i].value == 0.199E-06
                        
def test_specific_humidity_inc():
    harvest_data('sphum_inc', 0.296E-04, 0.473E-03)
    
def test_temperature_inc():
    harvest_data('T_inc', 0.378E-02, 0.604E+00)
    
def test_westerly_wind_component_inc():
    harvest_data('u_inc', 0.475E-01, 0.136E+01)
    
def test_southerly_wind_component_inc():
    harvest_data('v_inc', -0.588E-02, 0.135E+01)
    
def test_delta_pressure_inc():
    harvest_data('delp_inc', 0.313E-01, 0.223E+01)
    
def test_delta_z_inc():
    harvest_data('delz_inc', -0.319E-01, 0.407E+00)

def harvest_data(varname, expected_ans_mean, expected_ans_rms):
    for i, variable in enumerate(VALID_CONFIG_DICT['variable']):
        if variable == varname:
            variable_rank = i
    assert VALID_CONFIG_DICT['variable'][variable_rank]==varname
    
    n_stats = len(VALID_CONFIG_DICT['statistic'])
    
    valid_idxs_in_tuple = np.arange(n_stats) + variable_rank * n_stats
    
    stats_harvested = list()
    valid_tuple_subset = list()
    data1 = harvest(VALID_CONFIG_DICT)
    for i, harvested_data_tuple in enumerate(data1):
        
        if np.isin(i, valid_idxs_in_tuple):
            assert harvested_data_tuple.statistic in VALID_CONFIG_DICT['statistic']
            stats_harvested.append(harvested_data_tuple.statistic)
            
            if harvested_data_tuple.variable == 'u_inc_atm' or harvested_data_tuple.variable == 'v_inc_atm':
                """ This is a special case for wind velocity component 
                    increments, because these metrics share common names 
                    across atmosphere and ocean components. Because there is 
                    only one increment harvester, the harvester appends "_atm" 
                    or "_ocn" to these variable names so that these metrics 
                    could later be distinguished by atmosphere or ocean in the
                    downstream database.
                """
                assert harvested_data_tuple.variable == VALID_CONFIG_DICT['variable'][variable_rank] + "_atm"
            
            else:
                assert harvested_data_tuple.variable == VALID_CONFIG_DICT['variable'][variable_rank]
            
            valid_tuple_subset.append(harvested_data_tuple)
    
    for i, valid_statistic in enumerate(VALID_CONFIG_DICT['statistic']):
        assert valid_statistic == stats_harvested[i]
        assert valid_statistic == 'mean' or valid_statistic == 'RMS'
        
        if valid_statistic == 'mean':
            assert valid_tuple_subset[i].value == expected_ans_mean
        elif valid_statistic == 'RMS': # RMS
            assert valid_tuple_subset[i].value == expected_ans_rms

def test_cycletime():
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].cycletime == datetime(2019, 3, 21, 0)
    
def test_nocycletime():
    valid_config_dict = {'harvester_name': hv_registry.INC_LOGS,
                         'filename' : FILE_PATH_ATM_INC_LOGS,
                         'statistic': ['mean', 'RMS'],
                         'variable': ['o3mr_inc',
                                      'sphum_inc',
                                      'T_inc',
                                      'u_inc',
                                      'v_inc',
                                      'delp_inc',
                                      'delz_inc']}
    data1 = harvest(valid_config_dict)
    assert data1[0].cycletime == None
    
def run_tests():
    """ Run the test suite
    """
    test_inc_harvester_get_data()
    test_ozone_mixing_ratio_inc()
    test_specific_humidity_inc()
    test_temperature_inc()
    test_westerly_wind_component_inc()
    test_southerly_wind_component_inc()
    test_delta_pressure_inc()
    test_delta_z_inc()
    test_cycletime()
    test_nocycletime()
    
def main():
    run_tests()
    
if __name__=='__main__':
    import ipdb
    main()
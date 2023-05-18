#!/usr/bin/env python

""" Unit tests for ocean increment descriptive statistics harvester
"""

import pathlib
import os

import numpy as np

from score_hv import hv_registry
from score_hv.harvester_base import harvest
from score_hv.yaml_utils import YamlLoader

PYTEST_CALLING_DIR = pathlib.Path(__file__).parent.resolve()
LOG_HARVESTER_OCN__VALID = 'calc_ocn_inc.out'

DATA_DIR = 'data'
CONFIGS_DIR = 'configs'

TEST_DATA_PATH = os.path.join(PYTEST_CALLING_DIR, DATA_DIR)
FILE_PATH_OCN_INC_LOGS = os.path.join(TEST_DATA_PATH,
                                      LOG_HARVESTER_OCN__VALID)
                 
VALID_CONFIG_DICT = {'harvester_name': hv_registry.INC_LOGS,
                     'filename' : FILE_PATH_OCN_INC_LOGS,
                     'statistic': ['mean', 'RMS'],
                     'variable': ['pt_inc', 's_inc', 'u_inc', 'v_inc', 'SSH',
                                  'Salinity', 'Temperature', 'Speed of Currents']}

def test_inc_harvester_get_data():
    data1 = harvest(VALID_CONFIG_DICT)  
    assert type(data1) is list
    assert len(data1) > 0
        
def test_pt_inc(varname='pt_inc'):
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
            assert harvested_data_tuple[1] in VALID_CONFIG_DICT['statistic']
            stats_harvested.append(harvested_data_tuple[1])
            assert harvested_data_tuple[2] == VALID_CONFIG_DICT['variable'][variable_rank]
            
            pt_tuple_subset.append(harvested_data_tuple)
    
    for i, valid_statistic in enumerate(VALID_CONFIG_DICT['statistic']):
        assert valid_statistic == stats_harvested[i]
        assert valid_statistic == 'mean' or valid_statistic == 'RMS'
        
        if valid_statistic == 'mean':
            assert pt_tuple_subset[i][3] == -0.657E-02
        elif valid_statistic == 'RMS': # RMS
            assert pt_tuple_subset[i][3] == 0.944E-01
                        
def test_s_inc():
    harvest_data('s_inc', 0.108E-02, 0.330E-01)
    
def test_u_inc():
    harvest_data('u_inc', 0.300E-03, 0.304E-01)
    
def test_v_inc():
    harvest_data('v_inc', 0.155E-03, 0.283E-01)
    
def test_ssh():
    harvest_data('SSH', 0.667E-01, 0.664E+00)
    
def test_salinity():
    harvest_data('Salinity', 0.348E+02, 0.348E+02)
    
def test_temperature():
    harvest_data('Temperature', 0.112E+02, 0.150E+02)
    
def test_speed_of_currents():
    harvest_data('Speed of Currents', 0.928E-01, 0.154E+00)

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
            assert harvested_data_tuple[1] in VALID_CONFIG_DICT['statistic']
            stats_harvested.append(harvested_data_tuple[1])
            assert harvested_data_tuple[2] == VALID_CONFIG_DICT['variable'][variable_rank]
            
            valid_tuple_subset.append(harvested_data_tuple)
    
    for i, valid_statistic in enumerate(VALID_CONFIG_DICT['statistic']):
        assert valid_statistic == stats_harvested[i]
        assert valid_statistic == 'mean' or valid_statistic == 'RMS'
        
        if valid_statistic == 'mean':
            assert valid_tuple_subset[i][3] == expected_ans_mean
        elif valid_statistic == 'RMS': # RMS
            assert valid_tuple_subset[i][3] == expected_ans_rms

def run_tests():
    """ Run the test suite
    """
    test_inc_harvester_get_data()
    test_pt_inc()
    test_s_inc()
    test_u_inc()
    test_v_inc()
    test_ssh()
    test_salinity()
    test_temperature()
    test_speed_of_currents()
    
def main():
    run_tests()
    
if __name__=='__main__':
    import ipdb
    main()
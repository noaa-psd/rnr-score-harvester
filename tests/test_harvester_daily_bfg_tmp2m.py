#!/usr/bin/env python

import os
import sys
from pathlib import Path 

import numpy as np
from datetime import datetime
import pytest
import yaml
from netCDF4 import Dataset

from score_hv import hv_registry
from score_hv.harvester_base import harvest
from score_hv.yaml_utils import YamlLoader
from score_hv.harvesters.innov_netcdf import Region, InnovStatsCfg

TEST_DATA_FILE_NAMES = ['tmp2m_bfg_2023032100_fhr09_control.nc',
                        'tmp2m_bfg_2023032106_fhr06_control.nc',
                        'tmp2m_bfg_2023032106_fhr09_control.nc',
                        'tmp2m_bfg_2023032112_fhr06_control.nc',
                        'tmp2m_bfg_2023032112_fhr09_control.nc',
                        'tmp2m_bfg_2023032118_fhr06_control.nc',
                        'tmp2m_bfg_2023032118_fhr09_control.nc',
                        'tmp2m_bfg_2023032200_fhr06_control.nc']

DATA_DIR = os.path.join(Path(__file__).parent.parent.resolve(), 'data')
GRIDCELL_AREA_DATA_PATH = os.path.join(DATA_DIR,
                                       'gridcell-area' + 
                                       '_noaa-ufs-gefsv13replay-pds' + 
                                       '_bfg_control_1536x768_20231116.nc')

CONFIGS_DIR = 'configs'
PYTEST_CALLING_DIR = Path(__file__).parent.resolve()
TEST_DATA_PATH = os.path.join(PYTEST_CALLING_DIR, 'data')
BFG_PATH = [os.path.join(TEST_DATA_PATH,
                         file_name) for file_name in TEST_DATA_FILE_NAMES]

VALID_CONFIG_DICT = {'harvester_name': hv_registry.DAILY_BFG,
                     'filenames' : BFG_PATH,
                     'statistic': ['mean', 'variance', 'minimum', 'maximum'],
                     'variable': ['tmp2m']}

def test_variable_names():
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].variable == 'tmp2m'

def test_global_mean_values():
    """The value of 2.4695819e-05 is the mean value of the global means
    calculated from eight forecast files:
        
        tmp2m_bfg_2023032100_fhr09_control.nc
        tmp2m_bfg_2023032106_fhr06_control.nc
        tmp2m_bfg_2023032106_fhr09_control.nc
        tmp2m_bfg_2023032112_fhr06_control.nc
        tmp2m_bfg_2023032112_fhr09_control.nc
        tmp2m_bfg_2023032118_fhr06_control.nc
        tmp2m_bfg_2023032118_fhr09_control.nc
        tmp2m_bfg_2023032200_fhr06_control.nc
        
    When averaged together, these files represent a 24 hour mean. The average 
    value hard-coded in this test was calculated from these forecast files 
    using a separate python code.
    """
    data1 = harvest(VALID_CONFIG_DICT)
    global_mean = np.float32(2.4695819e-05)
    assert data1[0].value == global_mean

def test_global_mean_values2(tolerance=0.001):
    """Opens each background Netcdf file using the netCDF4 library function 
    Dataset and computes the expected value of the provided variable.  In this 
    case tmp2m.
    """
    data1 = harvest(VALID_CONFIG_DICT)
    
    gridcell_area_data = Dataset(GRIDCELL_AREA_DATA_PATH)
    norm_weights = gridcell_area_data.variables['area'][:] / np.sum(
                                        gridcell_area_data.variables['area'][:])
    
    summation = np.ma.zeros(gridcell_area_data.variables['area'].shape)
    for file_count, data_file in enumerate(BFG_PATH):
        test_rootgrp = Dataset(data_file)
    
        summation += test_rootgrp.variables[VALID_CONFIG_DICT['variable'][0]][0]
        
        test_rootgrp.close()
        
    temporal_mean = summation / (file_count + 1)
    global_mean = np.ma.sum(norm_weights * temporal_mean)    
    
    for i, harvested_tuple in enumerate(data1):
        if harvested_tuple.statistic == 'mean':
            assert global_mean <= (1 + tolerance) * harvested_tuple.value
            assert global_mean >= (1 - tolerance) * harvested_tuple.value
            
    gridcell_area_data.close()
                
def test_gridcell_variance(tolerance=0.001):
    """Opens each background Netcdf file using the netCDF4 library function 
    Dataset and computes the variance of the provided variable.  In this case 
    tmp2m.
    """
    data1 = harvest(VALID_CONFIG_DICT)
    
    gridcell_area_data = Dataset(GRIDCELL_AREA_DATA_PATH)
    norm_weights = gridcell_area_data.variables['area'][:] / np.sum(
                                        gridcell_area_data.variables['area'][:])
    
    summation = np.ma.zeros(gridcell_area_data.variables['area'].shape)
    for file_count, data_file in enumerate(BFG_PATH):
        test_rootgrp = Dataset(data_file)
    
        summation += test_rootgrp.variables[VALID_CONFIG_DICT['variable'][0]][0]
        
        test_rootgrp.close()
        
    temporal_mean = summation / (file_count + 1)
    
    global_mean = np.ma.sum(norm_weights * temporal_mean)
    variance = np.ma.sum((temporal_mean - global_mean)**2 * norm_weights)
    
    for i, harvested_tuple in enumerate(data1):
        if harvested_tuple.statistic == 'variance':
            assert variance <= (1 + tolerance) * harvested_tuple.value
            assert variance >= (1 - tolerance) * harvested_tuple.value
            
    gridcell_area_data.close()
    
def test_gridcell_min_max(tolerance=0.001):
    """Opens each background Netcdf file using the netCDF4 library function 
    Dataset and computes the maximum of the provided variable.  In this case 
    tmp2m.
    """
    data1 = harvest(VALID_CONFIG_DICT)
    
    gridcell_area_data = Dataset(GRIDCELL_AREA_DATA_PATH)
    
    summation = np.ma.zeros(gridcell_area_data.variables['area'].shape)
    for file_count, data_file in enumerate(BFG_PATH):
        test_rootgrp = Dataset(data_file)
    
        summation += test_rootgrp.variables[VALID_CONFIG_DICT['variable'][0]][0]
        
        test_rootgrp.close()
        
    temporal_mean = summation / (file_count + 1)
    minimum = np.ma.min(temporal_mean)
    maximum = np.ma.max(temporal_mean)
    
    for i, harvested_tuple in enumerate(data1):
        if harvested_tuple.statistic == 'maximum':
            assert maximum <= (1 + tolerance) * harvested_tuple.value
            assert maximum >= (1 - tolerance) * harvested_tuple.value
        elif harvested_tuple.statistic == 'minimum':
            assert minimum <= (1 + tolerance) * harvested_tuple.value
            assert minimum >= (1 - tolerance) * harvested_tuple.value
            
    gridcell_area_data.close()

def test_units():
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].units == "K"

def test_cycletime():
    """The hard coded datetimestr 2023-03-21 12:00:00 is the median midpoint 
    time of the filenames defined above in the BFG_PATH. We have to convert 
    this into a datetime object in order to compare this string to what is 
    returned by daily_bfg.py
    """
    data1 = harvest(VALID_CONFIG_DICT)
    expected_datetime = datetime.strptime("2023-03-21 12:00:00",
                                          "%Y-%m-%d %H:%M:%S")
    assert data1[0].mediantime == expected_datetime

def test_longname():
    data1 = harvest(VALID_CONFIG_DICT)
    var_longname = "2m temperature"
    assert data1[0].longname == var_longname

def test_precip_harvester():
    data1 = harvest(VALID_CONFIG_DICT)  
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].filenames==BFG_PATH

def main():
    test_gridcell_area_conservation()
    test_precip_harvester()
    test_variable_names()
    test_units()
    #test_global_mean_values()
    test_global_mean_values2()
    test_gridcell_variance()
    test_gridcell_min_max()
    test_cycletime() 
    test_longname()

if __name__=='__main__':
    main()    
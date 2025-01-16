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

TEST_DATA_FILE_NAMES = ['bfg_1994010100_fhr09_tmp2m_control.nc',
                        'bfg_1994010106_fhr06_tmp2m_control.nc',
                        'bfg_1994010106_fhr09_tmp2m_control.nc',
                        'bfg_1994010112_fhr06_tmp2m_control.nc',
                        'bfg_1994010112_fhr09_tmp2m_control.nc',
                        'bfg_1994010118_fhr06_tmp2m_control.nc',
                        'bfg_1994010118_fhr09_tmp2m_control.nc',
                        'bfg_1994010200_fhr06_tmp2m_control.nc']

DATA_DIR = os.path.join(Path(__file__).parent.parent.resolve(), 'src', 'score_hv', 'data')
GRIDCELL_AREA_DATA_PATH = os.path.join(DATA_DIR,
                                       'gridcell-area' + 
                                       '_noaa-ufs-gefsv13replay-pds' + 
                                       '_bfg_tmp2m_control_1536x768_20231116.nc')

CONFIGS_DIR = 'configs'
PYTEST_CALLING_DIR = Path(__file__).parent.resolve()
TEST_DATA_PATH = os.path.join(PYTEST_CALLING_DIR, 'data')
BFG_PATH = [os.path.join(TEST_DATA_PATH,
                         file_name) for file_name in TEST_DATA_FILE_NAMES]

VALID_CONFIG_DICT = {'harvester_name': hv_registry.DAILY_BFG,
                     'filenames' : BFG_PATH,
                     'statistic': ['mean', 'variance', 'minimum', 'maximum'],
                     'variable': ['tmp2m'],
                     'regions': {'global':{'north_lat': 90, 'south_lat': -90, 'west_long': 0, 'east_long':360},
                                },
                     'surface_mask': ['water'],
                     }

def test_variable_names():
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].variable == 'tmp2m'

def test_mean_values(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    
    for item in data1:
        if item.statistic == 'mean':
           calculated_means = 289.5156062703238 
           assert calculated_means <= (1 + tolerance) * item.value
           assert calculated_means >= (1 - tolerance) * item.value
    
def test_gridcell_variance(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)

    for item in data1:
        if item.statistic == 'variance':
           calculated_variance = 140.59315093732124
           assert calculated_variance <= (1 + tolerance) * item.value
           assert calculated_variance >= (1 - tolerance) * item.value

def test_gridcell_min_max(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    
    for item in data1:
        if item.statistic == 'minimum':
           calculated_min  = 231.94033432006833 
           assert calculated_min <= (1 + tolerance) * item.value
           assert calculated_min >= (1 - tolerance) * item.value
        if item.statistic == 'maximum':
           calculated_max = 304.18763732910156
           assert calculated_max <= (1 + tolerance) * item.value
           assert calculated_max >= (1 - tolerance) * item.value

def test_units():
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].units == "K"

def test_cycletime():
    """The hard coded datetimestr 1994-01-01 12:00:00 is the median midpoint 
    time of the filenames defined above in the BFG_PATH. We have to convert 
    this into a datetime object in order to compare this string to what is 
    returned by daily_bfg.py
    """
    data1 = harvest(VALID_CONFIG_DICT)
    expected_datetime = datetime.strptime("1994-01-01 12:00:00",
                                          "%Y-%m-%d %H:%M:%S")
    assert data1[0].mediantime == expected_datetime

def test_longname():
    data1 = harvest(VALID_CONFIG_DICT)
    var_longname = "2m temperature"
    assert data1[0].longname == var_longname

def test_daily_bfg_harvester():
    data1 = harvest(VALID_CONFIG_DICT)  
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].filenames==BFG_PATH

def main():
    test_daily_bfg_harvester()
    test_variable_names()
    test_units()
    test_mean_values()
    test_gridcell_variance()
    test_gridcell_min_max()
    test_cycletime() 
    test_longname()

if __name__=='__main__':
    main()    

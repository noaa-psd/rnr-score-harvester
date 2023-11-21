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

TEST_DATA_FILE_NAMES = ['bfg_1994010100_fhr09_prateb_control.nc',
                        'bfg_1994010106_fhr06_prateb_control.nc',
                        'bfg_1994010106_fhr09_prateb_control.nc',
                        'bfg_1994010112_fhr06_prateb_control.nc',
                        'bfg_1994010112_fhr09_prateb_control.nc',
                        'bfg_1994010118_fhr06_prateb_control.nc',
                        'bfg_1994010118_fhr09_prateb_control.nc',
                        'bfg_1994010200_fhr06_prateb_control.nc']

DATA_DIR = 'data'
CONFIGS_DIR = 'configs'
PYTEST_CALLING_DIR = Path(__file__).parent.resolve()
TEST_DATA_PATH = os.path.join(PYTEST_CALLING_DIR, DATA_DIR)
BFG_PATH = [os.path.join(TEST_DATA_PATH,
                         file_name) for file_name in TEST_DATA_FILE_NAMES]

VALID_CONFIG_DICT = {'harvester_name': hv_registry.GLOBAL_BUCKET_PRECIP_AVE,
                     'filenames' : BFG_PATH,
                     'statistic': ['mean','std'],
                     'variable': ['prateb_ave']}

def test_variable_names():
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].variable == 'prateb_ave'

def test_global_mean_values():
    """ The harvester returns a numpy 32 bit floating point number.
        The test must cast the global mean value hard coded here to a 
        numpy.float32. Otherwise the assert function fails.  The value
        of 2.4695819e-05 is the mean value of the global means calculated 
        from eight forecast files:
        
        bfg_1994010100_fhr09_prateb_control.nc
        bfg_1994010106_fhr06_prateb_control.nc
        bfg_1994010106_fhr09_prateb_control.nc
        bfg_1994010112_fhr06_prateb_control.nc
        bfg_1994010112_fhr09_prateb_control.nc
        bfg_1994010118_fhr06_prateb_control.nc
        bfg_1994010118_fhr09_prateb_control.nc
        bfg_1994010200_fhr06_prateb_control.nc
        
        When averaged together, these files represent a 24 hour mean. The 
        average value hard-coded in this test was calculated from 
        these forecast files using a separate python code.
    """
    data1 = harvest(VALID_CONFIG_DICT)
    global_mean = np.float32(3.117385391676263e-05)
    assert data1[0].value == global_mean
    global_std = np.float32(6.497697755052876e-05)
    assert data1[1].value == global_std

def test_units():
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].units == "kg/m**2/s"

def test_cycletime():
    """ The hard coded datetimestr 1994-01-01 12:00:00
        is the median midpoint time of the filenames defined above in the 
        BFG_PATH.  We have to convert this into a datetime object in order
        to compare this string to what is returned by 
        global_bucket_precip_ave.py
    """
    data1 = harvest(VALID_CONFIG_DICT)
    expected_datetime = datetime.strptime("1994-01-01 12:00:00",
                                          "%Y-%m-%d %H:%M:%S")
    assert data1[0].mediantime == expected_datetime

def test_longname():
    data1 = harvest(VALID_CONFIG_DICT)
    var_longname = "bucket surface precipitation rate"
    assert data1[0].longname == var_longname

def test_precip_harvester():
    data1 = harvest(VALID_CONFIG_DICT)  
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].filenames==BFG_PATH
    test_variable_names()
    test_units()
    test_global_mean_values()
    test_cycletime() 
    test_longname()

def main():
    test_precip_harvester()

if __name__=='__main__':
    main()

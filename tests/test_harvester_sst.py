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

TEST_DATA_FILE_NAMES = ['bfg_1994010100_fhr09_snowiceocean_control.nc',
                        'bfg_1994010106_fhr06_snowiceocean_control.nc',
                        'bfg_1994010106_fhr09_snowiceocean_control.nc',
                        'bfg_1994010112_fhr06_snowiceocean_control.nc',
                        'bfg_1994010112_fhr09_snowiceocean_control.nc',
                        'bfg_1994010118_fhr06_snowiceocean_control.nc',
                        'bfg_1994010118_fhr09_snowiceocean_control.nc',
                        'bfg_1994010200_fhr06_snowiceocean_control.nc']

DATA_DIR = os.path.join(Path(__file__).parent.parent.resolve(), 'src', 'score_hv', 'data')
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
                     'statistic': ['mean','variance', 'minimum', 'maximum'],
                     'variable': ['nsst','sst'],
                     }

def test_gridcell_area_conservation(tolerance=0.001):

    gridcell_area_data = Dataset(GRIDCELL_AREA_DATA_PATH)
    assert gridcell_area_data['area'].units == 'steradian'
    sum_gridcell_area = np.sum(gridcell_area_data.variables['area'])
    assert sum_gridcell_area < (1 + tolerance) * 4 * np.pi
    assert sum_gridcell_area > (1 - tolerance) * 4 * np.pi
    gridcell_area_data.close()

def test_variable_names():
    """Here we are testing two variables.  The daily_bfg harvester
       should return values for both variables at once.
       """
    expected_variables = ['nsst', 'sst'] 
    assert VALID_CONFIG_DICT['variable'] == expected_variables

def test_global_mean_values(tolerance=0.001):
    """ 
        The values of the calculated_means list were 
        calculated from these eight forecast files:

        bfg_1994010100_fhr09_snowiceocean_control.nc
        bfg_1994010106_fhr06_snowiceocean_control.nc
        bfg_1994010106_fhr09_snowiceocean_control.nc
        bfg_1994010112_fhr06_snowiceocean_control.nc
        bfg_1994010112_fhr09_snowiceocean_control.nc
        bfg_1994010118_fhr06_snowiceocean_control.nc
        bfg_1994010118_fhr09_snowiceocean_control.nc
        bfg_1994010200_fhr06_snowiceocean_control.nc
        
        When averaged together, these files represent a 24 hour mean. The 
        average values hard-coded in this test was calculated from 
        forecast files using a separate python code.

        In this test there are four regions.  The daily_bfg harvester will return
        the values of all four regions at once.  
    """
    data1 = harvest(VALID_CONFIG_DICT)

    for item in data1:
        if item.variable == 'nsst' and item.statistic == 'mean':
           calculated_means = 291.24683220759823
           assert calculated_means <= (1 + tolerance) * item.value
           assert calculated_means >= (1 - tolerance) * item.value
        elif item.variable == 'sst' and item.statistic == 'mean':
           calculated_means = 290.5971362792539
           assert calculated_means <= (1 + tolerance) * item.value
           assert calculated_means >= (1 - tolerance) * item.value

def test_gridcell_variance(tolerance=0.001):
    """
      The values of the calculated_variances list were calculated
      from the forecast files listed above in a separate python script.
      """
    data1 = harvest(VALID_CONFIG_DICT)
     
    for item in data1:
        if item.variable == 'nsst4' and item.statistic == 'variance':
           calculated_variances = 99.88760798914969
           assert calculated_variances <= (1 + tolerance) * item.value
           assert calculated_variances >= (1 - tolerance) * item.value
        elif item.variable == 'sst' and item.statistic == 'variance':
           calculated_variances = 145.90406096430016 
           assert calculated_variances <= (1 + tolerance) * item.value
           assert calculated_variances >= (1 - tolerance) * item.value
  
def test_gridcell_min_max(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
     
    for item in data1:
        if item.variable == 'nsst' and item.statistic == 'minimum':
           calculated_min  = 241.88905334472656
           assert calculated_min <= (1 + tolerance) * item.value
           assert calculated_min >= (1 - tolerance) * item.value

        elif item.variable == 'nsst' and item.statistic == 'maximum':
           calculated_max = 304.51293182373047
           assert calculated_max <= (1 + tolerance) * item.value
           assert calculated_max >= (1 - tolerance) * item.value

        elif item.variable == 'sst' and item.statistic == 'minimum':
           calculated_min = 232.33126258850098 
           assert calculated_min <= (1 + tolerance) * item.value
           assert calculated_min >= (1 - tolerance) * item.value

        elif item.variable == 'sst' and item.statistic == 'maximum':
           calculated_max = 304.88085556030273 
           assert calculated_max <= (1 + tolerance) * item.value
           assert calculated_max >= (1 - tolerance) * item.value               
    
def test_units():
    variable_dictionary = {}
    data1 = harvest(VALID_CONFIG_DICT)

    for item in data1:
        if item.variable == 'snowiceoceanl4':
           expected_units = 'xxx'
           assert expected_units == item.units 
        elif item.variable == 'snowiceoceanm':
           expected_units = 'kg/m**2'
           assert expected_units == item.units 

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

    for item in data1:
        if item.variable == 'snowiceoceant4':
           expected_longname = 'snowiceocean temperature unknown layer 4'
           assert expected_longname == item.longname 
        elif item.variable == 'tg3':
           expected_longname = 'deep snowiceocean temperature'
           assert expected_longname == item.longname

def test_snowiceocean_moisture_level4_harvester():
    data1 = harvest(VALID_CONFIG_DICT) 
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].filenames==BFG_PATH

def main():
    test_gridcell_area_conservation()
    test_snowiceocean_moisture_level4_harvester()
    test_variable_names()
    test_units()
    test_global_mean_values()
    test_gridcell_variance()
    test_gridcell_min_max()
    test_cycletime() 
    test_longname()

if __name__=='__main__':
    main()

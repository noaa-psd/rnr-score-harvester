#!/usr/bin/env python

import os
import sys
import math
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

TEST_DATA_FILE_NAMES = ['bfg_1994010100_fhr09_fluxes_control.nc',
                        'bfg_1994010106_fhr06_fluxes_control.nc',
                        'bfg_1994010106_fhr09_fluxes_control.nc',
                        'bfg_1994010112_fhr06_fluxes_control.nc',
                        'bfg_1994010112_fhr09_fluxes_control.nc',
                        'bfg_1994010118_fhr06_fluxes_control.nc',
                        'bfg_1994010118_fhr09_fluxes_control.nc',
                        'bfg_1994010200_fhr06_fluxes_control.nc']

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
                     'statistic': ['mean', 'variance', 'minimum', 'maximum'],
                     'variable': ['netef_ave']}

def test_gridcell_area_conservation(tolerance=0.001):

    gridcell_area_data = Dataset(GRIDCELL_AREA_DATA_PATH)
    
    assert gridcell_area_data['area'].units == 'steradian'
    
    sum_gridcell_area = np.sum(gridcell_area_data.variables['area'])
    
    assert sum_gridcell_area < (1 + tolerance) * 4 * np.pi
    assert sum_gridcell_area > (1 - tolerance) * 4 * np.pi
    
    gridcell_area_data.close()

def test_variable_names():
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].variable == 'netef_ave'

def test_global_mean_values(tolerance=0.001):
    """The value of 14.55159598489006 is the mean value of the global means 
    calculated from eight forecast files:
        
        bfg_1994010100_fhr09_fluxes_control.nc
        bfg_1994010106_fhr06_fluxes_control.nc
        bfg_1994010106_fhr09_fluxes_control.nc
        bfg_1994010112_fhr06_fluxes_control.nc
        bfg_1994010112_fhr09_fluxes_control.nc
        bfg_1994010118_fhr06_fluxes_control.nc
        bfg_1994010118_fhr09_fluxes_control.nc
        bfg_1994010200_fhr06_fluxes_control.nc
        
    When averaged together, these files represent a 24 hour mean. The 
    average value hard-coded in this test was calculated from 
    these forecast files using a separate python code.
    """
    data1 = harvest(VALID_CONFIG_DICT)

    global_mean = 14.55159598489006 
    for item in data1:
        if item.statistic == 'mean':
           assert item.value <= (1 + tolerance) * global_mean
           assert item.value >= (1 - tolerance) * global_mean

def test_gridcell_variance(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)

    variance = 17248.285817786993 
    for item in data1:
        if item.statistic == 'variance':
           assert item.value <= (1 + tolerance) * variance 
           assert item.value >= (1 - tolerance) * variance 
    
def test_gridcell_min_max(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    """The following offline min and max were calculated from an external 
    python code
    """
    offline_min = -1081.2091522216795 
    offline_max = 370.30528926849354 
    for item in data1:
        if item.statistic == 'minimum':
           assert abs(item.value) <= (1 + tolerance) * abs(offline_min) 
           assert abs(item.value) >= (1 - tolerance) * abs(offline_min)
        elif item.statistic == 'maximum':
            assert item.value <= (1 + tolerance) * offline_max 
            assert item.value >= (1 - tolerance) * offline_max
            
def test_units():
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].units == "W/m**2"

def test_cycletime():
    """ The hard coded datetimestr 1994-01-01 12:00:00
        is the median midpoint time of the filenames defined above in the 
        BFG_PATH.  We have to convert this into a datetime object in order
        to compare this string to what is returned by 
        daily_bfg.py
    """
    data1 = harvest(VALID_CONFIG_DICT)
    expected_datetime = datetime.strptime("1994-01-01 12:00:00",
                                          "%Y-%m-%d %H:%M:%S")
    assert data1[0].mediantime == expected_datetime

def test_longname():
    data1 = harvest(VALID_CONFIG_DICT)
    var_longname = "surface energy balance"
    assert data1[0].longname == var_longname

def test_toa_radiative_flux():
    data1 = harvest(VALID_CONFIG_DICT)  
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].filenames==BFG_PATH

def main():
    test_gridcell_area_conservation()
    test_toa_radiative_flux()
    test_variable_names()
    test_units()
    test_global_mean_values()
    test_gridcell_variance()
    test_gridcell_min_max()
    test_cycletime() 
    test_longname()

if __name__=='__main__':
    main()

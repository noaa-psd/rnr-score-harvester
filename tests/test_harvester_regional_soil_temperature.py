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

TEST_DATA_FILE_NAMES = ['bfg_1994010100_fhr09_soil_control.nc',
                        'bfg_1994010106_fhr06_soil_control.nc',
                        'bfg_1994010106_fhr09_soil_control.nc',
                        'bfg_1994010112_fhr06_soil_control.nc',
                        'bfg_1994010112_fhr09_soil_control.nc',
                        'bfg_1994010118_fhr06_soil_control.nc',
                        'bfg_1994010118_fhr09_soil_control.nc',
                        'bfg_1994010200_fhr06_soil_control.nc']

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
                     'variable': ['soilt4','tg3'],
                     'regions': {
                               'north_hemi': {'north_lat': 90.0, 'south_lat': 0.0, 'west_long': 0.0, 'east_long': 360.0},
                               'south_hemi': {'north_lat': 0.0, 'south_lat': -90.0, 'west_long': 0.0, 'east_long': 360.0},
                               'eastern_hemis': {'north_lat': 90.0, 'south_lat': -90.0, 'west_long': 0.0, 'east_long': 180.0},
                               'western_hemis': {'north_lat': 90.0, 'south_lat': -90.0, 'west_long': 180.0, 'east_long': 360.0},
                               'global': {'north_lat': 90.0, 'south_lat': -90.0, 'west_long': 0.0, 'east_long': 360.0},
                               }

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
    expected_variables = ['soilt4', 'tg3'] 
    assert VALID_CONFIG_DICT['variable'] == expected_variables

def test_global_mean_values(tolerance=0.001):
    """ 
        The values of the calculated_means list were 
        calculated from these eight forecast files:

        bfg_1994010100_fhr09_soil_control.nc
        bfg_1994010106_fhr06_soil_control.nc
        bfg_1994010106_fhr09_soil_control.nc
        bfg_1994010112_fhr06_soil_control.nc
        bfg_1994010112_fhr09_soil_control.nc
        bfg_1994010118_fhr06_soil_control.nc
        bfg_1994010118_fhr09_soil_control.nc
        bfg_1994010200_fhr06_soil_control.nc
        
        When averaged together, these files represent a 24 hour mean. The 
        average values hard-coded in this test was calculated from 
        forecast files using a separate python code.

        In this test there are four regions.  The daily_bfg harvester will return
        the values of all four regions at once.  
    """
    data1 = harvest(VALID_CONFIG_DICT)
    print("data1  ",data1)

    soilt_means = [283.39312230347826,298.0164576940641,287.4417380555854,286.83712118855755,287.231900730573]
    tg3_means = [284.79130915122187,294.553246977907,287.49533152594,287.08787370517393,287.3539198918497]
    soilt_index = 0
    tg3_index = 0
    for item in data1:
        if item.variable == 'soilt4' and item.statistic == 'mean':
           assert soilt_means[soilt_index] <= (1 + tolerance) * item.value
           assert soilt_means[soilt_index] >= (1 - tolerance) * item.value
           soilt_index = soilt_index + 1

        elif item.variable == 'tg3' and item.statistic == 'mean':
           assert tg3_means[tg3_index] <= (1 + tolerance) * item.value
           assert tg3_means[tg3_index] >= (1 - tolerance) * item.value
           tg3_index = tg3_index + 1

def test_gridcell_variance(tolerance=0.001):
    """
      The values of the calculated_variances list were calculated
      from the forecast files listed above in a separate python script.
      """
    data1 = harvest(VALID_CONFIG_DICT)
    
    soilt_variances = [159.27152912176592,20.987013339986156,168.20701798859776,156.91227453651263,164.3699225807664]
    tg3_variances = [160.23127318696643,18.239349630567105,139.84038834454338,144.2430235934427,141.40598164295744]
    soilt_index = 0
    tg3_index = 0
    for item in data1:
        if item.variable == 'soilt4' and item.statistic == 'variance':
           assert soilt_variances[soilt_index] <= (1 + tolerance) * item.value
           assert soilt_variances[soilt_index] >= (1 - tolerance) * item.value
           soilt_index = soilt_index + 1

        elif item.variable == 'tg3' and item.statistic == 'variance':
            assert tg3_variances[tg3_index] <= (1 + tolerance) * item.value
            assert tg3_variances[tg3_index] >= (1 - tolerance) * item.value
            tg3_index = tg3_index + 1

def test_gridcell_min(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
   
    soilt_min = [240.5829497518155,272.7433567678382,242.01396420200825,240.5829497518155,240.5829497518155]
    tg3_min = [250.65328979492188,273.11251509181625,257.85712288382484,250.65328979492188,250.65328979492188]
    soilt_index = 0
    tg3_index = 0

    for item in data1:
        if item.variable == 'soilt4' and item.statistic == 'minimum':
           assert soilt_min[soilt_index] <= (1 + tolerance) * item.value
           assert soilt_min[soilt_index] >= (1 - tolerance) * item.value
           soilt_index = soilt_index + 1

        elif item.variable == 'tg3' and item.statistic == 'minimum':
             assert tg3_min[tg3_index] <= (1 + tolerance) * item.value
             assert tg3_min[tg3_index] >= (1 - tolerance) * item.value
             tg3_index = tg3_index + 1
    
def test_gridcell_max(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)

    soilt_max = [308.44702529907227,308.444991167564,308.44702529907227,307.2143072168101,308.44702529907227]
    tg3_max = [302.3920593261719,301.1194466437604,302.3920593261719,302.3514404296875,302.3920593261719] 
    soilt_index = 0
    tg3_index = 0

    for item in data1:
        if item.variable == 'soilt4' and item.statistic == 'maximum':
           assert soilt_max[soilt_index] <= (1 + tolerance) * item.value
           assert soilt_max[soilt_index] >= (1 - tolerance) * item.value
           soilt_index = soilt_index + 1

        elif item.variable == 'tg3' and item.statistic == 'maximum':
               assert tg3_max[tg3_index] <= (1 + tolerance) * item.value
               assert tg3_max[tg3_index] >= (1 - tolerance) * item.value     
               tg3_index = tg3_index + 1

def test_units():
    variable_dictionary = {}
    data1 = harvest(VALID_CONFIG_DICT)

    for item in data1:
        if item.variable == 'soilt4':
           expected_units = 'K'
           assert expected_units == item.units 
        elif item.variable == 'tg3':
           expected_units = 'K'
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
        if item.variable == 'soilt4':
           expected_longname = 'soil temperature unknown layer 4'
           assert expected_longname == item.longname 
        elif item.variable == 'tg3':
           expected_longname = 'deep soil temperature'
           assert expected_longname == item.longname

def test_soil_moisture_level4_harvester():
    data1 = harvest(VALID_CONFIG_DICT) 
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].filenames==BFG_PATH

def main():
    test_gridcell_area_conservation()
    test_soil_moisture_level4_harvester()
    test_variable_names()
    test_units()
    test_global_mean_values()
    test_gridcell_variance()
    test_gridcell_min()
    test_gridcell_max()
    test_cycletime() 
    test_longname()

if __name__=='__main__':
    main()

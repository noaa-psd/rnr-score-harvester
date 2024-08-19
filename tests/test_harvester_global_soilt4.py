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
                     'statistic': ['mean','variance', 'minimum', 'maximum'],
                     'variable': ['soilt4','tg3'],
                     'surface_mask': ['land'],
                     'regions': {
                                 'conus': {'north_lat': 49, 'south_lat': 24, 'west_long': 235.0, 'east_long': 294.0},
                                 'date_line': {'north_lat': 90.0, 'south_lat': -90.0, 'west_long': 50.0, 'east_long': 355.0},
                                 'eastern_hemis': {'north_lat': 90.0, 'south_lat': -90.0, 'west_long': 0.0, 'east_long': 180.0},
                                 'western_hemis': {'north_lat': 90.0, 'south_lat': -90.0, 'west_long': 180.0, 'east_long': 360.0},
                                 'prime_meridian': {'north_lat': 90.0, 'south_lat': -90.0,'west_long': 270.0, 'east_long': 30.0},
                                 'global': {'north_lat': 90.0, 'south_lat': -90.0, 'west_long': 0, 'east_long': 360 }
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
    """
    data1 = harvest(VALID_CONFIG_DICT)

    for item in data1:
        if item.variable == 'soilt4' and item.statistic == 'mean':
           calculated_means = [185.32222398385198, 72.63987395153038, 110.10595539740916, 61.544335311892375]
           for index in range(len(calculated_means)):
               assert calculated_means[index] <= (1 + tolerance) * item.value[index]
               assert calculated_means[index] >= (1 - tolerance) * item.value[index]
        elif item.variable == 'tg3' and item.statistic == 'mean':
           calculated_means = [188.81661183377483, 72.58709232903506, 109.97426671485088, 61.52662792107943]
           for index in range(len(calculated_means)):
               assert calculated_means[index] <= (1 + tolerance) * item.value[index]
               assert calculated_means[index] >= (1 - tolerance) * item.value[index]

def test_gridcell_variance(tolerance=0.001):
    """
      The values of the calculated_variances list were calculated
      from the forecast files listed above in a separate python script.
      """
    data1 = harvest(VALID_CONFIG_DICT)
    
    for item in data1:
        if item.variable == 'soilt4' and item.statistic == 'variance':
          calculated_variances = [34.16445033781812, 359.9219902304048, 381.82574388177915, 317.4400943521678]
          for index in range(len(calculated_variances)):
               assert calculated_variances[index] <= (1 + tolerance) * item.value[index]
               assert calculated_variances[index] >= (1 - tolerance) * item.value[index]
        elif item.variable == 'tg3' and item.statistic == 'variance':
          calculated_variances = [29.086693999806407, 386.07377365686307, 400.09041459167867, 337.26524069147945]
          for index in range(len(calculated_variances)):
              assert calculated_variances[index] <= (1 + tolerance) * item.value[index]
              assert calculated_variances[index] >= (1 - tolerance) * item.value[index]

def test_gridcell_min_max(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    
    for item in data1:
        if item.variable == 'soilt4' and item.statistic == 'minimum':
           calculated_min  = [269.2041, 223.81133, 223.81133, 228.58289]
           for index in range(len(calculated_min)):
               assert calculated_min[index] <= (1 + tolerance) * item.value[index]
               assert calculated_min[index] >= (1 - tolerance) * item.value[index]

        elif item.variable == 'soilt4' and item.statistic == 'maximum':
           calculated_max = [299.17435, 308.445, 308.44702, 307.2143]
           for index in range(len(calculated_max)):
               assert calculated_max[index] <= (1 + tolerance) * item.value[index]
               assert calculated_max[index] >= (1 - tolerance) * item.value[index]

        elif item.variable == 'tg3' and item.statistic == 'minimum':
           calculated_min = [273.15, 215.50061, 215.50061, 222.30954]
           for index in range(len(calculated_min)):
               assert calculated_min[index] <= (1 + tolerance) * item.value[index]
               assert calculated_min[index] >= (1 - tolerance) * item.value[index]

        elif item.variable == 'tg3' and item.statistic == 'maximum':
           calculated_max = [298.1382, 301.79813, 302.39206, 302.35144]
           for index in range(len(calculated_max)):
               assert calculated_max[index] <= (1 + tolerance) * item.value[index]
               assert calculated_max[index] >= (1 - tolerance) * item.value[index]               
    
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
    test_gridcell_min_max()
    test_cycletime() 
    test_longname()

if __name__=='__main__':
    main()

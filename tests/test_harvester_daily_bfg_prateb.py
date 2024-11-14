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
from score_hv.region_utils import GeoRegionsCatalog 

TEST_DATA_FILE_NAMES = ['bfg_1994010100_fhr09_prateb_control.nc',
                        'bfg_1994010106_fhr06_prateb_control.nc',
                        'bfg_1994010106_fhr09_prateb_control.nc',
                        'bfg_1994010112_fhr06_prateb_control.nc',
                        'bfg_1994010112_fhr09_prateb_control.nc',
                        'bfg_1994010118_fhr06_prateb_control.nc',
                        'bfg_1994010118_fhr09_prateb_control.nc',
                        'bfg_1994010200_fhr06_prateb_control.nc']

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
                     'variable': ['prateb_ave'],
                     'regions':  {
                                 'conus': {'north_lat': 49, 'south_lat': 24, 'west_long': 235.0, 'east_long': 294.0},
                                 'date_line': {'north_lat': 90.0, 'south_lat': -90.0, 'west_long': 50.0, 'east_long': 355.0},
                                 'eastern_hemis': {'north_lat': 90.0, 'south_lat': -90.0, 'west_long': 0.0, 'east_long': 180.0},
                                 'western_hemis': {'north_lat': 90.0, 'south_lat': -90.0, 'west_long': 180.0, 'east_long': 360.0},
                                 'prime_meridian': {'north_lat': 90.0, 'south_lat': -90.0,'west_long': 270.0, 'east_long': 30.0},
                                 'global': {'north_lat': 90.0, 'south_lat': -90.0, 'west_long': 0, 'east_long': 360 },
                                 'tropical': {'north_lat': 5, 'south_lat': -5, 'west_long': 0, 'east_long': 360.0},
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
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].variable == 'prateb_ave'

def test_global_mean_values(tolerance=0.001):
    """The mean values are calculated from these 
       eight forecast files:
        
        bfg_1994010100_fhr09_prateb_control.nc
        bfg_1994010106_fhr06_prateb_control.nc
        bfg_1994010106_fhr09_prateb_control.nc
        bfg_1994010112_fhr06_prateb_control.nc
        bfg_1994010112_fhr09_prateb_control.nc
        bfg_1994010118_fhr06_prateb_control.nc
        bfg_1994010118_fhr09_prateb_control.nc
        bfg_1994010200_fhr06_prateb_control.nc
        
    When averaged together, these files represent a 24 hour mean. The 
    average values hard-coded in this test were calculated from 
    these forecast files using a separate python code.
    """
    data1 = harvest(VALID_CONFIG_DICT)
    """ 
      If the word region is in data1 returned by the harvester then has_region will be True.
      """
    for harvested_data in data1[0]: 
        has_region = any(hasattr(data, 'regions') for data in data1) #Returns a boolean.
        if has_region:
           global_means = [2.8757226299207095e-05, 3.275308514564545e-05, 3.225420289425872e-05, \
                           3.0093478472285123e-05, 3.25835162239216e-05, 3.117384068327193e-05, \
                           7.04825819962097e-05]
            
           for i, harvested_tuple in enumerate(data1):
               if harvested_tuple.statistic == 'mean':
                  num_values = len(harvested_tuple.value)
                  for inum in range(num_values):
                      assert global_means[inum] <= (1 + tolerance) * harvested_tuple.value[inum]
                      assert global_means[inum] >= (1 - tolerance) * harvested_tuple.value[inum]

def test_variance_values(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    for harvested_data in data1[0]:  
        has_region = any(hasattr(data, 'regions') for data in data1) #Returns a boolean.
        if has_region:
           variances = [4.404340892598467e-09, 6.321334139899629e-09, 6.012355081136634e-09, \
                        5.4622850553750265e-09, 6.268698538596581e-09, 5.738487271970866e-09, \
                        1.482636074512706e-08] 
           for i, harvested_tuple in enumerate(data1):
                if harvested_tuple.statistic == 'variance':
                   num_values = len(harvested_tuple.value)
                   for inum in range(num_values):
                       assert variances[inum] <= (1 + tolerance) * harvested_tuple.value[inum]
                       assert variances[inum] >= (1 - tolerance) * harvested_tuple.value[inum]
      
def test_gridcell_min(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
     
    """ 
      If the word region is in data1 returned by the harvester then has_region will be True.
      """
    for harvested_data in data1[0]:  
        has_region = any(hasattr(data, 'region') for data in data1) #Returns a boolean.
        if has_region:
           min_values = [ 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
           for i, harvested_tuple in enumerate(data1):
                if harvested_tuple.statistic == 'minimum':
                   num_values = len(harvested_tuple.value)
                   for inum in range(num_values):
                       assert min_values[inum] <= (1 + tolerance) * harvested_tuple.value[inum]
                       assert min_values[inum] >= (1 - tolerance) * harvested_tuple.value[inum]
 
def test_gridcell_max(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
     
    for harvested_data in data1[0]:  
        has_region = any(hasattr(data, 'region') for data in data1) #Returns a boolean.
        if has_region:
           max_values = [0.00071415555, 0.0043600933, 0.0043600933, \
                         0.0032889172, 0.0043600933, 0.0043600933, \
                         0.0032889172] 
 
           for i, harvested_tuple in enumerate(data1):
               if harvested_tuple.statistic == 'maximum':
                  num_values = len(harvested_tuple.value)
                  for inum in range(num_values):
                      assert max_values[inum] <= (1 + tolerance) * harvested_tuple.value[inum]
                      assert max_values[inum] >= (1 - tolerance) * harvested_tuple.value[inum]

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

def main():
    test_gridcell_area_conservation()
    test_precip_harvester()
    test_variable_names()
    test_units()
    test_global_mean_values()
    test_variance_values()
    test_gridcell_min()
    test_gridcell_max()
    test_cycletime() 
    test_longname()

if __name__=='__main__':
    main()

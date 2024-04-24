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
from score_hv.region_utils import GeoRegions 

TEST_DATA_FILE_NAMES = ['bfg_1994010100_fhr09_prateb_control.nc',
                        'bfg_1994010106_fhr06_prateb_control.nc',
                        'bfg_1994010106_fhr09_prateb_control.nc',
                        'bfg_1994010112_fhr06_prateb_control.nc',
                        'bfg_1994010112_fhr09_prateb_control.nc',
                        'bfg_1994010118_fhr06_prateb_control.nc',
                        'bfg_1994010118_fhr09_prateb_control.nc',
                        'bfg_1994010200_fhr06_prateb_control.nc']

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
                     'variable': ['prateb_ave'],
                     'region':   [
                                  ['tropical', -5.0, 5.0, 0.0, 360],
                                  ['north_hemis', 20.0, 60.0, 0.0, 360.0],
                                  ['south_hemis', -60.0, -20.0, 0.0, 360.0],
                                  ['conus',24.0, 49.0, 235.0, 293.0],
                                  ['global',-90.0, 90.0, 0.0, 360.0],
                                  ['prime_meridian',-90,90,130,90],
                                 ]}

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

def test_global_mean_values_offline(tolerance=0.001):
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
    if 'region' in str(data1[0]):
        global_means = [7.04825819962097e-05, 2.8965191456702544e-05,2.2748022739982528e-05, \
                        2.2748022739982528e-05,3.1183886948414354e-05,2.3081037860291425e-05]
    iregion = 0 
    for i, harvested_tuple in enumerate(data1):
        if harvested_tuple.statistic == 'mean':
           assert global_means[iregion] <= (1 + tolerance) * harvested_tuple.value[iregion]
           assert global_means[iregion] <= (1 + tolerance) * harvested_tuple.value[iregion]
           iregion = iregion + 1

def test_gridcell_variance(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    
    if 'region' in str(data1[0]):
        variances = [1.48348705705598e-08, 4.3899346663891055e-09, 2.452054630702822e-09, \
                 4.47877939776161e-09, 5.7414012487690275e-09,3.4993706919644485e-09]
    iregion = 0    
    for i, harvested_tuple in enumerate(data1):
        if harvested_tuple.statistic == 'variance': 
           assert variances[iregion] <= (1 + tolerance) * harvested_tuple.value[iregion]
           assert variances[iregion] <= (1 + tolerance) * harvested_tuple.value[iregion]
           iregion = iregion + 1

def test_gridcell_min(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    if 'region' in str(data1[0]):    
        min_values = [ 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    iregion = 0    
    for i, harvested_tuple in enumerate(data1):
        if harvested_tuple.statistic == 'minimum': 
           assert min_values[iregion] <= (1 + tolerance) * harvested_tuple.value[iregion]
           assert min_values[iregion] <= (1 + tolerance) * harvested_tuple.value[iregion]
           iregion = iregion + 1

def test_gridcell_max(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    if 'region' in str(data1[0]):
        max_values = [0.0032889172, 0.002300344, 0.0009843283, 0.00071415555, 0.004360093, 0.0022887615]

    iregion = 0    
    for i, harvested_tuple in enumerate(data1):
        if harvested_tuple.statistic == 'maximum': 
           assert max_values[iregion] <= (1 + tolerance) * harvested_tuple.value[iregion]
           assert max_values[iregion] <= (1 + tolerance) * harvested_tuple.value[iregion]
           iregion = iregion + 1

     
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
    test_global_mean_values_offline()
    test_gridcell_variance()
    test_gridcell_min()
    test_gridcell_max()
    test_cycletime() 
    test_longname()

if __name__=='__main__':
    main()

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
                     'variable': ['prate_ave'],
                     'regions': {'conus':{'north_lat': 49, 'south_lat': 24, 'west_long': 235, 'east_long':293},
                                 'south_hemis': {'north_lat':0, 'south_lat':-90, 'west_long':0, 'east_long':360},
                                 'north_hemis': {'north_lat':90, 'south_lat':0, 'west_long':0, 'east_long':360},
                                 'tropics': {'north_lat': 24.0, 'south_lat': -24.0, 'west_long': 0.0, 'east_long': 360.0},
                                 'global': { }
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
    assert data1[0].variable == 'prate_ave'

def test_mean_values(tolerance=0.001):
    """
      The values of the calculated_means list were
      calculated from these eight forecast files:

        bfg_1994010100_fhr09_prateb_control.nc
        bfg_1994010106_fhr06_prateb_control.nc
        bfg_1994010106_fhr09_prateb_control.nc
        bfg_1994010112_fhr06_prateb_control.nc
        bfg_1994010112_fhr09_prateb_control.nc
        bfg_1994010118_fhr06_prateb_control.nc
        bfg_1994010118_fhr09_prateb_control.nc
        bfg_1994010200_fhr06_prateb_control.nc

      When averaged together, these files represent a 24 hour mean.
      In this test there are four regions.  The daily_bfg harvester will return
      the values of all three regions at once.  
      """
    data1 = harvest(VALID_CONFIG_DICT)
    for item in data1:
        if item.statistic == 'mean':
           calculated_means = [0.03251096850286386,0.03876764799618554,0.043024001372664884,0.060860878009092546,0.0408958246844251]
           for index in range(len(calculated_means)):
               assert calculated_means[index] <= (1 + tolerance) * item.value[index]
               assert calculated_means[index] >= (1 - tolerance) * item.value[index]

                
def test_gridcell_variance(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    for item in data1:
        if item.statistic == 'variance':
           calculated_variances = [0.000430468651630288,0.00108603948347438,0.0016457705882051094,0.002221834374899518,0.0013704341718561103]
           for index in range(len(calculated_variances)):
               assert calculated_variances[index] <= (1 + tolerance) * item.value[index]
               assert calculated_variances[index] >= (1 - tolerance) * item.value[index]
 

def test_gridcell_min_max(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    for item in data1:
        if item.statistic == 'minimum':
           calculated_min  = [0.0015120203606784344,1.5071715324666002e-06,4.0326767099252425e-11,4.032676709925242e-11,4.032676709925242e-11]
           for index in range(len(calculated_min)):
               assert calculated_min[index] <= (1 + tolerance) * item.value[index]
               assert calculated_min[index] >= (1 - tolerance) * item.value[index]
        if item.statistic == 'maximum':
           calculated_max = [0.10341465473175052,0.2618738580495119,0.543392937630415,0.543392937630415,0.5433929376304149]
           for index in range(len(calculated_max)):
               assert calculated_max[index] <= (1 + tolerance) * item.value[index]
               assert calculated_max[index] >= (1 - tolerance) * item.value[index]

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
    var_longname = "surface precipitation rate"
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
    test_mean_values()
    test_gridcell_variance()
    test_gridcell_min_max()
    test_cycletime() 
    test_longname()

if __name__=='__main__':
    main()

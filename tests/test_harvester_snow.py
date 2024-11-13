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
                     'variable': ['snod','weasd'],
                     'regions': {
                               'north_hemi': {'north_lat': 90.0, 'south_lat': 0.0, 'west_long': 0.0, 'east_long': 360.0},
                               'west_hemi': {'north_lat':90, 'south_lat':0, 'west_long':180, 'east_long':360},
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
    expected_variables = ['snod','weasd'] 
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
    """
    data1 = harvest(VALID_CONFIG_DICT)
    for item in data1:
        if item.variable == 'snod' and item.statistic == 'mean':
           calculated_means = [0.11504197586536281,0.14035512130825797]
           for index in range(len(calculated_means)):
               assert calculated_means[index] <= (1 + tolerance) * item.value[index]
               assert calculated_means[index] >= (1 - tolerance) * item.value[index]                
        elif item.variable == 'weasd' and item.statistic == 'mean':
           calculated_means = [23.782534262971975,30.224421066570706]
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
        if item.variable == 'snod' and item.statistic == 'variance':
          calculated_variance = [0.040404931116929776,0.05529798607847377]
          for index in range(len(calculated_variance)):
               assert calculated_variance[index] <= (1 + tolerance) * item.value[index]
               assert calculated_variance[index] >= (1 - tolerance) * item.value[index]
        
        elif item.variable == 'weasd' and item.statistic == 'variance':
          calculated_variance = [2273.434235984401,3596.5679406750983] 
          for index in range(len(calculated_variance)):
               assert calculated_variance[index] <= (1 + tolerance) * item.value[index]
               assert calculated_variance[index] >= (1 - tolerance) * item.value[index]
  
def test_gridcell_min_max(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    
    for item in data1:
        if item.variable == 'snod' and item.statistic == 'minimum':
           calculated_min  = [0.0,0.0]
           for index in range(len(calculated_min)):
               assert calculated_min[index] <= (1 + tolerance) * item.value[index]
               assert calculated_min[index] >= (1 - tolerance) * item.value[index]

        elif item.variable == 'snod' and item.statistic == 'maximum':
           calculated_max = [4.501649915605916,4.501649915605916]
           for index in range(len(calculated_max)):
               assert calculated_max[index] <= (1 + tolerance) * item.value[index]
               assert calculated_max[index] >= (1 - tolerance) * item.value[index]

        elif item.variable == 'weasd' and item.statistic == 'minimum':
           calculated_min = [0.0,0.0]
           for index in range(len(calculated_min)):
               assert calculated_min[index] <= (1 + tolerance) * item.value[index]
               assert calculated_min[index] >= (1 - tolerance) * item.value[index]

        elif item.variable == 'weasd' and item.statistic == 'maximum':
           calculated_max = [1630.2353464365858,1630.2353464365858]
           for index in range(len(calculated_max)):
               assert calculated_max[index] <= (1 + tolerance) * item.value[index]
               assert calculated_max[index] >= (1 - tolerance) * item.value[index]               
    
def test_units():
    variable_dictionary = {}
    data1 = harvest(VALID_CONFIG_DICT)

    for item in data1:
        if item.variable == 'snod':
           expected_units = 'm'
           assert expected_units == item.units 
        elif item.variable == 'weasd':
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
        if item.variable == 'snod':
           expected_longname = 'surface snow depth'
           assert expected_longname == item.longname 
        elif item.variable == 'weasd':
           expected_longname = 'surface snow water equivalent'
           assert expected_longname == item.longname

def test_snowiceocean_harvester():
    data1 = harvest(VALID_CONFIG_DICT) 
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].filenames==BFG_PATH

def main():
    test_gridcell_area_conservation()
    test_variable_names()
    test_units()
    test_global_mean_values()
    test_gridcell_variance()
    test_gridcell_min_max()
    test_cycletime() 
    test_longname()
    test_snowiceocean_harvester()

if __name__=='__main__':
    main()

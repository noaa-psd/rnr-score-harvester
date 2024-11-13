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

TEST_DATA_FILE_NAMES = ['bfg_1994010100_fhr09_toa_radiative_flux_control.nc',
                        'bfg_1994010106_fhr06_toa_radiative_flux_control.nc',
                        'bfg_1994010106_fhr09_toa_radiative_flux_control.nc',
                        'bfg_1994010112_fhr06_toa_radiative_flux_control.nc',
                        'bfg_1994010112_fhr09_toa_radiative_flux_control.nc',
                        'bfg_1994010118_fhr06_toa_radiative_flux_control.nc',
                        'bfg_1994010118_fhr09_toa_radiative_flux_control.nc',
                        'bfg_1994010200_fhr06_toa_radiative_flux_control.nc']

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
                     'statistic': ['mean', 'minimum', 'maximum', 'variance'],
                     'variable': ['netrf_avetoa']}

"""
  This python script is the test for the Top atmosphere net radiative flux(netrf_avetoa).
  The top of the atmosphere net radiative flux is calculated by the formula:
  netrf_avetoa = weighted mean of dswrf_avetoa - ulwrf_avetoa - uswrf_avetoa
  dswrf_avetoa is top of atmos downward shortwave flux.
  ulwrf_avetoa is top of atmos upward longwave flux.
  uswrf_avetoa is top of atmos upward shortwave flux.
  These required variables are located in the eight bfg foreacast files
        bfg_1994010100_fhr09_toa_radiative_flux_control.nc
        bfg_1994010106_fhr06_toa_radiative_flux_control.nc
        bfg_1994010106_fhr09_toa_radiative_flux_control.nc
        bfg_1994010112_fhr06_toa_radiative_flux_control.nc
        bfg_1994010112_fhr09_toa_radiative_flux_control.nc
        bfg_1994010118_fhr06_toa_radiative_flux_control.nc
        bfg_1994010118_fhr09_toa_radiative_flux_control.nc
        bfg_1994010200_fhr06_toa_radiative_flux_control.nc
  The statistics asked for in the VALID_CONFIG_DICT are calculated in
  the harvester daily_bfg.py. 
  These required variables is a global python list: 
  required_vars = [dswrf_avetoa,ulwrf_avetoa,uswrf_avetoa]
"""  
  
required_vars  = ['dswrf_avetoa','ulwrf_avetoa','uswrf_avetoa']

def test_gridcell_area_conservation(tolerance=0.001):

    gridcell_area_data = Dataset(GRIDCELL_AREA_DATA_PATH)
    assert gridcell_area_data['area'].units == 'steradian'
    sum_gridcell_area = np.sum(gridcell_area_data.variables['area'])
    assert sum_gridcell_area < (1 + tolerance) * 4 * np.pi
    assert sum_gridcell_area > (1 - tolerance) * 4 * np.pi
    gridcell_area_data.close()

def test_harvester_get_files():
    data1 = harvest(VALID_CONFIG_DICT)
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].filenames==BFG_PATH

def test_variable_names():
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].variable == 'netrf_avetoa'

def test_units():
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].units == 'W/m**2'

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
    assert data1[0].longname == "Top of atmosphere net radiative flux"

def test_global_mean_values(tolerance=0.001):
    """The value of 10.022175263719816 is the mean value of the global means
    calculated from required variables which are in the eight
    forecast files listed above.
    When averaged together, these files represent a 24 hour mean. The
    average value hard-coded in this test was calculated from
    these forecast files using a separate python code.
    """
    data1 = harvest(VALID_CONFIG_DICT)
    global_mean = 10.022175263719816
    assert data1[0].value <= (1 + tolerance) * global_mean
    assert data1[0].value >= (1 - tolerance) * global_mean

'''temporarily commenting out the following 3 failing unit tests (https://github.com/NOAA-PSL/score-hv/issues/56)
     
def test_global_mean_values2(tolerance=0.001):
    """This function tests the weighted means of each of the required variables.
       The required variables[dswrf_avetoa, ulwrf_avetoa and uswrf_avetoa].
       The weighted means are calculated in a separate program from the
       files in the above bfg files and then hard coded in this function for a 
       test of what is returned from the harvester.
    """
    data1 = harvest(VALID_CONFIG_DICT)
    
    weighted_means = [351.93690539738895, 242.84720151427342, 99.06752861939572]
    weighted_means_array   = np.array(weighted_means)
    num_vars = len(required_vars)
    for i, harvested_tuple in enumerate(data1):
        if harvested_tuple.statistic == 'mean':
           for ivar in range(num_vars):
               var_weight_mean = np.float32(weighted_means_array[ivar])
               assert var_weight_mean <= (1 + tolerance) * harvested_tuple.value[ivar+1] 
               assert var_weight_mean >= (1 - tolerance) * harvested_tuple.value[ivar+1]

def test_gridcell_min_max(tolerance=0.001):
    """
      This function tests the minimum and maximum value 
      of each of the required variables. 
      required variables[dswrf_avetoa,ulwrf_avetoa and uswrf_avetoa].
      The minimum and maximum values are calculated in a 
      separate program from the bfg files above and then  
      hard coded in this function for a 
      test of what is returned from the harvester.
    """

    data1 = harvest(VALID_CONFIG_DICT)
    
    min_values = [0.0, 78.584885, 0.0]
    max_values = [550.00757, 343.95752, 373.3152]
    min_array  = np.array(min_values)
    max_array  = np.array(max_values)

    num_vars   = len(required_vars)
    for i, harvested_tuple in enumerate(data1):
        if harvested_tuple.statistic == 'maximum':
            for ivar in range(num_vars):
                assert max_array[ivar] <= (1 + tolerance) * harvested_tuple.value[ivar]
                assert max_array[ivar] >= (1 - tolerance) * harvested_tuple.value[ivar]
        elif harvested_tuple.statistic == 'minimum':
            for ivar in range(num_vars): 
                assert min_array[ivar] <= (1 + tolerance) * harvested_tuple.value[ivar]
                assert min_array[ivar] >= (1 - tolerance) * harvested_tuple.value[ivar]

def test_gridcell_variance(tolerance=0.001):
    """
      This function tests the variance's 
      of each of the required variables. 
      required variables[dswrf_avetoa, ulwrf_avetoa and uswrf_avetoa].
      The hard coded values are calculated in a 
      separate program from the bfg files above. 
      """
    data1 = harvest(VALID_CONFIG_DICT)
    variance_values = [28112.799, 1704.7006, 5749.81  ]
    variance_array  = np.array(variance_values)

    num_vars = len(required_vars)
    for i, harvested_tuple in enumerate(data1):
        if harvested_tuple.statistic == 'variance':
            for ivar in range(num_vars):
                assert variance_array[ivar] <= (1 + tolerance) * harvested_tuple.value[ivar]
                assert variance_array[ivar] >= (1 - tolerance) * harvested_tuple.value[ivar]
'''

def main():
    test_gridcell_area_conservation()
    test_harvester_get_files()
    test_variable_names()
    test_units()
    test_cycletime()
    test_longname()
    test_global_mean_values()
    #test_global_mean_values2()
    #test_gridcell_min_max()
    #test_gridcell_variance()

if __name__=='__main__':
    main()

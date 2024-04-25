#!/usr/bin/env python

import os
import sys
import xarray as xr
from pathlib import Path 

import numpy as np
from netCDF4 import Dataset
from datetime import datetime
import pytest
import yaml
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

def test_global_mean_values2(tolerance=0.001):
    """
       The weighted_means = [351.93690539738895, 242.84720151427342, 99.06752861939572]
       were calculated for each of the required variables in a separate python script using the
       bfg files listed above. 
       This function calculates the weighted mean for each of the required variables
       from the bfg files above.  The calculated weighted mean is then
       compared to the hard coded value of the weighted mean for that variable.
    """
    weighted_means = [351.93690539738895, 242.84720151427342, 99.06752861939572]
    weighted_means_array   = np.array(weighted_means)

    gridcell_area_data = Dataset(GRIDCELL_AREA_DATA_PATH)
    norm_weights = gridcell_area_data.variables['area'][:] / np.sum(
                                        gridcell_area_data.variables['area'][:])
    num_vars = len(required_vars)
    for ivar in range(num_vars): 
        summation = 0.0
        var_name = required_vars[ivar]
        for file_count, data_file in enumerate(BFG_PATH):
               test_rootgrp = Dataset(data_file)
               with Dataset(data_file, 'r') as data:
                    var_data = test_rootgrp.variables[var_name]
                    summation += var_data[0]
        value = summation/(file_count + 1) 
        ivar_weighted_mean = np.ma.sum(norm_weights * value) 
        assert ivar_weighted_mean <= (1 + tolerance) * weighted_means[ivar] 
        assert ivar_weighted_mean >= (1 - tolerance) * weighted_means[ivar]
    gridcell_area_data.close()

def test_global_min_max(tolerance=0.001):
    """
      The min_values = [0.0, 78.584885, 0.0] and 
      max_values = [550.00757, 343.95752, 373.3152] were calculated for 
      each of the required variables in a separate python script using the
      bfg files listed above. 
      This function gets the minimun and maximum values of the required
      variables from the temporal means that are calculated from the 
      bfg files above. Then the minimum and maximum values are compoared
      to the hard coded min_values and max_values.
      """ 
    
    min_values = [0.0, 78.584885, 0.0]
    max_values = [550.00757, 343.95752, 373.3152]
    
    num_vars = len(required_vars)
    for ivar in range(num_vars):
        summation = 0.0
        var_name = required_vars[ivar]
        for file_count, data_file in enumerate(BFG_PATH):
            test_rootgrp = Dataset(data_file)
            with Dataset(data_file, 'r') as data:
                 var_data = test_rootgrp.variables[var_name]
                 summation += var_data[0]
        value = summation/(file_count + 1)
        themin = np.ma.min(value)
        themax = np.ma.max(value)
        assert min_values[ivar] <= (1 + tolerance) * themin
        assert min_values[ivar] >= (1 - tolerance) * themin
        assert max_values[ivar] <= (1 + tolerance) * themax
        assert max_values[ivar] >= (1 - tolerance) * themax

def test_global_variance(tolerance=0.001):
    """
      The variance values [28112.799, 1704.7006, 5749.81  ] were calculated for 
      each of the required variables in a separate python script using the
      bfg files listed above. 
      This function calculates the variances for each of the required variables
      using temporal means and weighted means calculated in this function 
      and the normalized area weights from the gridcell_area_data file.  
      It then compares the calulated variance with
      the hard coded variance.  The variance is calculated using the formula:
      variance = sum_R{ w_i * (x_i - xbar)^2 },
      where sum_R represents the summation for each value x_i over the region of
      interest R with normalized gridcell area weights w_i and weighted mean xbar
      """
    variance_values = [28112.799, 1704.7006, 5749.81  ]

    gridcell_area_data = Dataset(GRIDCELL_AREA_DATA_PATH)
    norm_weights = gridcell_area_data.variables['area'][:] / np.sum(
                                        gridcell_area_data.variables['area'][:])
    num_vars = len(required_vars)
    for ivar in range(num_vars):
        summation = 0.0
        var_name = required_vars[ivar]
        for file_count, data_file in enumerate(BFG_PATH):
               test_rootgrp = Dataset(data_file)
               with Dataset(data_file, 'r') as data:
                    var_data = test_rootgrp.variables[var_name]
                    summation += var_data[0]
        value = summation/(file_count + 1)  
        weighted_mean = np.ma.sum(norm_weights * value)                           
        variance = -weighted_mean**2 + np.ma.sum( value**2 * norm_weights)
        assert variance_values[ivar] <= (1 + tolerance) * variance 
        assert variance_values[ivar] >= (1 - tolerance) * variance
    gridcell_area_data.close()     

def main():
    temporal_means = []
    test_gridcell_area_conservation()
    test_harvester_get_files()
    test_variable_names()
    test_units()
    test_cycletime()
    test_longname()
    test_global_mean_values()
    test_global_mean_values2()
    test_global_min_max()
    test_global_variance()

if __name__=='__main__':
    main()

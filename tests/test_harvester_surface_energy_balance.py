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

TEST_DATA_FILE_NAMES = ['bfg_1994010100_fhr09_fluxes_control.nc',
                        'bfg_1994010106_fhr06_fluxes_control.nc',
                        'bfg_1994010106_fhr09_fluxes_control.nc',
                        'bfg_1994010112_fhr06_fluxes_control.nc',
                        'bfg_1994010112_fhr09_fluxes_control.nc',
                        'bfg_1994010118_fhr06_fluxes_control.nc',
                        'bfg_1994010118_fhr09_fluxes_control.nc',
                        'bfg_1994010200_fhr06_fluxes_control.nc']

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
                     'variable': ['netef_ave']}

"""
  This python script is the test for the surface energy balance(netef_ave).
  The netR  is calculated by the formula:
  netR = dswrf_ave + dlwrf_ave - ulwrf_ave - uswrf_ave - shtfl_ave - lhtfl_ave
  Where:
       dswrf_ave : averaged surface downward shortwave flux
       dlwrf_ave : surface downward longwave flux
       ulwrf_ave : surface upward longwave flux
       uswrf_ave : averaged surface upward shortwave flux
       shtfl_ave : surface sensible heat flux
       lhtfl_ave : surface latent heat flux

  These required variables are located in the eight bfg foreacast files
        bfg_1994010100_fhr09_fluxes_control.nc
        bfg_1994010106_fhr06_fluxes_control.nc
        bfg_1994010106_fhr09_fluxes_control.nc
        bfg_1994010112_fhr06_fluxes_control.nc
        bfg_1994010112_fhr09_fluxes_control.nc
        bfg_1994010118_fhr06_fluxes_control.nc
        bfg_1994010118_fhr09_fluxes_control.nc
        bfg_1994010200_fhr06_fluxes_control.nc
  The statistics asked for in the VALID_CONFIG_DICT are calculated in
  the harvester daily_bfg.py. 
  These required variables is a global python list: 
  required_vars  = ['dswrf_ave','dlwrf_ave','ulwrf_ave','uswrf_ave','shtfl_ave','lhtfl_ave']  
"""  
  
required_vars  = ['dswrf_ave','dlwrf_ave','ulwrf_ave','uswrf_ave','shtfl_ave','lhtfl_ave'] 
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
    assert data1[0].variable == 'netef_ave'

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

def test_global_mean_values(tolerance=0.001):
    """The value of 14.551596002744859 the weighted mean value 
    calculated from required variables which are in the eight
    forecast files listed above.
    When averaged together, these files represent a 24 hour mean. The
    average value hard-coded in this test was calculated from
    these forecast files using a separate python code.
    The weighted mean returned from the daily_bfg.py was calculated as
    follows:
           weighted_averages[0] = weighted averages of dswrf_ave
           weighted_averages[1] = weighted averages of dlwrf_ave
           weighted_averages[2] = weighted_averages of ulwrf_ave
           weighted_averages[3] = weighted averages of uswrf_ave
           weighted_averages[4] = weighted averages of shtfl_ave
           weighted_averages[5] = weighted_averages of lhtfl_ave
           netR = weighted_averages[0] + weighted_averages[1] - weighted_averages[2] - 
                  weighted_averages[3] - weighted_averages[4] - weighted_averages[5] 
    """
    data1 = harvest(VALID_CONFIG_DICT)
    global_mean = 14.551596002744859 
    assert data1[0].value[0] <= (1 + tolerance) * global_mean
    assert data1[0].value[0] >= (1 - tolerance) * global_mean

def test_global_mean_values2(tolerance=0.001):
    """This function tests the weighted means of each of the required variables.
       The required variables ['dswrf_ave','dlwrf_ave','ulwrf_ave','uswrf_ave','shtfl_ave','lhtfl_ave'] .
       The weighted means are calculated in a separate program from the
       files in the above bfg files and then hard coded in this function for a 
       test of what is returned from the harvester.
    """
    data1 = harvest(VALID_CONFIG_DICT)
    weighted_means = [202.72681686615584, 328.63908911200036, 388.22007119987387, 27.270714216491278, 16.05044605736687, 85.27307850167932]
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

def test_gridcell_min_max(tolerance=0.001):
    """
      This function tests the minimum and maximum value 
      of each of the required variables. 
      required variables['dswrf_ave','dlwrf_ave','ulwrf_ave','uswrf_ave','shtfl_ave','lhtfl_ave'].
      The minimum and maximum values are calculated in a 
      separate program from the bfg files above and then  
      hard coded in this function for a 
      test of what is returned from the harvester.
      NOTE:  I had to take the absolute values of the negative
             values in order for the assert test to pass.
      """

    data1 = harvest(VALID_CONFIG_DICT)
    min_values = [0.0, 90.99187, 130.81378, 0.0, -119.094, -45.172398]
    max_values = [475.24536, 452.06378, 589.4178, 359.4239, 695.51825, 726.7792]

    num_vars   = len(required_vars)
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
        themin = abs(themin)
        min_values[ivar] = abs(min_values[ivar])
        assert min_values[ivar] <= (1 + tolerance) * themin
        assert min_values[ivar] >= (1 - tolerance) * themin
        assert max_values[ivar] <= (1 + tolerance) * themax
        assert max_values[ivar] >= (1 - tolerance) * themax

    """
      Test what was returned from the harvester.
      """
    offline_min = -1081.2091
    offline_min = abs(offline_min)
    harvester_min = abs(data1[1].value[0])
    assert offline_min <= (1 + tolerance) * harvester_min
    assert offline_min >= (1 - tolerance) * harvester_min
    
    offline_max = 370.3053
    harvester_max = abs(data1[2].value[0])
    assert offline_max <= (1 + tolerance) * harvester_max
    assert offline_max >= (1 - tolerance) * harvester_max
    
def test_gridcell_variance(tolerance=0.001):
    """
      This function calculates the variance's 
      of each of the required variables and compares them the hardcoded values
      that were calculated in a separate program from the bfg files above. 
      required variables ['dswrf_ave','dlwrf_ave','ulwrf_ave','uswrf_ave','shtfl_ave','lhtfl_ave'].
      It also tests the variance value returned by the harvester.
      """
    data1 = harvest(VALID_CONFIG_DICT)
    variance_values = [14481.714459614741, 6644.116039709712, 6807.88933309709, 2466.0538832157135, 1153.4818646788042, 6513.869633373836] 
    variance_array  = np.array(variance_values)

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

    """
      Now test the value of the variance returned by the harvester.
      """
    offline_variance = 17248.28581915531
    harvester_variance = data1[3].value[0]
    assert offline_variance <= (1 + tolerance) * harvester_variance
    assert offline_variance >= (1 - tolerance) * harvester_variance

def main():
    test_gridcell_area_conservation()
    test_harvester_get_files()
    test_variable_names()
    test_units()
    test_cycletime()
    test_longname()
    test_global_mean_values()
    test_global_mean_values2()
    test_gridcell_min_max()
    test_gridcell_variance()

if __name__=='__main__':
    main()

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

TEST_DATA_FILE_NAMES = ['bfg_1994010100_fhr09_surf_energy_balance_control.nc',
                        'bfg_1994010106_fhr06_surf_energy_balance_control.nc',
                        'bfg_1994010106_fhr09_surf_energy_balance_control.nc',
                        'bfg_1994010112_fhr06_surf_energy_balance_control.nc',
                        'bfg_1994010112_fhr09_surf_energy_balance_control.nc',
                        'bfg_1994010118_fhr06_surf_energy_balance_control.nc',
                        'bfg_1994010118_fhr09_surf_energy_balance_control.nc',
                        'bfg_1994010200_fhr06_surf_energy_balance_control.nc']

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
                     'variable': ['netR']}

"""
  This python script is the test for the surface energy balance(netR).
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
        bfg_1994010100_fhr09_surf_energy_balance_control.nc
        bfg_1994010106_fhr06_surf_energy_balance_control.nc
        bfg_1994010106_fhr09_surf_energy_balance_control.nc
        bfg_1994010112_fhr06_surf_energy_balance_control.nc
        bfg_1994010112_fhr09_surf_energy_balance_control.nc
        bfg_1994010118_fhr06_surf_energy_balance_control.nc
        bfg_1994010118_fhr09_surf_energy_balance_control.nc
        bfg_1994010200_fhr06_surf_energy_balance_control.nc
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
    assert data1[0].variable == 'netR'

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
    min_array  = np.array(min_values)
    max_array  = np.array(max_values)

    num_vars   = len(required_vars)
    for i, harvested_tuple in enumerate(data1):
        if harvested_tuple.statistic == 'maximum':
            for ivar in range(num_vars):
                cal_max     = abs(min_array[ivar])
                harvest_max = abs(harvested_tuple.value[ivar])
                assert cal_max <= (1 + tolerance) * harvest_max
                assert harvest_max >= (1 - tolerance) * harvest_max
        elif harvested_tuple.statistic == 'minimum':
            for ivar in range(num_vars): 
                cal_min     = abs(min_array[ivar])
                harvest_min = abs(harvested_tuple.value[ivar])
                assert cal_min <= (1 + tolerance) * harvest_min
                assert cal_min >= (1 - tolerance) * harvest_min

def test_gridcell_variance(tolerance=0.001):
    """
      This function tests the variance's 
      of each of the required variables. 
      required variables ['dswrf_ave','dlwrf_ave','ulwrf_ave','uswrf_ave','shtfl_ave','lhtfl_ave'].
      The hard coded values are calculated in a 
      separate program from the bfg files above. 
      """
    data1 = harvest(VALID_CONFIG_DICT)
    variance_values = [14481.714459614741, 6644.116039709712, 6807.88933309709, 2466.0538832157135, 1153.4818646788042, 6513.869633373836] 
    variance_array  = np.array(variance_values)

    num_vars = len(required_vars)
    for i, harvested_tuple in enumerate(data1):
        if harvested_tuple.statistic == 'variance':
            for ivar in range(num_vars):
                assert variance_array[ivar] <= (1 + tolerance) * harvested_tuple.value[ivar]
                assert variance_array[ivar] >= (1 - tolerance) * harvested_tuple.value[ivar]


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

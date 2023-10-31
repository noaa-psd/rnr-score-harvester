import numpy as np
import os,sys
from datetime import datetime
from pathlib import Path 
import pytest
import yaml
import glob
import xarray as xr
from netCDF4 import Dataset

from score_hv import hv_registry
from score_hv.harvester_base import harvest
from score_hv.yaml_utils import YamlLoader
from score_hv.harvesters.innov_netcdf import Region, InnovStatsCfg

#TEST_DATA_FILE_NAME = 'bfg_19940101_mean_ulwrf_avetoa_control.nc'
TEST_DATA_FILE_NAMES = ['bfg_1994010100_fhr09_ulwrf_avetoa_control.nc',
                        'bfg_1994010106_fhr06_ulwrf_avetoa_control.nc',
                        'bfg_1994010106_fhr09_ulwrf_avetoa_control.nc',
                        'bfg_1994010112_fhr06_ulwrf_avetoa_control.nc',
                        'bfg_1994010112_fhr09_ulwrf_avetoa_control.nc',
                        'bfg_1994010118_fhr06_ulwrf_avetoa_control.nc',
                        'bfg_1994010118_fhr09_ulwrf_avetoa_control.nc',
                        'bfg_1994010200_fhr06_ulwrf_avetoa_control.nc']
DATA_DIR           = 'data'
CONFIGS_DIR        = 'configs'
PYTEST_CALLING_DIR = Path(__file__).parent.resolve()
TEST_DATA_PATH     = os.path.join(PYTEST_CALLING_DIR, DATA_DIR)
BFG_PATH           = [os.path.join(TEST_DATA_PATH, file_name) for file_name in TEST_DATA_FILE_NAMES] 

VALID_CONFIG_DICT = {
    'harvester_name': hv_registry.GLOBAL_BUCKET_ULWRF_AVE,
    'filenames' : BFG_PATH,
    'statistic': ['var_mean','global_mean'],
    'variable': ['ulwrf_avetoa']
 }

def test_global_mean():
    """ The harvester returns a numpy 32 bit floating point number.
        The test must cast the global mean value hard coded here to a 
        numpy.float32. Otherwise the assert function fails.
    """
    data1               = harvest(VALID_CONFIG_DICT)
    for i, harvested_tuple in enumerate(data1):
        if data1[i].statistic == 'global_mean':
           global_mean         = np.float32(228.17545)
           assert data1[i].value == global_mean
    
def test_var_means():
       """ This function compares the values of the ulwrf_avetoa 
           (top of atmos upward longwave flux)  at each date and time from the
           the harvester global_bucket_ulwrf_ave.py, for the statistic var_mean.
           The ulwrf_time_means list contains the values for each of the dates
           and times that are in the bfg files that are being tested.
           The ulwrf_time_means were calculated in a separate program and are hard
           coded here for testing of the harvester values.  The harvester returns
           a numpy 32 bit floating point number. Each of the ulwrf_time_means list values
           are cast to a np.float32 value so the asser function will work."""
       data1       = harvest(VALID_CONFIG_DICT)
       ulwrf_time_means = [227.36816,228.61551,228.72586,229.17624,228.29858,228.37396,227.44615,227.39911]
       for i, harvested_tuple in enumerate(data1):
           if data1[i].statistic == 'var_mean':
              assert data1[i].value == np.float32(ulwrf_time_means[i])
              
def test_units():
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].units == "W/m**2"

def test_ulwrf_harvester_get_files():
    data1 = harvest(VALID_CONFIG_DICT)  
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].variable=='ulwrf_avetoa'
    assert data1[0].filenames==BFG_PATH

def test_mediantime():
    """ The hard coded datetimestr 1994-01-01 13:30:00
        is the median time of the filenames defined above in the
        BFG_PATH.  We have to convert this into a datetime object in order
        to compare this string to what is returned by global_bucket_precip_ave.py
    """
    data1       = harvest(VALID_CONFIG_DICT)
    datetimestr = datetime.strptime("1994-01-01 12:00:00", "%Y-%m-%d %H:%M:%S")
    assert data1[0].mediantime == datetimestr

def test_longname():
    data1       = harvest(VALID_CONFIG_DICT)
    var_longname = "top of atmos upward longwave flux"
    assert data1[0].longname == var_longname

def main():
    test_ulwrf_harvester_get_files()
    test_global_mean()
    test_var_means() 
    test_units()
    test_mediantime()
    test_longname()
    

if __name__=='__main__':
    main()

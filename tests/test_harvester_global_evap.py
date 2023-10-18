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

#TEST_DATA_FILE_NAME = 'bfg_19940101_mean_lhtfl_control.nc'
TEST_DATA_FILE_NAMES = ['bfg_1994010100_fhr09_lhtfl_control.nc',
                        'bfg_1994010106_fhr06_lhtfl_control.nc',
                        'bfg_1994010106_fhr09_lhtfl_control.nc',
                        'bfg_1994010112_fhr06_lhtfl_control.nc',
                        'bfg_1994010112_fhr09_lhtfl_control.nc',
                        'bfg_1994010118_fhr06_lhtfl_control.nc',
                        'bfg_1994010118_fhr09_lhtfl_control.nc',
                        'bfg_1994010200_fhr06_lhtfl_control.nc']
DATA_DIR           = 'data'
CONFIGS_DIR        = 'configs'
PYTEST_CALLING_DIR = Path(__file__).parent.resolve()
TEST_DATA_PATH     = os.path.join(PYTEST_CALLING_DIR, DATA_DIR)
BFG_PATH           = [os.path.join(TEST_DATA_PATH, file_name) for file_name in TEST_DATA_FILE_NAMES] 

VALID_CONFIG_DICT = {
    'harvester_name': hv_registry.GLOBAL_BUCKET_EVAP_AVE,
    'filenames' : BFG_PATH,
    'statistic': ['var_mean','global_mean'],
    'variable': ['lhtfl_ave']
 }


def test_variable_name(data1):
    assert data1[0].variable=='lhtfl_ave'

def test_global_mean(data1):
    """ The harvester returns a numpy 32 bit floating point number.
        The test must cast the global mean value hard coded here to a 
        numpy.float32. Otherwise the assert function fails.
    """
    for i, harvested_tuple in enumerate(data1):
        if data1[i].statistic == 'global_mean':
           global_mean         = np.float32(64.83899)
           assert data1[i].value == global_mean
    
def test_var_means(data1):
       """ This function compares the values of the precip at each date and time from the
           the harvester global_bucket_evap_ave.py, for the statistic var_mean.
           The precip_time_means list contains the values for each of the dates
           and times that are in the bfg files that are being tested.
           The precip_time_means were calculated in a separate program and are hard
           coded here for testing of the harvester values.  The harvester returns
           a numpy 32 bit floating point number. Each of the precip_time_means list values
           are cast to a np.float32 value so the asser function will work."""
       precip_time_means = [61.949924,62.337864,65.02045,66.1606,69.00131,67.125824,65.39551,61.72039]
       for i, harvested_tuple in enumerate(data1):
           if data1[i].statistic == 'var_mean':
              assert data1[i].value == np.float32(precip_time_means[i])


def test_units(data1):
    assert data1[0].units == "w/m**2"

def test_median_cftime(data1):
    """ The hard coded datetimestr 1994-01-01 13:30:00
        is the median midpoint time of the filenames defined above in the
        BFG_PATH.  We have to convert this into a datetime object in order
        to compare this string to what is returned by global_bucket_precip_ave.py
    """
    data1       = harvest(VALID_CONFIG_DICT)
    datetimestr = datetime.strptime("1994-01-01 12:00:00", "%Y-%m-%d %H:%M:%S")
    assert data1[0].mediantime == datetimestr

def test_longname(data1):
    var_longname = "surface latent heat flux"
    assert data1[0].longname == var_longname

def test_evaporation_harvester():
    data1 = harvest(VALID_CONFIG_DICT)  
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].filenames==BFG_PATH
    test_variable_name(data1)
    test_global_mean(data1)
    test_var_means(data1)
    test_units(data1)
    test_median_cftime(data1)
    test_longname(data1)

def main():
    test_evaporation_harvester()

if __name__=='__main__':
    main()

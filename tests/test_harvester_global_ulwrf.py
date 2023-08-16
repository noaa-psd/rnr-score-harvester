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
    'statistic': ['mean'],
    'variable': ['ulwrf_avetoa']
 }

def test_global_mean():
    """ The harvester returns a numpy 32 bit floating point number.
        The test must cast the global mean value hard coded here to a 
        numpy.float32. Otherwise the assert function fails.
    """
    print("in test get mean")
    data1               = harvest(VALID_CONFIG_DICT)
    global_mean         = np.float32(228.17545)
    assert data1[0].value == global_mean
    print("leaving test get mean")
    
def test_global_mean2():
    data1 = harvest(VALID_CONFIG_DICT)
    
    for i, harvested_tuple in enumerate(data1):
        global_means = list()
        for j, filename in enumerate(harvested_tuple.filenames):
            rootgrp = Dataset(filename)
            global_means.append(np.ma.mean(rootgrp.variables['ulwrf_avetoa'][:]))
        
        assert np.mean(global_means) == harvested_tuple.value

def test_units():
    print("in test units")
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].units == "W/m**2"
    print("leaving test units")

def test_ulwrf_harvester_get_files():
    print('in test ulwrf,ulwrf_avetoa, harvester get files')
    print(BFG_PATH)

    data1 = harvest(VALID_CONFIG_DICT)  
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].variable=='ulwrf_avetoa'
    assert data1[0].filenames==BFG_PATH
    print("Leaving the test of upper long wave flux harvester")

def main():
    test_ulwrf_harvester_get_files()
    test_global_mean()
    test_global_mean2()
    test_units()

if __name__=='__main__':
    main()

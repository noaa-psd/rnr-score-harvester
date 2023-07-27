import numpy as np
import os,sys
from datetime import datetime
from pathlib import Path 
import pytest
import yaml
import glob
import xarray as xr
import netCDF4 as nc


from score_hv import hv_registry
from score_hv.harvester_base import harvest
from score_hv.yaml_utils import YamlLoader
from score_hv.harvesters.innov_netcdf import Region, InnovStatsCfg

#TEST_DATA_FILE_NAME = 'bfg_19940101_mean_prateb_control.nc'
TEST_DATA_FILE_NAMES = [
    'bfg_1994010100_fhr09_prateb_control.nc',
    'bfg_1994010106_fhr06_prateb_control.nc',
    'bfg_1994010106_fhr09_prateb_control.nc',
    'bfg_1994010112_fhr06_prateb_control.nc',
    'bfg_1994010112_fhr09_prateb_control.nc',
    'bfg_1994010118_fhr06_prateb_control.nc',
    'bfg_1994010118_fhr09_prateb_control.nc',
    'bfg_1994010200_fhr06_prateb_control.nc'
]
DATA_DIR           = 'data'
CONFIGS_DIR        = 'configs'
PYTEST_CALLING_DIR = Path(__file__).parent.resolve()
TEST_DATA_PATH     = os.path.join(PYTEST_CALLING_DIR, DATA_DIR)
BFG_PATH           = [os.path.join(TEST_DATA_PATH, file_name) for file_name in TEST_DATA_FILE_NAMES] 



VALID_CONFIG_DICT = {
    'harvester_name': hv_registry.GLOBAL_BUCKET_PRECIP_AVE,
    'filenames' : BFG_PATH,
    'statistic': ['mean'],
    'variable': ['prateb_ave']
 }

def test_global_mean():
    print("in test get mean")
    data1               = harvest(VALID_CONFIG_DICT)
    global_mean         = 2.4695819e-05
    global_mean_float32 = np.float32(global_mean)
    #numpy will return a 32 bit floating point number from the harvester.
    #So we need to cast the global mean value hard coded in here to a 
    #float 32.  Otherwise the assert function fails.
    assert data1[0].value == global_mean_float32
    print("leaving test get mean") 

def test_units():
    print("in test units")
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].units == "kg/m**2/s"
    print("leaving test units")


def test_precip_harvester_get_files():
    print('in test precip harvester get files')
    print(BFG_PATH)

    data1 = harvest(VALID_CONFIG_DICT)  
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].variable=='prateb_ave'
    assert data1[0].filenames==BFG_PATH

    #assert data1[0].units
    print('leaving test precip harvester get files')



def main():

    test_precip_harvester_get_files()
    test_global_mean()
    test_units()      
if __name__=='__main__':
    main()
     





    
         


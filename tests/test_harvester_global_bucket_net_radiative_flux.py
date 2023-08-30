import os,sys
import xarray as xr
import numpy as np
import glob
import netCDF4 as nc
from netCDF4 import Dataset

TEST_DATA_FILE_NAMES = ['bfg_1994010100_fhr09_toa_radative_flux_control.nc',
                        'bfg_1994010106_fhr06_toa_radative_flux_control.nc',
                        'bfg_1994010106_fhr09_toa_radative_flux_control.nc',
                        'bfg_1994010112_fhr06_toa_radative_flux_control.nc',
                        'bfg_1994010112_fhr09_toa_radative_flux_control.nc',
                        'bfg_1994010118_fhr06_toa_radative_flux_control.nc',
                        'bfg_1994010118_fhr09_toa_radative_flux_control.nc',
                        'bfg_1994010200_fhr06_toa_radative_flux_control.nc']
DATA_DIR           = 'data'
CONFIGS_DIR        = 'configs'
PYTEST_CALLING_DIR = Path(__file__).parent.resolve()
TEST_DATA_PATH     = os.path.join(PYTEST_CALLING_DIR, DATA_DIR)
BFG_PATH           = [os.path.join(TEST_DATA_PATH, file_name) for file_name in TEST_DATA_FILE_NAMES]

VALID_CONFIG_DICT = {
    'harvester_name': hv_registry.GLOBAL_BUCKET_EVAP_AVE,
    'filenames' : BFG_PATH,
    'statistic': ['mean'],
    'variables': ['dswrf_avetoa','ulwrf_avetoa','uswrf_avetoa']
 }

def test_global_mean():
    print("leaving test get mean")

def test_global_mean2():
    data1 = harvest(VALID_CONFIG_DICT)

    for i, harvested_tuple in enumerate(data1):
        global_means = list()
        for j, filename in enumerate(harvested_tuple.filenames):
            rootgrp = Dataset(filename)
            global_means.append(np.ma.mean(rootgrp.variables['lhtfl_ave'][:]))

        assert np.mean(global_means) == harvested_tuple.value



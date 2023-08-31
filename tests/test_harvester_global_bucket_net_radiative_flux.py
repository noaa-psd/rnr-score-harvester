import numpy as np
import os,sys
from datetime import datetime
from pathlib import Path 
import pytest
import yaml
import glob
from netCDF4 import Dataset
from score_hv import hv_registry
from score_hv.harvester_base import harvest
from score_hv.yaml_utils import YamlLoader
from score_hv.harvesters.innov_netcdf import Region, InnovStatsCfg

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
    'harvester_name': hv_registry.GLOBAL_BUCKET_NET_RADIATIVE_FLUX,
    'filenames' : BFG_PATH,
    'statistic': ['mean'],
    'variables': ['dswrf_avetoa','ulwrf_avetoa','uswrf_avetoa']
 }

def test_NetRadiativeFlux_harvester_get_files():
    data1 = harvest(VALID_CONFIG_DICT)  
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].filenames==BFG_PATH

def test_NetRadiativeFlux_harvester_variables():
    """ These variables are from the Netcdf bfg files above.
    dswrf_avetoa - top of atmos downward shortwave flux
    ulwrf_avetoa - top of atmos upward longwave flux
    uswrf_avetoa - top of atmos upward shortwave flux 
    """
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].variables == 'dswrf_avetoa'
    assert data1[1].variables == 'ulwrf_avetoa'
    assert data1[2].variables == 'uswrf_avetoa'

def test_NetRadiativeFlux_harvester_units():
    """The units of all the requested variables are 
       the same W/m**2"""
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].units == 'W/m**2'


def main():
    test_NetRadiativeFlux_harvester_get_files()
    test_NetRadiativeFlux_harvester_variables()
    test_NetRadiativeFlux_harvester_units()

if __name__=='__main__':
    main()



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
    'variables': ['dswrf_avetoa','ulwrf_avetoa','uswrf_avetoa','net_radiative_flux'],
    'median_time': ['median_time'],
    'longname': ['longname']
 }

def test_variable_names():
    """ These variables are from the Netcdf bfg files above.
    dswrf_avetoa - top of atmos downward shortwave flux
    ulwrf_avetoa - top of atmos upward longwave flux
    uswrf_avetoa - top of atmos upward shortwave flux 
    """
    data1       = harvest(VALID_CONFIG_DICT)
    assert data1[0].variables == 'dswrf_avetoa'
    assert data1[1].variables == 'ulwrf_avetoa'
    assert data1[2].variables == 'uswrf_avetoa'

def test_units():
    """The units of all the requested variables are
       the same W/m**2"""
    data1       = harvest(VALID_CONFIG_DICT)
    assert data1[0].units == 'W/m**2'

def test_values():
    """Here we test to see if all of the requested variable means
       have valid values. The hard coded values of mean_dswrf, 
       mean_ulwrf, mean_uswrf and mean_net_radiative_flux
       were calculated in a separate python code using the 
       above netcdf files.  The top of the atmosphere net 
       radiative flux is defined as mean_dswrf - mean_ulwrf - mean_uswrf"""
    data1       = harvest(VALID_CONFIG_DICT)
    mean_dswrf = np.float32(326.76144)
    assert data1[0].value == mean_dswrf 
    mean_ulwrf = np.float32(228.17543)
    assert data1[1].value == mean_ulwrf
    mean_uswrf = np.float32(109.79811)
    assert data1[2].value == mean_uswrf
    mean_net_radiative_flux = np.float32(-11.212097)
    assert data1[3].value == mean_net_radiative_flux

def test_mediantime():
    """ The hard coded datetimestr 1994-01-01 13:30:00
        is the median time of the filenames defined above in the
        BFG_PATH.  We have to convert this into a datetime object in order
        to compare this string to what is returned by global_bucket_precip_ave.py
    """
    data1       = harvest(VALID_CONFIG_DICT)
    datetimestr = datetime.strptime("1994-01-01 12:00:00", "%Y-%m-%d %H:%M:%S")
    assert data1[0].median_time == datetimestr

def test_longname():
    data1       = harvest(VALID_CONFIG_DICT)
    var_longname = "TOA net radiative flux"
    assert data1[0].longname == var_longname

def test_NetRadiativeFlux_harvester():
    data1 = harvest(VALID_CONFIG_DICT)  
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].filenames==BFG_PATH
    test_variable_names() 
    test_units()
    test_values()
    test_mediantime()
    test_longname()

def main():
    test_NetRadiativeFlux_harvester()

if __name__=='__main__':
    main()



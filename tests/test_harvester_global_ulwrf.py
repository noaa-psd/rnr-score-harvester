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

TEST_DATA_FILE_NAMES = ['bfg_1994010100_fhr09_toa_radiative_flux_control.nc',
                        'bfg_1994010106_fhr06_toa_radiative_flux_control.nc',
                        'bfg_1994010106_fhr09_toa_radiative_flux_control.nc',
                        'bfg_1994010112_fhr06_toa_radiative_flux_control.nc',
                        'bfg_1994010112_fhr09_toa_radiative_flux_control.nc',
                        'bfg_1994010118_fhr06_toa_radiative_flux_control.nc',
                        'bfg_1994010118_fhr09_toa_radiative_flux_control.nc',
                        'bfg_1994010200_fhr06_toa_radiative_flux_control.nc']

DATA_DIR = os.path.join(Path(__file__).parent.parent.resolve(), 'src', 'score_hv', 'data')
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
                     'statistic': ['mean','variance', 'minimum', 'maximum'],
                     'variable': ['ulwrf_avetoa']}

def test_gridcell_area_conservation(tolerance=0.001):

    gridcell_area_data = Dataset(GRIDCELL_AREA_DATA_PATH)
    
    assert gridcell_area_data['area'].units == 'steradian'
    
    sum_gridcell_area = np.sum(gridcell_area_data.variables['area'])
    
    assert sum_gridcell_area < (1 + tolerance) * 4 * np.pi
    assert sum_gridcell_area > (1 - tolerance) * 4 * np.pi
    
    gridcell_area_data.close()

def test_variable_names():
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].variable == 'ulwrf_avetoa'

def test_global_mean_values_offline(tolerance=0.001):
    """ 
        The value of 242.84720151427342 the mean value of the 
        global meas calculated from these eight forecast files:

        bfg_1994010100_fhr09_toa_radiative_flux_control.nc
        bfg_1994010106_fhr06_toa_radiative_flux_control.nc
        bfg_1994010106_fhr09_toa_radiative_flux_control.nc
        bfg_1994010112_fhr06_toa_radiative_flux_control.nc
        bfg_1994010112_fhr09_toa_radiative_flux_control.nc
        bfg_1994010118_fhr06_toa_radiative_flux_control.nc
        bfg_1994010118_fhr09_toa_radiative_flux_control.nc
        bfg_1994010200_fhr06_toa_radiative_flux_control.nc
        
        When averaged together, these files represent a 24 hour mean. The 
        average value hard-coded in this test was calculated from 
        forecast files using a separate python code.
    """
    data1 = harvest(VALID_CONFIG_DICT)
    global_mean = 242.84720151427342 
    assert data1[0].value <= (1 + tolerance) * global_mean
    assert data1[0].value >= (1 - tolerance) * global_mean
 
def test_global_mean_values_netCDF4(tolerance=0.001):
    """Opens each background Netcdf file using the
    netCDF4 library function Dataset and computes the expected value
    of the provided variable.  In this case toa_radiative_flux.
    """
    data1 = harvest(VALID_CONFIG_DICT)
    gridcell_area_data = Dataset(GRIDCELL_AREA_DATA_PATH)
    norm_weights = gridcell_area_data.variables['area'][:] / np.sum(
                                        gridcell_area_data.variables['area'][:])
    
    summation = np.ma.zeros(gridcell_area_data.variables['area'].shape)
    for file_count, data_file in enumerate(BFG_PATH):
        test_rootgrp = Dataset(data_file)
    
        summation += test_rootgrp.variables[VALID_CONFIG_DICT['variable'][0]][0]
        
        test_rootgrp.close()
        
    temporal_mean = summation / (file_count + 1)
    global_mean = np.ma.sum(norm_weights * temporal_mean)    
    
    for i, harvested_tuple in enumerate(data1):
        if harvested_tuple.statistic == 'mean':
            assert global_mean <= (1 + tolerance) * harvested_tuple.value
            assert global_mean >= (1 - tolerance) * harvested_tuple.value
            
    gridcell_area_data.close()

def test_gridcell_min_max(tolerance=0.001):
    """Opens each background Netcdf file using the
    netCDF4 library function Dataset and computes the maximum
    of the provided variable.  In this case toa_radiative_flux.
    """
    data1 = harvest(VALID_CONFIG_DICT)

    gridcell_area_data = Dataset(GRIDCELL_AREA_DATA_PATH)

    summation = np.ma.zeros(gridcell_area_data.variables['area'].shape)
    for file_count, data_file in enumerate(BFG_PATH):
        test_rootgrp = Dataset(data_file)

        summation += test_rootgrp.variables[VALID_CONFIG_DICT['variable'][0]][0]

        test_rootgrp.close()

    temporal_mean = summation / (file_count + 1)
    minimum = np.ma.min(temporal_mean)
    maximum = np.ma.max(temporal_mean)

    """The following offline min and max were calculated from an external
    python code
    """
    offline_min = 78.584885 
    offline_max = 343.95752
    for i, harvested_tuple in enumerate(data1):
        if harvested_tuple.statistic == 'maximum':
            assert maximum <= (1 + tolerance) * harvested_tuple.value
            assert maximum >= (1 - tolerance) * harvested_tuple.value

            assert offline_max <= (1 + tolerance) * harvested_tuple.value
            assert offline_max >= (1 - tolerance) * harvested_tuple.value


        elif harvested_tuple.statistic == 'minimum':
            assert minimum <= (1 + tolerance) * harvested_tuple.value
            assert minimum >= (1 - tolerance) * harvested_tuple.value

            assert offline_min <= (1 + tolerance) * harvested_tuple.value
            assert offline_min >= (1 - tolerance) * harvested_tuple.value

    gridcell_area_data.close()

def test_gridcell_variance(tolerance=0.001):
    """Opens each background Netcdf file using the
    netCDF4 library function Dataset and computes the variance
    of the provided variable.  In this case toa_radiative_flux.
    """
    data1 = harvest(VALID_CONFIG_DICT)

    gridcell_area_data = Dataset(GRIDCELL_AREA_DATA_PATH)
    norm_weights = gridcell_area_data.variables['area'][:] / np.sum(
                                        gridcell_area_data.variables['area'][:])

    summation = np.ma.zeros(gridcell_area_data.variables['area'].shape)
    for file_count, data_file in enumerate(BFG_PATH):
        test_rootgrp = Dataset(data_file)

        summation += test_rootgrp.variables[VALID_CONFIG_DICT['variable'][0]][0]

        test_rootgrp.close()

    temporal_mean = summation / (file_count + 1)

    global_mean = np.ma.sum(norm_weights * temporal_mean)
    variance = np.ma.sum((temporal_mean - global_mean)**2 * norm_weights)

    for i, harvested_tuple in enumerate(data1):
        if harvested_tuple.statistic == 'variance':
            assert variance <= (1 + tolerance) * harvested_tuple.value
            assert variance >= (1 - tolerance) * harvested_tuple.value

    gridcell_area_data.close()

def test_units():
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].units == "W/m**2"

def test_ulwrf_harvester_get_files():
    data1 = harvest(VALID_CONFIG_DICT)  
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].variable=='ulwrf_avetoa'
    assert data1[0].filenames==BFG_PATH

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
    data1        = harvest(VALID_CONFIG_DICT)
    var_longname = "top of atmos upward longwave flux"
    assert data1[0].longname == var_longname

def main():
    test_gridcell_area_conservation()
    test_ulwrf_harvester_get_files()
    test_variable_names()
    test_units()
    test_global_mean_values_offline()
    test_global_mean_values_netCDF4() 
    test_gridcell_variance()
    test_gridcell_min_max()
    test_cycletime()
    test_longname()
    
if __name__=='__main__':
    main()

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

TEST_DATA_FILE_NAMES = ['bfg_1994010100_fhr09_soil_control.nc',
                        'bfg_1994010106_fhr06_soil_control.nc',
                        'bfg_1994010106_fhr09_soil_control.nc',
                        'bfg_1994010112_fhr06_soil_control.nc',
                        'bfg_1994010112_fhr09_soil_control.nc',
                        'bfg_1994010118_fhr06_soil_control.nc',
                        'bfg_1994010118_fhr09_soil_control.nc',
                        'bfg_1994010200_fhr06_soil_control.nc']

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
                     'statistic': ['mean','variance', 'minimum', 'maximum'],
                     'longname' : ['None','None'],
                     'units': ['K','K'],
                     'variable': ['soilt4','tg3'],
                     'surface_mask': ['land'],
                     'regions' : {'conus': {'latitude_range': (24.0, 49.0), 'longitude_range': (294.0, 235.0)},  
                                'western_hemis': {'latitude_range': (-90, 90), 'longitude_range': (200,360)},
                                'eastern_hemis': {'latitude_range': (-90, 90), 'longitude_range': ( 0, 200) }
                                }
                     }

def test_gridcell_area_conservation(tolerance=0.001):

    gridcell_area_data = Dataset(GRIDCELL_AREA_DATA_PATH)
    
    assert gridcell_area_data['area'].units == 'steradian'
    
    sum_gridcell_area = np.sum(gridcell_area_data.variables['area'])
    
    assert sum_gridcell_area < (1 + tolerance) * 4 * np.pi
    assert sum_gridcell_area > (1 - tolerance) * 4 * np.pi
    
    gridcell_area_data.close()

def test_variable_names():
    expected_variables = ['soilt4', 'tg3'] 
    assert VALID_CONFIG_DICT['variable'] == expected_variables

def test_global_mean_values(tolerance=0.001):
    """ 
        The value of 0.7740827966108876 if the meanvalue of the 
        global meas calculated from these eight forecast files:

        bfg_1994010100_fhr09_soil_control.nc
        bfg_1994010106_fhr06_soil_control.nc
        bfg_1994010106_fhr09_soil_control.nc
        bfg_1994010112_fhr06_soil_control.nc
        bfg_1994010112_fhr09_soil_control.nc
        bfg_1994010118_fhr06_soil_control.nc
        bfg_1994010118_fhr09_soil_control.nc
        bfg_1994010200_fhr06_soil_control.nc
        
        When averaged together, these files represent a 24 hour mean. The 
        average value hard-coded in this test was calculated from 
        forecast files using a separate python code.
    """
    variable_dictionary = {}
    data1 = harvest(VALID_CONFIG_DICT)
    for item in data1:
        variable_name = item.variable
        if variable_name not in variable_dictionary:
           variable_dictionary[variable_name] = []
        variable_dictionary[variable_name].append(item)

    for variable_name, data_list in variable_dictionary.items():
       if variable_name == 'soilt4':
          print("var name is soilt4")
          calculated_means = [185.32222398385198, 68.18650768390042, 99.94846250485294]
       elif variable_name == 'tg3':
          print("var name is tg3") 
          calculated_means = [188.81661183377483, 68.1763767691336, 99.82206535413387]
    
    # Filter out the HarvestedData instances with statistic 'mean'
       mean_data = [item for item in data_list if item.statistic == 'mean']
       if mean_data:
           for item in mean_data:
               for index in range(len(calculated_means)):
                   expected_value = calculated_means[index]
                   actual_value = item.value[index]
                   assert actual_value <= (1 + tolerance) * expected_value 
                   assert actual_value >= (1 - tolerance) * expected_value
   
def test_gridcell_variance(tolerance=0.001):
    """Opens each background Netcdf file using the
    netCDF4 library function Dataset and computes the variance
    of the provided variable.  In this case prateb_ave.
    """
    variable_dictionary = {}
    data1 = harvest(VALID_CONFIG_DICT)
    
    for item in data1:
        variable_name = item.variable
        if variable_name not in variable_dictionary:
           variable_dictionary[variable_name] = []
        variable_dictionary[variable_name].append(item)

    for variable_name, data_list in variable_dictionary.items():
       if variable_name == 'soilt4':
          print("var name is soilt4")
          calculated_variances = [34.16445033781812,314.57351141837273,383.1395968277926]
       elif variable_name == 'tg3':
          print("var name is tg3")
          calculated_variance = [29.086693999806407, 333.14902721533633, 402.0379207002041]

    # Filter out the HarvestedData instances with statistic 'variance'
       variance_data = [item for item in data_list if item.statistic == 'variance']
       if variance_data:
           for item in variance_data:
               for index in range(len(calculated_variances)):
                   expected_value = calculated_variances[index]
                   actual_value = item.value[index]
                   assert actual_value <= (1 + tolerance) * expected_value 
                   assert actual_value >= (1 - tolerance) * expected_value

    sys.exit(0)
def test_gridcell_min_max(tolerance=0.001):
    """Opens each background Netcdf file using the
    netCDF4 library function Dataset and computes the maximum
    of the provided variable.  In this case prateb_ave.
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
    offline_min = 0.0
    offline_max = 1.0 
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

def test_units():
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].units == 'K' 
    assert data1[1].units == 'K'

def test_cycletime():
    """ The hard coded datetimestr 1994-01-01 12:00:00
        is the median midpoint time of the filenames defined above in the 
        BFG_PATH.  We have to convert this into a datetime object in order
        to compare this string to what is returned by 
        global_bucket_precip_ave.py
    """
    data1 = harvest(VALID_CONFIG_DICT)
    expected_datetime = datetime.strptime("1994-01-01 12:00:00",
                                          "%Y-%m-%d %H:%M:%S")
    assert data1[0].mediantime == expected_datetime

def test_longname():
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].longname == 'soil temperature unknown layer 4'
    assert data1[1].longname == 'deep soil temperature'

def test_soil_moisture_level4_harvester():
    data1 = harvest(VALID_CONFIG_DICT) 
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].filenames==BFG_PATH

def main():
    test_gridcell_area_conservation()
    test_soil_moisture_level4_harvester()
    test_variable_names()
    test_units()
    test_global_mean_values()
    test_gridcell_variance()
    test_gridcell_min_max()
    test_cycletime() 
    test_longname()

if __name__=='__main__':
    main()

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
from score_hv.harvesters.ioda_meta_netcdf import IodaMetaCfg

IODA_SST_DATA = 'sst.nesdis.avhrr_l3u_noaa19.20150820.T120000Z.iodav3.nc'
IODA_INSITU_DATA = 'wod.ncei.insitu.20090605.T000000Z.iodav2.nc'
IODA_INSITU_V3_DATA = 'wod.ncei_insitu.20090605.T000000Z.iodav3.nc'
PYTEST_CALLING_DIR = Path(__file__).parent.resolve()
DATA_DIR = 'data'

file_path_ioda_sst_data = os.path.join(
    PYTEST_CALLING_DIR,
    DATA_DIR,
    IODA_SST_DATA
)

file_path_ioda_insitu_data = os.path.join(
    PYTEST_CALLING_DIR,
    DATA_DIR,
    IODA_INSITU_DATA
)

file_path_ioda_insitu_v3_data = os.path.join(
    PYTEST_CALLING_DIR,
    DATA_DIR,
    IODA_INSITU_V3_DATA
)

VALID_CONFIG_SST_DICT = {
    'harvester_name': hv_registry.IODA_META_NETCDF, 
    'filename': file_path_ioda_sst_data
}

VALID_CONFIG_INSITU_DICT = {
    'harvester_name': hv_registry.IODA_META_NETCDF, 
    'filename': file_path_ioda_insitu_data
}

VALID_CONFIG_INSITU_V3_DICT = {
    'harvester_name': hv_registry.IODA_META_NETCDF, 
    'filename': file_path_ioda_insitu_v3_data
}

#Test the ioda SST file is being parsed correctly
#Values being tested against are independently sourced from the file
def test_ioda_sst_meta():
    data = harvest(VALID_CONFIG_SST_DICT)
    sst_data = data[0]
    assert sst_data.filename == IODA_SST_DATA
    assert sst_data.file_date_time == '2015-08-20 12:00:00'
    assert sst_data.num_locs == 1880468
    assert sst_data.num_vars == 2
    assert sst_data.variable_name == 'seaSurfaceSkinTemperature'
    assert sst_data.var_count == 1880468
    assert sst_data.has_PreQC == True
    assert sst_data.has_ObsError == True
    assert sst_data.sensor == "AVHRR_GAC"
    assert sst_data.platform == "NOAA-19"
    assert sst_data.ioda_layout == "ObsGroup"
    assert sst_data.processing_level == "L3U"
    assert sst_data.thinning == 0.95
    assert sst_data.ioda_version == 'v3'

#Test insitu data stored in v2 for salinity and temp in one file, values are independently sourced from the file
def test_ioda_insitu_v2_meta():
    data = harvest(VALID_CONFIG_INSITU_DICT)
    insitu_data_salinity = data[0]
    insitu_data_temperature = data[1]
    #salinity values
    assert insitu_data_salinity.filename == IODA_INSITU_DATA
    assert insitu_data_salinity.file_date_time == '2009-06-05 12:00:00'
    assert insitu_data_salinity.min_date_time == '2009-06-05 00:00:00'
    assert insitu_data_salinity.max_date_time == '2009-06-06 00:00:00'
    assert insitu_data_salinity.num_locs == 22825
    assert insitu_data_salinity.num_vars == 2
    assert insitu_data_salinity.variable_name == 'sea_water_salinity'
    assert insitu_data_salinity.var_count == 18583
    assert insitu_data_salinity.has_PreQC == True
    assert insitu_data_salinity.has_ObsError == True
    assert insitu_data_salinity.sensor == None
    assert insitu_data_salinity.platform == None
    assert insitu_data_salinity.ioda_layout == "ObsGroup"
    assert insitu_data_salinity.processing_level == None
    assert insitu_data_salinity.thinning == None
    assert insitu_data_salinity.ioda_version == 'v2'

    #temperature values
    assert insitu_data_temperature.filename == IODA_INSITU_DATA
    assert insitu_data_temperature.file_date_time == '2009-06-05 12:00:00'
    assert insitu_data_temperature.min_date_time == '2009-06-05 00:00:00'
    assert insitu_data_temperature.max_date_time == '2009-06-06 00:00:00'
    assert insitu_data_temperature.num_locs == 22825
    assert insitu_data_temperature.num_vars == 2
    assert insitu_data_temperature.variable_name == 'sea_water_temperature'
    assert insitu_data_temperature.var_count == 22788
    assert insitu_data_temperature.has_PreQC == True
    assert insitu_data_temperature.has_ObsError == True
    assert insitu_data_temperature.sensor == None
    assert insitu_data_temperature.platform == None
    assert insitu_data_temperature.ioda_layout == "ObsGroup"
    assert insitu_data_temperature.processing_level == None
    assert insitu_data_temperature.thinning == None
    assert insitu_data_temperature.ioda_version == 'v2'

#Test institu data in v3 format with salinity and temp values, values are independently sourced from the file
def test_ioda_insitu_v3_meta():
    data = harvest(VALID_CONFIG_INSITU_V3_DICT)
    insitu_data_salinity = data[0]
    insitu_data_temperature = data[1]
    #salinity values
    assert insitu_data_salinity.filename == IODA_INSITU_V3_DATA
    assert insitu_data_salinity.file_date_time == '2009-06-05 12:00:00'
    assert insitu_data_salinity.min_date_time == '2009-06-05 00:00:00'
    assert insitu_data_salinity.max_date_time == '2009-06-06 00:00:00'
    assert insitu_data_salinity.num_locs == 22825
    assert insitu_data_salinity.num_vars == 2
    assert insitu_data_salinity.variable_name == 'salinity'
    assert insitu_data_salinity.var_count == 18583
    assert insitu_data_salinity.has_PreQC == True
    assert insitu_data_salinity.has_ObsError == True
    assert insitu_data_salinity.sensor == None
    assert insitu_data_salinity.platform == None
    assert insitu_data_salinity.ioda_layout == "ObsGroup"
    assert insitu_data_salinity.processing_level == None
    assert insitu_data_salinity.thinning == None
    assert insitu_data_salinity.ioda_version == 'v3'

    #temperature values
    assert insitu_data_temperature.filename == IODA_INSITU_V3_DATA
    assert insitu_data_temperature.file_date_time == '2009-06-05 12:00:00'
    assert insitu_data_temperature.min_date_time == '2009-06-05 00:00:00'
    assert insitu_data_temperature.max_date_time == '2009-06-06 00:00:00'
    assert insitu_data_temperature.num_locs == 22825
    assert insitu_data_temperature.num_vars == 2
    assert insitu_data_temperature.variable_name == 'waterTemperature'
    assert insitu_data_temperature.var_count == 22788
    assert insitu_data_temperature.has_PreQC == True
    assert insitu_data_temperature.has_ObsError == True
    assert insitu_data_temperature.sensor == None
    assert insitu_data_temperature.platform == None
    assert insitu_data_temperature.ioda_layout == "ObsGroup"
    assert insitu_data_temperature.processing_level == None
    assert insitu_data_temperature.thinning == None
    assert insitu_data_temperature.ioda_version == 'v3'
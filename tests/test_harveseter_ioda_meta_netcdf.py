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
PYTEST_CALLING_DIR = Path(__file__).parent.resolve()
DATA_DIR = 'data'

file_path_ioda_data = os.path.join(
    PYTEST_CALLING_DIR,
    DATA_DIR,
    IODA_SST_DATA
)

VALID_CONFIG_DICT = {
    'harvester_name': hv_registry.IODA_META_NETCDF, 
    'filename': file_path_ioda_data
}

#Test the ioda SST file is being parsed correctly
#Values being tested against are independently sourced from the file
def test_ioda_sst_meta():
    data = harvest(VALID_CONFIG_DICT)
    assert data.filename == IODA_SST_DATA
    assert data.date_time == '2015-08-20 12:00:00'
    assert data.num_locs == 1880468
    assert data.num_vars == 2
    assert np.array_equal(data.variable_names, ['sea_surface_temperature', 'sea_surface_skin_temperature'])
    assert data.has_PreQC == True
    assert data.has_ObsError == True
    assert data.sensor == "AVHRR_GAC"
    assert data.platform == "NOAA-19"
    assert data.ioda_layout == "ObsGroup"
    assert data.processing_level == "L3U"
    assert data.thinning == 0.95
    assert data.ioda_version == 'v3'
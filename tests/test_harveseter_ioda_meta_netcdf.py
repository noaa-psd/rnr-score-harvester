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

def test_ioda_sst_meta():
    data = harvest(VALID_CONFIG_DICT)
    print(data)
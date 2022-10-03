"""
Work by Jessica Knezha

Unit tests for observation information log harvester
"""

import os
import pathlib
import pytest
import yaml

from score_hv import hv_registry
from score_hv.harvester_base import harvest
from score_hv.yaml_utils import YamlLoader


PYTEST_CALLING_DIR = pathlib.Path(__file__).parent.resolve()
LOG_HARVESTER_CONFIG__VALID = 'log_harvester_config__valid.yaml'

DATA_DIR = 'data'
CONFIGS_DIR = 'configs'

file_path_obs_data = os.path.join(
    PYTEST_CALLING_DIR,
    DATA_DIR
)

VALID_CONFIG_DICT = {
    'harvester_name' : hv_registry.OBS_INFO_LOG,
    'filename' : file_path_obs_data,
    'variable' : 'TEMPERATURE'
}

def test_log_harvester_config():
    data1 = harvest(VALID_CONFIG_DICT)
    print(f'harvested {len(data1)} records using config: {VALID_CONFIG_DICT}')
    assert len(data1) > 0

"""
Copyright 2022 NOAA
All rights reserved.

Unit tests for io_utils

"""
import os
import pathlib
import pytest
import yaml
from datetime import datetime

from score_hv import hv_registry
from score_hv.harvester_base import harvest
from score_hv.yaml_utils import YamlLoader
from score_hv.harvesters.innov_netcdf import Region, InnovStatsCfg


PYTEST_CALLING_DIR = pathlib.Path(__file__).parent.resolve()
NETCDF_HARVESTER_CONFIG__VALID = 'netcdf_harvester_config__valid.yaml'

DATA_DIR = 'data'
CONFIGS_DIR = 'configs'

file_path_innov_stats = os.path.join(
    PYTEST_CALLING_DIR,
    DATA_DIR
)

VALID_CONFIG_DICT = {
    'harvester_name': hv_registry.INNOV_NETCDF,
    'file_meta': {
        'filepath_format_str': '%s/' % file_path_innov_stats,
        'filename_format_str': 'innov_stats.metric.%Y%m%d%H.nc',
        'cycletime': datetime(2015,12,1,0)
    },
    'stats': ['bias', 'count', 'rmsd'],
    'metrics': ['temperature','spechumid','uvwind'],
    'elevation_unit': 'plevs',
    'regions': {
        'equatorial': {
            'lat_min': -5.0,
            'lat_max': 5.0
        },
        'global': {
            'lat_min': -90.0,
            'lat_max': 90.0
        },
        'north_hemis': {
            'lat_min': 20.0,
            'lat_max': 60.0
        },
        'tropics': {
            'lat_min': -20.0,
            'lat_max': 20.0
        },
        'south_hemis': {
            'lat_min': -60.0,
            'lat_max': -20.0
        },
        'south_hemis': {
            'lat_min': -60.0,
            'lat_max': -20.0
        },
    },
    'output_format': hv_registry.PANDAS_DATAFRAME
}


def test_netcdf_harvester_config():
    """
    Test basic harvester configuration
    """
    conf_yaml_fn = os.path.join(
        PYTEST_CALLING_DIR,
        CONFIGS_DIR,
        NETCDF_HARVESTER_CONFIG__VALID
    )

    with open(conf_yaml_fn, 'w', encoding='utf8') as file:
        documents = yaml.dump(VALID_CONFIG_DICT, file)
        print(f'conf_dict: {conf_yaml_fn}, documents: {documents}')

    data1 = harvest(VALID_CONFIG_DICT)
    harvest_dict = YamlLoader(conf_yaml_fn).load()[0]
    data2 = harvest(conf_yaml_fn)

    assert len(data1) == len(data2)

    print(f'dataframe column names: {data2.columns.values.tolist()}')

    print(f'harvested {len(data1)} records using config: {VALID_CONFIG_DICT}')
    print(f'harvested {len(data2)} records using config: {harvest_dict}')
    print(f'harvested data type: {type(data2)}')
    print(f'harvested data: {data2}')

    os.remove(conf_yaml_fn)


def test_netcdf_harvester_region_config():
    """
    Test region class
    """

    region = Region('test_region', -10.0, 10.0)
    with pytest.raises(ValueError):
        region = Region(5, -10, 10)
    with pytest.raises(ValueError):
        region = Region({}, -10, 10)
    with pytest.raises(ValueError):
        region = Region([], -10, 10)
    with pytest.raises(ValueError):
        region = Region('test_region', -10, 10)
    with pytest.raises(ValueError):
        region = Region('test_region', -10, [])
    with pytest.raises(ValueError):
        region = Region('test_region', -10, {})

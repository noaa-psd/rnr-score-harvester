#!/usr/bin/env python

"""Unit tests for gsi_satellite_radiance.py
"""

import os
from pathlib import Path

from score_hv import hv_registry
from score_hv.harvester_base import harvest

PYTEST_CALLING_DIR = Path(__file__).parent.resolve()
FIT_FILE_PATH = os.path.join(PYTEST_CALLING_DIR, 'data',
                             'gsistats.1979032100_control')
                             
VALID_CONFIG_DICT = {'harvester_name': hv_registry.GSI_STATS,
                     'filename': FIT_FILE_PATH,
                     'data_types': ['satinfo_channels',
                                    'channel_stats',
                                    'radiance_observation_types',
                                    'observation_type_summary',
                                    'observation_totals']
                    }

def test_nchannels():
    data1 = harvest(VALID_CONFIG_DICT)
    assert len(data1['satinfo_channels']) == 4672
    
def test_bad_config():
    bad_config_dict = {'harvester_name': hv_registry.GSI_STATS,
                     'filename': FIT_FILE_PATH,
                     'data_types': ['satinfo_channel',
                                    'channel_statistics',
                                    'radiance_observation_types',
                                    'observation_type_summary',
                                    'observation_totals']
                    }

    try:
        data1 = harvest(bad_config_dict)
        exception_caught = False
    except KeyError:
        exception_caught = True
    
    assert exception_caught
    
def test_final_summary():
    data1 = harvest({'harvester_name': hv_registry.GSI_STATS,
                     'filename': FIT_FILE_PATH,
                     'data_types': ['observation_type_summary']
                    })
    try:
        print(data1['satinfo_channels'])
        exception_caught = False
    except KeyError:
        exception_caught = True
    
    assert exception_caught
    assert data1['observation_type_summary'][0].gsi_stage == 1
    assert data1['observation_type_summary'][0].instrument == 'hirs2'
    assert data1['observation_type_summary'][0].penalty == float(0.14907E+06)
    assert data1['observation_type_summary'][5].gsi_stage == 2
    assert data1['observation_type_summary'][5].instrument == 'ssu'
    assert data1['observation_type_summary'][5].penalty == 3949.3
    
def run_all():
    test_nchannels()
    
def main():
    run_all()
    
if __name__=='__main__':
    main()
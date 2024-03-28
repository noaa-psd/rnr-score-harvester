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
                             
VALID_CONFIG_DICT = {'harvester_name': hv_registry.GSI_RADIANCE_CHANNEL,
                     'filename': FIT_FILE_PATH,
                     'statistics': ('nobs_used',
                                    'nobs_tossed',
                                    'variance',
                                    'bias_pre_corr',
                                    'bias_post_corr',
                                    'penalty',
                                    'sqrt_bias',
                                    'std')
                    }
    
def test_bad_config():
    bad_config_dict = {'harvester_name': hv_registry.GSI_RADIANCE_CHANNEL,
                       'filename': FIT_FILE_PATH,
                       'statistics': ('nobs_used',
                                      'nobs_tossed',
                                      'variances',
                                      'bias_pre_corr',
                                      'bias_post_corr',
                                      'qcpenalty',
                                      'sqrt_bias',
                                      'std')
                    }

    try:
        data = harvest(bad_config_dict)
        exception_caught = False
    except KeyError:
        exception_caught = True
    
    assert exception_caught

def test_channel_stats_meta():
    datetime_format = '%Y%m%d%H'
    
    data = harvest(VALID_CONFIG_DICT)
    assert data[0].datetime.strftime(datetime_format) == '1979032100'
    assert data[0].iteration == 1
    assert data[0].series_number == 1881
    assert data[0].channel == 1
    assert data[0].satellite == 'tirosn'
    assert data[0].instrument == 'hirs2'
    
    assert data[-1].datetime.strftime(datetime_format) == '1979032100'
    assert data[-1].iteration == 2
    assert data[-1].series_number == 4653
    assert data[-1].channel == 2
    assert data[-1].satellite == 'tirosn'
    assert data[-1].instrument == 'ssu'
    
def test_channel_stats_nobs():
    valid_config_dict = VALID_CONFIG_DICT
    valid_config_dict['statistics'] = ('nobs_used', 'nobs_tossed')
    
    data = harvest(valid_config_dict)
    
    try:
        assert data[2].statistic == 'variance'
        exception_caught = False
    except AssertionError:
        exception_caught = True
        
    assert exception_caught
    
    assert data[0].statistic == 'nobs_used'
    assert data[0].value == 11482
    assert data[0].longname == 'number of observations used in the GSI analysis'
    assert data[1].statistic == 'nobs_tossed'
    assert data[1].value == 1184
    assert data[1].longname == 'number of observations tossed by gross check'
        
'''
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
'''
 
def run_all():
    test_bad_config()
    test_channel_stats_meta()
    
def main():
    run_all()
    
if __name__=='__main__':
    main()
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
                     'variables': ('var',
                                   'varch_cld',
                                   'use',
                                   'ermax',
                                   'b_rad',
                                   'pg_rad',
                                   'icld_det',
                                   'icloud',
                                   'iaeros',
                                   'bias_correction_coefficients'),
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
                       'variables': ('bias_correction_coefficients'),
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
    assert data[0].iteration == None
    assert data[0].series_numbers == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert data[0].channels == [7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
    assert data[0].observation_type == 'abi_g16'
    
    assert data[-1].datetime.strftime(datetime_format) == '1979032100'
    assert data[-1].iteration == 2
    assert data[-1].series_numbers == [4652, 4653, 4654]
    assert data[-1].channels == [1, 2, 3]
    assert data[-1].observation_type == 'ssu_tirosn'
    
def test_channel_stats_nobs():
    valid_config_dict = VALID_CONFIG_DICT
    valid_config_dict['variables'] = ['use']
    valid_config_dict['statistics'] = ('nobs_used', 'nobs_tossed')
    
    data = harvest(valid_config_dict)
    
    assert data[2].statistic != 'variance'
    
    assert data[0].statistic == 'use'
    assert data[0].values_by_channel == [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
    assert data[0].longnames == None
    assert data[-1].statistic == 'nobs_tossed'
    assert data[-1].values_by_channel == [19, 17, None]
    assert data[-1].longnames==['number of observations tossed by gross check',
                                'number of observations tossed by gross check',
                                None]
        
def test_active_channels():
    valid_config_dict = VALID_CONFIG_DICT
    valid_config_dict['variables'] = ('use', 'bias_correction_coefficients')
    
    data = harvest(valid_config_dict)
    
    for entry in data:
        if entry.statistic == 'bias_correction_coefficients':
            for i, series_number in enumerate(entry.series_numbers):
                if series_number == 1881:
                    assert entry.values_by_channel[i] == [2.962464,
                                                          0.000000,
                                                          0.000000,
                                                          -0.281547,
                                                          0.287098,
                                                          0.000000,
                                                          0.000000,
                                                          6.384764,
                                                          -10.056001,
                                                          3.726279,
                                                          12.347757,
                                                          -13.642057]
                
                elif series_number == 4040:
                    assert entry.values_by_channel[i] == [0.158032,
                                                          0.000000,
                                                          0.000000,
                                                          -0.348017,
                                                          0.887449,
                                                          0.000000,
                                                          0.000000,
                                                          -0.003456,
                                                          -62.243733,
                                                          -315.711133,
                                                          -27.730949,
                                                          1.005751]
                                                          
        if entry.statistic == 'bias_post_corr' and entry.observation_type=='ssu_tirosn':
            if entry.iteration == 1:
                # GSI stage 1
                assert entry.values_by_channel == [0.0555868, -0.0181311, 
                                                      None]
                assert entry.channels == [1,2,3]
            elif entry.iteration == 2:
                # GSI stage 2
                assert entry.values_by_channel == [-0.0067728, -0.0040200,
                                                      None]
                assert entry.channels == [1,2,3]
                                                      
        if entry.statistic == 'variance' and entry.observation_type=='msu_tirosn':
            if entry.iteration == 1:
                # GSI stage 1
                assert entry.values_by_channel == [2.5, 0.3, 0.23, 0.3]
                assert entry.channels == [1,2,3,4]
            elif entry.iteration == 2:
                # GSI stage 2
                assert entry.values_by_channel == [2.5, 0.3, 0.23, 0.3]
                assert entry.channels == [1,2,3,4]
                
def test_no_vars():
    valid_config_dict = {'harvester_name': hv_registry.GSI_RADIANCE_CHANNEL,
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
    
    data = harvest(valid_config_dict)
    
    for entry in data:
        assert entry.statistic not in ('var',
                                          'varch_cld',
                                          'use',
                                          'ermax',
                                          'b_rad',
                                          'pg_rad',
                                          'icld_det',
                                          'icloud',
                                          'iaeros',
                                          'bias_correction_coefficients')
                                             
        assert entry.observation_type in ('hirs2_tirosn', 'msu_tirosn',
                                             'ssu_tirosn')
    
'''
to be implemented with harvest GSI stats by observation type
                                             
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
    test_channel_stats_nobs()
    test_active_channels()
    test_no_vars()
    
def main():
    run_all()
    
if __name__=='__main__':
    main()
#!/usr/bin/env python

"""Unit tests for gsi_satellite_radiance.py
"""

import os
from pathlib import Path
from datetime import datetime

from score_hv import hv_registry
from score_hv.harvester_base import harvest

PYTEST_CALLING_DIR = Path(__file__).parent.resolve()
FIT_FILE_PATH = os.path.join(PYTEST_CALLING_DIR, 'data',
                             'gsistats.1979032100_control')
                             
FIT_FILE_PATH_GEOS_IT_1998 = os.path.join(PYTEST_CALLING_DIR, 'data',
                    'x0123_abcdef_xyz01.xyz_stats.log.19980101_00z.txt')
                             
VALID_CONFIG_DICT = {
    'harvester_name': hv_registry.GSI_CONVENTIONAL_OBS,
    'filename': FIT_FILE_PATH,
    'variables': ('fit_psfc_data', # fit of surface pressure data (mb)
                  'fit_u_data', # fit of u wind data (m/s),
                  'fit_v_data', # fit of v wind data (m/s),
                  'fit_t_data', # fit of temperature data (K)
                  'fit_q_data', # fit of moisture data (% of qsaturation guess)
                  ),
    'statistics': (
        'count', # number of obs summed under obs types and vertical layers
        'bias', # bias of obs departure for each outer loop (it)
        'rms', # root mean squre error of obs departure for each outer loop (it)
        'cpen', # obs part of penalty (cost function)
        'qcpen' # nonlinear qc penalty
        )
    }
                    
VALID_CONFIG_DICT_GEOS_IT_1998 = {
    'harvester_name': 
    hv_registry.GSI_CONVENTIONAL_OBS,
    'filename': FIT_FILE_PATH_GEOS_IT_1998,
    'variables': ('fit_psfc_data', # fit of surface pressure data (mb)
                  'fit_u_data', # fit of u wind data (m/s),
                  'fit_v_data', # fit of v wind data (m/s),
                  'fit_t_data', # fit of temperature data (K)
                  'fit_q_data', # fit of moisture data (% of qsaturation guess)
                  ),
    'statistics': (
        'count', # number of obs summed under obs types and vertical layers
        'bias', # bias of obs departure for each outer loop (it)
        'rms', # root mean squre error of obs departure for each outer loop (it)
        'cpen', # obs part of penalty (cost function)
        'qcpen' # nonlinear qc penalty
        )
                    }
                    
def test_datetime():
    data_list = harvest(VALID_CONFIG_DICT)
    test_datetime = datetime.strptime('1979032100', '%Y%m%d%H')
    for i, data_i in enumerate(data_list):
        assert test_datetime == data_i.datetime
        
def test_datetime_geos_it_1998():
    data_list = harvest(VALID_CONFIG_DICT_GEOS_IT_1998)
    test_datetime = datetime.strptime('1998010100', '%Y%m%d%H')
    for i, data_i in enumerate(data_list):
        assert test_datetime == data_i.datetime

def test_longnames():
    data_list = harvest(VALID_CONFIG_DICT)
    for i, data_i in enumerate(data_list):
        if data_i.variable == 'fit_psfc_data':
            assert data_i.longname == 'fit of surface pressure data'
            
def test_units():
    data_list = harvest(VALID_CONFIG_DICT)
    for i, data_i in enumerate(data_list):
        if data_i.statistic == 'count':
            assert data_i.units == None
        elif data_i.variable == 'fit_psfc_data':
            assert data_i.units == 'mb'
        elif data_i.variable == 'fit_q_data':
            assert data_i.units == r'%'

def test_bad_config():
    """test that a misconfigured config_dict does not result in data being
    returned by the harvester
    """
    
    bad_config_dict = {
        'harvester_name': 
        hv_registry.GSI_CONVENTIONAL_OBS,
        'filename': FIT_FILE_PATH,
        'variables': ('fit_psfc_data',
                      'bias_correction_coefficients'),
        'statistics': ('count',
                       'nobs_used',
                       'nobs_tossed',
                       'variance',
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
 
def test_run():
    import ipdb
    
    data_list = harvest(VALID_CONFIG_DICT)
    for i, data_i in enumerate(data_list):
        assert data_i.plevs_units == 'GET_PLEV_UNITS'
        #ipdb.set_trace()

def run_all():
    test_datetime()
    test_bad_config()
    test_longnames()
    test_units()
    test_run()
    
def main():
    run_all()
    
if __name__=='__main__':
    main()

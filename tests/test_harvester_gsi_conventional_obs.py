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
                  'fit_uv_data', # fit of u, v wind data (m/s),
                  #'fit_t_data', # fit of temperature data (K)
                  #'fit_q_data', # fit of moisture data (% of qsaturation guess)
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
                  #'fit_u_data', # fit of u wind data (m/s),
                  #'fit_v_data', # fit of v wind data (m/s),
                  #'fit_t_data', # fit of temperature data (K)
                  #'fit_q_data', # fit of moisture data (% of qsaturation guess)
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
 
def test_fit_of_surface_pressure_data():
    data_list = harvest(VALID_CONFIG_DICT)    
    
    for i, data_i in enumerate(data_list):
        if data_i.variable == 'fit_psfc_data':
            assert data_i.plevs_top == [[0.], [0.]]
            assert data_i.plevs_bot == [[2000.], [2000.]]
            assert data_i.plevs_units == ['hPa', 'hPa']
            
            if data_i.iteration == 1:
                if data_i.usage == 'asm':
                    if data_i.type == '120':
                        if data_i.statistic == 'count':
                            assert data_i.values == [672]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.224E+00]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.168E+01]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.569E+00]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.500E+00]
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [10716]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.411E+00]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.192E+01]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.827E+00]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.687E+00]
                elif data_i.usage == 'rej':
                    if data_i.type == '191':
                        if data_i.statistic == 'count':
                            assert data_i.values == [14]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.640E+01]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.100E+02]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.000E+00]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.000E+00]
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [551]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.559E+02]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.262E+03]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.000E+00]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.000E+00]
                elif data_i.usage == 'mon':
                    if data_i.type == '180' and data_i.subtype=='0001':
                        if data_i.statistic == 'count':
                            assert data_i.values == [25]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.245E+00]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.250E+01]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.122E+01]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.998E+00]
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [123]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.102E+01]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.294E+01]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.736E+00]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.513E+00]
            elif data_i.iteration == 2:
                if data_i.usage == 'asm':
                    if data_i.type == '191':
                        if data_i.statistic == 'count':
                            assert data_i.values == [38]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.438E+00]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.197E+01]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.173E+01]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.160E+01]
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [10745]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.319E+00]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.173E+01]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.650E+00]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.543E+00]
                
                elif data_i.usage == 'rej':
                    if data_i.type == '180' and data_i.subtype == '0001':
                        if data_i.statistic == 'count':
                            assert data_i.values == [55]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.555E+01]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.187E+02]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.000E+00]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.000E+00]
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [522]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.593E+02]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.269E+03]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.000E+00]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.000E+00]
                            
                elif data_i.usage == 'mon':
                    if data_i.type == '180' and data_i.subtype == '0000':
                        if data_i.statistic == 'count':
                            assert data_i.values == [2]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.634E+00]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.634E+00]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.197E+00]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.197E+00]
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [123]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.839E+00]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.288E+01]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.714E+00]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.483E+00 ]
                            
                                                        
def run_test():
    import ipdb
    
    data_list = harvest(VALID_CONFIG_DICT)
    for i, data_i in enumerate(data_list):
        ipdb.set_trace()

def run_all():
    test_datetime()
    test_bad_config()
    test_longnames()
    test_units()
    test_fit_of_surface_pressure_data()
    run_test()
    
def main():
    run_all()
    
if __name__=='__main__':
    main()

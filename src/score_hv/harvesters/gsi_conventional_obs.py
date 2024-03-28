"""methods to extract information from the Gridpoint Statistical Interpolation (GSI) analysis output (fit files), including innovation statistics for
conventional observations (including satellite retrievals)
"""

import os
import warnings
from collections import namedtuple
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime

from score_hv.config_base import ConfigInterface

HARVESTER_NAME = 'gsi_conv_obs'

VALID_VARIABLES = (
    'fit_psfc_data' # fit of surface pressure data (mb)
    'fit_u_data' # fit of u wind data (m/s),
    'fit_v_data' # fit of v wind data (m/s),
    'fit_t_data' # fit of temperature data (K)
    'fit_q_data' # fit of moisture data (% of qsaturation guess)
)

VALID_STATISTICS = (
    'count', # number of obs summed under obs types and vertical layers
    'bias', # bias of obs departure for each outer loop (it)
    'rms', # root mean squre error of obs departure for each outer loop (it)
    'cpen', # obs part of penalty (cost function)
    'qcpen' # nonlinear qc penalty
)

ObservationData = namedtuple(
    'HarvestedData',
    ['datetime', # datetime.datetime object (date and a time)
     'plevs_top', # pressures at the tops of the layers (for multi-level data)
     'plevs_bot', # pressure at the bottoms of the layers (for multi-level data)
     'variable',
     'statistic',
     'values',
     'units',
     'longname',
     'iteration' # GSI outer loop number
     'usage' # used (asm), read in but not assimilated (mon) or rejected (rej)
     'type', # prepbufr obs type    
    ]
)

@dataclass
class ConvObs(ConfigInterface):
    
    config_data: dict = field(default_factory=dict)
    
    def __post_init__(self):
        self.set_config()
        
    def set_config(self):
        """function to set configuration variables given dictionary
        """
        pass
        
def test(gsistats_test_file):
    test_datetime = datetime.strptime(
        gsistats_test_file.split('.')[-1].split('_')[0], '%Y%m%d%H')
    import ipdb
    ipdb.set_trace()
    print(test_datetime)
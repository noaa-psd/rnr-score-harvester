"""
Copyright 2022 NOAA
All rights reserved.

Collection of methods to facilitate file/object retrieval

"""
from collections import namedtuple
from score_hv.harvesters.innov_netcdf import InnovStatsCfg, InnovStatsHv
from score_hv.harvesters.obs_log import ObsInfoCfg, ObsInfoHv

NAMED_TUPLES_LIST = 'tuples_list'
PANDAS_DATAFRAME = 'pandas_dataframe'

INNOV_NETCDF = 'innov_stats_netcdf'
OBS_INFO_LOG = 'obs_info_log'

Harvester = namedtuple(
    'Harvester',
    [
        'name',
        'config_handler',
        'data_parser'
    ],
)

harvester_registry = {
    'innov_stats_netcdf': Harvester(
        'innovation statistics for temperature, spechumid, uvwind, and salinity (netcdf)',
        InnovStatsCfg,
        InnovStatsHv
    ),
    'obs_info_log': Harvester(
        'observation information for pressure, specific humidity, temperature, height, wind components, '
        'precipitable h2o, and relative humidity (log)',
         ObsInfoCfg,
         ObsInfoHv
    ),
}

"""
Copyright 2022 NOAA
All rights reserved.

Collection of methods to facilitate file/object retrieval

"""
from collections import namedtuple
from score_hv.harvesters.innov_netcdf import InnovStatsCfg, InnovStatsHv


NAMED_TUPLES_LIST = 'tuples_list'
PANDAS_DATAFRAME = 'pandas_dataframe'

INNOV_STATS_NETCDF = 'innov_stats_netcdf'


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
    )
}

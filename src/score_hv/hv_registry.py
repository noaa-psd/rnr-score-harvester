"""Copyright 2023 NOAA
All rights reserved.

Collection of methods to facilitate file/object retrieval
"""

from collections import namedtuple

from score_hv.harvesters.innov_netcdf import InnovStatsCfg, InnovStatsHv
from score_hv.harvesters.obs_log import ObsInfoCfg, ObsInfoHv
from score_hv.harvesters.inc_logs import LogIncCfg, LogIncHv
from score_hv.harvesters.daily_bfg import DailyBFGConfig, DailyBFGHv
from score_hv.harvesters.replay_analysis_increments import IncrementsConfig, IncrementsHv

NAMED_TUPLES_LIST = 'tuples_list'
PANDAS_DATAFRAME = 'pandas_dataframe'
INNOV_NETCDF = 'innov_stats_netcdf'
OBS_INFO_LOG = 'obs_info_log'
INC_LOGS = 'inc_logs'
DAILY_BFG = 'daily_bfg'
REPLAY_ANALYSIS_INCREMENTS = 'replay_analysis_increments'

Harvester = namedtuple('Harvester', ('name', 'config_handler', 'data_parser'),)

harvester_registry = {INNOV_NETCDF: Harvester(
                         'innovation statistics for temperature, spechumid, '
                          'uvwind, and salinity (netcdf)',
                          InnovStatsCfg,
                          InnovStatsHv),
                      OBS_INFO_LOG: Harvester(
                          'observation information for pressure, specific '
                          'humidity, temperature, height, wind components, '
                          'precipitable h2o, and relative humidity (log)',
                          ObsInfoCfg,
                          ObsInfoHv),
                      INC_LOGS: Harvester(
                          'increment descriptive statistics from '
                          'log files',
                          LogIncCfg,
                          LogIncHv),
                      DAILY_BFG: Harvester(
                          'Daily mean statistics from background forecast data',
                          DailyBFGConfig,
                          DailyBFGHv),
                      REPLAY_ANALYSIS_INCREMENTS: Harvester(
                          'Analysis increments from replay (fv3_increment6.nc)',
                          IncrementsConfig,
                          IncrementsHv)
                      }
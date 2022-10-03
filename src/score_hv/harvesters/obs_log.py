"""
Work by Jessica Knezha

Collection of methods to facilitate observation information retrieval from log files

"""

from collections import namedtuple
from dataclasses import dataclass, field
import pandas as pd

from score_hv.config_base import ConfigInterface
from score_hv import file_utils
from score_hv import hv_registry as hvr
valid_variables = [
    'PRESSURE',
    'SPECIFIC HUMIDTY',
    'TEMPERATURE',
    'HEIGHT',
    'WIND COMPONENTS',
    'PRECIPITABLE H20',
    'RELATIVE HUMIDTY'
]

HRVSTER_NAME = 'obs_info_'

HarvestedData = namedtuple(
    'HarvestedData',
    [
        'file_name',
        'cycletime',
        'variable',
        'instrument type',
        'number_obs',
        'number_obs',
        'number_obs_qc_0to3'
    ],
)

@dataclass
class ObsInfoCfg(ConfigInterface):
    """
    Dataclass to hold and provide configuration information
    pertaining to how the harvester should read log file

    Parameters:
    -----------
    config_data: dict - contains configuration data parsed from
                either an input yaml file or input dict

    file_meta: FileMeta - parsed configuration data

    """
    config_data: dict = field(default_factory=dict)
    harvest_config: dict = field(default_factory=dict, init=False)

    def __post_init__(self):
        self.harvest_config = self.set_config()



@dataclass
class ObsInfoHv:
    """
    Harvester dataclass used to parse observation information data stored in
    log files

    Parameters:
    -----------
    config: ObsInfoCfg object containing information used to determine
            how to parse the log file for which variable

    Methods:
    --------
    get_data: parses observation information from log files based on input config
              file, returns a list of tuples containing specific data
    """
    config: ObsInfoCfg = field(default_factory=ObsInfoCfg)

    def get_data(self):
        """
        Harvests observation information (instrument type, number of observations,
        and number of high quality observations) for a specified variable of the
        set {Pressure, Specific Humidity, Temperature, Height, Wind Components,
        Precipitable H20, Relative Humidity}. Input file is a log text file.

        Returns
        -------
        harvested_data: list of HarvestedData tuples each consisting of
                        file_name, cycletime, variable, instrument type,
                        number_obs, number_obs_qc_0to3
        """
        harvested_data = []
        return harvested_data

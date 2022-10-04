"""
Work by Jessica Knezha

Collection of methods to facilitate observation information retrieval from log files

"""

from collections import namedtuple
from dataclasses import dataclass, field
import pandas as pd
import os

from score_hv.config_base import ConfigInterface
from score_hv import file_utils
from score_hv import hv_registry as hvr
valid_variables = [
    'PRESSURE',
    'SPECIFIC HUMIDITY',
    'TEMPERATURE',
    'HEIGHT',
    'WIND COMPONENTS',
    'PRECIPITABLE H20',
    'RELATIVE HUMIDITY'
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
    harvest_variable: str
    harvest_filename: str
    config_data: dict = field(default_factory=dict)

    def __post_init__(self):
         self.set_config()

    # function to set configuration variables from given dictionary
    def set_config(self):
        try:
            self.harvest_variable = self.config_data.get('variable')
        except Exception as err:
            msg = f'\'variable\' key missing, must be one of ' \
                  f'({valid_variables}) - err: {err}'
            raise KeyError(msg) from err

        try:
            self.harvest_filename = self.config.data.get('filename')
        except Exception as err:
            msg = f'\'filename\' key missing, must be included for log file' \
                f' - err: {err}'
            raise KeyError(msg) from err

    # function to validate the values of the variable and filename for harvest
    # invalid values raise a value error
    def validate(self):
        if self.harvest_variable not in valid_variables :
            msg = f'given variable {self.harvest_variable} is ' \
                      f'not a valid variable type for harvester. valid options: {valid_variables}'
            raise ValueError(msg)

        if not os.path.exists(self.harvest_filename) :
            msg = f'given filename {self.harvest_filename} is not valid. ' \
                  f'valid filename required for harvester'
            raise ValueError(msg)


@dataclass
class ObsInfoHv:
    """
    Harvester dataclass used to parse observation information data stored in
    log files

    Parameters:
    -----------
    config: ObsInfoCfg object containing information used to determine
            which variable to parse the log file for

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

        # read in file
        # get cycletime from DATA VALID AT
        # find section for variable
        # read variable

        with open(self.config.harvest_filename) as log_file:
            data_valid_line = log_file.readline().split()
            cycletime = data_valid_line.last()

            on_variable = False

            for line in log_file:
                if line.isspace():
                    continue

                cleaned_line = line.strip() # strip to remove whitespace so calls can be to first character of line
                if cleaned_line[0] is '-':
                    continue

                if not on_variable and cleaned_line[0].isdigit():
                    continue

                # need to skip over the column headings
                if on_variable and cleaned_line[0].isalpha():
                    if cleaned_line[0:3] == 'typ':
                        continue
                    break

                if not on_variable and cleaned_line.upper() == self.config.harvest_variable:
                    on_variable = True

                if on_variable and line[0].isdigit():
                    split = cleaned_line.split()
                    type = split[0].replace('|', '')
                    num_obs = split[1].replace('|', '')
                    num_obs_qc = split[2].replace('|', '')
                    item = HarvestedData(
                        self.config.harvest_filename,
                        cycletime,
                        self.config.harvest_variable,
                        type,
                        num_obs,
                        num_obs_qc
                    )
                    harvested_data.append(item)

        return harvested_data

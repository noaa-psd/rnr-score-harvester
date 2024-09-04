"""
Copyright 2024 NOAA
All rights reserved.

Collection of methods to retrieve metadata from ioda formatted nc files.

"""
from collections import namedtuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from netCDF4 import Dataset
import pandas as pd

from score_hv.config_base import ConfigInterface
from score_hv import file_utils
from score_hv import hv_registry as hvr

HARVESTER_NAME = 'ioda_meta_netcdf'

HarvestedData = namedtuple(
    'HarvestedData',
    [
        'filename',
        'date_time',
        'num_locs',
        'variable_name',
        'has_PreQC',
        'has_ObsError',
        'sensor',
        'platform',
        'ioda_layout',
        'processing_level',
        'thinning',
    ]
)

@dataclass
class IodaMetaCfg(ConfigInterface):
    """
        Dataclass to hold and provide configuration information pertaining to
        how the harvester should retrieve the ioda metadata..
    
        Parameters:
        -----------
        config_data: dict - contains configuration data parsed from either an
                            input yaml file or input dict
    """

    config_data: dict = field(default_factory=dict)

    def __post_init__(self):
         self.set_config()
    
    def set_config(self):
        """ function to set configuration variables from given dictionary
        """ 
        self.harvest_filename = self.config_data.get('filename')

@dataclass
class ObsInfoHv:
    """
    Harvester dataclass used to parse metadata from ioda nc files

    Parameters:
    -----------
    config: IodaMetaCfg object containing information used to determine what file to get info for

    Methods:
    --------
    get_data: gets the metadata for a specified file in ioda format
    """
    config: IodaMetaCfg = field(default_factory=IodaMetaCfg)

    def get_data(self):
        """
        Harvests metadata for ioda files including number of observations and variables contained within. 

        Returns
        -------
        harvested_data: list of Harvested data for a given file, one per variable

        'filename',
        'date_time',
        'num_locs',
        'variable_name',
        'has_PreQC',
        'has_ObsError',
        'sensor',
        'platform',
        'ioda_layout',
        'processing_level',
        'thinning',
        """
        harvested_data = []
        dataset = Dataset(self.config.harvest_filename, 'r')

        date_time = dataset.getncattr('date_time') if 'date_time' in dataset.ncattrs() else None
        num_locs = dataset.getncattr('nlocs') if 'nlocs' in dataset.ncattrs() else None
        sensor = dataset.getncattr('sensor') if 'sensor' in dataset.ncattrs() else None
        platform = dataset.getncattr('platform') if 'platform' in dataset.ncattrs() else None
        ioda_layout = dataset.getncattr('_ioda_layout') if '_ioda_layout' in dataset.ncattrs() else None
        processing_level = dataset.getncattr('processing_level') if 'processing_level' in dataset.ncattrs() else None
        thinning = dataset.getncattr('thinning') if 'thinning' in dataset.ncattrs() else None

        has_PreQC = False
        if 'PreQC' in dataset.groups:
            has_PreQC = True
        
        has_ObsError = False
        if 'ObsError' in dataset.groups:
            has_ObsError = True

        variable_names = ''

        if 'MetaData' in dataset.groups:
            group = dataset.groups['MetaData']
            if 'variable_names' in group.variables:
                variable = group.variables['variable_names']
                variable_names = variable[:]


        harvested_data = HarvestedData (
            self.config.harvest_filename, 
            date_time,
            num_locs,
            variable_names,
            has_PreQC,
            has_ObsError,
            sensor,
            platform,
            ioda_layout,
            processing_level,
            thinning
        )

        return harvested_data

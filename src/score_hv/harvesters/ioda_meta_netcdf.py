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
import re
import os 
import numpy as np

from score_hv.config_base import ConfigInterface
from score_hv import file_utils
from score_hv import hv_registry as hvr

HARVESTER_NAME = 'ioda_meta_netcdf'

HarvestedData = namedtuple(
    'HarvestedData',
    [
        'filename',
        'file_date_time',
        'min_date_time',
        'max_date_time',
        'num_locs',
        'num_vars',
        'variable_name',
        'var_count',
        'has_PreQC',
        'has_ObsError',
        'sensor',
        'platform',
        'ioda_layout',
        'processing_level',
        'thinning',
        'ioda_version',
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
class IodaMetaHv:
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
        harvested_data: list of Harvested data for a given file, one per variable, some data is file level for every variable

        'filename',
        'date_time',
        'num_locs',
        'num_vars',
        'variable_name',
        'var_count',
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
        num_vars = dataset.getncattr('nvars') if 'nvars' in dataset.ncattrs() else None
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

        # variable_names = ''

        min_datetime = date_time
        max_datetime = date_time

        if 'MetaData' in dataset.groups:
            group = dataset.groups['MetaData']
            if 'datetime' in group.variables:
                #value used in v2 is just datetimes
                datetimes = group.variables['datetime']
                min_datetime = format_datetime_string(np.min(datetimes))
                max_datetime = format_datetime_string(np.max(datetimes))
            if 'dateTime' in group.variables:
                #the value used in v3 is units seconds since 1970
                datetimes = group.variables['dateTime']
                min_seconds = int(np.min(datetimes))
                max_seconds = int(np.max(datetimes))
                min_datetime_obj = datetime(1970, 1, 1) + timedelta(seconds=min_seconds)
                max_datetime_obj = datetime(1970, 1, 1) + timedelta(seconds=max_seconds)
                min_datetime = format_datetime_string(min_datetime_obj)
                max_datetime = format_datetime_string(max_datetime_obj)


        valid_value_counts = {}
        if 'ObsValue' in dataset.groups:
            group = dataset.groups['ObsValue']
            for var_name in group.variables:
                var = group.variables[var_name]
                data = var[:]
                flat_data = data.flatten()
                var_count = np.ma.count(flat_data)
                valid_value_counts[var_name] = var_count

        filename_parsed = parse_filename(self.config.harvest_filename) 
        ioda_version = filename_parsed['ioda_version']
        filename = filename_parsed['filename']

        #handle various options for reading datetime to make sure we provide a cycle time
        if date_time is str:
            date_time = format_int_based_datetime_string(date_time)

        if isinstance(date_time, np.int32):
            date_time = int_to_datetime_string(date_time)

        if date_time is None:
            date_time = filename_parsed['formatted_datetime_str']

        for variable in valid_value_counts:
            harvested_data.append(
                HarvestedData (
                    filename, 
                    date_time,
                    min_datetime,
                    max_datetime,
                    num_locs,
                    num_vars,
                    variable,
                    valid_value_counts[variable],
                    has_PreQC,
                    has_ObsError,
                    sensor,
                    platform,
                    ioda_layout,
                    processing_level,
                    thinning,
                    ioda_version
                )
            )

        dataset.close()
        return harvested_data


def format_datetime_string(datetime_obj):
    return datetime_obj.strftime("%Y-%m-%d %H:%M:%S")

def parse_filename(file_path):
    # Extract the file name from the full path
    filename = os.path.basename(file_path)
    
    # Regular expression to match the filename pattern
    pattern = r'.*\.(\d{8})\.T(\d{6})Z\.ioda(v\d+)\.nc$'
    
    match = re.match(pattern, filename)
    if match:
        # Extract date (YYYYMMDD) and time (HHMMSS)
        date_str = match.group(1)
        time_str = match.group(2)
        ioda_version = match.group(3)
        
        # Combine date and time into a datetime object
        dt = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
        
        # Format the datetime string as 'YYYY-MM-DD HH:MM:SS'
        formatted_datetime_str = format_datetime_string(dt)
        
        return {
            'filename': filename,
            'formatted_datetime_str': formatted_datetime_str,
            'datetime_obj': dt,
            'ioda_version': ioda_version
        }
    else:
        raise ValueError(f"Filename '{filename}' does not match the expected ioda format pattern.")

#put the datetime int from metadata into a useful format
def int_to_datetime_string(date_value):
    # Check if the value is either numpy int32 or plain int
    if isinstance(date_value, (np.int32, int)):
        # Convert the value to a string
        date_str = str(date_value)
        
        # Ensure the string is 10 characters long for the format 'YYYYMMDDHH'
        if len(date_str) != 10:
            raise ValueError(f"Input value {date_value} must be 10 digits long (YYYYMMDDHH format).")
        
        # Parse the string into a datetime object (format 'YYYYMMDDHH')
        dt = datetime.strptime(date_str, "%Y%m%d%H")
        
        # Format the datetime object into 'YYYY-MM-DD HH:MM:SS'
        formatted_datetime_str = format_datetime_string(dt)
        
        return formatted_datetime_str
    else:
        raise TypeError(f"Input value must be of type numpy int32 or int, got {type(date_value)} instead.")

def format_int_based_datetime_string(datetime_str):
    # Ensure the string is 10 characters long for the format 'YYYYMMDDHH'
    if len(datetime_str) != 10:
        #not in the format we will be resolving
        return datetime_str 
    
    # Parse the string into a datetime object (format 'YYYYMMDDHH')
    dt = datetime.strptime(datetime_str, "%Y%m%d%H")
    
    # Format the datetime object into 'YYYY-MM-DD HH:MM:SS'
    formatted_datetime_str = format_datetime_string(dt)
    
    return formatted_datetime_str

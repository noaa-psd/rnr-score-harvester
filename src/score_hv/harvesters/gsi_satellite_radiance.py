"""methods to extract information from the Gridpoint Statistical Interpolation 
(GSI) analysis output (fit files), including innovation statistics for 
satellite radiance/brightness temperature observation data for each channel
"""

import os
import warnings
from collections import namedtuple
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime

from score_hv.config_base import ConfigInterface

HARVESTER_NAME = 'gsi_radiance_channel'

BIAS_CORR_COEF_STR = 'bias_correction_coefficients'
N_BIAS_CORR_COEF = 12

# radiance data usage per channel from satinfo file
VALID_VARIABLES = (
        'var',
        'varch_cld',
        'use',
        'ermax',
        'b_rad',
        'pg_rad',
        'icld_det',
        'icloud',
        'iaeros',
        BIAS_CORR_COEF_STR)

# GSI statistics varying by instrument channel
VALID_STATISTICS = (
    'nobs_used', # number of obs used in GSI analysis
    'nobs_tossed', # number of obs tossed by gross check
    'variance', # variance for each satellite channel
    'bias_pre_corr', # observation minus guess before bias correction
    'bias_post_corr', # observation minus guess after bias correction
    'penalty', # penalty contribution
    'sqrt_bias', # square root of (o-g with bias correction)**2 (?)
    'std' # standard deviation
)

# meta data for each instrument channel in the satinfo file 
SatinfoChannel = namedtuple(
    'SatinfoChannel', [
        'series_number' # series number of the channel in satinfo file
        'observation_type', # radiance observation type (e.g., hirs2_tirosn)
        'chan', # channel number for certain radiance observation type
        'data_usage_dict' # key:value pairs corresponding to VALID_VARIABLES
    ]
)

# Summary statistics for each observation type
RadianceObservationTypeSummary = namedtuple(
    'RadianceObservationTypeSummary', [
        'cycletime',
        'gsi_stage', # GSI stage (determined by harvester)
        'it', # GSI stage (per the fit file)
        'satellite', # satellite name
        'instrument', # instrument name
        'nread', # num channels read in within analysis time window and domain
        'nkeep', # num channels kept after data thinning
        'nassim', # num channels used in analysis (passed all qc process)
        'penalty', # contribution from this observation type to cost function
        'qcpnlty', # nonlinear qc penalty from this data type
        'cpen', # penalty divided by the number of data assimilated
        'qccpen', # qcpnlty divided by the number of data assimilated
    ]
)

SatinfoStat = namedtuple(
    'SatinfoStat', [
        'datetime',
        'iteration',
        'observation_type', # radiance observation type (e.g., hirs2_tirosn)
        'series_numbers', # series numbers of the channels in satinfo file
        'channels', # channel numbers for certain radiance observation type
        'statistic' # name of statistic
        'values_by_channel',
        'longnames'
    ]
)

@dataclass
class SatinfoChannelConfig(ConfigInterface):

    config_data: dict = field(default_factory=dict)

    def __post_init__(self):
        self.set_config()

    def set_config(self):
        """ function to set configuration variables from given dictionary
        """
        self.harvest_filename = self.config_data.get('filename')
        self.set_variables()
        self.set_statistics()
    
    def set_variables(self):
        self.vars_to_harvest = self.config_data.get('variables')
        for var in self.vars_to_harvest:
            if var not in VALID_VARIABLES:
                msg = (f"{var} is not a supported variable "
                       "to harvest from the GSI analysis fit files. "
                       "Please reconfigure the input dictionary using only the "
                       f"following variables: {VALID_VARIABLES}")
                raise KeyError(msg)
    
    def set_statistics(self):
        self.stats_to_harvest = self.config_data.get('statistics')
        for stat in self.stats_to_harvest:
            if stat not in VALID_STATISTICS:
                msg = (f"{stat} is not a supported statistic "
                       "to harvest from the GSI analysis fit files. "
                       "Please reconfigure the input dictionary using only the "
                       f"following statistics: {VALID_STATISTICS}")
                raise KeyError(msg)

@dataclass
class SatinfoChannelHv(object):
    """Harvester dataclass used to parse GSI analysis fit file
    
    Parameters:
    -----------
    config: SatinfoChannelConfig object containing information used to 
    determine which data to extract from the GSI analysis fit file
    
    Methods:
    --------
    get_data: calls parse_fit_file()
    
    returns a list of tuples containing specific data
    """
    config: SatinfoChannelConfig = field(default_factory=SatinfoChannelConfig)

    def get_data(self):
        """Read the fit file (from the GSI analysis output)
        
        returns a list of SatinfoStat tuples
        """
        self.channels = dict() # iterate by series_number
        self.channel_stats = dict() # iterate by GSI stage
        
        self.obs_type_channels = dict() # iterate by observation type
        self.obs_type_series_numbers = dict() # iterate by observation type
        self.satinfo_stats = list() # iterate by observation type
        
        
        # get the datetime from the input file name
        self.datetime = datetime.strptime(
            self.config.harvest_filename.split('.')[-1].split('_')[0],
            '%Y%m%d%H')
        
        with open(self.config.harvest_filename, encoding="utf-8") as f:
            self.lines = list(f)
            
        self.parse_fit_file()           
        
        for obs_type, series_num_list in self.obs_type_series_numbers.items():
            for var in self.config.vars_to_harvest:            
                
                values_by_channel = list()
                for channel_index, series_number in enumerate(series_num_list):
                    """return data usage info (by channel)
                    """
                    assert obs_type == self.channels[series_number][
                                           'observation_type']
                    assert self.obs_type_channels[obs_type][
                               channel_index] == self.channels[series_number][
                                                     'channel']
                    values_by_channel.append(
                        self.channels[series_number]['data_usage_dict'][var]
                    )
                    
                self.satinfo_stats.append(SatinfoStat(
                    self.datetime,
                    None,
                    obs_type,
                    series_num_list,
                    self.obs_type_channels[obs_type],
                    var, # name of statistic
                    values_by_channel,
                    None
                    )
                )
        
        for obs_type, series_num_list in self.obs_type_series_numbers.items():
            for stat in self.config.stats_to_harvest:
                values_by_channel = list()
                longnames = list()
                
                for gsi_stage in self.channel_stats.keys():
                    for channel_index, series_number in enumerate(
                                                          series_num_list):
                        """return stats by channel
                        """
                        stats_dict = self.channel_stats[gsi_stage][
                                                            series_number][stat]
                        assert obs_type == stats_dict['observation_type']
                        assert self.obs_type_channels[obs_type][
                            channel_index] == stat_dict['channel_number']
                        
                        values_by_channel.append(stats_dict['value'])
                        longnames.append(stats_dict['longname'])
                    
                    self.satinfo_stats.append(SatinfoStat(
                        self.datetime,
                        gsi_stage,
                        obs_type,
                        series_num_list,
                        self.obs_type_channels[obs_type],
                        stat,
                        values_by_channel,
                        longnames
                    ))
        
        return self.satinfo_stats

    def get_channel_stats(self, line_parts):
        """iterate through the requested statistics and extract relevant data
        """
        series_number = int(line_parts[0]) # from satinfo file, index from 1 
        #channel_index = series_number - 1 # from self.channels, index from 0
        channel_number = int(line_parts[1])
        observation_type = line_parts[2]
        
        # make sure we have the correct channel
        #assert self.channels[channel_index].series_number==series_number
        assert self.channels[series_number][observation_type]==observation_type
        assert self.channels[series_number].chan = channel_number      
        
        self.channel_stats[self.gsi_stage][series_number] = dict()
        for stat in self.config.stats_to_harvest:
            if stat == 'nobs_used':
                value = int(line_parts[3])
                longname = 'number of observations used in the GSI analysis'
            elif stat == 'nobs_tossed':
                value = int(line_parts[4])
                longname = 'number of observations tossed by gross check'
            elif stat == 'variance':
                value = float(line_parts[5])
                longname = 'variance for satellite channel'
            elif stat == 'bias_pre_corr':
                value = float(line_parts[6])
                longname = 'observation minus guess before bias correction'
            elif stat == 'bias_post_corr':
                value = float(line_parts[7])
                longname = 'observation minus guess after bias correction'
            elif stat == 'penalty':
                value = float(line_parts[8])
                longname = 'penalty contribution from channel'
            elif stat == 'sqrt_bias':
                value = float(line_parts[9])
                longname = 'square root of (o-g with bias correction)**2'
            elif stat == 'std':
                value = float(line_parts[10])
                longname = 'standard deviation'
        

            self.channel_stats[self.gsi_stage][series_number][stat] = {
                                        'channel_number': int(line_parts[1]),
                                        'observation_type': observation_type,
                                        'value': value,
                                        'longname': longname}
                    
    def parse_fit_file(self):
        """ parse lines of fit file and extract statistics
        """
        self.gsi_stage = 1
        radinfo_read1 = False
        radinfo_read2 = False
        channelstats_read = False
        finalsummary_read = False
        for line_number, line in enumerate(self.lines):
            line_parts = line.split()
            
            if radinfo_read1:
                """RADINFO_READ PART 1
                
                harvest satinfo content
                """

                series_number = int(line_parts[0])
                #channel_index = series_number - 1
                observation_type = line_parts[1]
                channel = int(line2list[1].split()[0])
                
                line2list = line.split('=')
                data_usage_dict = dict()
                for var in self.config.vars_to_harvest:
                    if var == 'var':
                        value = float(line2list[2].split()[0])
                    elif var == 'varch_cld':
                        value = float(line2list[3].split()[0])
                    elif var == 'use':
                        value = int(line2list[4].split()[0])
                    elif var == 'ermax':
                        value = float(line2list[5].split()[0])
                    elif var == 'b_rad':
                        value = float(line2list[6].split()[0])
                    elif var == 'pg_rad':
                        value = float(line2list[7].split()[0])
                    elif var == 'icld_det':
                        value = int(line2list[8].split()[0])
                    elif var == 'icloud':
                        value = int(line2list[9].split()[0])
                    elif var == 'iaeros':
                        value = int(line2list[10].split()[0])
                    elif var == BIAS_CORR_COEF_STR:
                        value = list() # empty list for bias
                                       # correction coeficients
                    
                    data_usage_dict[var] = value    
                
                self.channels[series_number] = {
                    'observation_type': observation_type,
                    'channel': channel,
                    'data_usage_dict': data_usage_dict
                }
                
                # store channel numbers
                if observation_type in self.obs_type_channels.keys():
                    self.obs_type_channels[observation_type].append(
                        channel)
                else:
                    self.obs_type_channels[observation_type] = [channel]
                    
                # store series numbers
                if observation_type in self.obs_type_series_numbers.keys():
                    self.obs_type_series_numbers[observation_type].append(
                        series_number)
                else:
                    self.obs_type_series_numbers[observation_type] = [
                        series_number]
                
                if series_number == self.nchannels:
                    """this is the last channel
                    """
                    radinfo_read1 = False
                
            elif radinfo_read2:
                """RADINFO_READ PART 2
                
                harvest bias correction coeficients
                """

                series_number = int(line_parts[0])
                #channel_index = series_number - 1
                
                # partial assurance that this is the correct channel, by name
                assert line_parts[1] == self.channels[sereis_number][observation_type]
                bias_corr_coef = line_parts[2:]
                
                if len(bias_corr_coef) == N_BIAS_CORR_COEF: # there should always be 12 channels
                    self.channels[series_number
                    ][data_usage_dict][BIAS_CORR_COEF_STR].extend(
                                                                map(float, 
                                                                bias_corr_coef))
                else:
                    warnings.warn(f'cannot find exactly {N_BIAS_CORR_COEF} '
                                  'bias correction coefficients for '
                                  f'{self.channels[series_number]}\n'
                                  'returning this list of strings: '
                                  f'{bias_corr_coef}')

                    self.channels[series_number
                    ][data_usage_dict][BIAS_CORR_COEF_STR].extend(
                                                                 bias_corr_coef)
                                   
                if series_number == self.nchannels:
                    """this is the last channel
                    """
                    radinfo_read2 = False
            
            if channelstats_read and len(line_parts) == 11:
                """harvest radiance observation fit file statistics as a
                function of channel
                """
                self.get_channel_stats(line_parts)

            if finalsummary_read and len(line_parts) != 12:
                """Radiance observation statistics are provided in three
                stages from GSI; tracking GSI stage here, after
                completion of the final summary section
                """
                finalsummary_read = False
                self.gsi_stage += 1
            
            if not radinfo_read1 and len(line_parts) > 2:
                """determine how to proceed based on the line
                """
                if (line_parts[0] == 'RADINFO_READ:' and line_parts[1] == 'jpch_rad='):
                    """ proceed with satinfo channel data
                    """
                    radinfo_read1 = True
                    self.nchannels = int(line_parts[2])
                
                elif (line_parts[0] == 'RADINFO_READ:' and line_parts[1] == 'guess'):

                    if BIAS_CORR_COEF_STR in self.config.vars_to_harvest:
                    """proceed with bias correction coefficients
                    """
                    radinfo_read2 = True
                    
                elif line_parts[0] == 'rad' and line_parts[2] == 'penalty_all=':
                    """proceed with channel statistics
                    """

                    self.channel_stats[self.gsi_stage] = dict()

                    channelstats_read = True
                    
                elif line_parts[0] == 'it' and line_parts[1] == 'satellite':
                    """final summary for each observation type
                    """
                    channelstats_read = False

                    finalsummary_read = True
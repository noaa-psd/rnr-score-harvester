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
N_BIAS_CORR_COEF = 12

VALID_STATISTICS = (
    'nobs_used', # number of obs used in GSI analysis
    'nobs_tossed', # number of obs tossed by gross check
    'variance',
    'bias_pre_corr', # observation minus guess before bias correction
    'bias_post_corr', # observation minus guess after bias correction
    'penalty', # penalty contribution
    'sqrt_bias', # square root of (o-g with bias correction)**2 (?)
    'std' # standard deviation
)

SatinfoChannel = namedtuple(
    'SatinfoChannel', [
        'datetime',
        'name',
        'chan',
        'var',
        'varch_cld',
        'use',
        'ermax',
        'b_rad',
        'pg_rad',
        'icld_det',
        'icloud',
        'iaeros',
        'bias_correction_coefficients'
    ]
)

SatinfoChannelStat = namedtuple(
    'SatinfoChannelStat', [
        'datetime', # datetime.datetime object (date and a time)
        'iteration', # GSI outer loop number
        'series_number', # series number of the channel in satinfo file
        'channel', # channel number for certain radiance observation type
        'satellite', # radiance observation type (satellite)
        'instrument', # radiance observation type (instrument)
        'statistic',
        'value',
        'longname',
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
        self.set_statistics()
    
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
        
        returns a list of SatinfoChannelStat tuples
        """
        self.channels = list()
        self.channel_stats = list()
        
        # get the datetime from the input file name
        self.datetime = datetime.strptime(
            self.config.harvest_filename.split('.')[-1].split('_')[0],
            '%Y%m%d%H')
        
        with open(self.config.harvest_filename, encoding="utf-8") as f:
            self.lines = list(f)
            
        self.parse_fit_file()
        
        return self.channel_stats
        
    def get_channel_stats(self, line_parts):
        """iterate through the requested statistics and extract relevant data
        
        appends the self.channel_stats list with a SatinfoChannelStat tuple
        """
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
        
            self.channel_stats.append(SatinfoChannelStat(
                self.datetime,
                self.gsi_stage,
                int(line_parts[0]),
                int(line_parts[1]),
                line_parts[2].split('_')[1],
                line_parts[2].split('_')[0],
                stat,
                value,
                longname
            ))
                    
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
                channel_index = int(line_parts[0]) - 1
                
                line2list = line.split('=')
                self.channels.append(SatinfoChannel(
                                           self.datetime,
                                           line_parts[1],
                                           int(line2list[1].split()[0]),
                                           float(line2list[2].split()[0]),
                                           float(line2list[3].split()[0]),
                                           int(line2list[4].split()[0]),
                                           float(line2list[5].split()[0]),
                                           float(line2list[6].split()[0]),
                                           float(line2list[7].split()[0]),
                                           int(line2list[8].split()[0]),
                                           int(line2list[9].split()[0]),
                                           int(line2list[10].split()[0]),
                                           list() # empty list for bias
                                                  # correction coeficients
                                           ))
                                           
                if channel_index + 1 == self.nchannels:
                    """this is the last channel
                    """
                    radinfo_read1 = False
                
            elif radinfo_read2:
                """RADINFO_READ PART 2
                
                harvest bias correction coeficients
                """
                channel_index = int(line_parts[0]) - 1
                
                # partial assurance that this is the correct channel, by name
                assert line_parts[1] == self.channels[channel_index].name
                bias_corr_coef = line_parts[2:]
                
                try:
                    assert len(bias_corr_coef) == N_BIAS_CORR_COEF # there should always be 12 channels
                    self.channels[
                        channel_index].bias_correction_coefficients.extend(
                                                            map(float, 
                                                                bias_corr_coef))
                except AssertionError:
                    warnings.warn(f'cannot find exactly {N_BIAS_CORR_COEF} '
                                  'bias correction coefficients for '
                                  f'{self.channels[channel_index]}\n'
                                  'returning this list of strings: '
                                  f'{bias_corr_coef}')
                    self.channels[
                        channel_index].bias_correction_coefficients.extend(
                                                                 bias_corr_coef)
                                   
                if channel_index + 1 == self.nchannels:
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
                    """proceed with bias correction coefficients
                    """
                    radinfo_read2 = True
                    
                elif line_parts[0] == 'rad' and line_parts[2] == 'penalty_all=':
                    """proceed with channel statistics
                    """
                    channelstats_read = True
                    
                elif line_parts[0] == 'it' and line_parts[1] == 'satellite':
                    """final summary for each observation type
                    """
                    channelstats_read = False
                    finalsummary_read = True
"""methods to extract information from the Gridpoint Statistical Interpolation 
(GSI) analysis output (fit files), including innovation statistics for 
satellite radiance/brightness temperature observation data as a function of observation type
"""

import os
import warnings
from collections import namedtuple
from dataclasses import dataclass
from dataclasses import field

from score_hv.config_base import ConfigInterface

HARVESTER_NAME = 'gsi_radiance_obs_type'
N_BIAS_CORR_COEF = 12

VALID_VARIABLES = (
    'nobs_used', # number of obs used in GSI analysis
    'nobs_tossed', # number of obs tossed by gross check
    'variance',
    'bias_pre_corr', # observation minus guess before bias correction
    'bias_post_corr', # observation minus guess after bias correction
    'penalty', # penalty contribution
    'sqrt_bias', # square root of (o-g with bias correction)**2 (?)
    'std' # standard deviation
)

VALID_STATISTICS = (
    'penalty' # contribution to cost function
    'nobs', # number of good obs used in the assimilation
    'iland' # number of obs over land,
    'isnoice', # number of obs over sea ice and snow
    'icoast', # number of obs over coast
    'ireduce', # number of obs that reduce qc bounds in tropics
    'ivarl', # number of obs removed by gross check
    'nlgross', # number of obs removed by nonlinear qc
    'qcpenalty', # nonlinear qc penalty
    'qc1', # number of obs whose qc criteria has been adjusted by qc method 1
    'qc2', # number of obs whose qc criteria has been adjusted by qc method 1
    'qc3', # number of obs whose qc criteria has been adjusted by qc method 1
    'qc4', # number of obs whose qc criteria has been adjusted by qc method 1
    'qc5', # number of obs whose qc criteria has been adjusted by qc method 1
    'qc6', # number of obs whose qc criteria has been adjusted by qc method 1
    'qc7', # number of obs whose qc criteria has been adjusted by qc method 1 
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

SatinfoChannelStats = namedtuple(
    'SatinfoChannelStats', [
        'datetime',
        'iteration',
        'series_number', # series number of the channel in satinfo file
        'channel', # channel number for certain radiance observation type
        'observation_type', # radiance observation type (e.g., hirs2_tirosn)
        'nobs_used', # number of obs used in GSI analysis within this channel
        'nobs_tossed', # number of obs tossed by gross check within this channel
        'variance', # variance for each satellite channel
        'bias_pre_corr', # observation minus guess before bias correction
        'bias_post_corr', # observation minus guess after bias correction
        'penalty', # penalty contribution from this channel
        'sqrt_bias', # square root of (o-g with bias correction)**2 (?)
        'std' # standard deviation
    ]
)
                                               
RadianceObservationType = namedtuple(
    'RadianceObservationType',
        ['cycletime',
         'gsi_stage', 
         'sat', # satellite name
         'type', # instrument type
         
    ]
)

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
 
RadianceObservationTotals = namedtuple(
    'RadianceObservationTotals', [
        'cycletime',
        'gsi_stage',
        'rad_total_penalty_all', # summary of penalty for all radiance 
                                # observation types
        'rad_total_qcpenalty_all', # summary of qcpenalty for all radiance                             # observation types
        'rad_total_failed_nonlinqc' # summary of observations removed by 
                                    # nonlinear qc for all radiance observation
                                    # types
    ]
)

@dataclass
class RadianceDataConfig(ConfigInterface):

    config_data: dict = field(default_factory=dict)

    def __post_init__(self):
        self.set_config()

    def set_config(self):
        """ function to set configuration variables from given dictionary
        """
        self.harvest_filename = self.config_data.get('filename')
        self.set_data_types()
    
    def set_data_types(self):
        self.data_to_harvest = self.config_data.get('data_types')
        for data_type in self.data_to_harvest:
            if data_type not in VALID_DATA_TYPES:
                msg = (f"{data_type} is not a supported data "
                       "type to harvest from the gsistats file. "
                       "Please reconfigure the input dictionary using only the "
                       f"following data types: {VALID_DATA_TYPES}")
                raise KeyError(msg)

@dataclass
class RadianceDataHv(object):
    """Harvester dataclass used to parse gsistats file
    
    Parameters:
    -----------
    config: RadianceDataConfig object containing information used to determine 
    which data to extract from the gsistats file
    
    Methods:
    --------
    get_data: calls parse_fit_file()
    
    returns a list of tuples containing specific data
    """
    config: RadianceDataConfig = field(default_factory=RadianceDataConfig)

    def get_data(self):
        """Read the fit file (from gsistats)
        """
        self.channels = list()
        self.channel_stats = list()
        self.observation_type = list()
        self.radiance_totals = list()
        self.observation_type_summary = list()
        
        with open(self.config.harvest_filename, encoding="utf-8") as f:
            self.lines = list(f)
            
        self.parse_fit_file()
        
        harvested_data = dict()
        for data_type in self.config.data_to_harvest:
            if data_type == 'satinfo_channels':
                harvested_data[data_type] = self.channels
            elif data_type == 'channel_stats':
                harvested_data[data_type] = self.channel_stats
            elif data_type == 'radiance_observation_types':
                harvested_data[data_type] = self.observation_type
            elif data_type == 'observation_type_summary':
                harvested_data[data_type] = self.observation_type_summary
            elif data_type == 'observation_totals':
                harvested_data == self.radiance_totals
        
        return harvested_data
        
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
                """harvest satinfo content
                """
                channel_index = int(line_parts[0]) - 1
                
                line2list = line.split('=')
                self.channels.append(SatinfoChannel(
                                           'cycletime',
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
                """harvest bias correction coeficients
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
                self.channel_stats.append(SatinfoChannelStats(
                    'cycletime',
                    self.gsi_stage,
                    int(line_parts[0]),
                    int(line_parts[1]),
                    line_parts[2],
                    int(line_parts[3]),
                    int(line_parts[4]),
                    float(line_parts[5]),
                    float(line_parts[6]),
                    float(line_parts[7]),
                    float(line_parts[8]),
                    float(line_parts[9]),
                    float(line_parts[10])
                ))
            
            if finalsummary_read and len(line_parts) == 12:
                """harvest final summary for each observation type
                """
                self.observation_type_summary.append(
                    RadianceObservationTypeSummary(
                        'cycletime',
                        self.gsi_stage,
                        f'{line_parts[0]} {line_parts[1]} {line_parts[2]} ',
                        line_parts[3],
                        line_parts[4],
                        int(line_parts[5]),
                        int(line_parts[6]),
                        int(line_parts[7]),
                        float(line_parts[8]),
                        float(line_parts[9]),
                        float(line_parts[10]),
                        float(line_parts[11]),
                    )
                )
            elif finalsummary_read:
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
                
                elif line_parts[0] == 'sat' and line_parts[1] == 'type':
                    """harvest radiance observation fit file statistics as a
                    function of observation type
                    """ 
                    self.get_observation_type_stats(line_number)
                    
                elif line_parts[0] == 'rad' and line_parts[2] == 'penalty_all=':
                    """harvest radiance observation fit file statistics for
                    all observation types
                    """
                    self.get_radiance_totals(line_number)
                    channelstats_read = True
                    
                elif line_parts[0] == 'it' and line_parts[1] == 'satellite':
                    """proceed with final summary for each observation type
                    """
                    channelstats_read = False
                    finalsummary_read = True
            
    def get_radiance_totals(self, header_line_number):
        """extract totals for all radiance observation types
        """
        line0_list = self.lines[header_line_number].split()
        line1_list = self.lines[header_line_number + 1].split()
        line2_list = self.lines[header_line_number + 2].split()
        
        self.radiance_totals.append(RadianceObservationTotals(
            'cycletime',
            self.gsi_stage,
            float(line0_list[3]),
            float(line1_list[3]),
            int(line2_list[4])
            )
        )           
                    
    def get_observation_type_stats(self, header_line_number):
        """extract radiance observation type statistics
        """
        line1_list = self.lines[header_line_number + 1].split()
        line3_list = self.lines[header_line_number + 3].split()
        
        qc1to7 = list()
        qc1to7.extend(map(int, line3_list[1:]))
        
        self.observation_type.append(RadianceObservationType(
            'cycletime',
            self.gsi_stage,
            line1_list[0],
            line1_list[1],
            float(line1_list[2]),
            int(line1_list[3]),
            int(line1_list[4]),
            int(line1_list[5]),
            int(line1_list[6]),
            int(line1_list[7]),
            int(line1_list[8]),
            int(line1_list[9]),
            float(line3_list[0]),
            qc1to7
            )
        )
#!/usr/bin/env python

"""Monitor the Gridpoint Statistical Interpolation (GSI) observation innovation
statistics: satellite radiance data
"""

import os
import warnings
from collections import namedtuple

import ipdb

N_BIAS_CORR_COEF = 12

SatinfoChannel = namedtuple(
    'SatinfoChannel', [
        'cycletime',
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
                                               
RadianceObservationType = namedtuple(
    'RadianceObservationType',
        ['cycletime',
         'sat', # satellite name
         'type', # instrument type
         'penalty', # contribution to cost function from this observation type
         'nobs', # number of good observations used in the assimilation
         'iland', # number of observations over land
         'isnoice', # number of observations over sea ice and snow
         'icoast', # number of observations over coast
         'ireduce', # number of observations that reduce qc bounds in tropics
         'ivarl', # number of observations removed by gross check
         'nlgross', # number of observations removed by nonlinear qc
         'qcpenalty', # nonlinear qc penalty from this data type
         'qc1to7' # number of observations whose quality control criteria has
                  # been adjusted by each qc method (1-7)
    ]
)
        
RadianceObservationTotal = namedtuple(
    'RadianceObservationTotal', [
        'cycletime',
        'rad_total_penalty_all', # summary of penalty for all radiance 
                                # observation types
        'rad_total_qcpenalty_all', # summary of qcpenalty for all radiance                             # observation types
        'rad_total_failed_nonlinqc' # summary of observations removed by 
                                    # nonlinear qc for all radiance observation
                                    # types
    ]
)

class RadianceDataFitFile(object):
    """
    """
    def __init__(self, fitfile):
        """Read the fit file
        """
        self.channels = list()
        self.observation_type = list()
        self.radiance_total = list()
        
        with open(fitfile, encoding="utf-8") as f:
            self.lines = list(f)
        
    def parse_fit_file(self):
        """ parse lines of fit file and extract statistics
        """
        radinfo_read1 = False
        radinfo_read2 = False
        for line_number, line in enumerate(self.lines):
            if radinfo_read1:
                """harvest satinfo content
                """
                channel_index = int(line.split()[0]) - 1
                
                line2list = line.split('=')
                self.channels.append(SatinfoChannel(
                                           'cycletime',
                                           line.split()[1],
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
                channel_index = int(line.split()[0]) - 1
                
                # partial assurance that this is the correct channel, by name
                assert line.split()[1] == self.channels[channel_index].name
                bias_corr_coef = line.split()[2:]
                
                try:
                    assert len(bias_corr_coef) == N_BIAS_CORR_COEF # there should always be 12 channels
                    self.channels[
                        channel_index].bias_correction_coefficients.extend(
                                                            map(float, 
                                                                bias_corr_coef))
                except AssertionError:
                    warnings.warn('cannot find exactly %d bias correction '
                                  'coefficients for %r \n'
                                  'returning this list of strings: %r' %
                                      (N_BIAS_CORR_COEF,
                                       self.channels[channel_index],
                                       bias_corr_coef))
                    self.channels[
                        channel_index].bias_correction_coefficients.extend(
                                                                 bias_corr_coef)
                                   
                if channel_index + 1 == self.nchannels:
                    """this is the last channel
                    """
                    radinfo_read2 = False
            
            if not radinfo_read1 and len(line.split()) > 2:
                """determine how to proceed based on the line
                """
                if (line.split()[0] == 'RADINFO_READ:' and line.split()[1] == 'jpch_rad='):
                    """ proceed with satinfo channel data
                    """
                    radinfo_read1 = True
                    self.nchannels = int(line.split()[2])
                
                elif (line.split()[0] == 'RADINFO_READ:' and line.split()[1] == 'guess'):
                    """proceed with bias correction coefficients
                    """
                    radinfo_read2 = True
                
                elif line.split()[0] == 'sat' and line.split()[1] == 'type':
                    """harvest radiance observation fit file statistics
                    """
                    self.get_observation_type_stats(line_number)
                    
                    
    def get_observation_type_stats(self, header_line_number):
        """extract radiance observation type statistics
        """
        line1_list = self.lines[header_line_number + 1].split()
        line3_list = self.lines[header_line_number + 3].split()
        
        qc1to7 = list()
        qc1to7.extend(map(int, line3_list[1:]))
        
        self.observation_type.append(RadianceObservationType(
            'cycletime',
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

def run(radiance_data_fit_file = os.path.join('data_clean', 
                                              'gsistats.1979032100_control')):
    """
    """
    gsistats = RadianceDataFitFile(radiance_data_fit_file)
    gsistats.parse_fit_file()
    ipdb.set_trace()

def main():
    run()

if __name__=='__main__':
    main()
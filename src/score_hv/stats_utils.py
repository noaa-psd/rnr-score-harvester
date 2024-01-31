"""
Copyright 2022 NOAA
All rights reserved.

Collection of methods to calculate statistics requested
in the tests for daily_bfg.py.
"""
import sys,os
import numpy as np
import xarray as xr
from datetime import datetime
import pytest
import pdb
from netCDF4 import Dataset
from pathlib import Path
"""
  The class var_stats calculates statistics for the requested 
  variables that are needed for the tests of the havesters.
  """

class var_stats:
    def __init__(self):
        self.temporal_means        = []
        self.weighted_averages     = []

    def calculate_var_means(self,var_data,gridcell_area_data):  
        """This function calculates a temporal mean and a 
           weighted mean for the variable data passed in from
           the calling function.. 
           Parameters:
           var_data           : the variable data in an array 
                                opened with xarray in the calling 
                                routine.  
           gridcell_area_data : the gridcell data from the data file
                                bfg_control_1536x768_20231116.nc. 
                                Located in the data area of score-hv.
           Return             : Nothing is returned.                     
           """
        gridcell_area_weights = gridcell_area_data.variables['area']   
        value = np.ma.masked_invalid(var_data.mean(dim='time',skipna=True))
        self.temporal_means.append(value)
        wght_mean, sumweights = np.ma.average(value,
                                              weights=gridcell_area_weights,
                                              returned=True)
        self.weighted_averages.append(wght_mean)
        assert sumweights >= 0.999 * 4. * np.pi
        assert sumweights <= 1.001 * 4. * np.pi

    def calculate_var_variance(self,num_vars,gridcell_area_data):
        """This function calculates the variance of the requested variables
           Parameters:
           num_vars           : the number of requested variables.
           gridcell_area_data : the gridcell data from the data file
                                bfg_control_1536x768_20231116.nc. 
                                Located in the data area of score-hv.
           Return             : The variances of the number of requested 
                                variables is returned. 
           """
        norm_weights = gridcell_area_data.variables['area'][:] / np.sum(
                                        gridcell_area_data.variables['area'][:]) 
        variances = [] 
        for ivar in range(0,num_vars):
            temporal_means_array  = np.array(self.temporal_means[ivar])
            weighted_ave          = self.weighted_averages[ivar]
            value = -weighted_ave**2 + np.ma.sum( temporal_means_array**2 * norm_weights)
            variances.append(value)
        return(variances)

    def get_weighted_averages(self):
        """
          This function returns the weighted averages calculated in
          the function calculate_var_means above.
          """
        return(self.weighted_averages)

    def get_minimum_values(self,num_vars):
        """
          This function calculates the minimum values of the required 
          variables. The temporal_means is calculated in the calculate_var_means
          function in this file.
          Parameters:
          num_vars : The number of requested variables.
          Return   : The minimum values.
          """
        min_values = []
        for ivar in range(0,num_vars):
            temporal_means_array = np.array(self.temporal_means[ivar])
            min_values.append(np.ma.min(temporal_means_array))
        return(min_values)    

    def get_maximum_values(self,num_vars):
        """
          This function calculates the maximum values of the required
          variables. The temporal_means is calculated in the calculate_var_means
          function in this file.
          Parameters:
          num_vars : The number of requested variables.
          Return   : The minimum values.
          """
        max_values = []
        for ivar in range(0,num_vars):
            temporal_means_array = np.array(self.temporal_means[ivar])
            max_values.append(np.ma.max(temporal_means_array))
        return(max_values)


"""
Copyright 2024 NOAA
All rights reserved.

Methods to calculate gridcell area weighted statistics
The functions generally take the following two input variables:
    xarray_variable - xarray variable data
    gridcell_area_data - xarray variable containing gridcell areas, in the
    same shape as xarray_variable
"""
import sys,os
import numpy as np
import pytest
import pdb
from netCDF4 import Dataset
from pathlib import Path

class VarStatsCatalog :
    """
      This allows for the instantiation of the var_stats class.  The 
      requested list of statistics that the user wants is passed into this
      method and is used in the calculate_requested_statistics method
      below to calculate the desired statistics.
      """
    def __init__(self,stats_list):
        self.weighted_averages=[]
        self.variances=[]
        self.minimum=[]
        self.maximum=[]
        self.stats=stats_list
   
    def calculate_requested_statistics(self,gridcell_area_weights,temporal_mean):
        """This function calls the methods to calculate the statistics
           requested by the user.  
           gridcell_area_weights:the gridcell weights are from the data file
                                 bfg_control_1536x768_20231116.nc.
                                 Located in the data area of score-hv.
           temporal_mean:the temporal means array that is calculated in
                         the calling function.                      
           Return:Nothing is returned.
           """
        for stat in self.stats:
            if stat=="mean":
               self.calculate_weighted_average(gridcell_area_weights,temporal_mean) 
            if stat=='variance':
               self.calculate_var_variance(gridcell_area_weights,temporal_mean) 
            if stat=='minimum':
               self.find_minimum_value(temporal_mean)               
            if stat=='maximum':
               self.find_maximum_value(temporal_mean)

    def calculate_weighted_average(self,gridcell_area_weights,temporal_mean):
        """This function calculates a weighted average  
           for the variable data passed in from
           the calling function calcuate_requested_statistics. 
           Parameters:
           gridcell_area_weights:the gridcell weights are from the data file
                                 bfg_control_1536x768_20231116.nc. 
                                 Located in the data area of score-hv.
           temporal_mean:the temporal means array that is calculated in
                         the calling function.
           """
        value = np.ma.average(temporal_mean,weights=gridcell_area_weights)
        self.weighted_averages.append(value)

    def calculate_var_variance(self,gridcell_area_weights,temporal_mean):
        """
          This function returns the gridcell weighted variance of the requested variables using
          the following formula:
          variance = sum_R{ w_i * (x_i - xbar)^2 },
          where sum_R represents the summation for each value x_i over the region of 
          interest R with normalized gridcell area weights w_i and weighted mean xbar
          Parameters:
          gridcell_area_weights:the gridcell weights are from the data file
                                 bfg_control_1536x768_20231116.nc.
                                 Located in the data area of score-hv.
           temporal_mean:the temporal means array that is calculated in
                         the calling function. 
          """
        norm_weights = gridcell_area_weights/np.sum(gridcell_area_weights)
        
        weighted_average = np.ma.average(temporal_mean,weights=gridcell_area_weights)
        temporal_means_array = np.array(temporal_mean)
        value=-weighted_average**2 + np.ma.sum( temporal_means_array**2 * norm_weights)
        self.variances.append(value)

    def find_minimum_value(self,temporal_mean):
        """
          This function finds the minimum values of the temporal_means array 
          Parameters:
          temporal_means:The array of means for the requested variable that
                          is calculated in the calling script.
          Return:Nothing is returned.
          """
        temporal_means_array=np.array(temporal_mean)
        self.minimum.append(np.ma.min(temporal_means_array))

    def find_maximum_value(self,temporal_mean):
        """
          This function finds the maximum value of the temporal_means array. 
          Parameters:
          temporal_means:The array of means for the requested variable that is
                         calcuated in the calling script.
          Return:Nothing is returned.
          """
        temporal_means_array=np.array(temporal_mean)
        self.maximum.append(np.ma.max(temporal_means_array))


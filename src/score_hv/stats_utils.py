"""
Copyright 2024 NOAA
All rights reserved.

Collection of methods to calculate statistics requested.
"""
import sys,os
import numpy as np
import pytest
import pdb
from netCDF4 import Dataset
from pathlib import Path

class var_stats:
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
   
    def calculate_requested_statistics(self,var_data,gridcell_area_weights):
        """This function calls the methods to calculate the statistics
           requested by the user.  The calculated statistics are stored
           in the class and retrieved by the "get" methods below.
           Parameters:
           var_data:the variable data in an array
                    opened with xarray in the calling
                    routine.

           gridcell_area_weights:the gridcell weights are from the data file
                                 bfg_control_1536x768_20231116.nc.
                                 Located in the data area of score-hv.

           Return:Nothing is returned.
           """
        temporal_means=[]
        for stat in self.stats:
            if stat=='mean':
               temporal_means,weighted_average=self.calculate_var_means(var_data,gridcell_area_weights) 
            if stat=='variance':
               self.calculate_var_variance(gridcell_area_weights,temporal_means,weighted_average) 
            if stat=='minimum':
               self.find_minimum_value(temporal_means)               
            if stat=='maximum':
               self.find_maximum_value(temporal_means)

    def calculate_var_means(self,var_data,gridcell_area_weights):
        """This function calculates a temporal mean and a 
           weighted mean for the variable data passed in from
           the calling function calcuate_requested_statistics. 
           Parameters:
           var_data:the variable data in an array 
                    opened with xarray. 
                                
           gridcell_area_weights : the gridcell weights are from the data file
                                bfg_control_1536x768_20231116.nc. 
                                Located in the data area of score-hv.

           Return:temporal_means
                  weighted_means
           """
        value=np.ma.masked_invalid(var_data.mean(dim='time',skipna=True))
        temporal_means=value
        weighted_average=np.ma.average(value,weights=gridcell_area_weights)
        self.weighted_averages.append(weighted_average)
        return temporal_means,weighted_average

    def calculate_var_variance(self,gridcell_area_weights,temporal_means,weighted_average):
        """This function calculates the variance of the requested variables
           Parameters:
           gridcell_area_weights:the gridcell weights are from the data file
                                bfg_control_1536x768_20231116.nc.
                                Located in the data area of score-hv.
           Return:Nothing is returned.
           """
        norm_weights=gridcell_area_weights/np.sum(gridcell_area_weights)

        temporal_means_array=np.array(temporal_means)
        value=-weighted_average**2 + np.ma.sum( temporal_means_array**2 * norm_weights)
        self.variances.append(value)

    def find_minimum_value(self,temporal_means):
        """
          This function finds the minimum values of the temporal_means array 
          Parameters:
          temporal_means:The array of means for the requested variable.
          Return:Nothing is returned.
          """
        temporal_means_array=np.array(temporal_means)
        self.minimum.append(np.ma.min(temporal_means_array))

    def find_maximum_value(self,temporal_means):
        """
          This function finds the maximum value of the temporal_means array. 
          Parameters:
          temporal_means:The array of means for the requested variable.
          Return:Nothing is returned.
          """
        temporal_means_array=np.array(temporal_means)
        self.maximum.append(np.ma.max(temporal_means_array))

    """
      The following are methods to return the statistics
      that are calculated above.
      """
    def get_weighted_averages(self,index):
        """
          Parameters:
          index:The index into to weighted_averages list.
          Return:The weighted_average value cooresponding to
                 the index requested by the calling function. 
          """     
        return(self.weighted_averages[index])

    def get_variance(self,index):
        return(self.variances[index])

    def get_minimum(self,index):
        return(self.minimum[index])

    def get_maximum(self,index):
        return(self.maximum[index])

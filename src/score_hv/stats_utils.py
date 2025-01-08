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
import xarray as xr
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
    def __init__(self,stats_list,user_regions):
        self.weighted_averages=[]
        self.variances=[]
        self.minimum=[]
        self.maximum=[]
        self.regions=user_regions #this is a dictionary of user requested regions.
        self.stats=stats_list
        
    def clear_requested_statistics(self):
        self.weighted_averages=[]
        self.variances=[]
        self.minimum=[]
        self.maximum=[]

    def calculate_requested_statistics(self,weights,temporal_means,region_name):
        """This function calls the methods to calculate the statistics
           requested by the user. If the weights and/or temporal_means
           arrays come in as xr.DataArrays, we convert the weights and 
           temporal_means arrays to NumPy arrays for the 
           calculations.
           Parameters:
           weights: The weights are the normalized weights
                    based on the solid angle calculation in the 
                    calling routine. 
           temporal_means:The temporal means array that is calculated in
                         the calling function.                      
           region_name: The name of the region that the statistics will be
                        calculated for.  The region_name is a key for the 
                        regions dictionary.
           Return:Nothing is returned.
           """

        if isinstance(weights,xr.DataArray): 
           weights = weights.values 
        if isinstance(temporal_means , xr.DataArray):
           temporal_means = temporal_means.values
        
        wanted_region = self.regions.get(region_name)
        for stat in self.stats:
            if stat=="mean":
               wanted_region[stat] = self.calculate_weighted_average(weights,temporal_means) 
            if stat=='variance':
               wanted_region[stat] = self.calculate_var_variance(weights,temporal_means) 
            if stat=='minimum':
               wanted_region[stat] = self.find_minimum_value(temporal_means)               
            if stat=='maximum':
               wanted_region[stat] = self.find_maximum_value(temporal_means)


    def calculate_weighted_average(self,weights,temporal_means):
        """This method calculates a weighted average  
           for the variable data passed in from
           the calling function calcuate_requested_statistics. 
           Parameters:
           normalized_weights: The weights are read from the a weights file in the 
                               calling routine. This is a NumPy array.
           temporal_means:the temporal means array that is calculated in
                         the calling function. This is a NumPy array.
           return: None: The result is appended to self.weighted_averages.              
           """
        weights = weights.mean(axis=0)    
        spatial_weighted_sum = np.nansum(weights * temporal_means)
        total_weight = np.nansum(weights)
        value  = spatial_weighted_sum / total_weight if total_weight != 0 else np.nan
        self.weighted_averages.append(value)
        return(value)
    
    def calculate_var_variance(self,weights,temporal_means):
        """
          This method returns the gridcell weighted variance of the requested variables using
          the following formula:
          variance = sum_R( w_i * (x_i - xbar)^2 ),
          where sum_R represents the summation for each value x_i over the region of 
          interest R with normalized gridcell area weights w_i and weighted mean xbar
          Parameters:
          weights: The weights are the normalized weights
                   based on the solid angle calculation in the 
                   calling routine. 
           temporal_means:the temporal means array that is calculated in
                         the calling function. 
          """
        weights = weights.mean(axis=0)   
        # Ensure the weights and temporal_mean have compatible shapes
        try:
            assert weights.shape == temporal_means.shape
        except AssertionError:
           msg = f'Assertion failed: The shape of the weights array {weights.shape}' \
                 f'is not equal to the shape of the temporal mean array {temporal_means.shape}'
           raise ValueError(msg)

        # Calculate the weighted mean (xbar) for the two-dimensional array
        weighted_sum = np.nansum(weights * temporal_means)
        sum_of_weights = np.nansum(weights)
        weighted_average = weighted_sum / sum_of_weights
        value = np.nansum(weights * (temporal_means - weighted_average) ** 2) / sum_of_weights 
        self.variances.append(value)
        return(value)
        
    def find_minimum_value(self,temporal_means):
        """
          This method finds the minimum values of the temporal_means array 
          Parameters:
          temporal_means:The array of means for the requested variable that
                          is calculated in the calling script.
          Return:Nothing is returned.
          """
        self.minimum.append(np.nanmin(temporal_means))
        value = np.nanmin(temporal_means)
        return(value)

    def find_maximum_value(self,temporal_means):
        """
          This method finds the maximum value of the temporal_means array. 
          Parameters:
          temporal_means:The array of means for the requested variable that is
                         calcuated in the calling script.
          Return:Nothing is returned.
          """
        self.maximum.append(np.nanmax(temporal_means))
        value = np.nanmax(temporal_means)
        return(value)



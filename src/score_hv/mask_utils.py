"""
Copyright 2024 NOAA
All rights reserved.

Collection of methods to work with masking of user requested variables
"""
import sys,os
import numpy as np
import xarray as xr
import pytest
import pdb

VALID_MASKS = ['land','ocean','sea', 'ice']

class MaskCatalog:
    def __init__(self,user_mask_value,soil_type_values):
        """
          Here we initalize the MaskCatalog class.
          """
        self.name = None 
        self.user_mask = user_mask_value
        """The variable name on the data set
           that is used for masking is "sotyp".
           The sotyp array values are passed in from the
           calling routine where it is read from
           the data set.
           ocean = sotyp has vaues of 0
           sea   = sotyp has values of 0
           ice   = sotyp has values of 16
           land  = sotyp has values between ocean and ice.
           """
        self.data_mask = soil_type_values 

    def initial_mask_of_variable(self,var_name,variable_data):
        """
          This method does the initial masking special variables.
          The land variables that are masked initially are:
          soill4,soilm,soilt4 and tg3. 
          It uses the sotyp(soil type) variable in the data set.
          Parameters:
          var_name - The variable name.
          varaiable_data - The initial variable data with no masking.
          return - The variable data is returned with the ocean and ice
                   values set to missing.
          """
        
        self.name = var_name 
        """
          The values of 0 and 16 in the sotyp variable are used to delete values
          over ocean and ice.
          """
        masked_data = variable_data.where((self.data_mask != 0) & (self.data_mask != 16))
        return(masked_data)

    def replace_bad_values_with_nan(self,variable_data):
        """
          Check for _FillValue or missing_values in the variable data.
          This method will replace the missing or fill values with 
          NaN.
          Parameters;
          variable_data - The variable field data. Variable_data is of
                          type class 'xarray.core.dataarray.DataArray.
          Return - The variable field data with NaN's for where the 
                   grid values are missing or fill values. The returned
                   masked_variable_data is of type 
                   class 'xarray.core.dataarray.DataArray.
          """         
        fill_value = variable_data.encoding.get('_FillValue', None)
        missing_value = variable_data.encoding.get('missing_value', None)
     
        """
          Create a combined mask for fill_values,missing_value and non
          finite values. 
          """
        if fill_value is not None and missing_value is not None:
           mask = (variable_data != fill_value) & (variable_data != missing_value)
        elif fill_value is not None:
           mask = variable_data != fill_value
        elif missing_value is not None:
           mask = variable_data != missing_value
        else:
           mask = np.isfinite(variable_data)

       # Apply the mask
        masked_variable = variable_data.where(mask,np.nan)
        return(masked_variable)

        
    def user_mask_array(self,region_mask):
        """
         The user has requested a mask. Here we keep only the
         type of data that the user wants.  
         Parameters: 
         region_mask - This is the sotyp variable read in from the
                       bfg data file.   
         Return - The mask array is returned.  This will contain
                  boolean values. True for grid points we want and False
                  for grid points we do not want.
         """
        if 'land' in self.user_mask:
            masked_array = ~region_mask.isin([0, 16])
        return(masked_array)    
      

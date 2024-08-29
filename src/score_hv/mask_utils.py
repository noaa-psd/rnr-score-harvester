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

class MaskCatalog:
    def __init__(self,soil_type_variable):
        """
          Here we initalize the MaskCatalog class.
          """
        self.name = None
        self.data_mask = soil_type_variable

    def mask_variable(self,var_name,variable_data,dataset):
        """
          This method does the initial masking of special 
          variables. These variables are automatically masked.
          land soil variables = soill4,soilm,soilt4 and tg3 
          ocean,ice,atmos. 
          It uses the sotyp(soil type) variable in the data set.
          """
        self.name = var_name 
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

#     def apply_user_mask(self,iregion)
        


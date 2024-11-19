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

VARIABLES_TO_MASK = ['icetk','nsst','snod','soilm','soilt4','sst','tg3','tsnowp','weasd']
VALID_MASKS = ['none','land','water', 'ice']

class MaskCatalog:
    def __init__(self):
        """
          Here we initalize the MaskCatalog class.
          """
        pass 

    def check_variable_to_mask(self,var_name):
        """
          This method check to see if the variable the user has 
          requested is in the above VARIABLES_TO_MASK list.  If 
          it is the method returns true, if not the method returns false.
          """
        return var_name in VARIABLES_TO_MASK

    def initial_mask_variable(self,var_name,variable_data,fraction_data,weights,sotyp_data):
        """
          This method does the masking of the variables requested by the user.
          There are some variables that are always masked. 
          The variables that are always masked:
              soil variables: soill4,soilm and tg3.
              snow variables: snod,tsnowp,weasd
              ice variables: icetk
              sea_surface_temp: sst and nsst
          The sotyp(soil type) is the main variable in the data set used for
          maksing..
          Parameters:
          var_name - The variable name.
          varaiable_data - The initial variable data by region with no masking.
          fraction_data - This is the surface ice concentration variable(lcec) for
                          icetk(ice thinkness) or land fraction variable(lfrac)
                          for all other variables. By region.
          weights - The gridcell area weights with no masking. 
                                  The gridcell area weights do not have a 
                                  time dimension.  They are (grid_yt,grid_xt)
          sotyp_data - The sotyp variale from the data set that is by region.                        
          return - The variable data is returned with the unwanted grid cell
                   data deleted. The fraction variable is returned with the
                   variable data.
                   For the soil_snow_variables and the sst_variables the 
                   land fraction(lfrac) is returned.
                   For the ice_variables the ice fraction(icec) is returned.
                   The masked gridcell_area_weights are returned after masking.
          """
       
        soil_snow_variables = ['soilt4','soilm','snod','tg3','tsnowp', 'weasd']
        ice_variables = ['icetk']
        sst_variables = ['sst','nsst']
        print("the var name ",var_name)
        if var_name in soil_snow_variables:        
           """
             We will need the sotyp(soil type) variable from the dataset.
             The values of 0 and 16 in the sotyp variable are used to delete values
             over water and ice. This is used specifically for the 
             soil_snow variables: soilm,soilt4,tg3,snod and weasd. We also need
             the land fraction or the ice fraction variable depending on what
             variable the user has requested.
             """
           masked_variable = variable_data.where((sotyp_data != 0) & (sotyp_data != 16),drop=False)
           masked_fraction = fraction_data.where((sotyp_data != 0) & (sotyp_data != 16), drop=False)
           masked_weights  = weights.where((sotyp_data != 0) & (sotyp_data != 16), drop=False)
        
        elif var_name in ice_variables:
           print("in ice variables ",weights.shape)
           """
             The ice thikness variable has 0 everwhere except where there is ice.
             """
           masked_variable = variable_data  
           masked_weights =  weights.where(sotyp_data !=16,False,drop=False)
           masked_fraction = fraction_data

        elif var_name in sst_variables:
           print("Variable is a sea surface variable")
           if var_name == "sst":
              """
                For the sst(tmpsfc) variable we use the sotyp data and keep the
                values that are over the water. 
                """
              masked_variable = variable_data.where(sotyp_data == 0,False)
              masked_weights = weights.where(sotyp_data == 0,False)
              """
                This line replaces the lfrac values over the water where they are 0 with 1.  Then
                it subtracts the lfrac values that are between 0 and 1 from 1 to get the fraction
                of the land that is over the water.
                """
              masked_fraction = xr.where(fraction_data == 0, 1, xr.where(fraction_data == 1, 0, 1 - fraction_data))
           elif var_name == "nsst":
              masked_variable = variable_data.where(sotyp_data == 0,False)
              masked_weights  = weights.where(sotyp_data == 0,False)
              masked_fraction = xr.where(fraction_data == 0, 1, xr.where(fraction_data == 1, 0, 1 - fraction_data))
           else:
             raise KeyError(f"Variable is not in VARIABLES_TO_MASK list: {var_name}")
             sys.exit(1) 

        valid_variable_data = masked_variable.where(~masked_variable.isnull(),other=np.nan)
        valid_fraction_data = masked_fraction.where(~masked_fraction.isnull())
        return(valid_variable_data,valid_fraction_data,masked_weights)

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

    def user_mask(self,mask_type,variable_data,fraction_data,weights,sotyp_data):
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
        if mask_type == 'land':
            print("land")
            masked_variable = variable_data.where((sotyp_data != 0) & (sotyp_data != 16),drop=False)
            masked_fraction = fraction_data.where((sotyp_data != 0) & (sotyp_data != 16),drop=False)
            masked_weights  = weights.where((sotyp_data != 0) & (sotyp_data != 16),drop=False)
        
        elif mask_type == 'water':
            print("water")
            masked_variable = variable_data.where(sotyp_data == 0,False)
            masked_weights = weights.where(sotyp_data == 0,False)
            """
              This line replaces the lfrac values over the water where they are 0 with 1.  Then
              it subtracts the lfrac values that are between 0 and 1 from 1 to get the fraction
              of the land that is over water..
              """
            masked_fraction = xr.where(fraction_data == 0, 1, xr.where(fraction_data == 1, 0, 1 - fraction_data))

        elif mask_type == 'ice':
             print("ice")
             masked_variable = variable_data.where(sotyp_data == 16,False,drop=False)
             masked_weights = weights.where(sotyp_data == 16,False,drop=False)
             masked_fraction = fraction_data.where(sotyp_data == 16,False,drop=False)

        valid_variable_data = masked_variable.where(~masked_variable.isnull(),other=np.nan)
        valid_fraction_data = masked_fraction.where(~masked_fraction.isnull())
        return(valid_variable_data,valid_fraction_data,masked_weights)
     
    def check_surface_mask(self,user_surface_mask):
        print("in check surface mask")
        for mask in user_surface_mask:
            if mask not in VALID_MASKS:
               print(mask)
               msg = f'The mask: {mask} is not a supported mask. ' \
                     f'Valid masks are: "none, land, water, ice.'
               raise ValueError(msg)

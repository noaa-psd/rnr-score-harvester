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


class VarUtilsCatalog:
    def __init__(self,dataset):
        """
          Here we initalize the VariableUtils class. It
          is initialized with the entire data set opened in
          the calling routine with xarray.
          """
        self.dataset = dataset  
        self.dataset_variable_names = list(dataset.data_vars.keys())


    def check_variable_exists(self,var_name):
        """
          Checks if a field exists in the xarray dataset. If
          the variable does not exist we exit with a message giving
          the missing variable name.
          Parameters:
          var_name: The name of the variable to check for.
          dataset_variable_names: A list of variables names that are 
                              in the input dataset.
          """
        if var_name not in self.dataset_variable_names:
            raise KeyError(f"Missing required field in the dataset: {var_name}")
            sys.exit(1)

    def extract_variable_info(self,var_name):
        """
          This method reads the Netcdf data set opened in the calling routine
          and returns the variable data, the long name and the untits.  It checkes
          for special variable names that need to special processing.
          """
        if var_name == "netef_ave":
           variable_data = self.calculate_surface_energy_balance()
           longname = "surface energy balance"
           units = "W/m**2"
        elif var_name == "netrf_avetoa":
             variable_data = self.calculate_toa_radative_flux()
             longname = "Top of atmosphere net radiative flux"
             units = "W/m**2"
        elif var_name == 'sst':
             variable_data = self.get_sst()
             longname = 'sea surface temperature'
             units = 'K'
        elif var_name == 'nsst':
             variable_data = self.get_nsst()
             longname = 'near sea surface temperature'
             units = 'K'
        else:
             self.check_variable_exists(var_name)
             variable_data = self.dataset[var_name]
             if 'long_name' in variable_data.attrs:
                 longname=variable_data.attrs['long_name']
             else:
                 longname="None"
             if 'units' in variable_data.attrs:
                 units=variable_data.attrs['units']
             else:
                   units="None"
        return(variable_data,longname,units)


    def calculate_surface_energy_balance(self):
       """
         This method calculates the derived variable netef_ave.
         The required fields are:
         dswrf_ave : averaged surface downward shortwave flux
         dlwrf_ave : surface downward longwave flux
         ulwrf_ave : surface upward longwave flux
         uswrf_ave : averaged surface upward shortwave flux
         shtfl_ave : surface sensible heat flux
         lhtfl_ave : surface latent heat flux
         netef_ave = dswrf_ave + dlwrf_ave - ulwrf_ave - uswrf_ave - shtfl_ave - lhtfl_ave
         This method uses the dataset that is passed in when the class is
         instantiated in the calling routine.
         Return - The calculated surface energy balance variable.
         """
       required_variables = ['dswrf_ave', 'dlwrf_ave', 'ulwrf_ave', 'uswrf_ave', 'shtfl_ave', 'lhtfl_ave']
       for var_name in required_variables:
           self.check_variable_exists(var_name)

       dswrf = self.dataset['dswrf_ave']
       dlwrf = self.dataset['dlwrf_ave']
       ulwrf = self.dataset['ulwrf_ave']
       uswrf = self.dataset['uswrf_ave']
       shtfl = self.dataset['shtfl_ave']
       lhtfl = self.dataset['lhtfl_ave']
       netef_ave_data = dswrf + dlwrf - ulwrf - uswrf - shtfl - lhtfl
       return(netef_ave_data)

    def calculate_toa_radative_flux(self):
        """
          This method calculates the derived variable netef_ave.
          The variable name netrf_avetoa referes to the top of the
          atmosphere (TOA) net radiative energy flux.
          The required fields are:
          dswrf_avetoa:averaged surface downward shortwave flux
          uswrf_avetoa:averaged surface upward shortwave flux
          ulwrf_avetoa:surface upward longwave flux
          netrf_avetoa = dswrf_avetoa - uswrf_avetoa - ulwrf_avetoa
          Return - The calculated the top of atmosphere radiative energy flux.         
          """
        required_variables = ['dswrf_avetoa', 'uswrf_avetoa', 'ulwrf_avetoa']
        for var_name in required_variables:
            self.check_variable_exists(var_name)

        dswrf = self.dataset['dswrf_avetoa']
        uswrf = self.dataset['uswrf_avetoa']
        ulwrf = self.dataset['ulwrf_avetoa']
        netrf_avetoa = dswrf - uswrf - ulwrf
        netrf_avetoa.attrs = dswrf.attrs 
        return(netrf_avetoa)

    def get_sst(self):
        """
          This method reads the tmpsfc from the dataset.
          """
        sst_name = 'tmpsfc'  
        self.check_variable_exists(sst_name)
        sst = self.dataset[sst_name]
        return(sst)

    def get_nsst(self):
        nsst_name = 'tref'
        print("getting tref")
        self.check_variable_exists(nsst_name)
        nsst = self.dataset[nsst_name]
        return(nsst)

    def get_soil_type_data(self):
        """
          Most all of the variables will need to soil type data if the 
          users has requested a mask.  We only need the first time.
          """
        self.check_variable_exists('sotyp')
        soil_type_data = self.dataset['sotyp']
        return(soil_type_data)

    def get_fraction_data(self,var_name):
        """
          Get the ice fraction concentration for the ice thickness variable(icetk).
          Get the land fraction for all other variables.
          The dimension of the icec and lfrac is (time, grid_yt, grid_xt).
          The dimension of the gridcell_area_weights is (grid_yt, grid_xt).
          We need to git rid of the time dimension in the fraction variables
          in order to multiply them together when finding the sum of the grid
          So the dimensions of the fraction_data will be grid_yt, grid_xt.
          """
        if var_name == 'icetk':
           self.check_variable_exists('icec')
           fraction_data = self.dataset['icec']
        else:
           self.check_variable_exists('lfrac')
           fraction_data = self.dataset['lfrac']
        return(fraction_data)

import xarray as xr

# Open the NetCDF files
ds1 = xr.open_dataset('bfg_1994010100_fhr09_prateb_control.nc')
ds2 = xr.open_dataset('bfg_1994010100_fhr09_soil4_control.nc')

# Concatenate along a specified dimension (e.g., time)
ds_combined = xr.concat([ds1, ds2], dim='time')

# Save the concatenated dataset to a new NetCDF file
ds_combined.to_netcdf('combined_file.nc')

# Close the datasets
ds1.close()
ds2.close()

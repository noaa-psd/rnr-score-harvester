import xarray as xr
import glob
import shutil

file_pattern = 'bfg_*.nc'

# Get a list of file paths that match the pattern
file_paths = glob.glob(file_pattern)

# Loop through each file
for file_path in file_paths:
    print(file_path)
    # Open the dataset
    ds = xr.open_dataset(file_path, decode_times=False)

    # Check and modify the 'calendar' attribute
    if 'calendar' in ds['time'].attrs:
        print("we have calendar")
        del ds['time'].attrs['calendar']
    ds['time'].attrs['calendar'] = 'JULIAN'

    # Save the modified dataset to a new NetCDF file
    output_file = f'modified_{file_path}'
    ds.to_netcdf(output_file)

    # Close the dataset
    ds.close()


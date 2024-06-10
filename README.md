# score-hv/README.md
## Summary
Python package used to harvest metrics from reanalysis data.
This repositority is a standalone Python package that can be used as a part of
a larger workflow (e.g., with the score-db and score-monitoring repositories).

## Setup and installation
The repository can be downloaded using git:

`git clone https://github.com/NOAA-PSL/score-hv.git`

For testing and development, we recommend creating a new python environment 
(e.g., using [mamba](https://mamba.readthedocs.io/en/latest/index.html)). To 
install the required dependencies into a new environment using the micromamba 
command-line interface, run the following after installing mamba/micromamba:

`micromamba create -f environment.yml; micromamba activate score-hv-default-env`

Depending on your use case, install score-hv using one of three methods using 
(pip)[https://pip.pypa.io/en/stable/],

`pip install . # default installation into active environment`

`pip install -e . # editable installation into active enviroment, useful for development`

`pip install -t [TARGET_DIR] --upgrade . # target installation into TARGET_DIR, useful for deploying for cylc workflows (see https://cylc.github.io/cylc-doc/stable/html/tutorial/runtime/introduction.html#id3)`

Verify the installation by running the unit test suite. There are no expected test failures.

`pytest tests`

## Harvesting metric data with score-hv
score-hv takes in a yaml or dictionary which specifies the harvester to call, 
input data files and other inputs to the harvester (such as variables and
statistics to harvest)

For example, the following dictionary could be used to request the global, gridcell area weighted statistics for the temporally (in this case daily)
Weighted Netcdf gridcell area data.
A netcdf file containing area grid cell weights is required.  
This file should be included in the git hub repository with the down load 
of the harvester code.


Example input dictionary: 
```sh
{'harvester_name': 'daily_bfg',
    'filenames' : ['/filepath/tmp2m_bfg_2023032100_fhr09_control.nc',
                    '/filepath/tmp2m_bfg_2023032106_fhr06_control.nc',
                    '/filepath/tmp2m_bfg_2023032106_fhr09_control.nc',
                    '/filepath/tmp2m_bfg_2023032112_fhr06_control.nc',
                    '/filepath/tmp2m_bfg_2023032112_fhr09_control.nc',
                    '/filepath/tmp2m_bfg_2023032118_fhr06_control.nc',
                    '/filepath/tmp2m_bfg_2023032118_fhr09_control.nc',
                    '/filepath/tmp2m_bfg_2023032200_fhr06_control.nc']
```

A request dictionary must provide the harvester_name and filenames. Supported 
harester_name(s) are provided below, and each harvester may have additional 
input options or requirements. 

Required dictionary inputs: 'variable'

### daily_bfg
The daily_bfg python script contains the information that the user wants
returned.  It contains the following named tuple.
```sh
HarvestedData = namedtuple('HarvestedData', ['filenames',
                                             'statistics',
                                             'variable',
                                             'value',
                                             'units',
                                             'mediantime',
                                             'longname',
                                             'surface_mask', 
                                             'region'])
```

The example files names are listed above.

## Available Harvester statistics:
A list of statistics.  Valid statistics are ['mean', 'variance', 'minimum', 'maximum']

## Available Harvester variables:
```sh
VALID_VARIABLES  = (
                    'lhtfl_ave',# surface latent heat flux (W/m**2)
                    'shtfl_ave', # surface sensible heat flux (W/m**2)
                    'dlwrf_ave', # surface downward longwave flux (W/m**2)
                    'dswrf_ave', # averaged surface downward shortwave flux (W/m**2)
                    'ulwrf_ave', # surface upward longwave flux (W/m**2)
                    'uswrf_ave', # averaged surface upward shortwave flux (W/m**2)
                    'netrf_avetoa',#top of atmosphere net radiative flux (SW and LW) (W/m**2)
                    'netef_ave',#surface energy balance (W/m**2)
                    'prateb_ave', # surface precip rate (mm weq. s^-1)
                    'soil4', # liquid soil moisture at layer-4 (?)
                    'soilm', # total column soil moisture content (mm weq.)
                    'soilt4', # soil temperature unknown layer 4 (K)
                    'tg3', # deep soil temperature (K)
                    'tmp2m', # 2m (surface air) temperature (K)
                    'ulwrf_avetoa', # top of atmos upward longwave flux (W m^-2)
                    )
The variable netrf_avetoa is calculated from:
       dswrf_avetoa:averaged surface downward shortwave flux
       uswrf_avetoa:averaged surface upward shortwave flux
       ulwrf_avetoa:surface upward longwave flux
       Theses variables are found in the bfg control files.
       netrf_avetoa = dswrf_avetoa - uswrf_avetoa - ulwrf_avetoa

The variable netef_ave is calculated from:
       dswrf_ave : averaged surface downward shortwave flux
       dlwrf_ave : surface downward longwave flux
       ulwrf_ave : surface upward longwave flux
       uswrf_ave : averaged surface upward shortwave flux
       shtfl_ave : surface sensible heat flux
       lhtfl_ave : surface latent heat flux
       These variables are found in the bfg control files.
       netef_ave = dswrf_ave + dlwrf_ave - ulwrf_ave - uswrf_ave - shtfl_ave - lhtfl_ave
These variables will be updated as more harvesters are written.
```
Value:  The value entry of the harvested tuple contains the calculated value of valid 
        statistic that was requested by the user.
           
Units:  The units entry of the harvested tuple contains the untis associated with the
        requested variable from the BFG Netcdf file.  If no units were given on the 
        file then a value of None is returned.

Mediantime: The mediantime of the harvested tuple is calculated from the 
            endpoints of the variable time stamps on the BFG Netcdf file.

Longname: The long name entry of the harvested tuple is taken from the variable
          long name on the BFG Netcdf file.
```sh
Region: This entry of the harvested tuple is a nested dictionary. The region dictionary 
        contains the following information.
        regon name: this is a name given to the region by the user.  It is a required 
                    key word.
        latitude_range(min_latitude,max_latitude) 
        longitude range(east_lon,west_lon).
         The following nested dictionaries for region are accepted:
                    
              user name of region': {'latitude_range' : (min_lat,max_lat)}
              The user has not specified a longitude range.  The default will be applied. 
              default longitude is (360, 0)
              NOTE:  The longitude values on the bfg files are grid_xt : 0 to 359.7656 by 0.234375 degrees_E  circular

              'user name of region': {'longitude_range' : (min_lon,max_lon}
               The user has not specified a latitude_range.  The default will be applied.
               default latitude is (-90,90)
               NOTE:  The latitude values on the bfg files are grid_yt : 89.82071 to -89.82071 degrees_N
                    
               examples: 'region' : {
                                     'conus': {'latitude_range': (24.0, 49.0), 'longitude_range': (294.0, 235.0)},
                                     'western_hemis': 'longitude_range': (200,360)},
                                     'southern hemis': 'latitude_range': (20,-90)}
                                    }
                    
 ```                   
The daily_bfg.py file returns the following for each variable and statistic requested.
```sh
(HarvestedData(
                                      self.config.harvest_filenames,
                                       statistic, 
                                       variable,
                                       np.float32(value),
                                       units,
                                       dt.fromisoformat(median_cftime.isoformat()),
                                       longname,
                                       user_regions))
```
**Expected file format**: log

**Expected file format**: netcdf 

File format generated as bfg file

### innov_stats_netcdf
innovation statistics for temperature, spechumid, uvwind, and salinity 


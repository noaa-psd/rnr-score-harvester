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
averaged upwelling longwave radiation from the given netcdf files.
```sh
{'harvester_name': 'daily_bfg',
    'filenames' : ['/filepath/tmp2m_bfg_2023032100_fhr09_control.nc',
                    '/filepath/tmp2m_bfg_2023032106_fhr06_control.nc',
                    '/filepath/tmp2m_bfg_2023032106_fhr09_control.nc',
                    '/filepath/tmp2m_bfg_2023032112_fhr06_control.nc',
                    '/filepath/tmp2m_bfg_2023032112_fhr09_control.nc',
                    '/filepath/tmp2m_bfg_2023032118_fhr06_control.nc',
                    '/filepath/tmp2m_bfg_2023032118_fhr09_control.nc',
                    '/filepath/tmp2m_bfg_2023032200_fhr06_control.nc'],
    'statistic': ['mean','variance', 'minimum', 'maximum'],
    'variable': ['ulwrf_avetoa']}
```

A request dictionary must provide the harvester_name and filenames. Supported 
harester_name(s) are provided below, and each harvester may have additional 
input options or requirements. 

## Supported harvesters

### obs_info_log
observation information for pressure, specific humidity, temperature, height, wind components, precipitable h2o, and relative humidity

**Expected file format**: log 

File format generated from NCEPlibs cmpbqm command output 

Required dictionary inputs: 'variable'

Valid 'variable' options: 'Temperature', 'Pressure', 'Specific Humidity', 'Relative Humidity', 'Height', 'Wind Components', 'Precipitable H20' 

### inc_logs
increment descriptive statistics from log files

**Expected file format**: log

#TODO: add required dictionary inputs and options

### daily_bfg
Daily mean statistics from background forecast data 

**Expected file format**: netcdf 

File format generated as bfg file

#TODO: add required dictionary inputs and options

### innov_stats_netcdf
innovation statistics for temperature, spechumid, uvwind, and salinity 

**Expected file format**: netcdf 

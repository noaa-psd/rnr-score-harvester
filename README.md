# Score-HV 
Python package used to harvester data from provided files. 

This repositority is a standalone project but is also utilized as a part of the larger score-suite in conjunction with score-db and score-monitoring.

## Harvesting with score-hv
score-hv takes in a yaml or dictionary which specifies which harvester to use, files to harvest from, and if necessary details for that harvester of which specific data to harvest such as which variables. 

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
                    '/filepath/tmp2m_bfg_2023032200_fhr06_control.nc'],
    'statistic': ['mean','variance', 'minimum', 'maximum'],
    'variable': ['ulwrf_avetoa']}
```

All harvester calls must provide a harvester_name and filenames. The options for harester_name are the available harvesters below. Each harvester can have additional input options or requirements. 

## Available Harvesters

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
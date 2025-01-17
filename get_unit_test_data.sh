#!/bin/bash --posix
#The test data files for running the tests of the output of the daily_bfg.py.
#These files are Netcdf format files.  The files that start with bfg_date_fhr(hr)_fieldname_control.nc have the following
#data fields in them.
# grid_xt - longitude
# grid_yt - latitude
# time calendar = JULIAN
# field values - model output
# lfrac - land fraction 
#sotyp - soil type in integer 1-9

#To get a listing of the Netcdf files in the bucket type:
aws s3 ls s3://noaa-reanalyses-pds/score_suite/test_data/ --no-sign-request

#To copy a file to a local directory. cd to local directory then type:
aws s3 cp s3://noaa-reanalyses-pds/score_suite/test_data/* tests/data/ --no-sign-request


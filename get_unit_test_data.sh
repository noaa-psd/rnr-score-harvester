#!/bin/bash --posix

# grab select aws files stored in the bdp
aws s3 cp s3://noaa-reanalyses-pds/ufsrnr.baselines/ufsrnr.v1.0.linux_hera/C96L64.UFSRNR.GSI_SOCA_3DVAR.012016/gsi/innov_stats.uvwind.2016010300.nc data/innov_stats.uvwind.2016010300.nc --no-sign-request
aws s3 cp s3://noaa-reanalyses-pds/ufsrnr.baselines/ufsrnr.v1.0.linux_hera/C96L64.UFSRNR.GSI_SOCA_3DVAR.012016/gsi/innov_stats.uvwind.2016010300.nc data/innov_stats.temperature.2016010300.nc --no-sign-request
aws s3 cp s3://noaa-reanalyses-pds/ufsrnr.baselines/ufsrnr.v1.0.linux_hera/C96L64.UFSRNR.GSI_SOCA_3DVAR.012016/gsi/innov_stats.uvwind.2016010300.nc data/innov_stats.spechumid.2016010300.nc --no-sign-request

"""Copyright 2024 NOAA
All rights reserved.

Methods to calculate gridcell area weighted statistics
The functions generally take the following two input variables:
    xarray_variable - xarray variable data
    gridcell_area_data - xarray variable containing gridcell areas, in the
    same shape as xarray_variable
"""

import numpy as np

def area_weighted_mean(xarray_variable, gridcell_area_weights):  
    """returns the gridcell area weighted mean of the xarray_variable
    """
    weighted_mean, sumweights = np.ma.average(xarray_variable,
                                              weights=gridcell_area_weights,
                                              returned=True)

    #TODO: Build in try/except block for better error handling
    assert sumweights >= 0.999 * 4. * np.pi
    assert sumweights <= 1.001 * 4. * np.pi
    return(weighted_mean)

def area_weighted_variance(xarray_variable, gridcell_area_weights,
                        expected_value=None):
    """returns the gridcell weighted variance of the requested variables
    """
    if expected_value == None:
        expected_value = calculate_weighted_means(xarray_variable,
                                                  gridcell_area_weights)
    
    #TODO: provide the formula for weighted variance in human readable plain text
    weighted_variance = -expected_value**2 + np.ma.sum(
                                               xarray_variable**2 * 
                                               (gridcell_area_weights / 
                                                gridcell_area_weights.sum()))
    return(weighted_variance)

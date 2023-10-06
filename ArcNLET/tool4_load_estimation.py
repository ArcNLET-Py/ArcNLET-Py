"""
This script contains the Groundwater Flow module of ArcNLET model in the ArcGIS Python Toolbox.

For detailed algorithms, please see https://atmos.eoas.fsu.edu/~mye/ArcNLET/Techican_manual.pdf

@author: Wei Mao <wm23@@fsu.edu>
"""
from collections import namedtuple
import datetime
import arcpy
import os
import sys
import numpy as np

__version__ = "V1.0.0"


def LoadEstimation(dem, ks=None, wb=None, poro=None, smthf1=None, smthc=None, fsink=None,
              zfact=None, velname=None, veldname=None, gradname=None, smthname=None):
    """ Update the named field in every row of the input feature class with the given value. """

    arcpy.AddMessage("Groundwater Flow {}".format(__version__))

    try:
        arcpy.CheckOutExtension("Spatial")
    except RuntimeError as e:
        print("Unable to apply for Spatial Analyst Extension license: {}".format(e))
        return

    zero_threshold = 1E-8

    # Smoothing calculation
    neighborhood = arcpy.sa.NbrRectangle(smthc, smthc, "CELL")
    # Smoothing smthf1 times
    for i in range(smthf1):
        smthdem = arcpy.sa.FocalStatistics(dem, neighborhood, "MEAN", "DATA")
        dem = smthdem

    # Filling sinks if fsink is True
    if fsink:
        smoothed_filled_dem = arcpy.sa.Fill(smthdem)
    else:
        smoothed_filled_dem = smthdem

    # Calculation of Gx and Gy
    desc = arcpy.Describe(dem)
    cell_size_x = abs(desc.meanCellWidth)
    cell_size_y = abs(desc.meanCellHeight)
    gx = arcpy.sa.Convolution(smoothed_filled_dem, 18) / cell_size_x / 8 * zfact
    gy = arcpy.sa.Convolution(smoothed_filled_dem, 17) / cell_size_y / 8 * zfact
    # calculation of gradient
    gradient = arcpy.sa.SquareRoot(gx ** 2 + gy ** 2)

    # If gradient is less than zero_threshold, set it to zero_threshold
    gradient = arcpy.sa.Con(gradient < zero_threshold, zero_threshold, gradient)

    # Calculation of velocity, velocity = hydraulic conductivity / porosity * gradient
    velo = arcpy.sa.Raster(ks) / arcpy.sa.Raster(poro) * arcpy.sa.Raster(gradient)

    # calculate velocity direction
    gx_array = arcpy.RasterToNumPyArray(gx)
    gy_array = arcpy.RasterToNumPyArray(gy)
    tand_array = np.arctan2(gy_array, gx_array)
    # convert the radian to degree
    theta_array = np.degrees(tand_array)

    # Starting from north, and calculate the angle counter-clockwise
    nrows = desc.height
    ncols = desc.width
    for i in range(nrows):
        for j in range(ncols):
            if gx[i, j] < 0 < gy[i, j]:
                theta_array[i, j] = theta_array[i, j] - 90
            else:
                theta_array[i, j] = 270 + theta_array[i, j]

    # If the angle is 270, that means gx = gy = 0. Set the angle to the mean value of the surrounding values,
    # which are the values within the square of size smthc * smthc
    r0 = smthc // 2
    theta_array[theta_array == 270] = -1
    negative_indices = np.where(theta_array < 0)
    for row, col in zip(*negative_indices):
        surrounding_values = theta_array[row - r0:row + r0 + 1, col - r0:col + r0 + 1]
        valid_values = surrounding_values[surrounding_values >= 0]
        if valid_values.size > 0:
            theta_array[row, col] = np.mean(valid_values)

    # convert the numpy array back to raster
    tand = arcpy.NumPyArrayToRaster(theta_array, arcpy.Point(gx.extent.XMin, gx.extent.YMin),
                                    gx.meanCellWidth, gx.meanCellHeight)

    # save the output
    if arcpy.Exists(velname):
        arcpy.Delete_management(velname)
    velo.save(velname)
    if arcpy.Exists(veldname):
        arcpy.Delete_management(veldname)
    tand.save(veldname)
    if gradname is not None:
        if arcpy.Exists(gradname):
            arcpy.Delete_management(gradname)
        gradient.save(gradname)
    if smthname is not None:
        if arcpy.Exists(smthname):
            arcpy.Delete_management(smthname)
        smthdem.save(smthname)
    return


# ======================================================================
# Main program for debugging
if __name__ == '__main__':
    arcpy.env.workspace = ".\\test_pro"
    dem = os.path.join(arcpy.env.workspace, "test.tif")
    ks = os.path.join(arcpy.env.workspace, "hydr_cond.img")
    wb = os.path.join(arcpy.env.workspace, "waterbodies")
    poro = os.path.join(arcpy.env.workspace, "porosity.img")

    smthf1 = 1
    smthc = 3
    fsink = 0
    zfact = 1

    vel = os.path.join(arcpy.env.workspace, "2vel")
    veld = os.path.join(arcpy.env.workspace, "2veld")
    grad = os.path.join(arcpy.env.workspace, "2grad")
    smthd = os.path.join(arcpy.env.workspace, "2smthd")

    arcpy.AddMessage("starting geoprocessing")
    GroundwaterFlow(dem, ks, wb, poro, smthf1, smthc, fsink, zfact,
                    vel, veld, grad, smthd)

    print("Tests successful!")

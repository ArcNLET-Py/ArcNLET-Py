"""
This script contains the Groundwater Flow module of ArcNLET model in the ArcGIS Python Toolbox.

For detailed algorithms, please see https://atmos.eoas.fsu.edu/~mye/ArcNLET/Techican_manual.pdf

@author: Wei Mao <wm23a@fsu.edu>
"""

import os
import time
import arcpy
import shutil
import numpy as np

__version__ = "V1.0.0"
arcpy.env.parallelProcessingFactor = "100%"


class DarcyFlow:
    def __init__(self, c_dem, c_wb, c_ks, c_poro,
                 c_smthf1, c_smthc, c_fsink, c_merge, c_smthf2, c_zfact,
                 velname, veldname, gradname=None, smthname=None):
        # input files

        self.dem = arcpy.Describe(c_dem).catalogPath if not self.is_file_path(c_dem) else c_dem
        self.wb = arcpy.Describe(c_wb).catalogPath if not self.is_file_path(c_wb) else c_wb
        self.ks = arcpy.Describe(c_ks).catalogPath if not self.is_file_path(c_ks) else c_ks
        self.poro = arcpy.Describe(c_poro).catalogPath if not self.is_file_path(c_poro) else c_poro

        # input parameters
        self.smthf1 = c_smthf1
        self.smthc = c_smthc
        self.flag_fsink = c_fsink
        self.flag_merge = c_merge
        self.smthf2 = c_smthf2
        self.zfact = c_zfact

        # output file names
        self.velname = arcpy.Describe(velname).catalogPath if not self.is_file_path(velname) else velname
        self.veldname = arcpy.Describe(veldname).catalogPath if not self.is_file_path(veldname) else veldname
        if gradname is not None:
            self.gradname = arcpy.Describe(gradname).catalogPath if not self.is_file_path(gradname) else gradname
        else:
            self.gradname = None
        if smthname is not None:
            self.smthname = arcpy.Describe(smthname).catalogPath if not self.is_file_path(smthname) else smthname
        else:
            self.smthname = None

        self.zero_threshold = 1E-8
        self.temp_output_dir = None

    def calculateDarcyFlow(self):
        """main calculation function
        """
        workspace = os.path.dirname(self.dem)
        arcpy.env.workspace = os.path.abspath(workspace)

        self.temp_output_dir = os.path.join(workspace, 'temp')
        if os.path.exists(self.temp_output_dir):
            shutil.rmtree(self.temp_output_dir)
        os.mkdir(self.temp_output_dir)

        # first, smooth DEM, then fill sinks if flag_fsink is True
        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage("{}     Smoothing DEM".format(current_time))
        smoothed_filled_dem = self.smoothDEM(self.dem, self.smthf1, self.flag_fsink)
        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage("{}         Smoothing finished".format(current_time))

        if self.flag_merge:
            # first, merge DEM and waterbody, then smooth the merged dem
            current_time = time.strftime("%H:%M:%S", time.localtime())
            arcpy.AddMessage("{}     Merging and Smoothing DEM".format(current_time))
            smoothed_merge_dem = self.mergeDEM(self.dem, self.wb, self.smthf2, smoothed_filled_dem, self.flag_fsink)
            current_time = time.strftime("%H:%M:%S", time.localtime())
            arcpy.AddMessage("{}         Merging and smoothing finished".format(current_time))
        else:
            smoothed_merge_dem = smoothed_filled_dem

        # calculate slope
        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage("{}     Calculating Slope".format(current_time))
        gx, gy = self.slope(smoothed_merge_dem)
        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage("{}         Calculating slope finished".format(current_time))

        # calculate flow direction
        # flowdir is the flow direction in degree, while flowdir_d8 is the flow direction in D8 format
        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage("{}     Calculating Flow Directions".format(current_time))
        flowdrop, flowdir_d8 = self.flowdirection(smoothed_merge_dem)
        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage("{}         Calculating flow directions finished".format(current_time))

        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage("{}     Processing Flow Directions".format(current_time))
        flowdir_d8 = self.convertFD(flowdir_d8)
        flowdir_raster = self.flowdir2cal(gx, gy, flowdir_d8)
        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage("{}         Processing flow directions finished".format(current_time))

        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage("{}     Calculating Gradient Magnitude".format(current_time))
        gradient = self.gradient(gx, gy, flowdrop)
        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage("{}         Calculating gradient magnitude finished".format(current_time))

        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage("{}     Calculating Velocity Magnitude".format(current_time))
        velocity = self.velocity(gradient)
        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage("{}         Calculating velocity magnitude finished".format(current_time))

        # save the output
        if arcpy.Exists(self.velname):
            arcpy.Delete_management(self.velname)
        velocity.save(self.velname)
        if arcpy.Exists(self.veldname):
            arcpy.Delete_management(self.veldname)
        flowdir_raster.save(self.veldname)
        if self.gradname is not None:
            if arcpy.Exists(self.gradname):
                arcpy.Delete_management(self.gradname)
            gradient.save(self.gradname)
        if self.smthname is not None:
            if arcpy.Exists(self.smthname):
                arcpy.Delete_management(self.smthname)
            smoothed_merge_dem.save(self.smthname)

        return

    def smoothDEM(self, raster, factor, flag_fsink=False):
        """smooth the raster factor times"""
        neighborhood = arcpy.sa.NbrRectangle(self.smthc, self.smthc, "CELL")
        for i in range(factor):
            smoothed_dem = arcpy.sa.FocalStatistics(raster, neighborhood, "MEAN", "DATA")
            raster = smoothed_dem

        if flag_fsink:
            # https://pro.arcgis.com/en/pro-app/latest/tool-reference/spatial-analyst/how-fill-works.htm
            smoothed_filled_dem = arcpy.sa.Fill(smoothed_dem)
        else:
            smoothed_filled_dem = smoothed_dem
        return smoothed_filled_dem

    def mergeDEM(self, original_dem, waterbody, factor_list, smoothed_filled_dem, flag_fsink=False):
        """merge the original dem and waterbody, then smooth the merged dem"""
        # set the extent of the calculation environment to make sure the output raster has the same extent as the input
        desc = arcpy.Describe(original_dem)
        arcpy.env.extent = desc.extent
        # merge the original dem and waterbody
        extracted_dem = arcpy.sa.ExtractByMask(original_dem, waterbody)
        extracted_dem_name = os.path.join(self.temp_output_dir, "extracted_dem")
        extracted_dem.save(extracted_dem_name)

        # merge, then smooth. The number of times of smoothing is determined by the length of factor_list
        # the times of smoothing is determined by the value of factor_list
        for kk in factor_list:
            # merge the smoothed dem and waterbody
            merged_dem = arcpy.sa.Con(arcpy.sa.IsNull(extracted_dem), smoothed_filled_dem, extracted_dem)
            # smooth the merged dem kk times
            smoothed_filled_dem = self.smoothDEM(merged_dem, kk, flag_fsink)
        return smoothed_filled_dem

    def slope(self, raster):
        """calculate the slope of the raster"""
        # calculate the width and height of each cell
        desc = arcpy.Describe(raster)
        cell_size_x = abs(desc.meanCellWidth)
        cell_size_y = abs(desc.meanCellHeight)
        # use sobel horizontal and vertical filters to calculate the gx and gy
        # https://pro.arcgis.com/en/pro-app/latest/help/analysis/raster-functions/convolution-function.htm
        gx = arcpy.sa.Convolution(raster, 18) / cell_size_x / 8 * self.zfact * -1
        gy = arcpy.sa.Convolution(raster, 17) / cell_size_y / 8 * self.zfact
        return gx, gy

    def flowdirection(self, dem_raster):
        flowdrop = r'memory\flowdrop'
        if arcpy.Exists(flowdrop):
            arcpy.Delete_management(flowdrop)
        flow_dir_d8_raster = arcpy.sa.FlowDirection(dem_raster, out_drop_raster=flowdrop, flow_direction_type="D8")
        return flowdrop, flow_dir_d8_raster

    def convertFD(self, flow_dir_raster):
        converted_raster = arcpy.sa.RemapRange([[1, 1, 90], [2, 2, 135], [4, 4, 180], [8, 8, 225],
                                                [16, 16, 270], [32, 32, 315], [64, 64, 360], [128, 128, 45]])
        outreclass = arcpy.sa.Reclassify(flow_dir_raster, "Value", converted_raster, "NODATA")
        return outreclass

    def flowdir2cal(self, gx, gy, flowdir_raster):
        gx_array = arcpy.RasterToNumPyArray(gx)
        gy_array = arcpy.RasterToNumPyArray(gy)
        # in the range [-pi, pi]
        tand_array = np.arctan2(gy_array, gx_array)
        # convert the radian to degree, in the range [-180, 180], then adjust to 0 degrees at north direction
        theta_array = 90 - np.degrees(tand_array)
        # convert to the range [0, 360]
        theta_array = np.where(theta_array < 0, theta_array + 360, theta_array)
        desc = arcpy.Describe(flowdir_raster)
        reference = desc.spatialReference
        theta_raster = arcpy.NumPyArrayToRaster(theta_array, arcpy.Point(desc.extent.XMin,
                                                                         desc.extent.YMin),
                                                desc.meanCellWidth, desc.meanCellHeight)
        arcpy.management.DefineProjection(theta_raster, reference)
        theta_raster = arcpy.sa.Con(arcpy.sa.IsNull(theta_raster), flowdir_raster, theta_raster)
        return theta_raster

    def gradient(self, gx, gy, flowdir):
        gradient = arcpy.sa.SquareRoot(gx ** 2 + gy ** 2)

        # If gradient is less than zero_threshold, set it to zero_threshold
        gradient = arcpy.sa.Con(gradient < self.zero_threshold, 0, gradient)
        gradient = arcpy.sa.Con(arcpy.sa.IsNull(gradient), flowdir, gradient)
        return gradient

    def velocity(self, gradient):
        velocity = self.ks * gradient / self.poro
        return velocity

    @staticmethod
    def is_file_path(input_string):
        return os.path.sep in input_string


# ======================================================================
# Main program for debugging
if __name__ == '__main__':
    arcpy.env.workspace = ".\\test_pro"
    dem = os.path.join(arcpy.env.workspace, "Demodem.tif")
    wb = os.path.join(arcpy.env.workspace, "waterbodies")
    ks = os.path.join(arcpy.env.workspace, "hydr_cond.img")
    poro = os.path.join(arcpy.env.workspace, "porosity.img")

    smthf1 = 1
    smthc = 7
    fsink = 0
    merge = 0
    smthf2 = [0]
    zfact = 1

    vel = os.path.join(arcpy.env.workspace, "demovel")
    veld = os.path.join(arcpy.env.workspace, "demoveld")
    grad = os.path.join(arcpy.env.workspace, "demograd")
    smthd = os.path.join(arcpy.env.workspace, "demosmthd")

    arcpy.AddMessage("starting geoprocessing")
    GF = DarcyFlow(dem, wb, ks, poro,
                   smthf1, smthc, fsink, merge, smthf2, zfact,
                   vel, veld, grad, smthd)
    GF.calculateDarcyFlow()

    print("Tests successful!")

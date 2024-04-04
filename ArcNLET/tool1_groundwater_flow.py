"""
This script contains the Groundwater Flow module of ArcNLET model in the ArcGIS Python Toolbox.

For detailed algorithms, please see https://atmos.eoas.fsu.edu/~mye/ArcNLET/Techican_manual.pdf

@author: Wei Mao <wm23a@fsu.edu>， Michael Core <mcore@fsu.edu>, Ming Ye <mye@fsu.edu>
            The Department of Earth, Ocean, and Atmospheric Science, Florida State University
@date: 2023-11-13
"""

import os
import time
import arcpy
import shutil
import psutil
import numpy as np
import cProfile
import pstats
import stack_data

__version__ = "V1.0.0"
arcpy.env.parallelProcessingFactor = "100%"
arcpy.env.overwriteOutput = True


class DarcyFlow:
    def __init__(self, c_dem, c_wb, c_ks, c_poro,
                 c_smthf1, c_smthc, c_fsink, c_merge, c_smthf2, c_zfact, c_smthflimit,
                 velname, veldname, smthname=None, gradname=None):
        # input files
        self.pixel_type = "32_BIT_FLOAT"

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
        self.smthflimit = c_smthflimit

        # output file names
        if self.is_file_path(velname):
            self.velname = os.path.basename(velname)
            self.veldir = os.path.dirname(velname)
            if os.path.isabs(self.veldir):
                self.veldir = os.path.abspath(self.veldir)
        else:
            self.velname = velname
            if self.is_file_path(veldname):
                self.veldir = os.path.dirname(veldname)
            else:
                self.veldir = os.path.dirname(self.dem)
        if self.is_file_path(veldname):
            self.veldname = os.path.basename(veldname)
            self.velddir = os.path.dirname(veldname)
            if os.path.isabs(self.velddir):
                self.velddir = os.path.abspath(self.velddir)
        else:
            self.veldname = veldname
            if self.is_file_path(velname):
                self.velddir = os.path.dirname(veldname)
            else:
                self.velddir = os.path.dirname(self.dem)
        if gradname is not None:
            if self.is_file_path(gradname):
                self.gradname = os.path.basename(gradname)
                self.graddir = os.path.dirname(gradname)
                if os.path.isabs(self.graddir):
                    self.graddir = os.path.abspath(self.graddir)
            else:
                self.gradname = gradname
                self.graddir = os.path.dirname(self.dem)
        else:
            self.gradname = None
        if smthname is not None:
            if self.is_file_path(smthname):
                self.smthname = os.path.basename(smthname)
                self.smthdir = os.path.dirname(smthname)
                if os.path.isabs(self.smthdir):
                    self.velddir = os.path.abspath(self.smthdir)
            else:
                self.smthname = smthname
                self.smthdir = os.path.dirname(self.dem)
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
        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage("{}     Save output files".format(current_time))
        velocity.save(os.path.join(self.veldir, self.velname))
        flowdir_raster.save(os.path.join(self.velddir, self.veldname))
        if self.gradname is not None:
            gradient.save(os.path.join(self.graddir, self.gradname))
        if self.smthname is not None:
            # smoothed_merge_dem.save(os.path.join(self.smthdir, self.smthname))
            arcpy.management.CopyRaster(smoothed_merge_dem, os.path.join(self.smthdir, self.smthname))
        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage("{}         Output files saved".format(current_time))

        arcpy.management.Delete(smoothed_merge_dem)
        arcpy.management.Delete(smoothed_filled_dem)
        if os.path.exists(self.temp_output_dir):
            shutil.rmtree(self.temp_output_dir)
        return

    def smoothDEM(self, raster, factor, flag_fsink=False, flag=0):
        """Smooth the raster factor times"""
        neighborhood = arcpy.sa.NbrRectangle(self.smthc, self.smthc, "CELL")
        chunk_size = self.smthflimit
        def smooth_chunk(raster_chunk, start_factor, times):
            """Smooth a chunk of the raster"""
            smoothed_chunk = raster_chunk
            for i in range(times):
                smoothed_chunk = arcpy.sa.FocalStatistics(smoothed_chunk, neighborhood, "MEAN", "DATA")
                print("Smooth times, {}".format(start_factor + i + 1))
                if flag_fsink:
                    print("Filling sinks")
                    smoothed_chunk = arcpy.sa.Fill(smoothed_chunk)
                    print("Filling finished")
            return smoothed_chunk

        try:
            for i in range(0, factor, chunk_size):
                # Smooth a chunk of the raster
                chunk_start = i
                chunk_end = min(i + chunk_size, factor)
                if flag != 0:
                    fstartname = os.path.join(self.temp_output_dir, f"temp_dem_{i}_{flag}.tif")
                    fendname = os.path.join(self.temp_output_dir, f"temp_dem_{chunk_end}_{flag}.tif")
                else:
                    fstartname = os.path.join(self.temp_output_dir, f"temp_dem_{i}.tif")
                    fendname = os.path.join(self.temp_output_dir, f"temp_dem_{chunk_end}.tif")
                chunk_raster = raster if i == 0 else arcpy.Raster(fstartname)
                smoothed_dem = smooth_chunk(chunk_raster, chunk_start, chunk_end - chunk_start)
                # Save the smoothed chunk
                smoothed_dem.save(fendname)
        except Exception as e:
            arcpy.AddError(f"Error occurred while smoothing the DEM: {e}")
            return None

        # Combine all smoothed chunks to get the final smoothed DEM
        final_smoothed_dem = arcpy.Raster(fendname)

        return final_smoothed_dem

    def mergeDEM(self, original_dem, waterbody, factor_list, smoothed_filled_dem, flag_fsink=False):
        """merge the original dem and waterbody, then smooth the merged dem"""
        # set the extent of the calculation environment to make sure the output raster has the same extent as the input
        desc = arcpy.Describe(original_dem)
        arcpy.env.extent = desc.extent
        # merge the original dem and waterbody
        extracted_dem = arcpy.sa.ExtractByMask(original_dem, waterbody)
        extracted_dem_name = os.path.join(self.temp_output_dir, "extracted_dem")
        arcpy.management.CopyRaster(extracted_dem, extracted_dem_name, pixel_type=self.pixel_type)

        # merge, then smooth. The number of times of smoothing is determined by the length of factor_list
        # the times of smoothing is determined by the value of factor_list
        for index, kk in enumerate(factor_list):
            # merge the smoothed dem and waterbody
            merged_dem = arcpy.sa.Con(arcpy.sa.IsNull(extracted_dem), smoothed_filled_dem, extracted_dem)
            # smooth the merged dem kk times
            smoothed_filled_dem = self.smoothDEM(merged_dem, kk, flag_fsink, index + 1)
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

    @staticmethod
    def get_memory_usage():
        process = psutil.Process()
        memory_usage_bytes = process.memory_info().rss
        memory_usage_gb = memory_usage_bytes / 1024 / 1024 / 1024

        stack_usage = process.memory_info().rss
        stack_usage_gb = stack_usage / 1024 / 1024 / 1024
        return memory_usage_gb, stack_usage_gb


# ======================================================================
# Main program for debugging
if __name__ == '__main__':
    # for i in range(30):
        i = 0
        arcpy.env.workspace = "C:\\Users\\Wei\\Downloads\\Orlando\\debug"
        dem = os.path.join(arcpy.env.workspace, "fl_5meter")
        wb = os.path.join(arcpy.env.workspace, "LakesWbAdded.shp")
        ks = os.path.join(arcpy.env.workspace, "hydr_cond_ProjectRaster.tif")
        poro = os.path.join(arcpy.env.workspace, "porosity_ProjectRaster.tif")

        smthf1 = 30
        smthc = 15
        fsink = 0
        merge = 1
        smthf2 = [2]
        zfact = 1
        smthflimit = 50

        vel = os.path.join(arcpy.env.workspace, "demovel"+str(i))
        veld = os.path.join(arcpy.env.workspace, "demoveld"+str(i))
        grad = os.path.join(arcpy.env.workspace, "demograd"+str(i))
        smthd = os.path.join(arcpy.env.workspace, "demosmthd"+str(i))
        start_time = time.time()

        arcpy.AddMessage("starting geoprocessing")
        GF = DarcyFlow(dem, wb, ks, poro,
                       smthf1, smthc, fsink, merge, smthf2, zfact, smthflimit,
                       vel, veld, smthd, grad)
        GF.calculateDarcyFlow()

        # cProfile.run('GF.calculateDarcyFlow()', 'flow')
        # profile_stats = pstats.Stats('flow')
        # with open('flow.txt', 'w') as output_file:
        #     profile_stats.sort_stats('cumulative').print_stats(output_file)

        end_time = time.time()
        print("{} times, Time elapsed: {} seconds".format(i, end_time - start_time))
        print("Tests successful!")

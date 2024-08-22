"""
This script contains the Transport module of ArcNLET model in the ArcGIS Python Toolbox.

For detailed algorithms, please see https://atmos.eoas.fsu.edu/~mye/ArcNLET/Techican_manual.pdf

@author: Wei Mao <wm23a@fsu.edu>， Michael Core <mcore@fsu.edu>, Ming Ye <mye@fsu.edu>
            The Department of Earth, Ocean, and Atmospheric Science, Florida State University
@date: 2023-11-13
"""

import datetime
import shutil
import sys

import arcpy
import os
import tempfile
import psutil
import math
import time
import numpy as np
import pandas as pd
from scipy.stats import hmean
from scipy.ndimage import map_coordinates
from DomenicoRobbins import DomenicoRobbins
# from tps import ThinPlateSpline
import matplotlib.pyplot as plt
import cProfile
import pstats

__version__ = "V1.0.0"
arcpy.env.parallelProcessingFactor = "100%"
arcpy.env.overwriteOutput = True


class Transport:
    def __init__(self, type_of_contaminants, c_whethernh4, c_source_location, c_waterbodies, c_particlepath,
                 c_no3output, c_nh4output, c_no3output_info, c_nh4output_info,
                 c_option0, c_option1, c_option2, c_option3, c_option4, c_option5, c_option6,
                 c_param0, c_param1, c_param2, c_param3, c_param4, c_param5, c_param6, c_param7, c_param8,
                 c_no3param0, c_no3param1, c_no3param2, c_no3param3,
                 c_nh4param0, c_nh4param1, c_nh4param2, c_nh4param3, c_nh4param4,
                 c_poutput, c_poutput_info, phosparam0, phosparam1, phosparam2, phosparam3, phosparam4, phosparam5,
                 phosparam6, phosparam7):
        """Initialize the transport module
        """
        self.pixeltype = "32_BIT_FLOAT"
        self.type_of_contaminants = type_of_contaminants
        self.whether_nh4 = c_whethernh4

        self.source_location = arcpy.Describe(c_source_location).catalogPath if not self.is_file_path(
            c_source_location) else c_source_location
        self.waterbodies = arcpy.Describe(c_waterbodies).catalogPath if not self.is_file_path(
            c_waterbodies) else c_waterbodies
        self.waterbody_raster = None
        self.particle_path = arcpy.Describe(c_particlepath).catalogPath if not self.is_file_path(
            c_particlepath) else c_particlepath

        self.solution_type = c_option0  # solution type, DomenicoRobbinsSS2D or DomenicoRobbinsSSDecay2D
        self.warp_ctrl_pt_spacing = c_option1
        self.warp_method = c_option2.lower()  # Plume warping method, spline, polynomial1, polynomial2
        self.threshold = c_option3  # Threshold concentration
        self.post_process = c_option4.lower()  # Post process, none, medium, and full
        self.solute_mass_type = c_option5  # Solute mass type, specified input mass rate, or specified Z
        self.maxnum = c_option6

        self.Y = c_param2  # Y of the source plane
        if self.solute_mass_type.lower() == 'specified z':
            self.Z = c_param3  # Z of the source plane
        else:
            self.mass_in = c_param0  # mass in
            self.mass_in_phos = c_param1
            self.zmax_option = c_param4
            if self.zmax_option:
                self.zmax = c_param5  # Max Z of the source plane
        # Plume cell size of the output raster
        self.plume_cell_size = c_param6
        self.vol_conversion_factor = c_param7
        self.bulk_density = c_param8

        self.warp_option = False
        self.multiplier = 1.2
        self.working_dir = None

        self.contaminant_list = []
        if self.type_of_contaminants == "Nitrogen" or self.type_of_contaminants == "Nitrogen and Phosphorus":
            self.contaminant_list.append("NO3-N")
            if self.whether_nh4:
                self.contaminant_list.append("NH4-N")
        if self.type_of_contaminants == "Phosphorus" or self.type_of_contaminants == "Nitrogen and Phosphorus":
            self.contaminant_list.append("PO4-P")

        desc = arcpy.Describe(self.source_location)
        self.crs = desc.spatialReference
        field_list = desc.fields
        if "NO3-N" in self.contaminant_list:
            self.no3_output = os.path.basename(c_no3output) if self.is_file_path(c_no3output) else c_no3output
            if self.is_file_path(c_no3output):
                self.no3_dir = os.path.abspath(os.path.dirname(c_no3output))
            else:
                self.no3_dir = os.path.abspath(os.path.dirname(self.source_location))
            self.working_dir = self.no3_dir
            self.no3_output_info = c_no3output_info

            if not any(field.name.lower() == "no3_conc" for field in field_list):
                self.no3_init = c_no3param0  # NO3 concentration
            else:
                self.no3_init = None
            self.no3_dispx = c_no3param1  # NO3 dispersion X
            self.no3_dispyz = c_no3param2  # NO3 dispersion Y and Z
            self.denitrification_rate = c_no3param3

            # only calculate no3, nh4 can be calculated or not
            if "NH4-N" in self.contaminant_list:
                self.nh4_output = os.path.basename(c_nh4output) if self.is_file_path(c_nh4output) else c_nh4output
                self.nh4_output_info = c_nh4output_info
                if self.is_file_path(c_nh4output):
                    self.nh4_dir = os.path.abspath(os.path.dirname(c_nh4output))
                else:
                    self.nh4_dir = self.no3_dir
                if not any(field.name.lower() == "nh4_conc" for field in field_list):
                    self.nh4_init = c_nh4param0  # Initial NH4
                else:
                    self.nh4_init = None
                self.nh4_dispx = c_nh4param1
                self.nh4_dispyz = c_nh4param2
                self.nitrification_rate = c_nh4param3
                self.nh4_adsorption = c_nh4param4
            else:
                self.nh4_init = None
        else:
            self.no3_init = None
            self.nh4_init = None
        if "PO4-P" in self.contaminant_list:
            self.phos_output = os.path.basename(c_poutput) if self.is_file_path(c_poutput) else c_poutput
            if self.working_dir is None:
                self.working_dir = os.path.abspath(os.path.dirname(c_poutput))
            self.phos_output_info = c_poutput_info
            if self.is_file_path(c_poutput):
                self.phos_dir = os.path.abspath(os.path.dirname(c_poutput))
            else:
                self.phos_dir = os.path.abspath(os.path.dirname(self.source_location))

            if not any(field.name.lower() == "p_conc" for field in field_list):
                self.pho_init = phosparam0
            else:
                self.pho_init = None

            self.phos_dispx = phosparam1
            self.phos_dispyz = phosparam2
            self.phos_choice = phosparam3
            self.phos_prep = phosparam4
            self.phos_kd = phosparam5
            self.phos_kl = phosparam6
            self.phos_smax = phosparam7
        else:
            self.pho_init = None

        self.ano3 = 0.0
        self.kno3 = 0.0
        self.no3_Z = 0.0
        self.anh4 = 0.0
        self.knh4 = 0.0
        self.nh4_Z = 0.0
        self.apho = 0.0
        self.kpho = 0.0
        self.pho_Z = 0.0
        self.nh4massmdn = 0.0

    def main(self):
        arcpy.SetLogMetadata(False)
        arcpy.SetLogHistory(False)
        arcpy.env.workspace = self.working_dir
        factor = self.maxnum

        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage("{}     Creating water body raster...".format(current_time))
        try:
            self.waterbody_raster = r"memory\water_bodies"
            if arcpy.Exists(self.waterbody_raster):
                arcpy.management.Delete(self.waterbody_raster)
            arcpy.conversion.FeatureToRaster(self.waterbodies, "FID", self.waterbody_raster,
                                             max(self.plume_cell_size, 1))
        except Exception as e:
            arcpy.AddMessage("[Error]: Failed to create water body raster: "+str(e))
            sys.exit(-1)

        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage("{}     Calculating plumes...".format(current_time))

        no3plume = []
        no3plume_info = []
        nh4plume = []
        nh4plume_info = []
        phoplume = []
        phoplume_info = []

        ostds_number = int(arcpy.management.GetCount(self.source_location).getOutput(0))
        if ostds_number > self.maxnum:
            for num in range(0, ostds_number, factor):
                # delete temp files
                temp_folder = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Temp')
                delete_temp_files(temp_folder)

                chunk_start = num
                chunk_end = min(num + factor, ostds_number)
                if "NO3-N" in self.contaminant_list:
                    no3plume_name = "n3p{}_{}".format(chunk_start, chunk_end)
                    no3info_name = "n3i{}_{}".format(chunk_start, chunk_end)
                    if arcpy.Exists(os.path.join(self.no3_dir, no3plume_name)):
                        arcpy.management.Delete(os.path.join(self.no3_dir, no3plume_name))
                    if arcpy.Exists(os.path.join(self.no3_dir, no3info_name + '.shp')):
                        arcpy.management.Delete(os.path.join(self.no3_dir, no3info_name + '.shp'))
                    no3plume.append(no3plume_name)
                    no3plume_info.append(no3info_name)
                if "NH4-N" in self.contaminant_list:
                    nh4plume_name = "n4p{}_{}".format(chunk_start, chunk_end)
                    nh4info_name = "n4i{}_{}".format(chunk_start, chunk_end)
                    if arcpy.Exists(os.path.join(self.nh4_dir, nh4plume_name)):
                        arcpy.management.Delete(os.path.join(self.nh4_dir, nh4plume_name))
                    if arcpy.Exists(os.path.join(self.nh4_dir, nh4info_name + '.shp')):
                        arcpy.management.Delete(os.path.join(self.nh4_dir, nh4info_name + '.shp'))
                    nh4plume.append(nh4plume_name)
                    nh4plume_info.append(nh4info_name)
                if "PO4-P" in self.contaminant_list:
                    phoplume_name = "pp{}_{}".format(chunk_start, chunk_end)
                    phoplume_info_name = "pi{}_{}".format(chunk_start, chunk_end)
                    if arcpy.Exists(os.path.join(self.phos_dir, phoplume_name)):
                        arcpy.management.Delete(os.path.join(self.phos_dir, phoplume_name))
                    if arcpy.Exists(os.path.join(self.phos_dir, phoplume_info_name + '.shp')):
                        arcpy.management.Delete(os.path.join(self.phos_dir, phoplume_info_name + '.shp'))
                    phoplume.append(phoplume_name)
                    phoplume_info.append(phoplume_info_name)

                self.calculate_plumes(chunk_start, chunk_end)
        else:
            if "NO3-N" in self.contaminant_list:
                no3plume_name = self.no3_output
                no3info_name = self.no3_output_info
                if arcpy.Exists(os.path.join(self.no3_dir, no3plume_name)):
                    arcpy.management.Delete(os.path.join(self.no3_dir, no3plume_name))
                if arcpy.Exists(os.path.join(self.no3_dir, no3info_name + '.shp')):
                    arcpy.management.Delete(os.path.join(self.no3_dir, no3info_name + '.shp'))
            if "NH4-N" in self.contaminant_list:
                nh4plume_name = self.nh4_output
                nh4info_name = self.nh4_output_info
                if arcpy.Exists(os.path.join(self.nh4_dir, nh4plume_name)):
                    arcpy.management.Delete(os.path.join(self.nh4_dir, nh4plume_name))
                if arcpy.Exists(os.path.join(self.nh4_dir, nh4info_name + '.shp')):
                    arcpy.management.Delete(os.path.join(self.nh4_dir, nh4info_name + '.shp'))
            if "PO4-P" in self.contaminant_list:
                phoplume_name = self.phos_output
                phoplume_info_name = self.phos_output_info
                if arcpy.Exists(os.path.join(self.phos_dir, phoplume_name)):
                    arcpy.management.Delete(os.path.join(self.phos_dir, phoplume_name))
                if arcpy.Exists(os.path.join(self.phos_dir, phoplume_info_name + '.shp')):
                    arcpy.management.Delete(os.path.join(self.phos_dir, phoplume_info_name + '.shp'))
                phoplume.append(phoplume_name)
                phoplume_info.append(phoplume_info_name)

            self.calculate_plumes(0, ostds_number, True)

        try:
            if len(no3plume) < 2 and len(nh4plume) < 2 and len(phoplume) < 2 and ostds_number > self.maxnum:
                if "NO3-N" in self.contaminant_list:
                    arcpy.management.Rename(no3plume[0], self.no3_output)
                    arcpy.management.Rename(no3plume_info[0], self.no3_output_info)
                if "NH4-N" in self.contaminant_list:
                    arcpy.management.Rename(nh4plume[0], self.nh4_output)
                    arcpy.management.Rename(nh4plume_info[0], self.nh4_output_info)
                if "PO4-P" in self.contaminant_list:
                    arcpy.management.Rename(phoplume[0], self.phos_output)
                    arcpy.management.Rename(phoplume_info[0], self.phos_output_info)
            elif ostds_number > self.maxnum:
                if "NO3-N" in self.contaminant_list:
                    if arcpy.Exists(os.path.join(self.no3_dir, self.no3_output)):
                        arcpy.management.Delete(os.path.join(self.no3_dir, self.no3_output))
                    arcpy.management.MosaicToNewRaster(no3plume, self.no3_dir, self.no3_output, self.crs, self.pixeltype,
                                                       self.plume_cell_size, 1, "SUM")
                    arcpy.management.Merge(no3plume_info, self.no3_output_info)
                    for no3 in no3plume:
                        if arcpy.Exists(os.path.join(self.no3_dir, no3)):
                            arcpy.management.Delete(os.path.join(self.no3_dir, no3))
                    for no3 in no3plume_info:
                        if arcpy.Exists(os.path.join(self.no3_dir, no3 + '.shp')):
                            arcpy.management.Delete(os.path.join(self.no3_dir, no3 + '.shp'))
                if "NH4-N" in self.contaminant_list:
                    if arcpy.Exists(os.path.join(self.nh4_dir, self.nh4_output)):
                        arcpy.management.Delete(os.path.join(self.nh4_dir, self.nh4_output))
                    arcpy.management.MosaicToNewRaster(nh4plume, self.nh4_dir, self.nh4_output, self.crs, self.pixeltype,
                                                       self.plume_cell_size, 1, "SUM")
                    arcpy.management.Merge(nh4plume_info, self.nh4_output_info)
                    for nh4 in nh4plume:
                        if arcpy.Exists(os.path.join(self.nh4_dir, nh4)):
                            arcpy.management.Delete(os.path.join(self.nh4_dir, nh4))
                    for nh4 in nh4plume_info:
                        if arcpy.Exists(os.path.join(self.nh4_dir, nh4 + '.shp')):
                            arcpy.management.Delete(os.path.join(self.nh4_dir, nh4 + '.shp'))
                if "PO4-P" in self.contaminant_list:
                    if arcpy.Exists(os.path.join(self.phos_dir, self.phos_output)):
                        arcpy.management.Delete(os.path.join(self.phos_dir, self.phos_output))
                    arcpy.management.MosaicToNewRaster(phoplume, self.phos_dir, self.phos_output, self.crs, self.pixeltype,
                                                       self.plume_cell_size, 1, "SUM")
                    arcpy.management.Merge(phoplume_info, self.phos_output_info)
                    for pho in phoplume:
                        if arcpy.Exists(os.path.join(self.phos_dir, pho)):
                            arcpy.management.Delete(os.path.join(self.phos_dir, pho))
                    for pho in phoplume_info:
                        if arcpy.Exists(os.path.join(self.phos_dir, pho + '.shp')):
                            arcpy.management.Delete(os.path.join(self.phos_dir, pho + '.shp'))
        except Exception as e:
            arcpy.AddMessage("[Error]: Failed to mosaic the entire plumes: "+str(e))
            sys.exit(-1)

    def calculate_plumes(self, start_num, end_num, flag=False):
        info_names = self.create_new_plume_data_shapefile(start_num, end_num, flag)

        # read the segments feature class (flow paths)
        colname = ["Shape", "PathID", "SegID", "TotDist", "TotTime", "SegPrsity", "SegVel", "DirAngle", "WBId",
                   "PathWBId"]
        data = []
        with arcpy.da.SearchCursor(self.particle_path,
                                   ["SHAPE@", "PathID", "SegID", "TotDist", "TotTime", "SegPrsity", "SegVel",
                                    "DirAngle", "WBId", "PathWBId"]) as cursor:
            for row in cursor:
                data.append(row)
        segments = pd.DataFrame(data, columns=colname)
        sorted_segments = segments.sort_values(by=['PathID', 'SegID'])

        sl_segments = sorted_segments[(sorted_segments['PathID'] >= start_num) & (sorted_segments['PathID'] < end_num)]
        del segments
        del sorted_segments

        plume_name = []
        try:
            if "NH4-N" in self.contaminant_list:
                if flag:
                    nh4plume_name = self.nh4_output
                else:
                    nh4plume_name = "n4p{}_{}".format(start_num, end_num)
                arcpy.management.CreateRasterDataset(self.nh4_dir, nh4plume_name, self.plume_cell_size,
                                                     self.pixeltype, self.crs, 1)
            else:
                nh4plume_name = None
            if "NO3-N" in self.contaminant_list:
                if flag:
                    no3plume_name = self.no3_output
                else:
                    no3plume_name = "n3p{}_{}".format(start_num, end_num)
                arcpy.management.CreateRasterDataset(self.no3_dir, no3plume_name, self.plume_cell_size,
                                                     self.pixeltype, self.crs, 1)
            else:
                no3plume_name = None
            if "PO4-P" in self.contaminant_list:
                if flag:
                    phoplume_name = self.phos_output
                else:
                    phoplume_name = "pp{}_{}".format(start_num, end_num)
                arcpy.management.CreateRasterDataset(self.phos_dir, phoplume_name, self.plume_cell_size,
                                                     self.pixeltype, self.crs, 1)
            else:
                phoplume_name = None
            plume_name.append(nh4plume_name)
            plume_name.append(no3plume_name)
            plume_name.append(phoplume_name)
        except Exception as e:
            arcpy.AddMessage("[Error]: Failed to create output raster: "+str(e))
            sys.exit(-1)
        plume_info = []

        for pathid in sl_segments['PathID'].unique():
            current_time = time.strftime("%H:%M:%S", time.localtime())
            arcpy.AddMessage("{}     Calculating plume for location: {}".format(current_time, pathid))
            # memoryview, _ = self.get_memory_usage()
            # arcpy.AddMessage("Memory usage before calculation: {} GB".format(memoryview))

            seg = sl_segments[sl_segments['PathID'] == pathid]
            seg = seg.reset_index(drop=True)

            if (seg['SegPrsity'] < 0.01).any() or (seg['SegVel'] < 1E-8).any():
                arcpy.AddMessage("[Warning]: Skip {}th OSTDS. The Ks or porosity may be missed.\n".format(pathid))
                continue

            mean_poro = seg['SegPrsity'].mean()
            mean_velo = hmean(seg['SegVel'])  # harmonic mean
            mean_angle = seg['DirAngle'].mean()
            max_dist = seg['TotDist'].max()
            maxtime = seg['TotTime'].max()
            wbid = seg['WBId'].iloc[-1]
            path_wbid = seg['PathWBId'].iloc[-1]

            # calculate a single plume
            current_time = time.strftime("%H:%M:%S", time.localtime())
            arcpy.AddMessage("{}          Calculating reference plume for location: {}".format(current_time, pathid))
            filtered, tmp_list = self.calculate_single_plume(pathid, mean_poro, mean_velo, max_dist)
            filtered_nh4, filtered_no3, filtered_pho = filtered
            if filtered_no3 is None and filtered_nh4 is None and filtered_pho is None:
                continue

            # calculate info file
            current_time = time.strftime("%H:%M:%S", time.localtime())
            arcpy.AddMessage("{}          Calculating info file for location: {}".format(current_time, pathid))
            xvalue, yvalue = tmp_list[0].firstPoint.X, tmp_list[0].firstPoint.Y
            plume_seg = self.calculate_info(filtered, tmp_list, pathid, mean_poro, mean_velo,
                                            mean_angle, max_dist, maxtime, wbid, path_wbid)
            plume_info.append(plume_seg)

            # warp the plume
            current_time = time.strftime("%H:%M:%S", time.localtime())
            arcpy.AddMessage("{}          Warping plume for location: {}".format(current_time, pathid))
            if self.warp_option:
                # This function (affine transformation) is unavailable, Because the current algorithm is too
                # computationally intensive when the plume is large
                warped_plume = self.warp_affine_transformation(filtered, pathid, xvalue, yvalue, seg)
            else:
                warped_plumes, target_points_list, lengths = self.warp_arcgis(filtered, pathid, xvalue, yvalue, seg)

            post_plumes = self.post_process_plume(lengths, warped_plumes, pathid, seg, target_points_list, plume_name)

            ## merge the plume
            for index, post_plume in enumerate(post_plumes):
                if index == 0:
                    if "NH4-N" in self.contaminant_list:
                        filepath = self.nh4_dir
                    else:
                        continue
                elif index == 1:
                    if "NO3-N" in self.contaminant_list:
                        filepath = self.no3_dir
                    else:
                        continue
                elif index == 2:
                    if "PO4-P" in self.contaminant_list:
                        filepath = self.phos_dir
                    else:
                        continue
                try:
                    _, file_extension = os.path.splitext(plume_name[index])
                    wait_time = 0
                    if bool(file_extension):
                        lockfile = os.path.join(filepath, phoplume_name)
                        while is_file_locked(lockfile):
                            arcpy.AddMessage("The output raster is used by other software, waiting for 1 second...\n")
                            time.sleep(1)
                            wait_time += 1
                            if wait_time > 60:
                                arcpy.AddMessage("Skip the plume: {} for NO3-N calculation.".format(pathid))
                                raise Exception("The output raster is used by other software.")
            # print("post_no3 pixeltype is {}".format(arcpy.Describe(post_no3).pixelType))
            # print("Output pixeltype is {}".format(arcpy.Describe(self.no3_output).pixelType))
                    if post_plume is None:
                        plume_name[index] = plume_name[index]
                    else:
                        pixeltype1 = arcpy.Describe(plume_name[index]).pixelType
                        pixeltype2 = arcpy.Describe(post_plume).pixelType
                        filename = post_plume
                        if pixeltype1 != pixeltype2:
                            filename = r'post_tmp'
                            arcpy.management.CopyRaster(post_plume, filename, pixel_type=self.pixeltype)
                        nodataval1 = arcpy.Describe(plume_name[index]).noDataValue
                        nodataval2 = arcpy.Describe(filename).noDataValue
                        nodatavalue = nodataval1
                        if nodataval1 != nodataval2:
                            nodata = "1 " + str(min(nodataval1, nodataval2))
                            arcpy.management.SetRasterProperties(plume_name[index], nodata=nodata)
                            arcpy.management.SetRasterProperties(filename, nodata=nodata)
                            nodatavalue = min(nodataval1, nodataval2)
                        try:
                            temp_raster = os.path.join(tempfile.mkdtemp(), "tmpraster")
                            arcpy.management.CopyRaster(plume_name[index], temp_raster)
                            arcpy.management.Mosaic(filename, plume_name[index], mosaic_type="SUM")
                            # arcpy.management.Delete(filename)
                            if arcpy.Exists(temp_raster):
                                shutil.rmtree(tempfile.mkdtemp())
                        except:
                            try:
                                print("                    Try mosaic to new raster method")
                                if arcpy.Exists(temp_raster):
                                    arcpy.management.MosaicToNewRaster([filename, temp_raster], filepath,
                                                                       "tmp_plume", self.crs, self.pixeltype,
                                                                       self.plume_cell_size, 1, "SUM")
                                if arcpy.Exists(temp_raster):
                                    shutil.rmtree(tempfile.mkdtemp())
                                if arcpy.Exists(plume_name[index]):
                                    arcpy.management.Delete(plume_name[index])
                                arcpy.management.Rename("tmp_plume", plume_name[index])
                            except:
                                print("                    Try con method")

                                extent1 = arcpy.Describe(temp_raster).extent
                                extent2 = arcpy.Describe(filename).extent
                                extent_list = [extent1, extent2]
                                union_extent = extent_list[0]
                                for extent in extent_list[1:]:
                                    union_extent = arcpy.Extent(
                                        min(union_extent.XMin, extent.XMin),
                                        min(union_extent.YMin, extent.YMin),
                                        max(union_extent.XMax, extent.XMax),
                                        max(union_extent.YMax, extent.YMax))
                                arcpy.env.extent = union_extent

                                condition1 = (~arcpy.sa.IsNull(temp_raster)) & (~arcpy.sa.IsNull(filename))
                                condition2 = (~arcpy.sa.IsNull(temp_raster)) & (arcpy.sa.IsNull(filename))
                                sum_raster = arcpy.sa.Con(condition1, arcpy.Raster(temp_raster)+arcpy.Raster(filename),
                                                          arcpy.sa.Con(condition2, temp_raster, filename))
                                if arcpy.Exists(plume_name[index]):
                                    arcpy.management.Delete(plume_name[index])
                                sum_raster.save(plume_name[index])

                except Exception as e:
                    error_name = os.path.join(filepath, 'plm_no3_{}'.format(pathid))
                    arcpy.management.CopyRaster(post_plume, error_name)
                    if not arcpy.Exists(plume_name[index]):
                        if arcpy.Exists(temp_raster):
                            arcpy.management.Rename(temp_raster, plume_name[index])
                    arcpy.AddMessage("[Error]: Failed to mosaic plume {}: ".format(pathid) + str(e))
                    arcpy.AddMessage("Skip the plume: {} for NO3-N calculation.".format(pathid))

        if self.post_process == "medium":
            self.post_process_medium(plume_name)

        for index, infoname in enumerate(info_names):
            if infoname is not None:
                with arcpy.da.InsertCursor(infoname, ["SHAPE@", "PathID", "is2D", "domBdy", "decayCoeff",
                                                     "avgVel", "avgPrsity", "DispL", "DispTH", "DispTV",
                                                     "SourceY", "SourceZ", "MeshDX", "MeshDY", "MeshDZ",
                                                     "plumeTime", "pathTime", "plumeLen", "pathLen", "plumeArea",
                                                     "mslnRtNmr", "massInRate", "massDNRate", "avgAngle", "warp",
                                                     "PostP", "Init_conc", "VolFac", "nextConc", "threshConc",
                                                     "WBId_plume", "WBId_path", "load", "wb_conc"]) as cursor:
                    for row in plume_info:
                        cursor.insertRow(row[index])
        return

    def calculate_single_plume(self, pathid, mean_poro, mean_velo, max_dist):
        """
        Calculate a single plume
        """
        try:
            point, no3_conc, nh4_conc, pho_conc = self.get_initial_conc(pathid)
            ny = int(self.Y / self.plume_cell_size)
            nx = math.ceil(max_dist / self.plume_cell_size)
            nx_old = nx
            if self.post_process != 'none':
                nx = nx + int(ny * self.multiplier)

            if no3_conc < self.threshold and nh4_conc < self.threshold and pho_conc < self.threshold:
                return [None, None, None], [None, None, None, None]

            dr3 = None
            dr4 = None
            drp = None

            if "NH4-N" in self.contaminant_list:
                self.kno3 = self.denitrification_rate
                self.knh4 = self.nitrification_rate * (1 + self.nh4_adsorption * self.bulk_density / mean_poro)
                self.ano3 = no3_conc + self.knh4 / (self.knh4 - self.kno3) * nh4_conc
                self.anh4 = nh4_conc
                if self.solute_mass_type.lower() == 'specified input mass rate':
                    a2 = self.no3_init + self.nh4_init * self.knh4 / (self.knh4 - self.kno3)
                    dispcons = -(self.kno3 / (self.kno3 - self.knh4)) * self.anh4 * (
                            0.5 + 0.5 * math.sqrt(1 + 4 * self.knh4 * self.no3_dispx / mean_velo))
                    dispcons1 = a2 * (0.5 + 0.5 * math.sqrt(1 + 4 * self.kno3 * self.no3_dispx / mean_velo))
                    no3_Z = self.mass_in / (self.Y * mean_poro * mean_velo * self.vol_conversion_factor *
                                            max(dispcons1, dispcons + dispcons1))
                    dispcons = -(self.kno3 / (self.kno3 - self.knh4)) * self.anh4 * (
                            0.5 + 0.5 * math.sqrt(1 + 4 * self.knh4 * self.nh4_dispx / mean_velo))
                    dispcons1 = a2 * (0.5 + 0.5 * math.sqrt(1 + 4 * self.kno3 * self.nh4_dispx / mean_velo))
                    self.nh4_Z = self.mass_in / (self.Y * mean_poro * mean_velo * self.vol_conversion_factor *
                                                 max(dispcons1, dispcons + dispcons1))
                    if self.nh4_Z < 0:
                        self.nh4_Z = min(0.0001, self.zmax) if self.zmax_option else 0.0001
                    if self.no3_Z < 0:
                        self.no3_Z = min(0.0001, self.zmax) if self.zmax_option else 0.0001
                    if self.zmax_option:
                        if self.nh4_Z > self.zmax:
                            self.nh4_Z = self.zmax
                        if self.no3_Z > self.zmax:
                            self.no3_Z = self.zmax
                else:
                    self.no3_Z = self.Z
                    self.nh4_Z = self.Z

                dr4 = DomenicoRobbins(self.solution_type, self.anh4, self.nh4_dispx, self.nh4_dispyz, self.nh4_dispyz,
                                      self.Y, self.nh4_Z, self.knh4, mean_velo, -1)

                dr3 = DomenicoRobbins(self.solution_type, self.ano3, self.no3_dispx, self.no3_dispyz, self.no3_dispyz,
                                      self.Y, self.no3_Z, self.kno3, mean_velo, -1)

            elif "NO3-N" in self.contaminant_list and "NH4-N" not in self.contaminant_list:
                self.kno3 = self.denitrification_rate
                self.ano3 = no3_conc
                self.knh4 = 0.0
                self.anh4 = 0.0
                if self.solute_mass_type.lower() == 'specified input mass rate':
                    self.no3_Z = self.mass_in * 2 / (
                                 self.Y * mean_poro * mean_velo * self.ano3 * self.vol_conversion_factor * (
                                 1 + math.sqrt(1 + 4 * self.kno3 * self.no3_dispx / mean_velo)))
                    if self.no3_Z < 0:
                        self.no3_Z = min(0.0001, self.zmax) if self.zmax_option else 0.0001
                    if self.zmax_option:
                        if self.no3_Z > self.zmax:
                            self.no3_Z = self.zmax
                else:
                    self.no3_Z = self.Z
                dr3 = DomenicoRobbins(self.solution_type, self.ano3, self.no3_dispx, self.no3_dispyz, self.no3_dispyz,
                                      self.Y, self.no3_Z, self.kno3, mean_velo, -1)
            if "PO4-P" in self.contaminant_list:
                self.apho = pho_conc
                if self.phos_choice.lower() == 'linear':
                    self.kpho = self.phos_prep * (1 + self.phos_kd * self.bulk_density / mean_poro)
                else:
                    self.kpho = (1 + self.bulk_density / mean_poro * self.phos_smax * self.phos_kl / (
                                    1 + self.phos_kl * self.apho)) * self.phos_prep
                if self.solute_mass_type.lower() == 'specified input mass rate':
                    self.phos_Z = self.mass_in_phos * 2 / (
                                 self.Y * mean_poro * mean_velo * self.apho * self.vol_conversion_factor * (
                                 1 + math.sqrt(1 + 4 * self.apho * self.phos_dispx / mean_velo)))
                    if self.phos_Z < 0:
                        self.phos_Z = min(0.0001, self.zmax) if self.zmax_option else 0.0001
                    if self.zmax_option:
                        if self.phos_Z > self.zmax:
                            self.phos_Z = self.zmax
                else:
                    self.phos_Z = self.Z
                drp = DomenicoRobbins(self.solution_type, self.apho, self.phos_dispx, self.phos_dispyz, self.phos_dispyz,
                                      self.Y, self.phos_Z, self.kpho, mean_velo, -1)

            # calculate the plume
            edge = 500
            while True:
                xlist = np.arange(1, nx + 1) * self.plume_cell_size  # - self.plume_cell_size / 2
                if ny % 2 != 0:
                    ylist = np.arange(-edge, edge + 1) * self.plume_cell_size
                else:
                    ylist = np.arange(-edge, edge) * self.plume_cell_size  # + self.plume_cell_size / 2

                no3result = np.zeros((2, 2))
                nh4result = np.zeros((2, 2))
                phoresult = np.zeros((2, 2))

                if dr3 is not None:
                    no3result = dr3.eval(xlist, ylist, 0)
                if dr4 is not None:
                    nh4result = dr4.eval(xlist, ylist, 0)
                if drp is not None:
                    phoresult = drp.eval(xlist, ylist, 0)

                if "NO3-N" in self.contaminant_list and "NH4-N" in self.contaminant_list:
                    no3result = no3result - self.knh4 / (self.knh4 - self.kno3) * nh4result

                if no3result[0, :].any() > self.threshold or nh4result[0, :].any() > self.threshold or \
                    phoresult[0, :].any() > self.threshold:
                    edge = edge + 100
                else:
                    break

            check = [dr4, dr3, drp]
            results = [nh4result, no3result, phoresult]
            filtered_results = []
            for index, type_cont in enumerate(check):
                if type_cont is not None:
                    plumeresult = results[index]
                    if index == 0:
                        inivalue = nh4_conc
                    elif index == 1:
                        inivalue = no3_conc
                    else:
                        inivalue = pho_conc
                    if plumeresult[0, :].all() <= self.threshold and plumeresult[-1, :].all() <= self.threshold:
                        plumey = np.zeros((len(ylist)))
                        if ny % 2 != 0:
                            plumey[math.floor(len(ylist) / 2) - math.floor(ny / 2):
                                   math.floor(len(ylist) / 2) - math.floor(ny / 2) + ny] = inivalue
                        else:
                            plumey[math.floor(len(ylist) / 2 - ny / 2):
                                   math.floor(len(ylist) / 2 + ny / 2)] = inivalue
                        plumeresult = np.hstack((plumey.reshape(-1, 1), plumeresult))

                        row_to_delete = np.all(plumeresult <= self.threshold, axis=1)
                        filtered_result = plumeresult[~row_to_delete]
                        cols_to_delete = np.all(filtered_result <= self.threshold, axis=0)
                        filtered_result = filtered_result[:, ~cols_to_delete]
                        filtered_results.append(filtered_result)
                else:
                    filtered_results.append(None)

            no3_plume_len = nx_old
            nh4_plume_len = nx_old
            pho_plume_len = nx_old
            if self.post_process != 'none':
                if filtered_results[0] is not None and filtered_results[0].shape[1] < nx_old:
                    nh4_plume_len = filtered_results[0].shape[1]
                elif filtered_results[0] is None:
                    nh4_plume_len = 0
                if filtered_results[1] is not None and filtered_results[1].shape[1] < nx_old:
                    no3_plume_len = filtered_results[1].shape[1]
                elif filtered_results[1] is None:
                    no3_plume_len = 0
                if filtered_results[2] is not None and filtered_results[2].shape[1] < nx_old:
                    pho_plume_len = filtered_results[2].shape[1]
                elif filtered_results[2] is None:
                    pho_plume_len = 0
            output_list = [point, nh4_plume_len, no3_plume_len, pho_plume_len]
            return filtered_results, output_list

        except Exception as e:
            arcpy.AddMessage("[Error] Calculate single plume {}: ".format(pathid) + str(e))
            arcpy.AddMessage("Skip the plume: {} for calculation.".format(pathid))
            return None, None

    def calculate_info(self, filtered, tmp_list, pathid, mean_poro, mean_velo, mean_angle,
                       max_dist, maxtime, wbid, path_wbid):
        """
        Calculate the info file
        """
        point = tmp_list[0]
        segments = []

        for index, plume in enumerate(filtered):
            if plume is not None:
                if index == 0:
                    plume_name = "NH4-N"
                    z_value = self.nh4_Z
                    init_value = self.nh4_init
                    dispx = self.nh4_dispx
                    dispyz = self.nh4_dispyz
                    kvalue = self.knh4
                elif index == 1:
                    plume_name = "NO3-N"
                    z_value = self.no3_Z
                    init_value = self.no3_init
                    dispx = self.no3_dispx
                    dispyz = self.no3_dispyz
                    kvalue = self.kno3
                else:
                    plume_name = "PO4-P"
                    z_value = self.phos_Z
                    init_value = self.pho_init
                    dispx = self.phos_dispx
                    dispyz = self.phos_dispyz
                    kvalue = self.kpho

                if plume.shape[1] < 1:
                    segment = [point, pathid, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                               0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    segments.append(segment)
                    continue

                plumelen = tmp_list[index + 1] * self.plume_cell_size
                plume_result = plume[:, 0: tmp_list[index + 1]]

                plume_area = (plume_result > self.threshold).sum() * self.plume_cell_size ** 2
                non_zero_indices = np.nonzero(plume_result[:, 0])
                if plume_result.shape[1] > 1:
                    massinratemt3d = (
                                mean_poro * self.plume_cell_size * z_value * mean_velo * self.vol_conversion_factor * (
                                    init_value - dispx * (
                                        plume_result[non_zero_indices, 1] - init_value) / self.plume_cell_size)).sum()
                else:
                    massinratemt3d = (mean_poro * self.plume_cell_size * z_value * mean_velo *
                                      self.vol_conversion_factor * (init_value - dispx * (0 - init_value) / self.plume_cell_size))

                if self.solute_mass_type.lower() == 'specified input mass rate':
                    dombdy = 1
                    if "NH4-N" in self.contaminant_list and "NO3-N" in self.contaminant_list:
                        if index == 0:
                            massin = self.mass_in * self.nh4_init / (self.nh4_init + self.no3_init)
                        elif index == 1:
                            massin = self.mass_in * self.no3_init / (self.nh4_init + self.no3_init)
                    elif "NO3-N" in self.contaminant_list and "NH4-N" not in self.contaminant_list:
                        if index == 1:
                            massin = self.mass_in
                    if "PO4-P" in self.contaminant_list:
                        if index == 2:
                            massin = self.mass_in_phos
                elif self.solute_mass_type.lower() == 'specified z':
                    dombdy = 2
                    if "NH4-N" in self.contaminant_list and "NO3-N" in self.contaminant_list:
                        if index == 0:
                            massin = mean_velo * mean_poro * z_value * self.Y * self.vol_conversion_factor * \
                                     init_value * (0.5 + 0.5 * math.sqrt(1 + (4 * self.knh4 * dispx) / mean_velo))
                        elif index == 1:
                            dispcon0 = 0.5 * self.nh4_init * (self.knh4 / (self.knh4 - self.kno3)) * (
                                    math.sqrt(1 + 4 * self.kno3 * self.no3_dispx / mean_velo) - math.sqrt(
                                1 + (4 * self.knh4 * self.no3_dispx) / mean_velo))
                            dispcon1 = self.no3_init * (
                                        0.5 + 0.5 * math.sqrt(1 + (4 * self.kno3 * self.no3_dispx) / mean_velo))
                            massin = mean_velo * mean_poro * self.no3_Z * self.Y * self.vol_conversion_factor * max(
                                dispcon1, dispcon1 + dispcon0)
                    elif "NO3-N" in self.contaminant_list and "NH4-N" not in self.contaminant_list:
                        if index == 1:
                            massin = mean_velo * mean_poro * z_value * self.Y * self.vol_conversion_factor * \
                                     init_value * (0.5 + 0.5 * math.sqrt(1 + (4 * self.kno3 * dispx) / mean_velo))
                            # advcon = mean_velo * mean_poro * z_value * self.Y * self.vol_conversion_factor * init_value
                            # nonzero_indices = np.flatnonzero(plume_result[:, 0])
                            # discon = mean_velo * mean_poro * z_value * self.vol_conversion_factor * \
                            #     dispx * (plume_result[nonzero_indices, 1] - init_value).sum()
                            # massin = advcon - discon
                    if "PO4-P" in self.contaminant_list:
                        if index == 2:
                            massin = mean_velo * mean_poro * z_value * self.Y * self.vol_conversion_factor * \
                                     init_value * (0.5 + 0.5 * math.sqrt(1 + (4 * self.kpho * dispx) / mean_velo))

                plume_nextconc = 0
                if plume_name == "NO3-N":
                    massmdn = (self.kno3 * mean_poro * self.no3_Z * self.plume_cell_size * self.plume_cell_size *
                               self.vol_conversion_factor * plume_result[:, 1:]).sum()
                    if plume_result.shape[1] > 1:
                        plume_nextconc = plume_result[:, 1].max()
                    if "NH4-N" in self.contaminant_list:
                        load = self.nh4massmdn + massin - massmdn
                    else:
                        load = massin - massmdn
                elif plume_name == "NH4-N":
                    massmdn = (self.knh4 * mean_poro * self.nh4_Z * self.plume_cell_size * self.plume_cell_size *
                               self.vol_conversion_factor * plume_result[:, 1:]).sum()
                    self.nh4massmdn = massmdn
                    if plume_result.shape[1] > 1:
                        plume_nextconc = plume_result[:, 1].max()
                    load = massin - massmdn
                else:
                    massmdn = (self.kpho * mean_poro * self.phos_Z * self.plume_cell_size * self.plume_cell_size *
                               self.vol_conversion_factor * plume_result[:, 1:]).sum()
                    if plume_result.shape[1] > 1:
                        plume_nextconc = plume_result[:, 1].max()
                    load = massin - massmdn

                if self.post_process == "none":
                    processes = 0
                elif self.post_process == "medium":
                    processes = 1
                elif self.post_process == "full":
                    processes = 2

                if self.warp_method == "spline":
                    warp_method = 0
                elif self.warp_method == "polyorder1":
                    warp_method = 1
                elif self.warp_method == "polyorder2":
                    warp_method = 2

                if plumelen < max_dist:
                    wbid = -1
                else:
                    plumelen = max_dist
                    wbid = wbid
                nrow, ncol = plume_result.shape
                if int(plumelen/self.plume_cell_size) - 1 < ncol:
                    wb_conc = plume_result[nrow//2, int(plumelen/self.plume_cell_size) - 1]
                else:
                    wb_conc = plume_result[nrow//2, ncol - 1]

                if load < 0:
                    load = 0
                if wbid == -1:
                    load = 0

                # if massin < massmdn:
                #     massmdn = massin

                segment = [point, pathid, 1, dombdy, kvalue, mean_velo, mean_poro, dispx, dispyz, 0, self.Y,
                           z_value, self.plume_cell_size, self.plume_cell_size, z_value, -1, maxtime, plumelen,
                           max_dist, plume_area, massinratemt3d, massin, massmdn, mean_angle, warp_method, processes,
                           init_value, self.vol_conversion_factor, plume_nextconc, self.threshold, wbid, path_wbid,
                           load, wb_conc]
                segments.append(segment)
            else:
                segments.append(None)
        return segments

    def warp_affine_transformation(self, plume_array, pathid, xvalue, yvalue, segment):
        """
        Warp the plume
        """
        row, col = plume_array.shape
        nshape = row + col
        max_value = plume_array.max()

        if row % 2 == 0:
            input_array = np.zeros((2 * nshape, 2 * nshape))
            input_array[nshape - int(row / 2): nshape + int(row / 2), nshape: nshape + col] = plume_array
        else:
            input_array = np.zeros((2 * nshape + 1, 2 * nshape))
            input_array[nshape - int(row / 2): nshape + int(row / 2) + 1, nshape: nshape + col] = plume_array

        center_pts, body_pts = self.get_control_points(plume_array)
        target_center_pts, target_body_pts = self.get_target_points(segment, center_pts, body_pts)

        source_pts = np.vstack((center_pts, body_pts[:, [0, 1]], body_pts[:, [0, 2]]))
        deform_pts = np.vstack((target_center_pts, target_body_pts))

        # col_max = math.ceil(max(source_pts[:, 0].max(), deform_pts[:, 0].max()))
        # col_min = math.ceil(min(source_pts[:, 0].min(), deform_pts[:, 0].min()))
        # row_max = math.ceil(max(source_pts[:, 1].max(), deform_pts[:, 1].max()))
        # row_min = math.ceil(min(source_pts[:, 1].min(), deform_pts[:, 1].min()))
        # input_array = input_array[row_min - 1: row_max + 2, col_min - 1:col_max + 2]
        # source_pts = source_pts - np.array([col_min, row_min]) + 1
        # deform_pts = deform_pts - np.array([col_min, row_min]) + 1

        # tps = ThinPlateSpline(0.5)
        # tps.fit(source_pts, deform_pts)
        #
        # height, width = input_array.shape
        # output_indices = np.indices((height, width), dtype=np.int16).transpose(1, 2, 0)  # Shape: (H, W, 2)
        # input_indices = tps.transform(output_indices.reshape(-1, 2)).reshape(height, width, 2)
        # warped_array = map_coordinates(input_array, input_indices.transpose(2, 0, 1))

        # target_body_pts[:, 0] = target_body_pts[:, 0] - col_min
        # target_body_pts[:, 1: 2] = target_body_pts[:, 1: 2] - row_min
        # modified_warped_array = self.modify_warped_array(warped_array, target_body_pts, plume_array, max_value)
        #
        # if row % 2 == 0:
        #     new_xvalue = xvalue - self.plume_cell_size * (nshape + 1 / 2)
        #     new_yvalue = yvalue - self.plume_cell_size * (nshape + 1 / 2)
        # else:
        #     new_xvalue = xvalue - self.plume_cell_size * (nshape + 1 / 2)
        #     new_yvalue = yvalue - self.plume_cell_size * (nshape + 1 / 2)

        # plt.figure(figsize=(10, 5))
        # plt.subplot(1, 2, 1)
        # input_array[input_array < self.threshold] = np.nan
        # plt.imshow(input_array)
        # plt.scatter(source_pts[:, 0], source_pts[:, 1], c='r')
        # plt.subplot(1, 2, 2)
        # plt.imshow(modified_warped_array)
        # plt.scatter(deform_pts[:, 0] + 1 / 2, deform_pts[:, 1] + 1 / 2, c='r')
        # plt.gca().invert_yaxis()
        # figname = name + '_{}'.format(pathid)
        # plt.savefig(figname+'.png')
        # # plt.show()

        name = r'memory\plume_raster'

        # warped_raster = arcpy.NumPyArrayToRaster(modified_warped_array[::-1], arcpy.Point(new_xvalue, new_yvalue),
        #                                          self.plume_cell_size, self.plume_cell_size)
        # arcpy.management.DefineProjection(warped_raster, self.crs)
        # warped_raster.save(name)

        return name

    def warp_arcgis(self, plume_arrays, pathid, xvalue, yvalue, segment):
        """
        Warp the plume
        """
        perstepnum = segment['TotDist'].iloc[0] / self.plume_cell_size
        warped_plumes = []
        target_body_pts_list = []
        lengths = []
        target_body_pts_term = None

        for index, plume_array in enumerate(plume_arrays):
            if plume_array is None:
                warped_plumes.append(None)
                target_body_pts_list.append(None)
                lengths.append(0)
            else:
                lengths.append(plume_array.shape[1])
                try:
                    y_lower_left = yvalue - plume_array.shape[0] * self.plume_cell_size / 2
                    plume_array[plume_array <= self.threshold] = np.nan
                    plume_array = plume_array.astype(np.float32)

                    langle = np.array(segment['DirAngle'][
                                      0:int(plume_array.shape[1] * self.plume_cell_size / segment['TotDist'].iloc[0])])
                    if len(langle) > 1:
                        diffs = (np.diff(langle) + 180) % 360 - 180
                        maxangle_diff = np.max(np.abs(diffs))
                    else:
                        maxangle_diff = 90

                    plume_raster = arcpy.NumPyArrayToRaster(plume_array, arcpy.Point(xvalue, y_lower_left),
                                                            self.plume_cell_size, self.plume_cell_size)
                    if index == 0:
                        plume_name = r'memory\pnh4_{}'.format(pathid)
                        name = r'memory\rnh4_{}'.format(pathid)
                    elif index == 1:
                        plume_name = r'memory\pno3_{}'.format(pathid)
                        name = r'memory\rno3_{}'.format(pathid)
                    else:
                        plume_name = r'memory\phos_{}'.format(pathid)
                        name = r'memory\rphos_{}'.format(pathid)
                    if arcpy.Exists(plume_name):
                        arcpy.management.Delete(plume_name)
                    if arcpy.Exists(name):
                        arcpy.management.Delete(name)
                    plume_raster.save(plume_name)
                    arcpy.management.DefineProjection(plume_name, self.crs)

                    if maxangle_diff < 0.1 and abs(langle[0] - 90) < 0.1:
                        warped_plumes.append(plume_name)
                        target_body_pts_list.append(None)
                        continue

                    if plume_array.shape[1] <= perstepnum or maxangle_diff > 30:
                        end_number = int(plume_array.shape[1] * self.plume_cell_size / segment['TotDist'].iloc[0])
                        if end_number > len(segment['Shape']):
                            end_number = len(segment['Shape'])
                        elif end_number < 1:
                            end_number = 1
                        first_x = segment['Shape'].iloc[0].firstPoint.X
                        first_y = segment['Shape'].iloc[0].firstPoint.Y
                        last_x = segment['Shape'].iloc[end_number - 1].lastPoint.X
                        last_y = segment['Shape'].iloc[end_number - 1].lastPoint.Y
                        if first_x == last_x:
                            if first_y > last_y:
                                angle = 90
                            else:
                                angle = 270
                        else:
                            angle = math.degrees(math.atan2((last_y - first_y), (last_x - first_x)))
                        if (last_y - first_y) >= 0:
                            angle = 360 - angle
                        else:
                            angle = - angle
                        pivot_point = "" + str(xvalue) + " " + str(yvalue)
                        arcpy.management.Rotate(plume_name, name, angle, pivot_point, "NEAREST")
                        warped_plumes.append(name)
                    else:
                        center_pts, body_pts = self.get_control_points(plume_array, True)

                        if center_pts is None and body_pts is None:
                            return plume_name, None

                        results = self.get_target_points_gis(segment, center_pts, body_pts, xvalue, yvalue)
                        target_center_pts, origin_center_pts, target_body_pts, origin_body_pts = results
                        if len(target_center_pts) > 10:
                            source_control_points = np.vstack((origin_center_pts, origin_body_pts))
                            target_control_points = np.vstack((target_center_pts, target_body_pts))
                        else:
                            source_control_points = origin_center_pts
                            target_control_points = target_center_pts

                        # shp1_list = []
                        # shp2_list = []
                        # for index in range(len(source_control_points)):
                        #     xvalue = source_control_points[index][0]
                        #     yvalue = source_control_points[index][1]
                        #     point = arcpy.Point(xvalue, yvalue)
                        #     geometry = arcpy.PointGeometry(point, self.crs)
                        #     shp1_list.append(geometry)
                        #
                        #     xvalue = target_control_points[index][0]
                        #     yvalue = target_control_points[index][1]
                        #     point = arcpy.Point(xvalue, yvalue)
                        #     geometry = arcpy.PointGeometry(point, self.crs)
                        #     shp2_list.append(geometry)
                        # shp1_name = 'shp1.shp'
                        # arcpy.management.CopyFeatures(shp1_list, shp1_name)
                        # shp2_name = 'shp2.shp'
                        # arcpy.management.CopyFeatures(shp2_list, shp2_name)

                        source_control_points = ';'.join([f"'{x} {y}'" for x, y in source_control_points])
                        target_control_points = ';'.join([f"'{x} {y}'" for x, y in target_control_points])

                        try:
                            if body_pts is None:
                                raise Exception("No body points")
                            arcpy.management.Warp(plume_name, source_control_points, target_control_points, name,
                                                  self.warp_method.upper(), "BILINEAR")
                            if arcpy.Describe(
                                name).meanCellHeight == 0 or arcpy.Describe(name).meanCellWidth == 0 or arcpy.Raster(
                                name).maximum is None or arcpy.Raster(name).maximum < self.threshold:
                                # abs(arcpy.Describe(
                                #     name).meanCellHeight - self.plume_cell_size) > self.plume_cell_size or abs(
                                #     arcpy.Describe(
                                #         name).meanCellWidth - self.plume_cell_size) > self.plume_cell_size or
                                # arcpy.AddMessage("              Warp failed for plume {}, use rotate method.".format(pathid))
                                raise Exception("Warp error!")
                            if arcpy.Exists(plume_name):
                                arcpy.management.Delete(plume_name)
                            warped_plumes.append(name)
                            target_body_pts_term = target_body_pts
                        except:
                            end_number = int(plume_array.shape[1] * self.plume_cell_size / segment['TotDist'].iloc[0])
                            if end_number > len(segment['Shape']):
                                end_number = len(segment['Shape'])
                            elif end_number < 1:
                                end_number = 1
                            first_x = segment['Shape'].iloc[0].firstPoint.X
                            first_y = segment['Shape'].iloc[0].firstPoint.Y
                            last_x = segment['Shape'].iloc[end_number - 1].lastPoint.X
                            last_y = segment['Shape'].iloc[end_number - 1].lastPoint.Y
                            if first_x == last_x:
                                if first_y > last_y:
                                    angle = 90
                                else:
                                    angle = 270
                            else:
                                angle = math.degrees(math.atan2((last_y - first_y), (last_x - first_x)))
                            if (last_y - first_y) >= 0:
                                angle = 360 - angle
                            else:
                                angle = - angle
                            pivot_point = "" + str(xvalue) + " " + str(yvalue)
                            try:
                                if arcpy.Exists(name):
                                    arcpy.management.Delete(name)
                            except:
                                print("Delete failed")
                            arcpy.management.Rotate(plume_name, name, angle, pivot_point, "NEAREST")
                            warped_plumes.append(name)
                except Exception as e:
                    arcpy.AddMessage("[Error] Plume {} cannot be warped.".format(pathid) + str(e))
                    arcpy.AddMessage("Skip the plume: {} for warp calculation.".format(pathid))
                    warped_plumes.append(None)
                    target_body_pts_list.append(None)
                    continue
            target_body_pts_list.append(target_body_pts_term)
        return warped_plumes, target_body_pts_list, lengths

    def post_process_plume(self, lengths, name_list, pathid, segment, target_body_pts_list, output_raster_list):
        """
        Post process the plume
        """
        fnames = []
        maxDist = segment['TotDist'].iloc[-1]
        for index, name in enumerate(name_list):
            if name is None:
                fnames.append(None)
                continue
            else:
                if index == 0:
                    fname = r'memory\rsn4_{}'.format(pathid)
                elif index == 1:
                    fname = r'memory\rsn3_{}'.format(pathid)
                else:
                    fname = r'memory\rsp_{}'.format(pathid)

                if pathid != 0:
                    try:
                        out_raster = arcpy.sa.SetNull(name, name, "VALUE < {}".format(self.threshold))
                        max_value = arcpy.Raster(out_raster).maximum
                        if float(max_value) < self.threshold:
                            fnames.append(None)
                            continue

                        arcpy.env.snapRaster = output_raster_list[index]
                        arcpy.management.Resample(name, fname, str(self.plume_cell_size), "NEAREST")
                        arcpy.env.snapRaster = None
                    except Exception as e:
                        continue
                else:
                    fname = name

                if lengths[index] * self.plume_cell_size < maxDist or target_body_pts_list[index] is None:
                    fnames.append(fname)
                    continue

                if self.post_process == 'none' or self.post_process == 'medium':
                    if pathid != 0:
                        fnames.append(fname)
                    else:
                        fnames.append(name)
                elif self.post_process == 'full':
                    try:
                        point_list = []
                        for row in target_body_pts_list[index]:
                            point = arcpy.Point(row[0], row[1])
                            point_list.append(point)
                        polyline = arcpy.Polyline(arcpy.Array(point_list), self.crs)

                        arcpy.management.CopyFeatures(polyline, r'memory\polyline')
                        arcpy.management.Delete(polyline)

                        arcpy.management.FeatureToPolygon([polyline], r'memory\linecheck', "", "NO_ATTRIBUTES")
                        if arcpy.management.GetCount(r'memory\linecheck')[0] == "1":
                            arcpy.management.Delete(r'memory\linecheck')
                            arcpy.management.Delete(polyline)
                            fnames.append(fname)
                            continue

                        if arcpy.Exists(r'memory\slwb'):
                            arcpy.management.Delete(r'memory\slwb')
                        arcpy.analysis.Select(self.waterbodies, r'memory\slwb',
                                              "fid = {}".format(segment["WBId"].iloc[-1]))

                        inFeatures = [r'memory\polyline', r'memory\slwb']
                        outFeatures = r'memory\polygon'
                        arcpy.management.FeatureToPolygon(inFeatures, outFeatures, "", "NO_ATTRIBUTES")
                        Erase_polygon = r'memory\Erase_polygon'
                        arcpy.analysis.Erase(outFeatures, r'memory\slwb', Erase_polygon)

                        if index == 0:
                            save_name = r'memory\pfn4_{}'.format(pathid)
                        elif index == 1:
                            save_name = r'memory\pfn3_{}'.format(pathid)
                        else:
                            save_name = r'memory\pfph_{}'.format(pathid)
                        if arcpy.Exists(save_name):
                            arcpy.management.Delete(save_name)

                        if arcpy.management.GetCount(Erase_polygon)[0] == "1":
                            result = arcpy.sa.ExtractByMask(fname, Erase_polygon)
                            result.save(save_name)
                            fnames.append(save_name)
                            arcpy.management.Delete(polyline)
                            arcpy.management.Delete(outFeatures)
                            arcpy.management.Delete(Erase_polygon)
                            continue

                        elif arcpy.management.GetCount(Erase_polygon)[0] == "0":
                            while True:
                                with arcpy.da.UpdateCursor(r'memory\polyline', ['SHAPE@']) as cursor:
                                    for row in cursor:
                                        polyline = row[0]

                                        first_point = polyline.firstPoint
                                        last_point = polyline.lastPoint
                                        new_first_x = 2 * first_point.X - polyline.getPart(0)[1].X
                                        new_first_y = 2 * first_point.Y - polyline.getPart(0)[1].Y
                                        new_last_x = 2 * last_point.X - polyline.getPart(0)[-2].X
                                        new_last_y = 2 * last_point.Y - polyline.getPart(0)[-2].Y

                                        new_part = arcpy.Array()
                                        new_part.add(arcpy.Point(new_first_x, new_first_y))
                                        for point in polyline.getPart(0):
                                            new_part.add(point)
                                        new_part.add(arcpy.Point(new_last_x, new_last_y))

                                        new_polyline = arcpy.Polyline(new_part)
                                        row[0] = new_polyline
                                        cursor.updateRow(row)

                                arcpy.analysis.Intersect([r'memory\polyline', r'memory\slwb'], r'memory\Intersect')
                                ppp = arcpy.da.SearchCursor(r'memory\Intersect', ["SHAPE@"]).next()[0]
                                if ppp.isMultipart:
                                    break

                            if arcpy.Exists(r'memory\linecheck'):
                                arcpy.management.Delete(r'memory\linecheck')
                            arcpy.management.FeatureToPolygon([polyline], r'memory\linecheck', "", "NO_ATTRIBUTES")
                            if arcpy.management.GetCount(r'memory\linecheck')[0] == "1":
                                arcpy.management.Delete(r'memory\linecheck')
                                arcpy.management.Delete(polyline)
                                fnames.append(fname)
                                continue

                            inFeatures = [r'memory\polyline', r'memory\slwb']
                            outFeatures = r'memory\polygon'
                            arcpy.management.FeatureToPolygon(inFeatures, outFeatures, "", "NO_ATTRIBUTES")
                            Erase_polygon = r'memory\Erase_polygon'
                            arcpy.analysis.Erase(outFeatures, r'memory\slwb', Erase_polygon)

                            result = arcpy.sa.ExtractByMask(fname, Erase_polygon)
                            result.save(save_name)
                            fnames.append(save_name)
                        else:
                            fnames.append(fname)
                            continue
                    except Exception as e:
                        arcpy.AddMessage("[Error] Post process plume {}: ".format(pathid) + str(e))
                        arcpy.AddMessage("Skip the plume: {} for post process.".format(pathid))
                        fnames.append(fname)
        return fnames

    def post_process_medium(self, plume_names):
        """
        Medium post process the plume
        """
        for index, name in enumerate(plume_names):
            if name is not None:
                try:
                    # if arcpy.Describe(name).extent.overlaps(arcpy.Describe(self.waterbodies).extent):
                    result = arcpy.sa.ExtractByMask(name, self.waterbodies, "OUTSIDE", name)

                    arcpy.env.snapRaster = None
                    result = arcpy.sa.SetNull(result, result, "VALUE < {}".format(self.threshold))
                    result = arcpy.sa.SetNull(result, result, "VALUE > {}".format(10000))
                    result.save(name)

                    polygon = arcpy.sa.Con(result, 1, "", "VALUE > 0")
                    shp_name = r"memory\polygon"
                    arcpy.conversion.RasterToPolygon(polygon, shp_name, "NO_SIMPLIFY", "VALUE")
                    shp_buffer = r"memory\buffer"
                    arcpy.analysis.Buffer(shp_name, shp_buffer, "1 Meters")

                    with arcpy.da.UpdateCursor(shp_buffer, ['SHAPE@']) as poly_cursor:
                        for poly_row in poly_cursor:
                            polygon_geom = poly_row[0]

                            with arcpy.da.SearchCursor(self.source_location, ['SHAPE@']) as point_cursor:
                                point_inside_polygon = False
                                for point_row in point_cursor:
                                    point_geom = point_row[0]

                                    if polygon_geom.contains(point_geom):
                                        point_inside_polygon = True
                                        break

                                if not point_inside_polygon:
                                    poly_cursor.deleteRow()

                    result = arcpy.management.GetCount(shp_buffer)
                    count = int(result.getOutput(0))
                    if count < 1:
                        continue
                    outpt = arcpy.sa.ExtractByMask(name, shp_buffer, "INSIDE", name)
                    outpt.save(name)

                except Exception as e:
                    # arcpy.AddMessage("[Error] Post process medium: " + str(e))
                    continue
        return None

    def get_initial_conc(self, fid):
        """
        Get the initial concentration of the no3 and nh4
        """
        try:
            desc = arcpy.Describe(self.source_location)
            field_list = desc.fields
            no3_exists = any(field.name.lower() == "no3_conc" for field in field_list)
            nh4_exists = any(field.name.lower() == "nh4_conc" for field in field_list)
            pho_exists = any(field.name.lower() == "p_conc" for field in field_list)

            query = "FID = {}".format(fid)
            point = None

            if no3_exists and "NO3-N" in self.contaminant_list:
                cursor = arcpy.da.SearchCursor(self.source_location, ["SHAPE@", "FID", "no3_conc"], query)
                row = cursor.next()
                point = row[0]
                no3_conc = row[2]
                self.no3_init = no3_conc
            elif "NO3-N" in self.contaminant_list and (not no3_exists):
                no3_conc = self.no3_init
            else:
                no3_conc = 0

            if nh4_exists and "NH4-N" in self.contaminant_list:
                cursor = arcpy.da.SearchCursor(self.source_location, ["SHAPE@", "FID", "nh4_conc"], query)
                row = cursor.next()
                if point is None:
                    point = row[0]
                nh4_conc = row[2]
                self.nh4_init = nh4_conc
            elif "NH4-N" in self.contaminant_list and (not nh4_exists):
                nh4_conc = self.nh4_init
            else:
                nh4_conc = 0

            if pho_exists and "PO4-P" in self.contaminant_list:
                cursor = arcpy.da.SearchCursor(self.source_location, ["SHAPE@", "FID", "p_conc"], query)
                row = cursor.next()
                if point is None:
                    point = row[0]
                pho_conc = row[2]
                self.pho_init = pho_conc
            elif "PO4-P" in self.contaminant_list and (not pho_exists):
                pho_conc = self.pho_init
            else:
                pho_conc = 0

            if point is None:
                cursor = arcpy.da.SearchCursor(self.source_location, ["SHAPE@", "FID"], query)
                row = cursor.next()
                point = row[0]

            return point, no3_conc, nh4_conc, pho_conc
        except Exception as e:
            arcpy.AddMessage("[Error] Can not get initial value of NO3 and NH4 for point {}: ".format(fid) + str(e))
            return None, None, None, None

    def create_new_plume_data_shapefile(self, start_num, end_num, flag=False):
        """Create a new shapefile to store the plume data
        """
        try:
            if "NO3-N" in self.contaminant_list:
                if flag:
                    no3info_name = self.no3_output_info
                else:
                    no3info_name = "n3i{}_{}".format(start_num, end_num)
                if arcpy.Exists(os.path.join(self.no3_dir, no3info_name)):
                    arcpy.Delete_management(os.path.join(self.no3_dir, no3info_name))
                create_shapefile(self.no3_dir, no3info_name, self.crs)
            else:
                no3info_name = None
            if "NH4-N" in self.contaminant_list:
                if flag:
                    nh4info_name = self.nh4_output_info
                else:
                    nh4info_name = "n4i{}_{}".format(start_num, end_num)
                if arcpy.Exists(os.path.join(self.nh4_dir, nh4info_name)):
                    arcpy.Delete_management(os.path.join(self.nh4_dir, nh4info_name))
                create_shapefile(self.nh4_dir, nh4info_name, self.crs)
            else:
                nh4info_name = None
            if "PO4-P" in self.contaminant_list:
                if flag:
                    phoinfo_name = self.phos_output_info
                else:
                    phoinfo_name = "pi{}_{}".format(start_num, end_num)
                if arcpy.Exists(os.path.join(self.phos_dir, phoinfo_name)):
                    arcpy.Delete_management(os.path.join(self.phos_dir, phoinfo_name))
                create_shapefile(self.phos_dir, phoinfo_name, self.crs)
            else:
                phoinfo_name = None
        except Exception as e:
            arcpy.AddMessage("[Error] Can not create new plume data shapefile: " + str(e))
            sys.exit(-1)
        return nh4info_name, no3info_name, phoinfo_name

    def get_control_points(self, plume_array, ifgis=False):
        """
        Get the control points for warping
        """
        plumelen = plume_array.shape[1]
        if plumelen < 20:
            warp_ctrl_pt_spacing = 2
            center_number = math.ceil(plumelen / warp_ctrl_pt_spacing) + 1
        else:
            # get the number of center line control points
            warp_ctrl_pt_spacing = self.warp_ctrl_pt_spacing
            center_number = math.ceil(plumelen / warp_ctrl_pt_spacing) + 1
            while center_number < 10:
                warp_ctrl_pt_spacing = warp_ctrl_pt_spacing / 2
                center_number = math.ceil(plumelen / warp_ctrl_pt_spacing) + 1
                if warp_ctrl_pt_spacing <= 2:
                    warp_ctrl_pt_spacing = 2
                    center_number = math.ceil(plumelen / warp_ctrl_pt_spacing) + 1
                    break

        # get the center line control points
        index_array = np.arange(0, plumelen)
        center_pts = index_array[::int(warp_ctrl_pt_spacing)]
        if (plumelen - 1) % warp_ctrl_pt_spacing != 0:
            center_pts = np.append(center_pts, plumelen - 1)
        if plumelen > 5:
            values_to_add = np.array([1, 2, 3, 4, 5])
        else:
            values_to_add = np.arange(1, plumelen)
        center_pts = np.sort(np.append(center_pts, values_to_add))
        center_pts = np.unique(center_pts)
        if len(center_pts) < 10:
            return center_pts, None

        # get the start and end points bigger than the threshold
        plume_array = np.nan_to_num(plume_array)
        if np.nanmax(plume_array[:, -1]) >= self.threshold:
            cols = plume_array[:, center_pts]
        else:
            cols = plume_array[:, center_pts[:-1]]
        starts = []
        for col in cols.T:
            start = np.where(col > self.threshold)[0][0]
            starts.append(start)
        ends = [len(col) - 1 - start for start in starts]

        starts = np.array(starts)
        ends = np.array(ends)
        body_pts = np.vstack((starts, ends)).T

        if ifgis:
            return center_pts, body_pts

        # get the x, y index of the center line control points in the big temp array
        nrow, ncol = plume_array.shape
        nshape = nrow + ncol
        # set lower left corner as the origin
        x_value = center_pts + nshape
        y_value = np.full_like(x_value, nshape)
        center_pts_new = np.vstack((x_value, y_value)).T

        # get the x, y index of the body control points in the big temp array
        if plume_array[:, -1].max() >= self.threshold:
            body_pts = np.hstack(((center_pts + nshape).reshape(-1, 1), body_pts))
        else:
            body_pts = np.hstack(((center_pts[:-1] + nshape).reshape(-1, 1), body_pts))
        if nrow % 2 == 0:
            body_pts[:, 1] = nshape + int(nrow / 2) - body_pts[:, 1] - 1
            body_pts[:, 2] = nshape + int(nrow / 2) - body_pts[:, 2] - 1
        else:
            body_pts[:, 1] = nshape + int(nrow / 2) - body_pts[:, 1]
            body_pts[:, 2] = nshape + int(nrow / 2) - body_pts[:, 2]
        # np.savetxt("plume_array.txt", plume_array, delimiter=',')
        body_pts_new = body_pts

        return center_pts_new, body_pts_new

    def get_target_points(self, segment, center_pts, body_pts):
        """
        Get the target points for warping
        """
        target_center_pts = []
        target_body_right_pts = []
        target_body_left_pts = []

        segment['dist'] = segment['TotDist'] - segment['TotDist'].shift(1)
        segment.loc[0, 'dist'] = segment['TotDist'].iloc[0]

        x_origin_value = segment['Shape'].iloc[0].firstPoint.X
        y_origin_value = segment['Shape'].iloc[0].firstPoint.Y
        for i in range(len(center_pts)):
            length = (center_pts[i, 0] - center_pts[0, 0]) * self.plume_cell_size
            index = (segment['TotDist'] >= length).idxmax()
            if i == len(center_pts) - 1 and index == 0:
                index = len(segment) - 1
            first_x = segment['Shape'].iloc[index].firstPoint.X
            first_y = segment['Shape'].iloc[index].firstPoint.Y
            last_x = segment['Shape'].iloc[index].lastPoint.X
            last_y = segment['Shape'].iloc[index].lastPoint.Y
            target_x = last_x - (last_x - first_x) / segment['dist'].iloc[index] * (
                    segment['TotDist'].iloc[index] - length)
            target_y = last_y - (last_y - first_y) / segment['dist'].iloc[index] * (
                    segment['TotDist'].iloc[index] - length)
            delta_x = (target_x - x_origin_value) / self.plume_cell_size
            delta_y = (target_y - y_origin_value) / self.plume_cell_size
            target_center_pts.append([center_pts[0, 0] + delta_x, center_pts[0, 1] + delta_y])
            if len(center_pts) - len(body_pts) == 1 and i == len(center_pts) - 1:
                pass
            else:
                distance = (body_pts[i][1] - body_pts[i][2]) * self.plume_cell_size / 2
                point_right, point_left = find_perpendicular_point(first_x, first_y, last_x, last_y, distance,
                                                                   target_x, target_y)
                delta_x_right = (point_right[0] - target_x) / self.plume_cell_size
                delta_y_right = (point_right[1] - target_y) / self.plume_cell_size
                target_body_right_pts.append([center_pts[0, 0] + delta_x + delta_x_right,
                                              center_pts[0, 1] + delta_y + delta_y_right])
                delta_x_left = (point_left[0] - target_x) / self.plume_cell_size
                delta_y_left = (point_left[1] - target_y) / self.plume_cell_size
                target_body_left_pts.append([center_pts[0, 0] + delta_x + delta_x_left,
                                             center_pts[0, 1] + delta_y + delta_y_left])

        target_center_pts = np.array(target_center_pts)
        target_body_right_pts = np.array(target_body_right_pts)
        target_body_left_pts = np.array(target_body_left_pts)
        target_body_pts = np.vstack((target_body_left_pts, target_body_right_pts))
        return target_center_pts, target_body_pts

    def get_target_points_gis(self, segment, center_pts, body_pts, xvalue, yvalue):
        """
        Get the target points for warping
        """
        segment['dist'] = segment['TotDist'] - segment['TotDist'].shift(1)
        segment['dist'] = segment['dist'].apply(lambda x: 0.1 if x < 0.1 else x)
        segment.loc[0, 'dist'] = segment['TotDist'].iloc[0]

        target_center_pts = []
        origin_center_pts = []
        target_body_pts_left = []
        target_body_pts_right = []
        origin_body_pts_left = []
        origin_body_pts_right = []

        for i in range(len(center_pts)):
            center_origin_x = xvalue + center_pts[i] * self.plume_cell_size
            center_origin_y = yvalue
            length = (center_pts[i] - center_pts[0]) * self.plume_cell_size
            index = (segment['TotDist'] >= length).idxmax()
            # if (i == len(center_pts) - 1 and index == 0) or length >= segment['TotDist'].iloc[-1]:
            if length >= segment['TotDist'].iloc[-1]:
                index = len(segment) - 1
            first_x = segment['Shape'].iloc[index].firstPoint.X
            first_y = segment['Shape'].iloc[index].firstPoint.Y
            last_x = segment['Shape'].iloc[index].lastPoint.X
            last_y = segment['Shape'].iloc[index].lastPoint.Y
            target_x = last_x - (last_x - first_x) / segment['dist'].iloc[index] * (
                    segment['TotDist'].iloc[index] - length)
            target_y = last_y - (last_y - first_y) / segment['dist'].iloc[index] * (
                    segment['TotDist'].iloc[index] - length)
            origin_center_pts.append([center_origin_x, center_origin_y])
            target_center_pts.append([target_x, target_y])

            if len(center_pts) < 10:
                continue
            elif len(center_pts) - len(body_pts) != 1 or i != len(center_pts) - 1:
                body_origin_x = center_origin_x
                distance = (body_pts[i][1] - body_pts[i][0]) * self.plume_cell_size / 2
                point_right, point_left = find_perpendicular_point(first_x, first_y, last_x, last_y, distance,
                                                                   target_x, target_y)
                origin_body_pts_right.append([body_origin_x, center_origin_y - distance])
                origin_body_pts_left.append([body_origin_x, center_origin_y + distance])
                target_body_pts_right.append(point_right)
                target_body_pts_left.append(point_left)
        if len(center_pts) < 10:
            return np.array(target_center_pts), np.array(origin_center_pts), None, None
        target_body_pts = np.vstack((target_body_pts_left[::-1], target_body_pts_right))
        origin_body_pts = np.vstack((origin_body_pts_left[::-1], origin_body_pts_right)) 
        return np.array(target_center_pts), np.array(origin_center_pts), target_body_pts, origin_body_pts

    def modify_warped_array(self, array, target_pts, plume_array, max_value):
        """
        Modify the warped array
        """
        p1 = target_pts[0: 6, :]
        p2 = target_pts[int(target_pts.shape[0] / 2): int(target_pts.shape[0] / 2) + 6, :]
        for i in range(6):
            if i == 0:
                line_a = p2[i, 1] - p1[i, 1]
                line_b = p1[i, 0] - p2[i, 0]
                line_c = p2[i, 0] * p1[i, 1] - p1[i, 0] * p2[i, 1]
                x, y = np.meshgrid(np.arange(array.shape[1]), np.arange(array.shape[0]))
                values = line_a * x + line_b * y + line_c
                array[values > 0] = np.nan
            else:
                line_a1 = p1[i - 1, 1] - p1[i, 1]
                line_b1 = p1[i, 0] - p1[i - 1, 0]
                line_c1 = p1[i - 1, 0] * p1[i, 1] - p1[i, 0] * p1[i - 1, 1]
                x1, y1 = np.meshgrid(np.arange(array.shape[1]), np.arange(array.shape[0]))
                values1 = line_a1 * x1 + line_b1 * y1 + line_c1
                array[values1 > 0] = np.nan

                line_a2 = p2[i, 1] - p2[i - 1, 1]
                line_b2 = p2[i - 1, 0] - p2[i, 0]
                line_c2 = p2[i, 0] * p2[i - 1, 1] - p2[i - 1, 0] * p2[i, 1]
                x2, y2 = np.meshgrid(np.arange(array.shape[1]), np.arange(array.shape[0]))
                values2 = line_a2 * x2 + line_b2 * y2 + line_c2
                array[values2 > 0] = np.nan
        if plume_array[:, -1].max() > self.threshold:
            p2 = target_pts[int(target_pts.shape[0] / 2) - 1, :]
            p1 = target_pts[-1, :]
            line_a = p2[1] - p1[1]
            line_b = p1[0] - p2[0]
            line_c = p2[0] * p1[1] - p1[0] * p2[1]
            x, y = np.meshgrid(np.arange(array.shape[1]), np.arange(array.shape[0]))
            values = line_a * x + line_b * y + line_c
            array[values > 0] = np.nan
        array[array < self.threshold] = np.nan
        array[array > max_value] = max_value
        return array

    def clear_memory(self):
        if arcpy.Exists(r'memory\water_bodies'):
            arcpy.management.Delete(r'memory\water_bodies')
        if arcpy.Exists(r'memory\plume_raster'):
            arcpy.management.Delete(r'memory\plume_raster')
        if arcpy.Exists(r'memory\plume_full'):
            arcpy.management.Delete(r'memory\plume_full')
        if arcpy.Exists(r'memory\Resample'):
            arcpy.management.Delete(r'memory\Resample')
        if arcpy.Exists(r'memory\polyline'):
            arcpy.management.Delete(r'memory\polyline')
        if arcpy.Exists(r'memory\polygon'):
            arcpy.management.Delete(r'memory\polygon')
        if arcpy.Exists(r'memory\Erase_polygon'):
            arcpy.management.Delete(r'memory\Erase_polygon')
        if arcpy.Exists(r'memory\Intersect'):
            arcpy.management.Delete(r'memory\Intersect')
        if arcpy.Exists(r'memory\plume_name'):
            arcpy.management.Delete(r'memory\plume_name')

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


def create_shapefile(save_path, name, crs):
    arcpy.management.CreateFeatureclass(
        out_path=save_path,
        out_name=name,
        geometry_type="POINT",
        spatial_reference=crs)

    arcpy.management.AddField(name, "PathID", "LONG")
    arcpy.management.AddField(name, "is2D", "LONG")
    arcpy.management.AddField(name, "domBdy", "LONG")
    arcpy.management.AddField(name, "decayCoeff", "DOUBLE")
    arcpy.management.AddField(name, "avgVel", "DOUBLE")
    arcpy.management.AddField(name, "avgPrsity", "DOUBLE")
    arcpy.management.AddField(name, "DispL", "DOUBLE")
    arcpy.management.AddField(name, "DispTH", "DOUBLE")
    arcpy.management.AddField(name, "DispTV", "DOUBLE")
    arcpy.management.AddField(name, "SourceY", "DOUBLE")
    arcpy.management.AddField(name, "SourceZ", "DOUBLE")
    arcpy.management.AddField(name, "MeshDX", "DOUBLE")
    arcpy.management.AddField(name, "MeshDY", "DOUBLE")
    arcpy.management.AddField(name, "MeshDZ", "DOUBLE")
    arcpy.management.AddField(name, "plumeTime", "DOUBLE")
    arcpy.management.AddField(name, "pathTime", "DOUBLE")
    arcpy.management.AddField(name, "plumeLen", "DOUBLE")
    arcpy.management.AddField(name, "pathLen", "DOUBLE")
    arcpy.management.AddField(name, "plumeArea", "DOUBLE")
    arcpy.management.AddField(name, "mslnRtNmr", "DOUBLE")
    arcpy.management.AddField(name, "massInRate", "DOUBLE")
    arcpy.management.AddField(name, "massDNRate", "DOUBLE")
    arcpy.management.AddField(name, "avgAngle", "DOUBLE")
    arcpy.management.AddField(name, "warp", "LONG")
    arcpy.management.AddField(name, "PostP", "LONG")
    arcpy.management.AddField(name, "Init_conc", "DOUBLE")
    arcpy.management.AddField(name, "volFac", "DOUBLE")
    arcpy.management.AddField(name, "nextConc", "DOUBLE")
    arcpy.management.AddField(name, "threshConc", "DOUBLE")
    arcpy.management.AddField(name, "WBId_plume", "LONG")
    arcpy.management.AddField(name, "WBId_path", "LONG")
    arcpy.management.AddField(name, "load", "DOUBLE")
    arcpy.management.AddField(name, "wb_conc", "DOUBLE")


def find_perpendicular_point(x1, y1, x2, y2, distance, x0, y0):
    dx = x2 - x1
    dy = y2 - y1

    direction_vector = np.array([dx, dy]) / math.sqrt(dx ** 2 + dy ** 2)
    perpendicular_vector_left = np.array([-dy, dx]) / math.sqrt(dx ** 2 + dy ** 2)
    perpendicular_vector_right = np.array([dy, -dx]) / math.sqrt(dx ** 2 + dy ** 2)

    point_right = np.array([x0, y0]) + perpendicular_vector_right * distance
    point_left = np.array([x0, y0]) + perpendicular_vector_left * distance

    return point_right, point_left


def is_file_locked(file_path):
    try:
        with open(file_path, 'r') as ffile:
            return False
    except IOError as e:
        return True


def delete_temp_files(folder):
    pass
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path):
            try:
                os.unlink(file_path)
            except PermissionError:
                print(f"Permission denied: {file_path}. Skipping ...")
            except Exception as e:
                print(f"Error while deleting {file_path}. Reason: {e}")
        elif os.path.isdir(file_path):
            for sub_filename in os.listdir(file_path):
                sub_file_path = os.path.join(file_path, sub_filename)
                if os.path.isfile(sub_file_path):
                    try:
                        os.unlink(file_path)
                    except PermissionError:
                        print(f"Permission denied: {file_path}. Skipping ...")
                    except Exception as e:
                        print(f"Error while deleting {file_path}. Reason: {e}")
                elif os.path.isdir(sub_file_path):
                    try:
                        shutil.rmtree(sub_file_path)
                    except PermissionError:
                        print(f"Permission denied: {file_path}. Skipping ...")
                    except Exception as e:
                        print(f"Error while deleting {file_path}. Reason: {e}")


# ======================================================================
# Main program for debugging
if __name__ == '__main__':
    # for i in range(1):
    arcpy.env.workspace = "C:\\Users\\Wei\\Downloads\\ArcNLET-Model-1-TurkeyCreek\\Phos\\04-Regional"

    types_of_contaminants = "Nitrogen and Phosphorus"  # Nitrogen, Phosphorus, Nitrogen and Phosphorus
    whethernh4 = True
    # source_location = os.path.join(arcpy.env.workspace, "01-OSTDS.shp")
    water_bodies = os.path.join(arcpy.env.workspace, "01-waterbodies.shp")
    # particlepath = os.path.join(arcpy.env.workspace, "01-pathssy.shp")

    # no3output = os.path.join(arcpy.env.workspace, "dno3")
    # nh4output = os.path.join(arcpy.env.workspace, "dnh4")
    # no3output_info = "demo_no3"+"_info.shp"
    # nh4output_info = "demo_nh4"+"_info.shp"
    # phosoutput = os.path.join(arcpy.env.workspace, "demo_phos")
    # phosoutput_info = "demo_phos"+"_info.shp"

    option0 = "DomenicoRobbinsSSDecay2D"
    option1 = 48
    option2 = "Spline"
    option3 = 0.000001
    option4 = "none"  # post process, none, medium, full
    option5 = "Specified z"  # input mass rate or z
    maxnum = 400

    param0 = 20000
    param1 = 1000
    param2 = 6
    param3 = 1.5
    param4 = True
    param5 = 3.0
    param6 = 0.4
    param7 = 1000
    param8 = 1.42

    no3param0 = 40
    no3param1 = 2.113
    no3param2 = 0.234
    no3param3 = 0.008
    nh4param0 = 5
    nh4param1 = 2.113
    nh4param2 = 0.234
    nh4param3 = 0.0001
    nh4param4 = 2

    phosparam0 = 2
    phosparam1 = 2.113
    phosparam2 = 0.234
    phosparam3 = 'Linear'
    phosparam4 = 0.0002
    phosparam5 = 15.1
    phosparam6 = 0.2
    phosparam7 = 700

    # name = ['ls', 's', 'scl', 'sl']
    # for ii in range(4):
    #     for i in range(50):
    #         for j in range(10):
    #             print("{}H{}V{}".format(name[ii], j, i))
    #             source_location = os.path.join(arcpy.env.workspace, "{}H{}V{}.shp".format(name[ii], j, i))
    #             particlepath = os.path.join(arcpy.env.workspace, "1-paths_{}.shp".format(name[ii]))
    #
    #             no3output = os.path.join(arcpy.env.workspace, "dno3_{}H{}V{}".format(name[ii], j, i))
    #             nh4output = os.path.join(arcpy.env.workspace, "dnh4_{}H{}V{}".format(name[ii], j, i))
    #             no3output_info = "dno3_{}H{}V{}".format(name[ii], j, i) + "_info.shp"
    #             nh4output_info = "dnh4_{}H{}V{}".format(name[ii], j, i) + "_info.shp"
    #
    #             phosoutput = os.path.join(arcpy.env.workspace, "dp_{}H{}V{}".format(name[ii], j, i))
    #             phosoutput_info = "dp_{}H{}V{}".format(name[ii], j, i) + "_info.shp"
    #
    #             arcpy.AddMessage("starting geoprocessing")
    #             start_time = datetime.datetime.now()
    #             Tr = Transport(types_of_contaminants, whethernh4, source_location, water_bodies, particlepath,
    #                            no3output, nh4output, no3output_info, nh4output_info,
    #                            option0, option1, option2, option3, option4, option5, maxnum,
    #                            param0, param1, param2, param3, param4, param5, param6, param7, param8,
    #                            no3param0, no3param1, no3param2, no3param3,
    #                            nh4param0, nh4param1, nh4param2, nh4param3, nh4param4,
    #                            phosoutput, phosoutput_info, phosparam0, phosparam1, phosparam2, phosparam3, phosparam4, phosparam5)

        # cProfile.run('Tr.calculate_plumes()', 'transport')
        # profile_stats = pstats.Stats('transport')
        # with open('transport.txt', 'w') as output_file:
        #     profile_stats.sort_stats('cumulative').print_stats(output_file)
        #
        #         Tr.main()
        #         end_time = datetime.datetime.now()
        #         print("Total time: {}".format(end_time - start_time))
        #         print("Tests successful!")

    source_location = os.path.join(arcpy.env.workspace, "01-septictanks_Clip.shp")
    particlepath = os.path.join(arcpy.env.workspace, "02-paths.shp")

    no3output = os.path.join(arcpy.env.workspace, "demono3")
    nh4output = os.path.join(arcpy.env.workspace, "demonh4")
    no3output_info = "demono3_info.shp"
    nh4output_info = "demonh4_info.shp"

    phosoutput = os.path.join(arcpy.env.workspace, "demop")
    phosoutput_info = "demop_info.shp"

    arcpy.AddMessage("starting geoprocessing")
    start_time = datetime.datetime.now()
    Tr = Transport(types_of_contaminants, whethernh4, source_location, water_bodies, particlepath,
                   no3output, nh4output, no3output_info, nh4output_info,
                   option0, option1, option2, option3, option4, option5, maxnum,
                   param0, param1, param2, param3, param4, param5, param6, param7, param8,
                   no3param0, no3param1, no3param2, no3param3,
                   nh4param0, nh4param1, nh4param2, nh4param3, nh4param4,
                   phosoutput, phosoutput_info, phosparam0, phosparam1, phosparam2, phosparam3, phosparam4, phosparam5,
                   phosparam6, phosparam7)

        # cProfile.run('Tr.calculate_plumes()', 'transport')
        # profile_stats = pstats.Stats('transport')
        # with open('transport.txt', 'w') as output_file:
        #     profile_stats.sort_stats('cumulative').print_stats(output_file)

    Tr.main()
    end_time = datetime.datetime.now()
    print("Total time: {}".format(end_time - start_time))
    print("Tests successful!")

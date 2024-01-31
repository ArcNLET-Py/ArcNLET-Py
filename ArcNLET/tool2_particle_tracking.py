"""
This script contains the Particle Tracking module of ArcNLET model in the ArcGIS Python Toolbox.

For detailed algorithms, please see https://atmos.eoas.fsu.edu/~mye/ArcNLET/Techican_manual.pdf

@author: Wei Mao <wm23a@fsu.edu>， Michael Core <mcore@fsu.edu>, Ming Ye <mye@fsu.edu>
            The Department of Earth, Ocean, and Atmospheric Science, Florida State University
@date: 2023-11-13
"""

import arcpy
import os
import sys
import math
import time
import datetime
import pandas as pd
import numpy as np
import cProfile

__version__ = "V1.0.0"
arcpy.env.parallelProcessingFactor = "100%"
arcpy.env.overwriteOutput = True


class ParticleTracking:
    """ Update the named field in every row of the input feature class with the given value. """

    def __init__(self, c_source_location, c_water_bodies, c_velocity, c_velocity_dir, c_poro, c_option,
                 c_resolution, c_step_size, c_max_steps, c_output):
        self.source_location = arcpy.Describe(c_source_location).catalogPath if not self.is_file_path(
            c_source_location) else c_source_location
        self.water_bodies = arcpy.Describe(c_water_bodies).catalogPath if not self.is_file_path(
            c_water_bodies) else c_water_bodies
        self.velocity = arcpy.Describe(c_velocity).catalogPath if not self.is_file_path(c_velocity) else c_velocity
        self.velocity_dir = arcpy.Describe(c_velocity_dir).catalogPath if not self.is_file_path(
            c_velocity_dir) else c_velocity_dir
        self.poro = arcpy.Describe(c_poro).catalogPath if not self.is_file_path(c_poro) else c_poro

        self.resolution = c_resolution
        self.step_size = c_step_size
        self.max_steps = c_max_steps

        if self.is_file_path(c_output):
            self.output_dir = os.path.dirname(c_output)
            self.output_name = os.path.basename(c_output)
            self.output_fc = c_output
        else:
            self.output_dir = os.path.dirname(self.velocity)
            self.output_name = c_output
            self.output_fc = os.path.join(self.output_dir, self.output_name)
        self.output_exist = False

        desc = arcpy.Describe(self.source_location)
        crs = desc.spatialReference
        self.crs = crs
        self.index = 0

        # Convert water bodies to raster
        self.waterbody_raster = r"memory\water_bodies"
        arcpy.conversion.FeatureToRaster(self.water_bodies, "FID", self.waterbody_raster, self.resolution)

        self.waterbody_array = arcpy.RasterToNumPyArray(self.waterbody_raster, nodata_to_value=-9999)
        self.velocity_array = arcpy.RasterToNumPyArray(self.velocity)
        self.velocity_dir_array = arcpy.RasterToNumPyArray(self.velocity_dir)
        self.poro_array = arcpy.RasterToNumPyArray(self.poro)

        desc = arcpy.Describe(self.waterbody_raster)
        self.waterx = desc.extent.XMin
        self.watery = desc.extent.YMax
        self.water_cell_size = desc.meanCellWidth

        desc = arcpy.Describe(self.velocity)
        self.velox = desc.extent.XMin
        self.veloy = desc.extent.YMax
        self.velo_cell_size = desc.meanCellWidth

        desc = arcpy.Describe(self.velocity_dir)
        self.veldx = desc.extent.XMin
        self.veldy = desc.extent.YMax
        self.veld_cell_size = desc.meanCellWidth

        desc = arcpy.Describe(self.poro)
        self.porox = desc.extent.XMin
        self.poroy = desc.extent.YMax
        self.poro_cell_size = desc.meanCellWidth

        self.modify_seg = c_option
        self.temp_layer_name = "temp_layer"

    def create_shapefile(self):
        """ Create a shapefile with the given name and spatial reference """

        # arcpy.env.workspace(self.output_dir)

        arcpy.CreateFeatureclass_management(
            out_path=self.output_dir,
            out_name=self.output_name,
            geometry_type="POLYLINE",
            spatial_reference=self.crs)

        arcpy.AddField_management(self.output_fc, "PathID", "LONG")
        arcpy.AddField_management(self.output_fc, "SegID", "LONG")
        arcpy.AddField_management(self.output_fc, "TotDist", "DOUBLE")
        arcpy.AddField_management(self.output_fc, "TotTime", "DOUBLE")
        arcpy.AddField_management(self.output_fc, "SegPrsity", "DOUBLE")
        arcpy.AddField_management(self.output_fc, "SegVel", "DOUBLE")
        arcpy.AddField_management(self.output_fc, "DirAngle", "DOUBLE")
        arcpy.AddField_management(self.output_fc, "WBId", "LONG")
        arcpy.AddField_management(self.output_fc, "PathWBId", "LONG")

        self.output_exist = True

    def track(self):
        """ Track the particles """
        # Create a new feature class
        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage('')
        arcpy.AddMessage(f"{current_time} START CALCULATING...")
        workspace = os.path.dirname(self.velocity)
        arcpy.env.workspace = os.path.abspath(workspace)
        arcpy.AddMessage(f"Workspace: {arcpy.env.workspace}")

        self.create_shapefile()

        count = arcpy.management.GetCount(self.source_location)
        segments = []

        arcpy.MakeFeatureLayer_management(self.water_bodies, self.temp_layer_name)

        if count == 0:
            arcpy.AddError("No source location found!")
            return
        else:
            with arcpy.da.SearchCursor(self.source_location, ["OID@", "SHAPE@XY"]) as cursor:
                for row in cursor:
                    oid = row[0]
                    point = row[1]
                    segment = self.track_point(point, oid, count)
                    segments.extend(segment)

        with arcpy.da.InsertCursor(self.output_fc,
                                   ["SHAPE@", "PathID", "SegID", "TotDist", "TotTime", "SegPrsity", "SegVel",
                                    "DirAngle", "WBId", "PathWBId"]) as cursor:
            for seg in segments:
                cursor.insertRow(seg)

        return self.output_fc

    # @jit
    def track_point(self, point, oid, count):
        """ Track the particles from a point source """
        self.index += 1
        cur_x, cur_y = point
        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage(
            "{}  {} of {}   FID:{:04} - x:{:.8f}   y:{:.8f}".format(current_time, self.index, count, oid, cur_x, cur_y))

        steps = 0
        total_dist = 0
        total_time = 0
        wbid = -1
        path_wbid = -1
        pi_over_180 = math.pi / 180
        poro_last_step = 0
        velo_last_step = 0

        segments = []

        while steps < self.max_steps:
            # print("Step {}...".format(steps))
            index, velo, angle, poro = self.get_values(cur_x, cur_y)
            if poro > 1 or poro <= 0:
                poro = poro_last_step
            poro_last_step = poro
            if velo > 1E10 or velo <= 0:
                velo = velo_last_step
            velo_last_step = velo
            if index != -9999:
                if steps == 0:
                    print("The {} source point is in a water body! x = {}, y = {}".format(oid, cur_x, cur_y))
                else:
                    segments[-1][-2] = int(index)
                    for seg in segments:
                        seg[-1] = int(index)

                    if self.modify_seg:
                        segments = self.modify_segments(segments)
                return segments

            next_x = cur_x + self.step_size * math.sin(angle * pi_over_180)
            next_y = cur_y + self.step_size * math.cos(angle * pi_over_180)

            seg_polyline = self.polyline(cur_x, cur_y, next_x, next_y)

            dirangle = math.degrees(math.atan2(next_x - cur_x, next_y - cur_y))
            if dirangle < 0:
                dirangle += 360

            total_dist += self.step_size
            velo = 1E-8 if velo < 1E-8 else velo
            total_time += self.step_size / velo

            segments.append([seg_polyline, oid, steps, total_dist, total_time, poro, velo, dirangle, wbid, path_wbid])

            cur_x = next_x
            cur_y = next_y
            steps += 1
        return segments

    def get_values(self, x, y):
        water_col_index = int((x - self.waterx) / self.water_cell_size)
        water_row_index = int((self.watery - y) / self.water_cell_size)

        velo_col_index = int((x - self.velox) / self.velo_cell_size)
        velo_row_index = int((self.veloy - y) / self.velo_cell_size)

        veld_col_index = int((x - self.veldx) / self.veld_cell_size)
        veld_row_index = int((self.veldy - y) / self.veld_cell_size)

        poro_col_index = int((x - self.porox) / self.poro_cell_size)
        poro_row_index = int((self.poroy - y) / self.poro_cell_size)

        indd = self.waterbody_array[water_row_index, water_col_index]
        velo = self.velocity_array[velo_row_index, velo_col_index]
        angl = self.velocity_dir_array[veld_row_index, veld_col_index]
        porv = self.poro_array[poro_row_index, poro_col_index]

        return indd, velo, angl, porv

    def polyline(self, cur_x, cur_y, next_x, next_y):
        seg_array = arcpy.Array([arcpy.Point(cur_x, cur_y), arcpy.Point(next_x, next_y)])
        seg_polyline = arcpy.Polyline(seg_array, self.crs)
        return seg_polyline

    def modify_segments(self, segments):
        """
        Modify the segments
        """
        if segments[-1][-2] != -1:
            water_bodies_id = segments[-1][-2]
            # temp_layer_name = "temp_layer"
            try:
                # arcpy.MakeFeatureLayer_management(self.water_bodies, temp_layer_name)
                query = "FID = {}".format(water_bodies_id)
                arcpy.SelectLayerByAttribute_management(self.temp_layer_name, "NEW_SELECTION", query)

                intersect_output = r'memory\intersect'

                index = 0
                with arcpy.da.SearchCursor(self.water_bodies, ["SHAPE@"], where_clause=query) as cursor:
                    for row in cursor:
                        polygon = row[0]
                        for i in range(-1, -len(segments) - 1, -1):
                            if segments[i][0].crosses(polygon):
                                arcpy.analysis.Intersect([self.temp_layer_name, segments[i][0]], intersect_output,
                                                         "ALL", "", "POINT")
                                delete_index = len(segments) + i
                                segments = segments[: delete_index + 1]
                                segments[-1][-2] = water_bodies_id
                                index = 1
                                break
                if index == 1:
                    with arcpy.da.SearchCursor(intersect_output, ["SHAPE@"]) as cursor:
                        row_count = sum(1 for _ in cursor)
                        if row_count != 0:
                            with arcpy.da.SearchCursor(intersect_output, ["SHAPE@"]) as cursorr:
                                for row in cursorr:
                                    intersect_polyline = row[0]
                                    first_x = intersect_polyline.firstPoint.X
                                    first_y = intersect_polyline.firstPoint.Y
                                    break
                else:
                    first_x = segments[-1][0].lastPoint.X
                    first_y = segments[-1][0].lastPoint.Y
                    index, velo, angle, poro = self.get_values(first_x, first_y)
                    next_x = first_x + self.step_size * 10 * math.sin(angle * math.pi / 180)
                    next_y = first_y + self.step_size * 10 * math.cos(angle * math.pi / 180)

                    dirangle = math.degrees(math.atan2(next_x - first_x, next_y - first_y))
                    if dirangle < 0:
                        dirangle += 360
                    intersect_polyline = self.polyline(first_x, first_y, next_x, next_y)

                    total_dist = segments[-1][3] + self.step_size
                    velo = 1E-8 if velo < 1E-8 else velo
                    total_time = segments[-1][4] + self.step_size / velo
                    segments.append([intersect_polyline, segments[-1][1], segments[-1][2] + 1, total_dist,
                                     total_time, segments[-1][5], segments[-1][6], dirangle,
                                     segments[-1][-2], segments[-1][-1]])
                    segments[-2][-2] = -1

                    arcpy.analysis.Intersect([self.temp_layer_name, intersect_polyline], intersect_output,
                                             "ALL", "", "LINE")

                    with arcpy.da.SearchCursor(intersect_output, ["SHAPE@"]) as cursor:
                        for row in cursor:
                            intersect_polyline = row[0]
                            first_x = intersect_polyline.firstPoint.X
                            first_y = intersect_polyline.firstPoint.Y
                            break

                origin_x = segments[-1][0].firstPoint.X
                origin_y = segments[-1][0].firstPoint.Y
                tdist = segments[-1][3] + math.sqrt((first_x - origin_x) ** 2 + (first_y - origin_y) ** 2) - 10
                if len(segments) > 1:
                    ttime = segments[-2][4] + (tdist - segments[-1][3] + 10) / segments[-1][6]
                else:
                    ttime = tdist / segments[-1][6]

                tshape = self.polyline(origin_x, origin_y, first_x, first_y)
                segments[-1][0] = tshape
                segments[-1][3] = tdist
                segments[-1][4] = ttime
                return segments

            except Exception as e:
                print(e)

    @staticmethod
    def is_file_path(input_string):
        return os.path.sep in input_string


# ======================================================================
# Main program for debugging
if __name__ == '__main__':
    arcpy.env.workspace = ".\\test_pro"
    source_location = os.path.join(arcpy.env.workspace, "OneSepticTank.shp")
    water_bodies = os.path.join(arcpy.env.workspace, "waterbodies")
    velocity = os.path.join(arcpy.env.workspace, "demovel")
    velocity_dir = os.path.join(arcpy.env.workspace, "demoveld")
    porosity = os.path.join(arcpy.env.workspace, "porosity.img")

    option = True
    resolution = 5
    step_size = 10
    max_steps = 1000

    output_fc = os.path.join(arcpy.env.workspace, "demoPath.shp")

    start_time = datetime.datetime.now()

    PT = ParticleTracking(source_location, water_bodies, velocity, velocity_dir, porosity, option,
                          resolution, step_size, max_steps, output_fc)

    # cProfile.run('PT.track()', 'profileout.txt')
    PT.track()

    end_time = datetime.datetime.now()

    print("Tests successful!")
    print("Total time: {}".format(end_time - start_time))

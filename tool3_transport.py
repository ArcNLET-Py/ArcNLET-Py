"""
This script contains the Groundwater Flow module of ArcNLET model in the ArcGIS Python Toolbox.

For detailed algorithms, please see https://atmos.eoas.fsu.edu/~mye/ArcNLET/Techican_manual.pdf

@author: Wei Mao <wm23a@fsu.edu>
"""

import datetime
import arcpy
import os
import math
import numpy as np
import pandas as pd
from scipy.stats import hmean
from scipy.ndimage import map_coordinates
from DomenicoRobbins import DomenicoRobbins
import matplotlib.pyplot as plt
import cProfile

__version__ = "V1.0.0"


class Transport:
    def __init__(self, whethernh4, sourcelocation, waterbodies, particlepath, no3output, nh4output,
                 option0, option1, option2, option3, option4, option5, option6,
                 param1, param2, param3, param4, param5,
                 no3param0, no3param1, no3param2, no3param3, no3param4,
                 nh4param0, nh4param1, nh4param2, nh4param3, nh4param4, nh4param5, nh4param6):
        """Initialize the transport module
        """
        self.whether_nh4 = whethernh4  # whether to calculate NH4
        self.source_location = sourcelocation  # source location, point feature class
        self.waterbodies = waterbodies  # water bodies, polygon feature class
        self.waterbody_raster = None
        self.particle_path = particlepath  # particle path, polyline feature class
        self.no3_output = os.path.basename(no3output)  # NO3 output, raster
        self.nh4_output = os.path.basename(nh4output)  # NH4 output, raster

        self.working_dir = os.path.abspath(os.path.dirname(self.source_location))
        self.no3_output_info = os.path.basename(self.no3_output) + "_info.shp"
        self.nh4_output_info = os.path.basename(self.nh4_output) + "_info.shp"
        desc = arcpy.Describe(self.source_location)
        self.crs = desc.spatialReference

        self.solution_type = option0  # solution type, DomenicoRobbinsSS2D or DomenicoRobbinsSSDecay2D
        self.warp_ctrl_pt_spacing = option1  # Control point spacing for warping
        self.warp_method = option2  # Plume warping method, spline, polynomial1, polynomial2
        self.use_approximation = option3  # Whether to use approximation
        self.threshold = option4  # Threshold of concentration
        self.post_process = option5.lower()  # Post process, none, medium, and full
        self.solute_mass_type = option6  # Solute mass type, specified input mass rate, or specified Z

        self.mass_in = param1  # mass in
        self.Y = param2  # Y of the source plane
        self.Z = param3  # Z of the source plane
        self.zmax = param4  # Max Z of the source plane
        self.plume_cell_size = param5  # Plume cell size of the output raster
        self.no3_init = no3param0  # Initial NO3 concentration
        self.no3_dispx = no3param1  # NO3 dispersion in X direction
        self.no3_dispyz = no3param2  # NO3 dispersion in Y and Z direction
        self.no3_decay_rate = no3param3  # NO3 decay rate, denitrification rate
        self.vol_conversion_factor = no3param4  # Volume conversion factor, default is 1000
        self.nh4_init = nh4param0  # Initial NH4 concentration
        self.nh4_dispx = nh4param1  # NH4 dispersion in X direction
        self.nh4_dispyz = nh4param2  # NH4 dispersion in Y and Z direction
        self.nh4_decay_rate = nh4param3  # NH4 decay rate, nitrification rate
        self.bulk_density = nh4param4  # Bulk density
        self.nh4_adsorption = nh4param5  # NH4 adsorption coefficient
        self.average_theta = nh4param6  # Average theta

        self.warp_option = False

    def calculate_plumes(self):
        arcpy.AddMessage('Calculating plumes...')

        return


# ======================================================================
# Main program for debugging
if __name__ == '__main__':
    arcpy.env.workspace = ".\\test_pro"
    whethernh4 = True
    source_location = os.path.join(arcpy.env.workspace, "PotentialSepticTankLocations.shp")
    water_bodies = os.path.join(arcpy.env.workspace, "waterbodies")
    particlepath = os.path.join(arcpy.env.workspace, "Path3.shp")

    no3output = os.path.join(arcpy.env.workspace, "no3output")
    nh4output = os.path.join(arcpy.env.workspace, "nh4output")

    option0 = "DomenicoRobbinsSSDecay2D"
    option1 = 48
    option2 = "Polyorder2"
    option3 = 1
    option4 = 0.000001
    option5 = "none"
    option6 = "Specified Z"

    param1 = 20000
    param2 = 6
    param3 = 1.5
    param4 = 3.0
    param5 = 0.4

    no3param0 = 40
    no3param1 = 2.113
    no3param2 = 0.234
    no3param3 = 0.008
    no3param4 = 1000.0
    nh4param0 = 10
    nh4param1 = 2.113
    nh4param2 = 0.234
    nh4param3 = 0.0001
    nh4param4 = 1.42
    nh4param5 = 2
    nh4param6 = 0.4

    arcpy.AddMessage("starting geoprocessing")
    start_time = datetime.datetime.now()
    Tr = Transport(whethernh4, source_location, water_bodies, particlepath, no3output, nh4output,
                   option0, option1, option2, option3, option4, option5, option6,
                   param1, param2, param3, param4, param5,
                   no3param0, no3param1, no3param2, no3param3, no3param4,
                   nh4param0, nh4param1, nh4param2, nh4param3, nh4param4, nh4param5, nh4param6)
    # cProfile.run('Tr.calculate_plumes()', 'transport.txt')
    Tr.calculate_plumes()
    end_time = datetime.datetime.now()
    print("Total time: {}".format(end_time - start_time))
    print("Tests successful!")

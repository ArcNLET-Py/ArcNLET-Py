"""
This script contains the VZMOD module of ArcNLET model in the ArcGIS Python Toolbox.

For detailed algorithms, please see https://atmos.eoas.fsu.edu/~mye/VZMOD/user_manual.pdf

@author: Wei Mao <wm23a@fsu.edu>， Michael Core <mcore@fsu.edu>, Ming Ye <mye@fsu.edu>
            The Department of Earth, Ocean, and Atmospheric Science, Florida State University
@date: 2023-11-21
"""

import datetime
import arcpy
import os
import sys
import math
import numpy as np
import pandas as pd

__version__ = "V1.0.0"
arcpy.env.parallelProcessingFactor = "100%"
arcpy.env.overwriteOutput = True

Nlayer = 100
hydraulic_default = {"clay":            [2.0, 0.015, 14.75,  0.098, 0.459, 1.260],
                     "clay loam":       [2.0, 0.016, 8.180,  0.079, 0.442, 1.415],
                     "loam":            [2.0, 0.011, 12.04,  0.061, 0.399, 1.474],
                     "loamy sand":      [2.0, 0.035, 105.12, 0.049, 0.390, 1.747],
                     "sand":            [2.0, 0.035, 642.98, 0.053, 0.375, 3.180],
                     "sandy clay":      [2.0, 0.033, 11.35,  0.117, 0.385, 1.207],
                     "sandy clay loam": [2.0, 0.021, 13.19,  0.063, 0.384, 1.330],
                     "sandy loam":      [2.0, 0.027, 38.25,  0.039, 0.387, 1.448],
                     "silt":            [2.0, 0.007, 43.74,  0.050, 0.489, 1.677],
                     "silty clay":      [2.0, 0.016, 9.61,   0.111, 0.481, 1.321],
                     "silty clay loam": [2.0, 0.008, 11.11,  0.090, 0.482, 1.520],
                     "silty loam":      [2.0, 0.005, 18.26,  0.065, 0.439, 1.663]}

nitrification_default = {"clay":            [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809],
                         "clay loam":       [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809],
                         "loam":            [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809],
                         "loamy sand":      [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809],
                         "sand":            [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809],
                         "sandy clay":      [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809],
                         "sandy clay loam": [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809],
                         "sandy loam":      [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809],
                         "silt":            [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809],
                         "silty clay":      [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809],
                         "silty clay loam": [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809],
                         "silty loam":      [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809]}

denitrification_default = {"clay":            [0.025, 26.0, 0.347, 3.774, 0.0],
                           "clay loam":       [0.025, 26.0, 0.347, 3.774, 0.0],
                           "loam":            [0.025, 26.0, 0.347, 3.774, 0.0],
                           "loamy sand":      [0.025, 26.0, 0.347, 2.865, 0.0],
                           "sand":            [0.025, 26.0, 0.347, 2.865, 0.0],
                           "sandy clay":      [0.025, 26.0, 0.347, 2.865, 0.0],
                           "sandy clay loam": [0.025, 26.0, 0.347, 2.865, 0.0],
                           "sandy loam":      [0.025, 26.0, 0.347, 2.865, 0.0],
                           "silt":            [0.025, 26.0, 0.347, 3.867, 0.0],
                           "silty clay":      [0.025, 26.0, 0.347, 3.867, 0.0],
                           "silty clay loam": [0.025, 26.0, 0.347, 3.867, 0.0],
                           "silty loam":      [0.025, 26.0, 0.347, 3.867, 0.0]}

adsorption_default = {"clay":            [1.46, 1.50],
                      "clay loam":       [1.46, 1.50],
                      "loam":            [0.35, 1.50],
                      "loamy sand":      [0.35, 1.50],
                      "sand":            [0.35, 1.50],
                      "sandy clay":      [1.46, 1.50],
                      "sandy clay loam": [1.46, 1.50],
                      "sandy loam":      [0.35, 1.50],
                      "silt":            [0.35, 1.50],
                      "silty clay":      [1.46, 1.50],
                      "silty clay loam": [1.46, 1.50],
                      "silty loam":      [0.35, 1.50]}

phosphorus_default = {"Clay":            [873, 0],
                      "Clay Loam":       [690, 0],
                      "Loam":            [690, 0],
                      "Loamy Sand":      [188, 0],
                      "Sand":            [188, 0],
                      "Sandy Clay":      [873, 0],
                      "Sandy Clay Loam": [690, 0],
                      "Sandy Loam":      [383, 0],
                      "Silt":            [690, 0],
                      "Silty Clay":      [873, 0],
                      "Silty Clay Loam": [690, 0],
                      "Silty Loam":      [690, 0]}

class VZMOD:
    def __init__(self, types_of_contaminants, soiltypes, hlr, alpha, ks, thetar, thetas, n,
                 knit, toptnit, beltanit, e2, e3, fs, fwp, Swp, Sl, Sh, kdnt, toptdnt, beltadnt, e1, Sdnt,
                 kd, rho, Temp, disp, NH4, NO3, DTW, dist,
                 phoschoice, rprep, kl, pmax, phoskd, phos,
                 options, output_file, hetero_ks_theta=0, calc_DTW=0, multi_soil_type=0,
                 septic_tank=None, hydraulic_conductivity=None, soil_porosity=None, DEM=None,
                 smoothed_DEM=None, soil_type=None):
        """Initialize the load estimation module.
        """
        self.keep_parameters = False
        self.minimum_value = 0.0001
        self.types_of_contaminants = types_of_contaminants

        self.soiltypes = soiltypes
        self.hlr = hlr
        self.alpha = alpha
        self.ks = ks
        self.thetar = thetar
        self.thetas = thetas
        self.n = n

        self.knit = knit
        self.toptnit = toptnit
        self.beltanit = beltanit
        self.e2 = e2
        self.e3 = e3
        self.fs = fs
        self.fwp = fwp
        self.Swp = Swp
        self.Sl = Sl
        self.Sh = Sh

        self.kdnt = kdnt
        self.toptdnt = toptdnt
        self.beltadnt = beltadnt
        self.e1 = e1
        self.Sdnt = Sdnt

        self.kd = kd
        self.rho = rho
        self.Temp = Temp
        self.disp = disp
        self.NH4 = NH4
        self.NO3 = NO3
        self.DTW = DTW
        self.dist = dist

        self.phoschoice = phoschoice
        self.rprep = rprep
        self.kl = kl
        self.pmax = pmax
        self.phoskd = phoskd
        self.phos = phos

        self.multi_ostds = options
        self.hetero_ks_theta = hetero_ks_theta
        self.calc_DTW = calc_DTW
        self.multi_soil_type = multi_soil_type

        self.septic_tank = None
        self.hydraulic_conductivity = None
        self.soil_porosity = None
        self.DEM = None
        self.smoothed_DEM = None
        self.soil_type = None
        self.workdir = os.getcwd()
        if self.multi_ostds:
            self.septic_tank = arcpy.Describe(septic_tank).catalogPath if not self.is_file_path(
                septic_tank) else septic_tank
            self.tmp_septictank = None
            self.workdir = os.path.dirname(self.septic_tank)
            if self.hetero_ks_theta:
                self.hydraulic_conductivity = arcpy.Describe(hydraulic_conductivity).catalogPath if not (
                    self.is_file_path(hydraulic_conductivity)) else hydraulic_conductivity
                self.soil_porosity = arcpy.Describe(soil_porosity).catalogPath if not self.is_file_path(
                    soil_porosity) else soil_porosity
            if self.calc_DTW:
                self.DEM = arcpy.Describe(DEM).catalogPath if not self.is_file_path(DEM) else DEM
                self.smoothed_DEM = arcpy.Describe(smoothed_DEM).catalogPath if not self.is_file_path(
                    smoothed_DEM) else smoothed_DEM
            if self.multi_soil_type:
                self.soil_type = arcpy.Describe(soil_type).catalogPath if not self.is_file_path(
                    soil_type) else soil_type

        self.output_file = output_file if os.path.isabs(output_file) else os.path.join(self.workdir, output_file)

    def runVZMOD(self):
        arcpy.env.workspace = os.path.abspath(self.workdir)

        try:
            output_folder = os.path.dirname(self.output_file)
            if not os.access(output_folder, os.W_OK):
                arcpy.AddMessage(f"No write permission for the output directory.")
                raise PermissionError(f"No write permission for the output directory.")

            file = open(self.output_file, "w")
            file.write("ArcNLET VZMOD Module \n")

        except PermissionError as pe:
            arcpy.AddMessage(f"No write permission for the output directory.")
            print(f"Permission error: {pe}")
            sys.exit(1)
        except Exception as e:
            print(f"An error occurred: {e}")

        if self.multi_ostds:
            DTW_hete, hydr_hete, poro_hete, soil_hete = self.arcgis_map(self.septic_tank, self.hydraulic_conductivity,
                                                                        self.soil_porosity, self.dist, self.DEM,
                                                                        self.smoothed_DEM, self.soil_type)
            if self.hetero_ks_theta or self.calc_DTW or self.multi_soil_type:
                if (self.hetero_ks_theta or self.calc_DTW) and (not self.multi_soil_type):
                    para = self.get_parameters()
                if self.hetero_ks_theta:
                    nlen = len(hydr_hete)
                if self.calc_DTW:
                    nlen = len(DTW_hete)
                    out_depth = np.array(DTW_hete) * 100
                else:
                    out_depth = self.DTW
                if self.multi_soil_type:
                    nlen = len(soil_hete)

                for i in range(nlen):
                    arcpy.AddMessage("Calculating for septic tank {}\n".format(i))
                    file.write("Calculating for septic tank {}\n".format(i))

                    if self.multi_soil_type:
                        para = self.get_parameters(soil_hete[i])
                    if self.hetero_ks_theta:
                        para['ks'] = hydr_hete[i] * 100
                        para['thetas'] = poro_hete[i]
                    if self.calc_DTW:
                        para['newDTW'] = DTW_hete[i] * 100

                    theta = self.singlflow(para)

                    if self.types_of_contaminants.lower() == "nitrogen":
                        CNH4, CNO3, fsw_nit, fsw_dnt = self.singlesolute(theta, para)
                        arcpy.AddMessage("Depth(cm)   Theta   FSW_Nit   FSW_Dnt   C_NH4-N(mg/l)   C_NO3-N(mg/l) \n")
                        file.write("Depth(cm)   Theta   FSW_Nit   FSW_Dnt   C_NH4-N(mg/l)   C_NO3-N(mg/l) \n")
                        for jj in range(len(CNH4)):
                            arcpy.AddMessage(
                                "{0:8.2f}   {1:8.3f}   {2:8.3f}   {3:8.3f}   {4:8.3f}   {5:8.3f} \n".format(
                                    para['newDTW'] / Nlayer * jj, theta[jj], fsw_nit[jj], fsw_dnt[jj], CNH4[jj], CNO3[jj]))
                            file.write(
                                "{0:8.2f}   {1:8.3f}   {2:8.3f}   {3:8.3f}   {4:8.3f}   {5:8.3f} \n".format(
                                    para['newDTW'] / Nlayer * jj, theta[jj], fsw_nit[jj], fsw_dnt[jj], CNH4[jj], CNO3[jj]))
                    elif self.types_of_contaminants.lower() == "phosphorus":
                        if self.phoschoice.lower() == "langmuir":
                            CP, AP = self.singlphos_steady(para, theta)
                        else:
                            CP = self.phos_linear(para, theta)
                        arcpy.AddMessage("Depth(cm)   C_PO4-P(mg/l)\n")
                        file.write("Depth(cm)   C_PO4-P(mg/l) \n")
                        for jj in range(len(CP)):
                            arcpy.AddMessage(
                                "{0:8.2f}   {1:8.3f} \n".format(para['newDTW'] / Nlayer * jj, CP[jj]))
                            file.write(
                                "{0:8.2f}   {1:8.3f} \n".format(para['newDTW'] / Nlayer * jj, CP[jj]))
                    else:
                        CNH4, CNO3, fsw_nit, fsw_dnt = self.singlesolute(theta, para)
                        if self.phoschoice.lower() == "langmuir":
                            CP, AP = self.singlphos_steady(para, theta)
                        else:
                            CP = self.phos_linear(para, theta)
                        arcpy.AddMessage(
                            "Depth(cm)   Theta   FSW_Nit   FSW_Dnt   C_NH4-N(mg/l)   C_NO3-N(mg/l)   C_PO4-P(mg/l)  \n")
                        file.write(
                            "Depth(cm)   Theta   FSW_Nit   FSW_Dnt   C_NH4-N(mg/l)   C_NO3-N(mg/l)   C_PO4-P(mg/l)  \n")
                        for jj in range(len(CNH4)):
                            arcpy.AddMessage(
                                "{0:8.2f}   {1:8.3f}   {2:8.3f}   {3:8.3f}   {4:8.3f}   {5:8.3f}   {6:8.3f} \n".format(
                                    para['newDTW'] / Nlayer * jj, theta[jj], fsw_nit[jj], fsw_dnt[jj],
                                    CNH4[jj], CNO3[jj], CP[jj]))
                            file.write(
                                "{0:8.2f}   {1:8.3f}   {2:8.3f}   {3:8.3f}   {4:8.3f}   {5:8.3f}   {6:8.3f} \n".format(
                                    para['newDTW'] / Nlayer * jj, theta[jj], fsw_nit[jj], fsw_dnt[jj],
                                    CNH4[jj], CNO3[jj], CP[jj]))
                    if i == 0:
                        total_theta = theta
                        if self.types_of_contaminants.lower() == "nitrogen":
                            total_CNH4 = CNH4
                            total_CNO3 = CNO3
                            total_CP = np.full(Nlayer, np.nan)
                        elif self.types_of_contaminants.lower() == "phosphorus":
                            total_CNH4 = np.full(Nlayer, np.nan)
                            total_CNO3 = np.full(Nlayer, np.nan)
                            total_CP = CP
                        else:
                            total_CNH4 = CNH4
                            total_CNO3 = CNO3
                            total_CP = CP
                    else:
                        total_theta = np.vstack((total_theta, theta))
                        if self.types_of_contaminants.lower() == "nitrogen":
                            total_CNH4 = np.vstack((total_CNH4, CNH4))
                            total_CNO3 = np.vstack((total_CNO3, CNO3))
                            total_CP = np.full((Nlayer, 1), np.nan)
                        elif self.types_of_contaminants.lower() == "phosphorus":
                            total_CNH4 = np.full((Nlayer, 1), np.nan)
                            total_CNO3 = np.full((Nlayer, 1), np.nan)
                            total_CP = np.vstack((total_CP, CP))
                        else:
                            total_CNH4 = np.vstack((total_CNH4, CNH4))
                            total_CNO3 = np.vstack((total_CNO3, CNO3))
                            total_CP = np.vstack((total_CP, CP))
                self.add_shapefile(total_CNH4[:, -1], total_CNO3[:, -1], total_CP[:, -1], out_depth)
            else:
                arcpy.AddMessage("Calculating the load estimation for single source... \n")
                if self.types_of_contaminants.lower() == "nitrogen":
                    arcpy.AddMessage("Depth(cm)   Theta   FSW_Nit   FSW_Dnt   C_NH4-N(mg/l)   C_NO3-N(mg/l) \n")
                    file.write("Depth(cm)   Theta   FSW_Nit   FSW_Dnt   C_NH4-N(mg/l)   C_NO3-N(mg/l) \n")
                    para = self.get_parameters()
                    theta = self.singlflow(para)
                    CNH4, CNO3, fsw_nit, fsw_dnt = self.singlesolute(theta, para)
                    for jj in range(len(CNH4)):
                        arcpy.AddMessage(
                            "{0:8.2f}   {1:8.3f}   {2:8.3f}   {3:8.3f}   {4:8.3f}   {5:8.3f} \n".format(
                                para['newDTW'] / Nlayer * jj, theta[jj], fsw_nit[jj], fsw_dnt[jj], CNH4[jj], CNO3[jj]))
                        file.write(
                            "{0:8.2f}   {1:8.3f}   {2:8.3f}   {3:8.3f}   {4:8.3f}   {5:8.3f} \n".format(
                                para['newDTW'] / Nlayer * jj, theta[jj], fsw_nit[jj], fsw_dnt[jj], CNH4[jj], CNO3[jj]))
                    self.add_shapefile(CNH4[-1], CNO3[-1], None, para['newDTW'])
                elif self.types_of_contaminants.lower() == "phosphorus":
                    arcpy.AddMessage("Depth(cm)   C_PO4-P(mg/l)  \n")
                    file.write("Depth(cm)   C_PO4-P(mg/l)  \n")
                    para = self.get_parameters()
                    theta = self.singlflow(para)
                    if self.phoschoice.lower() == "langmuir":
                        CP, AP = self.singlphos_steady(para, theta)
                    else:
                        CP = self.phos_linear(para, theta)
                    for jj in range(len(CP)):
                        arcpy.AddMessage(
                            "{0:8.2f}   {1:8.3f} \n".format(para['newDTW'] / Nlayer * jj, CP[jj]))
                        file.write(
                            "{0:8.2f}   {1:8.3f} \n".format(para['newDTW'] / Nlayer * jj, CP[jj]))
                    self.add_shapefile(None, None, CP[-1], para['newDTW'])
                else:
                    arcpy.AddMessage(
                        "Depth(cm)   Theta   FSW_Nit   FSW_Dnt   C_NH4-N(mg/l)   C_NO3-N(mg/l)   C_PO4-P(mg/l) \n")
                    file.write(
                        "Depth(cm)   Theta   FSW_Nit   FSW_Dnt   C_NH4-N(mg/l)   C_NO3-N(mg/l)   C_PO4-P(mg/l) \n")
                    para = self.get_parameters()
                    theta = self.singlflow(para)
                    CNH4, CNO3, fsw_nit, fsw_dnt = self.singlesolute(theta, para)
                    if self.phoschoice.lower() == "langmuir":
                        CP, AP = self.singlphos_steady(para, theta)
                    else:
                        CP = self.phos_linear(para, theta)
                    for jj in range(len(CNH4)):
                        arcpy.AddMessage(
                            "{0:8.2f}   {1:8.3f}   {2:8.3f}   {3:8.3f}   {4:8.3f}   {5:8.3f}   {6:8.3f} \n".format(
                                para['newDTW'] / Nlayer * jj, theta[jj], fsw_nit[jj], fsw_dnt[jj],
                                CNH4[jj], CNO3[jj], CP[jj]))
                        file.write(
                            "{0:8.2f}   {1:8.3f}   {2:8.3f}   {3:8.3f}   {4:8.3f}   {5:8.3f}   {6:8.3f} \n".format(
                                para['newDTW'] / Nlayer * jj, theta[jj], fsw_nit[jj], fsw_dnt[jj],
                                CNH4[jj], CNO3[jj], CP[jj]))
                    self.add_shapefile(CNH4[-1], CNO3[-1], CP[-1], para['newDTW'])
        else:
            arcpy.AddMessage("Calculating the load estimation for single source...")
            if self.types_of_contaminants.lower() == "nitrogen":
                arcpy.AddMessage("Depth(cm)   Theta   FSW_Nit   FSW_Dnt   C_NH4-N(mg/l)   C_NO3-N(mg/l) \n")
                file.write("Depth(cm)   Theta   FSW_Nit   FSW_Dnt   C_NH4-N(mg/l)   C_NO3-N(mg/l) \n")
                para = self.get_parameters()
                theta = self.singlflow(para)
                CNH4, CNO3, fsw_nit, fsw_dnt = self.singlesolute(theta, para)
                for jj in range(len(CNH4)):
                    arcpy.AddMessage(
                        "{0:8.2f}   {1:8.3f}   {2:8.3f}   {3:8.3f}   {4:8.3f}   {5:8.3f} \n".format(
                            para['newDTW'] / Nlayer * jj, theta[jj], fsw_nit[jj], fsw_dnt[jj], CNH4[jj], CNO3[jj]))
                    file.write(
                        "{0:8.2f}   {1:8.3f}   {2:8.3f}   {3:8.3f}   {4:8.3f}   {5:8.3f} \n".format(
                            para['newDTW'] / Nlayer * jj, theta[jj], fsw_nit[jj], fsw_dnt[jj], CNH4[jj], CNO3[jj]))
            elif self.types_of_contaminants.lower() == "phosphorus":
                arcpy.AddMessage("Depth(cm)   C_P(mg/l)\n")
                file.write("Depth(cm)   C_P(mg/l)\n")
                para = self.get_parameters()
                theta = self.singlflow(para)
                if self.phoschoice.lower() == "langmuir":
                    CP, AP = self.singlphos_steady(para, theta)
                else:
                    CP = self.phos_linear(para, theta)
                for jj in range(len(CP)):
                    arcpy.AddMessage(
                        "{0:8.2f}   {1:8.3f} \n".format(para['newDTW'] / Nlayer * jj, CP[jj]))
                    file.write("{0:8.2f}   {1:8.3f} \n".format(para['newDTW'] / Nlayer * jj, CP[jj]))
            else:
                arcpy.AddMessage("Depth(cm)    Theta   FSW_Nit   FSW_Dnt  C_NH4-N(mg/l)   C_NO3-N(mg/l)   C_PO4-P(mg/l) \n")
                file.write("Depth(cm)   Theta   FSW_Nit   FSW_Dnt   C_NH4-N(mg/l)   C_NO3-N(mg/l)   C_PO4-P(mg/l) \n")
                para = self.get_parameters()
                theta = self.singlflow(para)
                CNH4, CNO3, fsw_nit, fsw_dnt = self.singlesolute(theta, para)
                if self.phoschoice.lower() == "langmuir":
                    CP, AP = self.singlphos_steady(para, theta)
                else:
                    CP = self.phos_linear(para, theta)
                for jj in range(len(CNH4)):
                    arcpy.AddMessage(
                        "{0:8.2f}   {1:8.3f}   {2:8.3f}   {3:8.3f}   {4:8.3f}   {5:8.3f}   {6:8.3f} \n".format(
                            para['newDTW'] / Nlayer * jj, theta[jj], fsw_nit[jj], fsw_dnt[jj],
                            CNH4[jj], CNO3[jj], CP[jj]))
                    file.write(
                        "{0:8.2f}   {1:8.3f}   {2:8.3f}   {3:8.3f}   {4:8.3f}   {5:8.3f}   {6:8.3f} \n".format(
                            para['newDTW'] / Nlayer * jj, theta[jj], fsw_nit[jj], fsw_dnt[jj],
                            CNH4[jj], CNO3[jj], CP[jj]))
        file.close()
        pass

    def get_parameters(self, soiltypenum=None):
        para = {}
        para['hlr'] = self.hlr
        para['alpha'] = self.alpha
        para['ks'] = self.ks
        para['thetas'] = self.thetas
        para['thetar'] = self.thetar
        para['n'] = self.n

        para['knit'] = self.knit
        para['toptnit'] = self.toptnit
        para['beltanit'] = self.beltanit
        para['e2'] = self.e2
        para['e3'] = self.e3
        para['fs'] = self.fs
        para['fwp'] = self.fwp
        para['Swp'] = self.Swp
        para['Sl'] = self.Sl
        para['Sh'] = self.Sh

        para['kdnt'] = self.kdnt
        para['toptdnt'] = self.toptdnt
        para['beltadnt'] = self.beltadnt
        para['e1'] = self.e1
        para['Sdnt'] = self.Sdnt

        para['kd'] = self.kd
        para['rho'] = self.rho

        para['Temp'] = self.Temp
        para['disp'] = self.disp
        para['NH4'] = self.NH4
        para['NO3'] = self.NO3
        para['DTW'] = self.DTW
        para['newDTW'] = self.DTW

        para['phoschoice'] = self.phoschoice
        para['rprep'] = self.rprep
        para['kl'] = self.kl
        para['phoskd'] = self.phoskd
        para['phos'] = self.phos
        para['Smax'] = self.pmax

        if self.multi_soil_type:
            soiltype_list = ["clay", "clay loam", "loam", "loamy sand", "sand", "sandy clay", "sandy clay loam",
                             "sandy loam", "silt", "silty clay", "silty clay loam", "silty loam"]
            try:
                soiltype = soiltype_list[soiltypenum - 1]
                hydraulic_name = [("hlr", 1), ("alpha", 2), ("ks", 3), ("thetar", 4), ("thetas", 5), ("n", 6)]
                nitrification_name = [("knit", 1), ("toptnit", 2), ("beltanit", 3), ("e2", 4), ("e3", 5), ("fs", 6),
                                      ("fwp", 7), ("Swp", 8), ("Sl", 9), ("Sh", 10)]
                denitrification_name = [("kdnt", 1), ("toptdnt", 2), ("beltadnt", 3), ("e1", 4), ("Sdnt", 5)]
                adsorption_name = [("kd", 1), ("rho", 2)]
                phosphorus_name = [("Smax", 1), ("none", 2)]

                variablename = [hydraulic_name, nitrification_name, denitrification_name, adsorption_name, phosphorus_name]
                for k in range(4):
                    for pname, index in variablename[k]:
                        if k == 0:
                            if pname != "hlr":
                                para[pname] = hydraulic_default[soiltype.lower()][index - 1]
                        elif k == 1:
                            pass
                        elif k == 2:
                            if pname == "e1":
                                para[pname] = denitrification_default[soiltype.lower()][index - 1]
                        elif k == 3:
                            if pname != "rho":
                                para[pname] = adsorption_default[soiltype.lower()][index - 1]
                        elif k == 4:
                            if pname != "none":
                                para[pname] = phosphorus_default[soiltype.lower()][index - 1]

            except IndexError:
                arcpy.AddMessage("Error: soil type {} is wrong!".format(soiltype))
                arcpy.AddMessage("Please check the soil type in the soil file.")

        para['m'] = 1 - 1 / para['n']
        para['ft_nit'] = math.exp(-0.5 * para['beltanit'] * para['toptnit'] + para['beltanit'] *
                                  para['Temp'] * (1 - 0.5 * para['Temp'] / para['toptnit']))
        para['ft_dnt'] = math.exp(-0.5 * para['beltadnt'] * para['toptdnt'] + para['beltadnt'] *
                                  para['Temp'] * (1 - 0.5 * para['Temp'] / para['toptdnt']))
        return para

    def singlflow(self, para):
        "Newton single flow"
        head = [0]
        theta = [para['thetas']]
        if para['newDTW'] < 0.0:
            para['newDTW'] = 0.1
        thickness = para['newDTW'] / Nlayer

        for layer in range(1, Nlayer + 1):
            if head[-1] < 0.0:
                se0 = pow((1.0 + pow(abs(para['alpha'] * head[-1]), para['n'])), -para['m'])
                k0 = para['ks'] * pow(se0, 0.5) * pow((1 - pow((1 - pow(se0, 1 / para['m'])), para['m'])), 2)
            else:
                k0 = para['ks']

            h = -0.1
            nn = 0
            while True:
                if nn > 100:
                    break
                    print("The soil water movement calculation can't converge")
                nn = nn + 1
                if h < 0.0:
                    se1 = 1 / pow((1.0 + pow(-para['alpha'] * h, para['n'])), para['m'])
                    k1 = para['ks'] * pow(se1, 0.5) * pow((1 - pow((1 - pow(se1, 1 / para['m'])), para['m'])), 2)
                    fh = 0.5 * (k0 + k1) * (h - head[-1] + thickness) / thickness - para['hlr']
                    dse = (para['m'] * pow((1.0 + pow(abs(para['alpha'] * h), para['n'])), -para['m'] - 1) * para['n']
                           * pow(abs(para['alpha'] * h), para['n'] - 1) * para['alpha'])
                    temp0 = 1 - pow(se1, 1 / para['m'])
                    temp1 = 1 - pow(temp0, para['m'])
                    dk = para['ks'] * pow(se1, -0.5) * dse * (
                            0.5 * pow(temp1, 2) + 2 * temp1 * pow(temp0, para['m'] - 1) * pow(se1, (1 - para['m']) /
                                                                                              para['m']))
                    dfh = 0.5 * (k0 + k1) / thickness + 0.5 * (h - head[-1] + thickness) / thickness * dk
                    h2 = h - fh / dfh
                    if abs((h2 - h) / h) < 0.01:
                        thetaz = para['thetar'] + (para['thetas'] - para['thetar']) / pow(
                            (1.0 + pow(abs(para['alpha'] * h), para['n'])), para['m'])
                        h = h2
                        break
                    else:
                        h = h2
                else:
                    k1 = para['ks']
                    h2 = thickness * para['hlr'] * 2.0 / (k0 + k1) + head[-1] - thickness
                    if h2 > 0.0:
                        thetaz = para['thetas']
                        h = h2
                        break
                    else:
                        h = -0.1 * pow(10, -nn)
            theta.append(thetaz)
            head.append(h)
        theta.reverse()
        head.reverse()
        return np.array(theta)

    def singlesolute(self, theta, para):

        thickness = para['newDTW'] / Nlayer
        f1_nit = []
        f1_dnt = []
        E = []
        single_fsw_nit = []
        single_fsw_dnt = []

        for layer in range(0, Nlayer + 1):
            s = (theta[layer] - para['thetar']) / (para['thetas'] - para['thetar'])
            if s > para['Sh']:
                fsw_nit = para['fs'] + (1 - para['fs']) * pow((1 - s) / (1 - para['Sh']), para['e2'])
            elif s > para['Sl']:
                fsw_nit = 1.0
            elif s > para['Swp']:
                fsw_nit = para['fwp'] + (1 - para['fwp']) * pow((s - para['Swp']) / (para['Sh'] - para['Swp']),
                                                                para['e3'])
            else:
                fsw_nit = 0.0

            if s > para['Sdnt']:
                fsw_dnt = pow((s - para['Sdnt']) / (1 - para['Sdnt']), para['e1'])
            else:
                fsw_dnt = 0.0

            f1_nit.append(para["knit"] * (theta[layer] + para["kd"] * para["rho"]) * fsw_nit * para['ft_nit'])
            f1_dnt.append(para["kdnt"] * para['ft_dnt'] * fsw_dnt * theta[layer])

            E.append(theta[layer] * para['disp'])

            single_fsw_nit.append(fsw_nit)
            single_fsw_dnt.append(fsw_dnt)

        f = [para['hlr'] * para['NH4']]
        a = []
        b = [(0.5 / thickness) * (E[0] + E[1]) + 0.5 * para['hlr'] + (3.0 * f1_nit[0] + f1_nit[1]) * thickness / 12.0]
        c = []

        for nd in range(1, Nlayer + 1):
            a.append((0.5 / thickness) * (-E[nd - 1] - E[nd]) - 0.5 * para['hlr'] + (
                    f1_nit[nd - 1] + f1_nit[nd]) * thickness / 12.0)
            c.append((0.5 / thickness) * (-E[nd - 1] - E[nd]) + 0.5 * para['hlr'] + (
                    f1_nit[nd - 1] + f1_nit[nd]) * thickness / 12.0)
            f.append(0.0)
            if nd == Nlayer:
                b.append((0.5 / thickness) * (E[nd - 1] + E[nd]) - 0.5 * para['hlr'] + (
                        f1_nit[nd - 1] + 3.0 * f1_nit[nd]) * thickness / 12.0)

            else:
                b.append((0.5 / thickness) * (E[nd - 1] + 2.0 * E[nd] + E[nd + 1]) + (
                        f1_nit[nd - 1] + 6.0 * f1_nit[nd] + f1_nit[nd + 1]) * thickness / 12.0)

        b[Nlayer] = b[Nlayer] + para['hlr']

        CNH4 = tridiagonal_matrix(a, b, c, f)
        for j in range(len(CNH4)):
            if CNH4[j] <= 0.0:
                CNH4[j] = 0.0

        a = []
        b = [(0.5 / thickness) * (E[0] + E[1]) + 0.5 * para['hlr'] + (3.0 * f1_dnt[0] + f1_dnt[1]) * thickness / 12.0]
        f = [1.0 / 6.0 * thickness * (2.0 * f1_nit[0] * CNH4[0] + f1_nit[1] * CNH4[1]) + para['hlr'] * para['NO3']]
        c = []
        for nd in range(1, Nlayer + 1):
            a.append((0.5 / thickness) * (-E[nd - 1] - E[nd]) - 0.5 * para['hlr'] + (
                    f1_dnt[nd - 1] + f1_dnt[nd]) * thickness / 12.0)
            c.append((0.5 / thickness) * (-E[nd - 1] - E[nd]) + 0.5 * para['hlr'] + (
                    f1_dnt[nd - 1] + f1_dnt[nd]) * thickness / 12.0)
            if nd == Nlayer:
                b.append((0.5 / thickness) * (E[nd - 1] + E[nd]) - 0.5 * para['hlr'] + (
                        f1_dnt[nd - 1] + 3.0 * f1_dnt[nd]) * thickness / 12.0)
                f.append(1.0 / 6.0 * thickness * (f1_nit[nd - 1] * CNH4[nd - 1] + 2.0 * f1_nit[nd] * CNH4[nd]))
            else:
                b.append((0.5 / thickness) * (E[nd - 1] + 2.0 * E[nd] + E[nd + 1]) + (
                        f1_dnt[nd - 1] + 6.0 * f1_dnt[nd] + f1_dnt[nd + 1]) * thickness / 12.0)
                f.append(1.0 / 6.0 * thickness * (
                        f1_nit[nd - 1] * CNH4[nd - 1] + 4.0 * f1_nit[nd] * CNH4[nd] + f1_nit[nd + 1] * CNH4[
                    nd + 1]))

        b[Nlayer] = b[Nlayer] + para['hlr']
        CNO3 = tridiagonal_matrix(a, b, c, f)
        for i in range(len(CNO3)):
            if CNO3[i] <= 0.0:
                CNO3[i] = 0.0

        return np.array(CNH4), np.array(CNO3), np.array(single_fsw_nit), np.array(single_fsw_dnt)

    def phos_linear(self, para, theta):
        thickness = para['newDTW'] / Nlayer
        f1 = []
        E = []

        for layer in range(0, Nlayer + 1):
            s = (theta[layer] - para['thetar']) / (para['thetas'] - para['thetar'])
            f1.append(para["rprep"] * ((theta[layer] + para["phoskd"] * para["rho"]) + 1))
            E.append(theta[layer] * para['disp'])

        f = [para['hlr'] * para['phos']]
        a = []
        b = [(0.5 / thickness) * (E[0] + E[1]) + 0.5 * para['hlr'] + (3.0 * f1[0] + f1[1]) * thickness / 12.0]
        c = []

        for nd in range(1, Nlayer + 1):
            a.append((0.5 / thickness) * (-E[nd - 1] - E[nd]) - 0.5 * para['hlr'] + (
                    f1[nd - 1] + f1[nd]) * thickness / 12.0)
            c.append((0.5 / thickness) * (-E[nd - 1] - E[nd]) + 0.5 * para['hlr'] + (
                    f1[nd - 1] + f1[nd]) * thickness / 12.0)
            f.append(0.0)
            if nd == Nlayer:
                b.append((0.5 / thickness) * (E[nd - 1] + E[nd]) - 0.5 * para['hlr'] + (
                        f1[nd - 1] + 3.0 * f1[nd]) * thickness / 12.0)

            else:
                b.append((0.5 / thickness) * (E[nd - 1] + 2.0 * E[nd] + E[nd + 1]) + (
                        f1[nd - 1] + 6.0 * f1[nd] + f1[nd + 1]) * thickness / 12.0)

        b[Nlayer] = b[Nlayer] + para['hlr']

        CP = tridiagonal_matrix(a, b, c, f)
        for j in range(len(CP)):
            if CP[j] <= 0.0:
                CP[j] = 0.0
        return CP

    def singlphos_steady(self, para, theta):

        thickness = para['newDTW'] / Nlayer

        thetad = para["disp"] * theta

        Cinit = np.linspace(para['phos'], 0, Nlayer + 1)
        fc = np.zeros((Nlayer + 1))
        dfc = np.zeros((Nlayer + 1))
        iter = 0

        while True:
            if iter == 0:
                cold = Cinit
            for layer in range(Nlayer + 1):
                kc = para['kl'] * cold[layer] / (1 + para['kl'] * cold[layer])
                if layer == 0:
                    da = 0
                    db = math.sqrt(thetad[layer] * thetad[layer + 1]) / thickness
                    fc[layer] = db * (cold[layer + 1] - cold[layer]) / thickness - \
                                para['hlr'] * (cold[layer] - para['phos']) / thickness - \
                                (theta[layer] * cold[layer] + para['rho'] * para['Smax'] * kc) * para['rprep']
                    dfc[layer] = (- db / thickness - para['hlr'] / thickness - theta[layer] * para['rprep']
                                  - para['rho'] * para['rprep'] * para['Smax'] * para['kl'] / (1 + para['kl'] * cold[layer]) ** 2)
                elif layer == Nlayer:
                    da = math.sqrt(thetad[layer - 1] * thetad[layer]) / thickness
                    db = 0
                    fc[layer] = da * (cold[layer - 1] - cold[layer]) / thickness - \
                                para['hlr'] * (cold[layer] - cold[layer - 1]) / thickness - \
                                (theta[layer] * cold[layer] + para['rho'] * para['Smax'] * kc) * para['rprep']
                    dfc[layer] = (- da / thickness - para['hlr'] / thickness  - theta[layer] * para['rprep']
                                  - para['rho'] * para['rprep'] * para['Smax'] * para['kl'] / (1 + para['kl'] * cold[layer]) ** 2)
                else:
                    da = math.sqrt(thetad[layer - 1] * thetad[layer]) / thickness
                    db = math.sqrt(thetad[layer] * thetad[layer + 1]) / thickness
                    fc[layer] = (da * (cold[layer - 1] - cold[layer]) + db * (cold[layer + 1] - cold[layer])) / \
                                thickness - para['hlr'] * (cold[layer] - cold[layer-1]) / thickness - \
                                (theta[layer] * cold[layer] + para['rho'] * para['Smax'] * kc) * para['rprep']
                    dfc[layer] = (- (da + db) / thickness - para['hlr'] / thickness - theta[layer] * para['rprep']
                                 - para['rho'] * para['rprep'] * para['Smax'] * para['kl'] / (1 + para['kl'] * cold[layer]) ** 2)

            cnew = cold - fc / dfc
            is_close = np.isclose(cold, cnew, rtol=1e-4)
            if is_close.all():
                break
            else:
                cold = cnew
                iter += 1
        # ffc = np.array(ffc)
        # np.savetxt("ffc.csv", ffc, delimiter=",")
        return cnew, cnew * para['kl']/ (1 + para['kl'] * cnew) * 100

    def arcgis_map(self, septictankfile, hydraulicfile, porosityfile, dist, DEMfile, smoothedDEMfile, soilfile):
        arcpy.env.workspace = self.workdir
        tmp = os.path.join(self.workdir, "tmp_shapefile.shp")
        self.tmp_septictank = tmp
        arcpy.management.CopyFeatures(septictankfile, tmp)
        field = []

        if self.hetero_ks_theta:
            arcpy.sa.ExtractMultiValuesToPoints(tmp,
                                                [[hydraulicfile, "hydro_con"], [porosityfile, "porosity"]], "NONE")
            field.append("hydro_con")
            field.append("porosity")
        if self.calc_DTW:
            arcpy.sa.ExtractMultiValuesToPoints(tmp, [[DEMfile, "DEM"], [smoothedDEMfile, "smthDEM"]],
                                                "NONE")
            field.append("DEM")
            field.append("smthDEM")
        if self.multi_soil_type:
            arcpy.sa.ExtractMultiValuesToPoints(tmp, [[soilfile, "soiltype"]], "NONE")
            field.append("soiltype")

        data = []
        if bool(field):
            with arcpy.da.SearchCursor(tmp, field) as cursor:
                for row in cursor:
                    data.append(row)

            data = pd.DataFrame(data, columns=field)
            DTW_hete = (dist / 100 + data["DEM"] - data["smthDEM"]).to_numpy() if self.calc_DTW else None
            hydr_hete = data["hydro_con"].to_numpy() if self.hetero_ks_theta else None
            poro_hete = data["porosity"].to_numpy() if self.hetero_ks_theta else None
            soil_hete = data["soiltype"] if self.multi_soil_type else None

            hydr_hete[hydr_hete < 0] = 10
            poro_hete[poro_hete < 0] = 0.4

            # arcpy.management.Delete(tmp)
            return DTW_hete, hydr_hete, poro_hete, soil_hete
        else:
            return None, None, None, None

    def add_shapefile(self, CH4, CO3, CP, depth):
        fieldnameNO3 = "no3_conc"
        fieldnameNH4 = "nh4_conc"
        fieldnameP = "P_conc"
        depthname = "Depth"

        field_name = [field.name.lower() for field in arcpy.ListFields(self.tmp_septictank)]
        if self.types_of_contaminants.lower() == "nitrogen":
            if fieldnameNO3 not in field_name:
                arcpy.management.AddField(self.tmp_septictank, fieldnameNO3, "DOUBLE")
            if fieldnameNH4 not in field_name:
                arcpy.management.AddField(self.tmp_septictank, fieldnameNH4, "DOUBLE")
            if depthname not in field_name:
                arcpy.management.AddField(self.tmp_septictank, depthname, "DOUBLE")

            with arcpy.da.UpdateCursor(self.tmp_septictank, ["FID", fieldnameNO3, fieldnameNH4, depthname]) as cursor:
                for row in cursor:
                    if self.multi_soil_type or self.calc_DTW or self.hetero_ks_theta:
                        fid = row[0]
                        row[1] = max(CO3[fid], self.minimum_value)
                        row[2] = max(CH4[fid], self.minimum_value)
                        if self.keep_parameters:
                            if self.calc_DTW:
                                row[4] = max(depth[fid], 0.1)
                            else:
                                row[4] = max(self.DTW, 0.1)
                        cursor.updateRow(row)
                    else:
                        row[1] = max(CO3, self.minimum_value)
                        row[2] = max(CH4, self.minimum_value)
                        if self.keep_parameters:
                            if self.calc_DTW:
                                row[4] = max(depth[fid], 0.1)
                            else:
                                row[4] = max(self.DTW, 0.1)
                        cursor.updateRow(row)

        elif self.types_of_contaminants.lower() == "phosphorus":
            if fieldnameP not in field_name:
                arcpy.management.AddField(self.tmp_septictank, fieldnameP, "DOUBLE")
            if depthname not in field_name:
                arcpy.management.AddField(self.tmp_septictank, depthname, "DOUBLE")

            with arcpy.da.UpdateCursor(self.tmp_septictank, ["FID", fieldnameP, depthname]) as cursor:
                for row in cursor:
                    if self.multi_soil_type or self.calc_DTW or self.hetero_ks_theta:
                        fid = row[0]
                        row[1] = max(CP[fid], self.minimum_value)
                        if self.keep_parameters:
                            if self.calc_DTW:
                                row[4] = max(depth[fid], 0.1)
                            else:
                                row[4] = max(self.DTW, 0.1)
                        cursor.updateRow(row)
                    else:
                        row[1] = max(CP, self.minimum_value)
                        if self.keep_parameters:
                            if self.calc_DTW:
                                row[4] = max(depth[fid], 0.1)
                            else:
                                row[4] = max(self.DTW, 0.1)
                        cursor.updateRow(row)

        else:
            try:
                if fieldnameNO3 not in field_name:
                    arcpy.management.AddField(self.tmp_septictank, fieldnameNO3, "DOUBLE")
                if fieldnameNH4 not in field_name:
                    arcpy.management.AddField(self.tmp_septictank, fieldnameNH4, "DOUBLE")
                if fieldnameP not in field_name:
                    arcpy.management.AddField(self.tmp_septictank, fieldnameP, "DOUBLE")
                if depthname not in field_name:
                    arcpy.management.AddField(self.tmp_septictank, depthname, "DOUBLE")
            except Exception as e:
                arcpy.AddMessage("Error: {}".format(e))
                arcpy.AddMessage("Please make sure the file is unlocked and try again.")
                arcpy.AddError("Error!")

            with arcpy.da.UpdateCursor(self.tmp_septictank, ["FID", fieldnameNO3,
                                                          fieldnameNH4, fieldnameP, depthname]) as cursor:
                for row in cursor:
                    if self.multi_soil_type or self.calc_DTW or self.hetero_ks_theta:
                        fid = row[0]
                        row[1] = max(CO3[fid], self.minimum_value)
                        row[2] = max(CH4[fid], self.minimum_value)
                        row[3] = max(CP[fid], self.minimum_value)
                        if self.keep_parameters:
                            if self.calc_DTW:
                                row[4] = max(depth[fid], 0.1)
                            else:
                                row[4] = max(self.DTW, 0.1)
                        cursor.updateRow(row)
                    else:
                        row[1] = max(CO3, self.minimum_value)
                        row[2] = max(CH4, self.minimum_value)
                        row[3] = max(CP, self.minimum_value)
                        if self.keep_parameters:
                            if self.calc_DTW:
                                row[4] = max(depth[fid], 0.1)
                            else:
                                row[4] = max(self.DTW, 0.1)
                        cursor.updateRow(row)
        arcpy.management.Delete(self.septic_tank)
        arcpy.management.Rename(self.tmp_septictank, os.path.basename(self.septic_tank))
        if not self.keep_parameters:
            if self.hetero_ks_theta:
                arcpy.management.DeleteField(self.septic_tank, "hydro_con")
                arcpy.management.DeleteField(self.septic_tank, "porosity")
            if self.calc_DTW:
                arcpy.management.DeleteField(self.septic_tank, "smthDEM")
                arcpy.management.DeleteField(self.septic_tank, "DEM")
            if self.multi_soil_type:
                arcpy.management.DeleteField(self.septic_tank, "soiltype")
            arcpy.management.DeleteField(self.septic_tank, "Depth")

    @staticmethod
    def is_file_path(input_string):
        return os.path.sep in input_string


def tridiagonal_matrix(a, b, c, f, n=Nlayer + 1):
    bb = []
    rr = []
    yy = []
    xx = [0] * n
    bb.append(b[0])
    rr.append(c[0] / bb[0])
    yy.append(f[0] / bb[0])
    for i in range(1, n):
        bb.append(b[i] - a[i - 1] * rr[i - 1])
        yy.append((f[i] - a[i - 1] * yy[i - 1]) / bb[i])
        if i < n - 1: rr.append(c[i] / bb[i])
    xx[n - 1] = yy[n - 1]
    for j in range(n - 2, -1, -1):
        xx[j] = yy[j] - rr[j] * xx[j + 1]
    return xx


# ======================================================================
# Main program for debugging
if __name__ == '__main__':
    arcpy.env.workspace = "C:\\Users\\Wei\\Downloads\\lakeshore_example\\1_lakeshore_example_complex\\3_VZMOD_module\\Inputs"
    # arcpy.env.workspace = ".\\test_pro"

    types_of_contaminants = "nitrogen and phosphorus"

    options = False
    hetero_Ks_thetas = False
    calc_DTW = False
    multi_soil_type = False

    septic_tank = os.path.join(arcpy.env.workspace, "PotentialSepticTankLocations.shp")
    hydraulic_conductivity = os.path.join(arcpy.env.workspace, "hydr_cond")
    soil_porosity = os.path.join(arcpy.env.workspace, "porosity")
    DEM = None  # os.path.join(arcpy.env.workspace, "01-islanddem_3m.tif")
    smoothed_DEM = None  # os.path.join(arcpy.env.workspace, "03-smth4052")
    soiltypefile = os.path.join(arcpy.env.workspace, "soiltype")
    #
    # soiltype = "loam"
    # hlr = 2.0
    # alpha = 0.011
    # ks = 12.04
    # thetar = 0.061
    # thetas = 0.399
    # n = 1.474

    soiltype = "sand"
    hlr = 2.0
    alpha = 0.035
    ks = 642.98
    thetar = 0.053
    thetas = 0.375
    n = 3.180

    # soiltype = "clay"
    # hlr = 2.0
    # alpha = 0.015
    # ks = 14.75
    # thetar = 0.098
    # thetas = 0.459
    # n = 1.260
    #
    # soiltype = "silt"
    # hlr = 2.0
    # alpha = 0.007
    # ks = 43.74
    # thetar = 0.050
    # thetas = 0.489
    # n = 1.677

    knit = 2.9
    toptnit = 25.0
    beltanit = 0.347
    e2 = 2.267
    e3 = 1.104
    fs = 0.0
    fwp = 0.0
    Swp = 0.154
    Sl = 0.665
    Sh = 0.809

    kdnt = 0.08
    toptdnt = 26.0
    beltadnt = 0.347
    e1 = 2.865
    Sdnt = 0.0

    kd = 0.35
    rho = 1.5
    Temp = 25.5
    disp = 4.32

    NH4 = 60
    NO3 = 1
    dist = 0
    DTW = 150

    phoschoice = "Linear"
    rprep = 0.002
    phoskd_array = np.linspace(0, 100, 100)

    kl = 0.2
    pmax = 237
    phos = 10

    path = "C:\\Users\\Wei\\Downloads\\lakeshore_example\\2_lakeshore_example_phosphorus\\3_VZMOD_module\\Outputs"
    for ii in range(100):
        phoskd = phoskd_array[ii]
        filename = "output_{:02d}.txt".format(ii)
        output_file_name = os.path.join(path, filename)

        vzmod = VZMOD(types_of_contaminants, soiltype, hlr, alpha, ks, thetar, thetas, n,
                      knit, toptnit, beltanit, e2, e3, fs, fwp, Swp, Sl, Sh, kdnt, toptdnt, beltadnt, e1, Sdnt,
                      kd, rho, Temp, disp, NH4, NO3, DTW, dist,
                      phoschoice, rprep, kl, pmax, phoskd, phos,
                      options, output_file_name, hetero_Ks_thetas, calc_DTW, multi_soil_type,
                      septic_tank, hydraulic_conductivity, soil_porosity, DEM, smoothed_DEM, soiltypefile)
        vzmod.runVZMOD()

    # vzmod = VZMOD(types_of_contaminants, soiltype, hlr, alpha, ks, thetar, thetas, n,
    #               knit, toptnit, beltanit, e2, e3, fs, fwp, Swp, Sl, Sh, kdnt, toptdnt, beltadnt, e1, Sdnt,
    #               kd, rho, Temp, disp, NH4, NO3, DTW, dist,
    #               rprep, kl, pmax, phos,
    #               options, output_file_name, hetero_Ks_thetas, calc_DTW, multi_soil_type,
    #               septic_tank, hydraulic_conductivity, soil_porosity, DEM, smoothed_DEM, soiltypefile)
    # vzmod.runVZMOD()

    print("Tests successful!")

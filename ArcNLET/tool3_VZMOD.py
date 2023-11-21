"""
This script contains the VZMOD module of ArcNLET model in the ArcGIS Python Toolbox.

For detailed algorithms, please see https://atmos.eoas.fsu.edu/~mye/VZMOD/user_manual.pdf

@author: Wei Mao <wm23@@fsu.edu>, Michael Core <mcore@fsu.edu>
"""

import datetime
import arcpy
import os
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


class VZMOD:
    def __init__(self, soiltypes, hlr, alpha, ks, thetar, thetas, n, knit, toptnit, beltanit, e2, e3, fs, fwp, Swp,
                 Sl, Sh, kdnt, toptdnt, beltadnt, e1, Sdnt, kd, rho, Temp, Tran, NH4, NO3, DTW, dist,
                 options, output_folder, hetero_ks_theta=0, calc_DTW=0, multi_soil_type=0,
                 septic_tank=None, hydraulic_conductivity=None, soil_porosity=None, DEM=None,
                 smoothed_DEM=None, soil_type=None):
        """Initialize the load estimation module.
        """
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
        self.Tran = Tran
        self.NH4 = NH4
        self.NO3 = NO3
        self.DTW = DTW
        self.dist = dist

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
        if self.multi_ostds:
            self.septic_tank = arcpy.Describe(septic_tank).catalogPath if not self.is_file_path(
                septic_tank) else septic_tank
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

        self.output_folder = output_folder

    def runVZMOD(self):
        total_CNH4 = np.zeros((Nlayer, 1))
        total_CNO3 = np.zeros((Nlayer, 1))
        total_theta = np.zeros((Nlayer, 1))
        total_fsw_nit = np.zeros((Nlayer, 1))
        total_fsw_dnt = np.zeros((Nlayer, 1))

        os.chdir(self.output_folder)
        file = open("results.txt", "w")
        file.write('Depth    CNH4       CNO3     Theta   fsw_nit    fsw_dnt'+'\n')
        if self.multi_ostds:
            DTW_hete, hydr_hete, poro_hete, soil_hete = self.arcgis_map(self.septic_tank, self.hydraulic_conductivity,
                                                                        self.soil_porosity, self.dist, self.DEM,
                                                                        self.smoothed_DEM, self.soil_type)
            if self.hetero_ks_theta or self.calc_DTW or self.multi_soil_type:
                if self.hetero_ks_theta:
                    nlen = len(hydr_hete)
                if self.calc_DTW:
                    nlen = len(DTW_hete)
                if self.multi_soil_type:
                    nlen = len(soil_hete)
                if (self.hetero_ks_theta or self.calc_DTW) and (not self.multi_soil_type):
                    para = self.get_parameters()

                for i in range(nlen):
                    arcpy.AddMessage("Calculating for septic tank {}\n".format(i))
                    file.write("Calculating for septic tank {}\n".format(i))

                    if self.multi_soil_type:
                        para = self.get_parameters(soil_hete[i])
                    if self.hetero_ks_theta:
                        para['ks'] = hydr_hete[i]*100
                        para['thetas'] = poro_hete[i]
                    if self.calc_DTW:
                        para['newDTW'] = DTW_hete[i]*100

                    theta = self.singlflow(para)
                    CNH4, CNO3, fsw_nit, fsw_dnt = self.singlesolute(theta, para, file)

                    if i == 0:
                        total_CNH4 = CNH4
                        total_CNO3 = CNO3
                        total_theta = theta
                        total_fsw_nit = fsw_nit
                        total_fsw_dnt = fsw_dnt
                    else:
                        total_CNH4 = np.vstack((total_CNH4, CNH4))
                        total_CNO3 = np.vstack((total_CNO3, CNO3))
                        total_theta = np.vstack((total_theta, theta))
                        total_fsw_nit = np.vstack((total_fsw_nit, fsw_nit))
                        total_fsw_dnt = np.vstack((total_fsw_dnt, fsw_dnt))
                self.create_shapefile(total_CNH4[:, -1], total_CNO3[:, -1])
            else:
                arcpy.AddMessage("Calculating the load estimation for single source...")
                arcpy.AddMessage("Depth     CNH4     CNO3")
                para = self.get_parameters()
                theta = self.singlflow(para)
                CNH4, CNO3, fsw_nit, fsw_dnt = self.singlesolute(theta, para, file)
                total_CNH4 = CNH4
                total_CNO3 = CNO3
                total_theta = theta
                total_fsw_nit = fsw_nit
                total_fsw_dnt = fsw_dnt
                self.create_shapefile(total_CNH4[-1], total_CNO3[-1])
        else:
            arcpy.AddMessage("Calculating the load estimation for single source...")
            arcpy.AddMessage("Depth     CNH4     CNO3")
            para = self.get_parameters()
            theta = self.singlflow(para)
            CNH4, CNO3, fsw_nit, fsw_dnt = self.singlesolute(theta, para, file)
            total_CNH4 = CNH4
            total_CNO3 = CNO3
            total_theta = theta
            total_fsw_nit = fsw_nit
            total_fsw_dnt = fsw_dnt
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
        para['Tran'] = self.Tran
        para['NH4'] = self.NH4
        para['NO3'] = self.NO3
        para['DTW'] = self.DTW
        para['newDTW'] = self.DTW

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

                variablename = [hydraulic_name, nitrification_name, denitrification_name, adsorption_name]
                for k in range(4):
                    for pname, index in variablename[k]:
                        if k == 0:
                            if pname != "hlr":
                                para[pname] = hydraulic_default[soiltype.lower()][index-1]
                        elif k == 1:
                            pass
                        elif k == 2:
                            if pname == "e1":
                                para[pname] = denitrification_default[soiltype.lower()][index-1]
                        elif k == 3:
                            if pname != "rho":
                                para[pname] = adsorption_default[soiltype.lower()][index-1]

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
        return theta

    def singlesolute(self, theta, para, ff, ooo=1):

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

            E.append(theta[layer] * para['Tran'])

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

        for layer in range(0, Nlayer + 1):
            if ooo:
                arcpy.AddMessage('')
                arcpy.AddMessage(
                    '{:6.2f}   {:6.3f}   {:6.3f}   {:6.3f}   {:6.3f}   {:6.3f}'.format(thickness * layer, CNH4[layer],
                                                                                       CNO3[layer], theta[layer],
                                                                                       single_fsw_nit[layer],
                                                                                       single_fsw_dnt[layer]) + '\n')
            ff.write('{:6.2f}   {:6.3f}   {:6.3f}   {:6.3f}   {:6.3f}   {:6.3f}'.format(thickness * layer, CNH4[layer],
                                                                                        CNO3[layer], theta[layer],
                                                                                        single_fsw_nit[layer],
                                                                                        single_fsw_dnt[layer]) + '\n')

        return CNH4, CNO3, single_fsw_nit, single_fsw_dnt

    def arcgis_map(self, septictankfile, hydraulicfile, porosityfile, dist, DEMfile, smoothedDEMfile, soilfile):
        arcpy.env.workspace = self.output_folder

        septictankfile_tmp = os.path.join(self.output_folder, "septictanks.shp")
        arcpy.management.Copy(septictankfile, septictankfile_tmp)
        field = []

        if self.hetero_ks_theta:
            arcpy.sa.ExtractMultiValuesToPoints(septictankfile_tmp,
                                                [[hydraulicfile, "hydro_con"], [porosityfile, "porosity"]], "NONE")
            field.append("hydro_con")
            field.append("porosity")
        if self.calc_DTW:
            arcpy.sa.ExtractMultiValuesToPoints(septictankfile_tmp, [[DEMfile, "DEM"], [smoothedDEMfile, "smthDEM"]],
                                                "NONE")
            field.append("DEM")
            field.append("smthDEM")
        if self.multi_soil_type:
            arcpy.sa.ExtractMultiValuesToPoints(septictankfile_tmp, [[soilfile, "soiltype"]], "NONE")
            field.append("soiltype")

        data = []
        if bool(field):
            with arcpy.da.SearchCursor(septictankfile_tmp, field) as cursor:
                for row in cursor:
                    data.append(row)

            data = pd.DataFrame(data, columns=field)
            DTW_hete = (dist / 100 + data["DEM"] - data["smthDEM"]).to_numpy() if self.calc_DTW else None
            hydr_hete = data["hydro_con"].to_numpy() if self.hetero_ks_theta else None
            poro_hete = data["porosity"].to_numpy() if self.hetero_ks_theta else None
            soil_hete = data["soiltype"] if self.multi_soil_type else None

            arcpy.management.DeleteField(septictankfile_tmp, field)
            return DTW_hete, hydr_hete, poro_hete, soil_hete
        else:
            return None, None, None, None

    def create_shapefile(self, CH4, CO3):
        output_shapefile = os.path.join(self.output_folder, "septictanks.shp")
        fieldnameNO3 = "no3_conc"
        fieldnameNH4 = "nh4_conc"

        field_name = [field.name.lower() for field in arcpy.ListFields(output_shapefile)]
        if fieldnameNO3 not in field_name:
            arcpy.management.AddField(output_shapefile, fieldnameNO3, "DOUBLE")
        if fieldnameNH4 not in field_name:
            arcpy.management.AddField(output_shapefile, fieldnameNH4, "DOUBLE")

        with arcpy.da.UpdateCursor(output_shapefile, ["FID", fieldnameNO3, fieldnameNH4]) as cursor:
            for row in cursor:
                if self.multi_soil_type or self.calc_DTW or self.hetero_ks_theta:
                    fid = row[0]
                    row[1] = max(CO3[fid], 0.0001)
                    row[2] = max(CH4[fid], 0.0001)
                    cursor.updateRow(row)
                else:
                    row[1] = max(CO3, 0.0001)
                    row[2] = max(CH4, 0.0001)
                    cursor.updateRow(row)

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
    arcpy.env.workspace = "C:\\Users\\Wei\\Downloads\\test_pro\\test_pro"
    # arcpy.env.workspace = ".\\test_pro"

    options = True
    hetero_Ks_thetas = True
    calc_DTW = True
    multi_soil_type = True

    septic_tank = os.path.join(arcpy.env.workspace, "PotentialSepticTankLocations.shp")
    hydraulic_conductivity = os.path.join(arcpy.env.workspace, "hydr")
    soil_porosity = os.path.join(arcpy.env.workspace, "poro")
    DEM = os.path.join(arcpy.env.workspace, "lakeshore")
    smoothed_DEM = os.path.join(arcpy.env.workspace, "00smth")
    soiltypefile = os.path.join(arcpy.env.workspace, "solt")

    soiltype = "loam"
    hlr = 2.342
    alpha = 0.011
    ks = 12.04
    thetar = 0.061
    thetas = 0.399
    n = 1.474

    knit = 0.162
    toptnit = 25.0
    beltanit = 0.347
    e2 = 2.267
    e3 = 1.104
    fs = 0.0
    fwp = 0.0
    Swp = 0.154
    Sl = 0.665
    Sh = 0.809

    kdnt = 0.354
    toptdnt = 26.0
    beltadnt = 0.347
    e1 = 3.774
    Sdnt = 0.0

    kd = 0.35
    rho = 1.5

    Temp = 25.5
    Tran = 4.32

    NH4 = 40
    NO3 = 0.04
    DTW = 150
    dist = 41.15

    output_folder = arcpy.env.workspace

    vzmod = VZMOD(soiltype, hlr, alpha, ks, thetar, thetas, n, knit, toptnit, beltanit, e2, e3, fs, fwp, Swp,
                  Sl, Sh, kdnt, toptdnt, beltadnt, e1, Sdnt, kd, rho, Temp, Tran, NH4, NO3, DTW, dist,
                  options, output_folder, hetero_Ks_thetas, calc_DTW, multi_soil_type,
                  septic_tank, hydraulic_conductivity, soil_porosity, DEM, smoothed_DEM, soiltypefile)
    vzmod.runVZMOD()

    print("Tests successful!")

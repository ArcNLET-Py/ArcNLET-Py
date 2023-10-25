"""
This script contains the VZMOD module of ArcNLET model in the ArcGIS Python Toolbox.

For detailed algorithms, please see https://atmos.eoas.fsu.edu/~mye/ArcNLET/Techican_manual.pdf

@author: Wei Mao <wm23@@fsu.edu>
"""

import datetime
import arcpy
import os
import numpy as np
import pandas as pd

__version__ = "V1.0.0"

Nlayer = 100

class VZMOD:
    def __init__(self, soiltypes, hlr, alpha, ks, thetar, thetas, n, knit, toptnit, beltanit, e2, e3, fs, fwp, Swp,
                 Sl, Sh, kdnt, toptdnt, beltadnt, e1, Sdnt, kd, rho, Temp, Tran, NH4, NO3, DTW, dist,
                 multi_sources, output_folder, hetero_ks_theta=0, calc_DTW=0, multi_soil_type=0,
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

        self.multi_sources = multi_sources
        self.hetero_ks_theta = hetero_ks_theta
        self.calc_DTW = calc_DTW
        self.multi_soil_type = multi_soil_type

        self.septic_tank = septic_tank
        self.hydraulic_conductivity = hydraulic_conductivity
        self.soil_porosity = soil_porosity
        self.DEM = DEM
        self.smoothed_DEM = smoothed_DEM
        self.soil_type = soil_type

        self.output_folder = output_folder

    def runVZMOD(self):

        pass

    def singlflow(self, para):

        head = [0]
        theta = [para['θs']]
        if para['newWTD'] < 0.0:
            para['newWTD'] = 0.1
        thickness = para['newWTD'] / Nlayer
        for layer in range(1, Nlayer + 1):
            z = -para['newWTD'] + thickness * layer
            if head[-1] < 0.0:
                se0 = pow((1.0 + pow(abs(para['ɑ'] * head[-1]), para['n'])), -para['m'])
                k0 = para['Ks'] * pow(se0, 0.5) * pow((1 - pow((1 - pow(se0, 1 / para['m'])), para['m'])), 2)
            else:
                se0 = 1.0
                k0 = para['Ks']

            h = -0.1
            nn = 0
            while True:
                if nn > 100:
                    break
                    print("can't converge")
                nn = nn + 1
                if h < 0.0:
                    se1 = 1 / pow((1.0 + pow(-para['ɑ'] * h, para['n'])), para['m'])
                    k1 = para['Ks'] * pow(se1, 0.5) * pow((1 - pow((1 - pow(se1, 1 / para['m'])), para['m'])), 2)
                    fh = 0.5 * (k0 + k1) * (h - head[-1] + thickness) / thickness - para['HLR']
                    dse = para['m'] * pow((1.0 + pow(abs(para['ɑ'] * h), para['n'])), -para['m'] - 1) * para['n'] * pow(
                        abs(para['ɑ'] * h), para['n'] - 1) * para['ɑ']
                    temp0 = 1 - pow(se1, 1 / para['m'])
                    temp1 = 1 - pow(temp0, para['m'])
                    dk = para['Ks'] * pow(se1, -0.5) * dse * (
                                0.5 * pow(temp1, 2) + 2 * temp1 * pow(temp0, para['m'] - 1) * pow(se1, (1 - para['m']) /
                                                                                                  para['m']))
                    dfh = 0.5 * (k0 + k1) / thickness + 0.5 * (h - head[-1] + thickness) / thickness * dk
                    h2 = h - fh / dfh
                    if abs((h2 - h) / h) < 0.01:
                        thetaz = para['θr'] + (para['θs'] - para['θr']) / pow(
                            (1.0 + pow(abs(para['ɑ'] * h), para['n'])), para['m'])
                        h = h2
                        break
                    else:
                        h = h2
                else:
                    k1 = para['Ks']
                    h2 = thickness * para['HLR'] * 2.0 / (k0 + k1) + head[-1] - thickness
                    if h2 > 0.0:
                        thetaz = para['θs']
                        h = h2
                        break
                    else:
                        h = -0.1 * pow(10, -nn)
            theta.append(thetaz)
            head.append(h)
        theta.reverse()
        head.reverse()
        # print theta
        # print head
        return theta

    @staticmethod
    def is_file_path(input_string):
        return os.path.sep in input_string


# ======================================================================
# Main program for debugging
if __name__ == '__main__':
    # arcpy.env.workspace = ".\\test_pro"
    arcpy.env.workspace = "C:\\Users\\Wei\\Downloads\\llake\\lakeshore_example\\lakeshore_example"

    whether_nh4 = False
    risk_factor = 1
    plumesno3 = os.path.join(arcpy.env.workspace, "pyno3_info.shp")
    plumesnh4 = ""

    LE = VZMOD(whether_nh4, risk_factor, plumesno3, plumesnh4)
    LE.simulations()

    print("Tests successful!")

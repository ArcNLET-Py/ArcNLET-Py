"""
This script contains the Load Estimation module of ArcNLET model in the ArcGIS Python Toolbox.

For detailed algorithms, please see https://atmos.eoas.fsu.edu/~mye/ArcNLET/Techican_manual.pdf

@author: Wei Mao <wm23@@fsu.edu>, Michael Core <mcore@fsu.edu>
"""

import datetime
import arcpy
import os
import numpy as np
import pandas as pd

__version__ = "V1.0.0"
arcpy.env.parallelProcessingFactor = "100%"
arcpy.env.overwriteOutput = True


class LoadEstimation:
    def __init__(self, c_whethernh4, riskf, c_plumesno3, c_outfileno3, c_plumesnh4=None, c_outfilenh4=None):
        """Initialize the load estimation module.
        """
        if isinstance(c_whethernh4, str):
            self.whether_nh4 = True if c_whethernh4.lower() == 'true' else False
        elif isinstance(c_whethernh4, bool):
            self.whether_nh4 = c_whethernh4
        else:
            arcpy.AddMessage("Error: format of whether to calculate NH4 is wrong.")

        self.risk_factor = riskf
        self.plumesno3 = arcpy.Describe(c_plumesno3).catalogPath if not self.is_file_path(c_plumesno3) else c_plumesno3
        self.outfileno3 = c_outfileno3
        if self.whether_nh4:
            self.plumesnh4 = arcpy.Describe(c_plumesnh4).catalogPath if not self.is_file_path(
                c_plumesnh4) else c_plumesnh4
            self.outfilenh4 = c_outfilenh4

    def calculate_load_estimation(self):

        data = []
        with arcpy.da.SearchCursor(self.plumesno3, ["massInRate", "massDNRate", "WBId_plume"]) as cursor:
            for row in cursor:
                data.append(row)
        segments = pd.DataFrame(data, columns=["massInRate", "massDNRate", "WBId_plume"])
        no3_load = segments.groupby("WBId_plume").sum()
        no3_load = no3_load.reset_index()
        no3_load = no3_load.assign(Massoutput=no3_load["massInRate"] - no3_load["massDNRate"])
        no3_load = no3_load.assign(Massoutputrisk=no3_load["Massoutput"] * self.risk_factor)
        no3_load = no3_load.rename(columns={"WBId_plume": "Waterbody FID", "Massoutput": "Mass Output Load [M/T]",
                                            "Massoutputrisk": "Mass Output Load * Risk Factor [M/T]",
                                            "massInRate": "Mass Input Load [M/T]",
                                            "massDNRate": "Mass Removal Rate [M/T]"})
        no3_load = no3_load[["Waterbody FID", "Mass Output Load [M/T]", "Mass Output Load * Risk Factor [M/T]",
                             "Mass Input Load [M/T]", "Mass Removal Rate [M/T]"]]
        arcpy.AddMessage(no3_load)
        if os.path.exists(self.outfileno3):
            try:
                os.remove(self.outfileno3)
            except PermissionError:
                arcpy.AddMessage("Please close the file: " + self.outfileno3)
                return
        no3_load.to_csv(self.outfileno3, index=False)

        if self.whether_nh4:
            data = []
            with arcpy.da.SearchCursor(self.plumesnh4, ["massInRate", "massDNRate", "WBId_plume"]) as cursor:
                for row in cursor:
                    data.append(row)
            segments = pd.DataFrame(data, columns=["massInRate", "massDNRate", "WBId_plume"])
            nh4_load = segments.groupby("WBId_plume").sum()
            nh4_load = nh4_load.reset_index()
            nh4_load = nh4_load.assign(Massoutput=nh4_load["massInRate"] - nh4_load["massDNRate"])
            nh4_load = nh4_load.assign(Massoutputrisk=nh4_load["Massoutput"] * self.risk_factor)
            nh4_load = nh4_load.rename(columns={"WBId_plume": "Waterbody FID", "Massoutput": "Mass Output Load [M/T]",
                                                "Massoutputrisk": "Mass Output Load * Risk Factor [M/T]",
                                                "massInRate": "Mass Input Load [M/T]",
                                                "massDNRate": "Mass Removal Rate [M/T]"})
            nh4_load = nh4_load[["Waterbody FID", "Mass Output Load [M/T]", "Mass Output Load * Risk Factor [M/T]",
                                 "Mass Input Load [M/T]", "Mass Removal Rate [M/T]"]]
            arcpy.AddMessage(nh4_load)
            if os.path.exists(self.outfilenh4):
                try:
                    os.remove(self.outfilenh4)
                except PermissionError:
                    arcpy.AddMessage("Please close the file: " + self.outfilenh4)
                    return
            nh4_load.to_csv(self.outfilenh4, index=False)

    @staticmethod
    def is_file_path(input_string):
        return os.path.sep in input_string


# ======================================================================
# Main program for debugging
if __name__ == '__main__':
    arcpy.env.workspace = ".\\test_pro"

    whether_nh4 = False
    risk_factor = 1
    plumesno3 = os.path.join(arcpy.env.workspace, "pyno3_info.shp")
    plumesnh4 = ""

    LE = LoadEstimation(whether_nh4, risk_factor, plumesno3, plumesnh4)
    LE.calculate_load_estimation()

    print("Tests successful!")

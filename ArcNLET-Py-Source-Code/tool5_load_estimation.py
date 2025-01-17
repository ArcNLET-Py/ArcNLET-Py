"""
This script contains the Load Estimation module of ArcNLET model in the ArcGIS Python Toolbox.

For detailed algorithms, please see https://atmos.eoas.fsu.edu/~mye/ArcNLET and then find "techican_manual.pdf"

@author: Wei Mao <wm23a@fsu.edu>， Michael Core <mcore@fsu.edu>, Ming Ye <mye@fsu.edu>
            The Department of Earth, Ocean, and Atmospheric Science, Florida State University
@date: 2023-11-13
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
    def __init__(self, type_of_contaminants, c_whethernh4, riskf,
                 c_plumesno3, c_outfileno3, c_plumesnh4, c_outfilenh4, c_plumesp, c_outfilep):
        """Initialize the load estimation module.
        """
        if isinstance(c_whethernh4, str):
            self.whether_nh4 = True if c_whethernh4.lower() == 'true' else False
        elif isinstance(c_whethernh4, bool):
            self.whether_nh4 = c_whethernh4
        else:
            arcpy.AddMessage("Error: format of whether to calculate NH4 is wrong.")

        self.contaminant_list = []
        if type_of_contaminants == "Nitrogen" or type_of_contaminants == "Nitrogen and Phosphorus":
            self.contaminant_list.append("NO3-N")
            if self.whether_nh4:
                self.contaminant_list.append("NH4-N")
        if type_of_contaminants == "Phosphorus" or type_of_contaminants == "Nitrogen and Phosphorus":
            self.contaminant_list.append("PO4-P")

        self.risk_factor = riskf

        if "NO3-N" in self.contaminant_list:
            self.plumesno3 = arcpy.Describe(c_plumesno3).catalogPath if not self.is_file_path(
                c_plumesno3) else c_plumesno3
            self.outfileno3 = c_outfileno3
        if "NH4-N" in self.contaminant_list:
            self.plumesnh4 = arcpy.Describe(c_plumesnh4).catalogPath if not self.is_file_path(
                c_plumesnh4) else c_plumesnh4
            self.outfilenh4 = c_outfilenh4
        if "PO4-P" in self.contaminant_list:
            self.plumesp = arcpy.Describe(c_plumesp).catalogPath if not self.is_file_path(
                c_plumesp) else c_plumesp
            self.outfilep = c_outfilep

    def calculate_load_estimation(self):

        if "NH4-N" in self.contaminant_list:
            data = []
            with arcpy.da.SearchCursor(self.plumesnh4, ["massInRate", "massRMRate", "load", "WBId_plume"]) as cursor:
                for row in cursor:
                    data.append(row)
            segments = pd.DataFrame(data, columns=["massInRate", "massRMRate", "load", "WBId_plume"])
            nh4segments = segments.copy()
            nh4_load = segments.groupby("WBId_plume").sum()
            nh4_load = nh4_load.reset_index()
            nh4_load.loc[nh4_load['WBId_plume'] == -1, 'massRMRate'] = nh4_load.loc[nh4_load['WBId_plume'] == -1,
                                                                                    'massInRate']
            nh4_load = nh4_load.assign(Massoutput=nh4_load["massInRate"] - nh4_load["massRMRate"])
            nh4_load = nh4_load.assign(Massoutputrisk=nh4_load["Massoutput"] * self.risk_factor)
            nh4_load = nh4_load.rename(columns={"WBId_plume": "Waterbody FID", "Massoutput": "Mass Output Load [mg/d]",
                                                "Massoutputrisk": "Mass Output Load * Risk Factor [mg/d]",
                                                "massInRate": "Mass Input Load [mg/d]",
                                                "massRMRate": "Mass Removal Rate [mg/d]"})
            nh4_load = nh4_load[["Waterbody FID", "Mass Output Load [mg/d]", "Mass Output Load * Risk Factor [mg/d]",
                                 "Mass Input Load [mg/d]", "Mass Removal Rate [mg/d]"]]
            nh4_load = nh4_load[nh4_load["Waterbody FID"] != -1]
            arcpy.AddMessage(nh4_load)
            if os.path.exists(self.outfilenh4):
                try:
                    os.remove(self.outfilenh4)
                except PermissionError:
                    arcpy.AddMessage("Please close the file: " + self.outfilenh4)
                    return
            nh4_load.to_csv(self.outfilenh4, index=False)

        if "NO3-N" in self.contaminant_list:
            data = []
            with arcpy.da.SearchCursor(self.plumesno3, ["massInRate", "massRMRate", "load", "WBId_plume"]) as cursor:
                for row in cursor:
                    data.append(row)
            segments = pd.DataFrame(data, columns=["massInRate", "massRMRate", "load", "WBId_plume"])
            if "NH4-N" in self.contaminant_list:
                segments["massInRate"] = segments["massInRate"] + nh4segments["massRMRate"]
            no3_load = segments.groupby("WBId_plume").sum()
            no3_load = no3_load.reset_index()
            no3_load.loc[no3_load['WBId_plume'] == -1, 'massRMRate'] = no3_load.loc[no3_load['WBId_plume'] == -1,
                                                                                    'massInRate']
            no3_load = no3_load.assign(Massoutput=no3_load["massInRate"] - no3_load["massRMRate"])
            no3_load = no3_load.assign(Massoutputrisk=no3_load["Massoutput"] * self.risk_factor)
            no3_load = no3_load.rename(columns={"WBId_plume": "Waterbody FID", "Massoutput": "Mass Output Load [mg/d]",
                                                "Massoutputrisk": "Mass Output Load * Risk Factor [mg/d]",
                                                "massInRate": "Mass Input Load [mg/d]",
                                                "massRMRate": "Mass Removal Rate [mg/d]"})
            no3_load = no3_load[["Waterbody FID", "Mass Output Load [mg/d]", "Mass Output Load * Risk Factor [mg/d]",
                                 "Mass Input Load [mg/d]", "Mass Removal Rate [mg/d]"]]
            no3_load = no3_load[no3_load["Waterbody FID"] != -1]
            arcpy.AddMessage(no3_load)
            if os.path.exists(self.outfileno3):
                try:
                    os.remove(self.outfileno3)
                except PermissionError:
                    arcpy.AddMessage("Please close the file: " + self.outfileno3)
                    return
            no3_load.to_csv(self.outfileno3, index=False)

        if "PO4-P" in self.contaminant_list:
            data = []
            with arcpy.da.SearchCursor(self.plumesp, ["massInRate", "massRMRate", "load", "WBId_plume"]) as cursor:
                for row in cursor:
                    data.append(row)
            segments = pd.DataFrame(data, columns=["massInRate", "massRMRate", "load", "WBId_plume"])
            p_load = segments.groupby("WBId_plume").sum()
            p_load = p_load.reset_index()
            p_load.loc[p_load['WBId_plume'] == -1, 'massRMRate'] = p_load.loc[p_load['WBId_plume'] == -1,
                                                                              'massInRate']
            p_load = p_load.assign(Massoutput=p_load["massInRate"] - p_load["massRMRate"])
            p_load = p_load.assign(Massoutputrisk=p_load["Massoutput"] * self.risk_factor)
            p_load = p_load.rename(columns={"WBId_plume": "Waterbody FID", "Massoutput": "Mass Output Load [mg/d]",
                                            "Massoutputrisk": "Mass Output Load * Risk Factor [mg/d]",
                                            "massInRate": "Mass Input Load [mg/d]",
                                            "massRMRate": "Mass Removal Rate [mg/d]"})
            p_load = p_load[["Waterbody FID", "Mass Output Load [mg/d]", "Mass Output Load * Risk Factor [mg/d]",
                             "Mass Input Load [mg/d]", "Mass Removal Rate [mg/d]"]]
            p_load = p_load[p_load["Waterbody FID"] != -1]
            arcpy.AddMessage(p_load)
            if os.path.exists(self.outfilep):
                try:
                    os.remove(self.outfilep)
                except PermissionError:
                    arcpy.AddMessage("Please close the file: " + self.outfilep)
                    return
            p_load.to_csv(self.outfilep, index=False)

    @staticmethod
    def is_file_path(input_string):
        return os.path.sep in input_string


# ======================================================================
# Main program for debugging
if __name__ == '__main__':
    arcpy.env.workspace = "C:\\Users\\Wei\\Downloads\\Orlando\\debug"

    whether_nh4 = False
    risk_factor = 1
    plumesno3 = os.path.join(arcpy.env.workspace, "demo_no3_info.shp")
    plumesnh4 = ""

    LE = LoadEstimation(whether_nh4, risk_factor, plumesno3, plumesnh4)
    LE.calculate_load_estimation()

    print("Tests successful!")

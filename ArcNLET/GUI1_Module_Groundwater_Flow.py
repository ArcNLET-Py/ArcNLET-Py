"""
Python code that implements an ArcGIS Tool,
to be included in an ArcGIS Python Toolbox.

@author: Wei Mao <wm23a@fsu.edu>， Michael Core <mcore@fsu.edu>, Ming Ye <mye@fsu.edu>
            The Department of Earth, Ocean, and Atmospheric Science, Florida State University
@date: 2023-11-07
"""

import os
import arcpy
import time
import importlib
import tool1_groundwater_flow

importlib.reload(tool1_groundwater_flow)

from tool1_groundwater_flow import DarcyFlow


class InterfaceGroundwaterFlow(object):
    """This class has the methods to define the interface of the tool."""

    def __init__(self) -> None:
        """Define the tool.
        """
        self.label = "1-Groundwater Flow"
        self.description = """Groundwater flow module."""
        self.category = "ArcNLET"

    def getParameterInfo(self):
        """Define parameter definitions.
        """

        infile0 = arcpy.Parameter(name="DEM",
                                  displayName="Input DEM [m] (raster)",  # shown in Geoprocessing pane
                                  datatype=["GPRasterLayer"],  # data type
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input")  # Input|Output

        infile1 = arcpy.Parameter(name="Water bodies",
                                  displayName="Input Water bodies (polygon)",
                                  datatype="GPFeatureLayer",
                                  parameterType="Required",
                                  direction="Input")
        infile1.filter.list = ["Polygon"]

        infile2 = arcpy.Parameter(name="Hydraulic Conductivity",
                                  displayName="Input Hydraulic conductivity [m/d] (raster)",
                                  datatype=["GPRasterLayer"],
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  )

        infile3 = arcpy.Parameter(name="Porosity",
                                  displayName="Input Soil porosity (raster)",
                                  datatype=["GPRasterLayer"],
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  )

        param0 = arcpy.Parameter(name="Smoothing Factor",
                                 displayName="Smoothing Factor",
                                 datatype="GPLong",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 )
        param0.value = 20

        param1 = arcpy.Parameter(name="Smoothing Cell",
                                 displayName="Smoothing Cell",
                                 datatype="GPLong",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 )
        param1.value = 7

        param2 = arcpy.Parameter(name="Fill Sinks",
                                 displayName="Fill Sinks",
                                 datatype="GPBoolean",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 )
        param2.value = 0

        param3 = arcpy.Parameter(name="Merge Waterbodies",
                                 displayName="Merge Waterbodies",
                                 datatype="GPBoolean",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 )
        param3.value = 0

        param4 = arcpy.Parameter(name="Smoothing Factor after Merging",
                                 displayName="Smoothing Factor after Merging",
                                 datatype="GPLong",
                                 parameterType="Optional",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 multiValue=True,
                                 )
        param4.value = 0
        param4.parameterDependencies = [param3.name]

        param5 = arcpy.Parameter(name="Changing Smoothing Cell",
                                 displayName="Changing Smoothing Cell",
                                 datatype="GPBoolean",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 )
        param5.value = 0

        param6 = arcpy.Parameter(name="Smoothing Cell after Merging",
                                 displayName="Smoothing Cell after Merging",
                                 datatype="GPLong",
                                 parameterType="Optional",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 multiValue=True,
                                 )
        param6.value = 7
        param6.parameterDependencies = [param3.name]

        param7 = arcpy.Parameter(name="Z-Factor",
                                 displayName="Z-Factor",
                                 datatype="GPLong",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 )
        param7.value = 1

        param8 = arcpy.Parameter(name="Maximum number of continuous smoothing",
                                 displayName="Maximum number of continuous smoothing",
                                 datatype="GPLong",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 )
        param8.value = 50

        outfile0 = arcpy.Parameter(name="Velocity Magnitude",
                                   displayName="Output Velocity Magnitude [m/d]",
                                   datatype=["GPRasterLayer"],
                                   parameterType="Required",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )

        outfile1 = arcpy.Parameter(name="Velocity Direction",
                                   displayName="Output Velocity Direction [°wrt N]",
                                   datatype=["GPRasterLayer"],
                                   parameterType="Required",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )

        outfile2 = arcpy.Parameter(name="Smoothed DEM",
                                   displayName="(Optional) Output Smoothed DEM (VZMOD required)",
                                   datatype=["GPRasterLayer"],
                                   parameterType="Optional",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )

        outfile3 = arcpy.Parameter(name="Hydraulic Gradient",
                                   displayName="(Optional) Output Hydraulic Gradient",
                                   datatype=["GPRasterLayer"],
                                   parameterType="Optional",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )

        return [infile0, infile1, infile2, infile3,                                       # 0-3
                param0, param1, param2, param3, param4, param5, param6, param7, param8,   # 4-12
                outfile0, outfile1, outfile2, outfile3]                                   # 13-16

    def isLicensed(self) -> bool:
        """Set whether tool is licensed to execute.
        Allow the tool to run, only if the ArcGIS pro spatial analyst extension is available.
        """
        try:
            if arcpy.CheckExtension("Spatial") != "Available":
                raise Exception
        except Exception:
            return False  # tool cannot be executed
        return True  # tool can be executed

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed. This method is called whenever a parameter
        has been changed."""
        if parameters[7].value:
            parameters[8].enabled = True
            parameters[9].enabled = True
        else:
            parameters[8].enabled = False
            parameters[9].enabled = False

        if parameters[9].value:
            parameters[10].enabled = True
        else:
            parameters[10].enabled = False
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        if parameters[0].altered and parameters[0].value is not None:
            dem = parameters[0].value
            desc = arcpy.Describe(dem)
            band_count = desc.bandCount
            crs1 = desc.spatialReference
            xsize = desc.meanCellWidth
            ysize = desc.meanCellHeight
            if band_count != 1:
                parameters[0].setErrorMessage("Input DEM must have only one band.")
            if abs(xsize - ysize) > 1E-4 :
                parameters[0].setErrorMessage("Input DEM must be square cells.")
            if crs1.linearUnitName != "Meter":
                parameters[0].setErrorMessage("Input DEM must be in meters.")
            filedir = desc.catalogPath
            if ".gdb" in filedir or ".mdb" in filedir:
                geodatabase = True
            else:
                geodatabase = False

        if parameters[1].altered:
            wb = parameters[1].value
            desc = arcpy.Describe(wb)
            crs2 = desc.spatialReference
            if crs2.linearUnitName != "Meter":
                parameters[1].setErrorMessage("Input water bodies must be in meters.")

        if parameters[2].altered:
            ks = parameters[2].value
            desc = arcpy.Describe(ks)
            band_count = desc.bandCount
            crs3 = desc.spatialReference
            if band_count != 1:
                parameters[2].setErrorMessage("Input Hydraulic conductivity must have only one band.")
            if crs3.linearUnitName != "Meter":
                parameters[2].setErrorMessage("Input Hydraulic conductivity must be in meters.")

        if parameters[3].altered:
            poro = parameters[3].value
            desc = arcpy.Describe(poro)
            band_count = desc.bandCount
            crs4 = desc.spatialReference
            if band_count != 1:
                parameters[3].setErrorMessage("Input porosity must have only one band.")
            if crs4.linearUnitName != "Meter":
                parameters[3].setErrorMessage("Input porosity must be in meters.")

        if parameters[0].altered and parameters[1].altered and parameters[2].altered and parameters[3].altered:
            if crs1.name != crs2.name or crs1.name != crs3.name or crs1.name != crs4.name:
                parameters[0].setErrorMessage("All input files must have the same coordinate system. \n"
                                              + "\n" +
                                              "DEM projected coordinate system : {} \n".format(crs1.name)
                                              + "Water bodies projected coordinate system : {} \n".format(crs2.name)
                                              + "Hydraulic conductivity projected coordinate system : {} \n".format(crs3.name)
                                              + "Porosity projected coordinate system : {} \n".format(crs4.name))
                parameters[1].setErrorMessage("All input files must have the same coordinate system. \n"
                                              + "\n" +
                                              "DEM projected coordinate system : {} \n".format(crs1.name)
                                              + "Water bodies projected coordinate system : {} \n".format(crs2.name)
                                              + "Hydraulic conductivity projected coordinate system : {} \n".format(crs3.name)
                                              + "Porosity projected coordinate system : {} \n".format(crs4.name))
                parameters[2].setErrorMessage("All input files must have the same coordinate system. \n"
                                              + "\n" +
                                              "DEM projected coordinate system : {} \n".format(crs1.name)
                                              + "Water bodies projected coordinate system : {} \n".format(crs2.name)
                                              + "Hydraulic conductivity projected coordinate system : {} \n".format(crs3.name)
                                              + "Porosity projected coordinate system : {} \n".format(crs4.name))
                parameters[3].setErrorMessage("All input files must have the same coordinate system. \n"
                                              + "\n" +
                                              "DEM projected coordinate system : {} \n".format(crs1.name)
                                              + "Water bodies projected coordinate system : {} \n".format(crs2.name)
                                              + "Hydraulic conductivity projected coordinate system : {} \n".format(crs3.name)
                                              + "Porosity projected coordinate system : {} \n".format(crs4.name))
        if parameters[4].value is not None and parameters[4].value < 0:
            parameters[4].setErrorMessage("The Smoothing Factor must be greater than 0.")
        if parameters[5].value is not None and parameters[5].value < 0:
            parameters[5].setErrorMessage("The Smoothing Cell must be greater than 0.")
        if parameters[5].value is not None and parameters[5].value >= 0 and parameters[5].value % 2 == 0:
            parameters[5].setWarningMessage("The Smoothing Cell is recommended to be an odd number.")
        if parameters[11].value is not None and parameters[11].value < 0:
            parameters[11].setErrorMessage("The Z-Factor must be greater than 0.")
        if parameters[12].value is not None and parameters[12].value < 0:
            parameters[12].setErrorMessage("The Maximum number of continuous smoothing must be greater than 0.")

        if parameters[7].value:
            if parameters[8].altered and parameters[8].value is not None:
                values_list = parameters[8].valueAsText.split(";")
                try:
                    values_list = [int(i) for i in values_list]
                    values_greater_than_zero = all(val >= 0 for val in values_list)
                except ValueError:
                    values_greater_than_zero = False
                if not values_greater_than_zero:
                    parameters[8].setErrorMessage("The Smoothing Factor must be greater than 0.")
                try:
                    values_list = [int(i) for i in values_list]
                    values_smaller_than_2h = all(val <= 200 for val in values_list)
                except ValueError:
                    values_smaller_than_2h = False
                if not values_smaller_than_2h:
                    parameters[8].setWarningMessage("The Smoothing Factor may be too large.")

            if parameters[9].value:
                if parameters[10].altered and parameters[10].value is not None:
                    values_list2 = parameters[10].valueAsText.split(";")
                    if len(values_list) != len(values_list2):
                        parameters[10].setErrorMessage("The number of Smoothing Factor and Smoothing Cell must be the same.")
                    try:
                        values_list2 = [int(i) for i in values_list2]
                        values_greater_than_zero = all(val >= 0 for val in values_list2)
                    except ValueError:
                        values_greater_than_zero = False
                    if not values_greater_than_zero:
                        parameters[10].setErrorMessage("The Smoothing Cell must be greater than 0.")
                    try:
                        values_list2 = [int(i) for i in values_list2]
                        values_odd = all(val % 2 != 0 for val in values_list2)
                    except ValueError:
                        values_odd = False
                    if not values_odd:
                        parameters[10].setWarningMessage("The Smoothing Cell is recommended to be an odd number.")

        if parameters[0].altered and parameters[0].value is not None:
            if parameters[13].altered and parameters[13].value is not None:
                if self.is_file_path(parameters[13].valueAsText):
                    if ".gdb" in parameters[13].valueAsText or ".mdb" in parameters[13].valueAsText:
                        filename = os.path.basename(parameters[13].valueAsText)
                        if "." in filename:
                            parameters[13].setErrorMessage(
                                "When storing a raster dataset in a geodatabase, "
                                "do not add a file extension to the name of the raster dataset.")
                else:
                    if "." in parameters[13].valueAsText and geodatabase:
                        parameters[13].setErrorMessage(
                            "When storing a raster dataset in a geodatabase, "
                            "do not add a file extension to the name of the raster dataset."
                            "The default output location is same as DEM file")

            if parameters[14].altered and parameters[14].value is not None:
                if self.is_file_path(parameters[14].valueAsText):
                    if ".gdb" in parameters[14].valueAsText or ".mdb" in parameters[14].valueAsText:
                        filename = os.path.basename(parameters[14].valueAsText)
                        if "." in filename:
                            parameters[14].setErrorMessage(
                                "When storing a raster dataset in a geodatabase, "
                                "do not add a file extension to the name of the raster dataset.")
                else:
                    if "." in parameters[14].valueAsText and geodatabase:
                        parameters[14].setErrorMessage(
                            "When storing a raster dataset in a geodatabase, "
                            "do not add a file extension to the name of the raster dataset."
                            "The default output location is same as DEM file")

            if parameters[15].altered and parameters[15].value is not None:
                if self.is_file_path(parameters[15].valueAsText):
                    if ".gdb" in parameters[15].valueAsText or ".mdb" in parameters[15].valueAsText:
                        filename = os.path.basename(parameters[15].valueAsText)
                        if "." in filename:
                            parameters[15].setErrorMessage(
                                "When storing a raster dataset in a geodatabase, "
                                "do not add a file extension to the name of the raster dataset.")
                else:
                    if "." in parameters[15].valueAsText and geodatabase:
                        parameters[15].setErrorMessage(
                            "When storing a raster dataset in a geodatabase, "
                            "do not add a file extension to the name of the raster dataset."
                            "The default output location is same as DEM file")

            if parameters[16].altered and parameters[16].value is not None:
                if self.is_file_path(parameters[16].valueAsText):
                    if ".gdb" in parameters[16].valueAsText or ".mdb" in parameters[16].valueAsText:
                        filename = os.path.basename(parameters[16].valueAsText)
                        if "." in filename:
                            parameters[16].setErrorMessage(
                                "When storing a raster dataset in a geodatabase, "
                                "do not add a file extension to the name of the raster dataset.")
                else:
                    if "." in parameters[16].valueAsText and geodatabase:
                        parameters[16].setErrorMessage(
                            "When storing a raster dataset in a geodatabase, "
                            "do not add a file extension to the name of the raster dataset."
                            "The default output location is same as DEM file")
        return

    def execute(self, parameters, messages) -> None:
        """This is the code that executes when you click the "Run" button."""

        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage(f"{current_time} Compute Darcy Flow: START")

        if not self.is_file_path(parameters[0].valueAsText):
            parameters[0].value = arcpy.Describe(parameters[0].valueAsText).catalogPath
        if not self.is_file_path(parameters[1].valueAsText):
            parameters[1].value = arcpy.Describe(parameters[1].valueAsText).catalogPath
        if not self.is_file_path(parameters[2].valueAsText):
            parameters[2].value = arcpy.Describe(parameters[2].valueAsText).catalogPath
        if not self.is_file_path(parameters[3].valueAsText):
            parameters[3].value = arcpy.Describe(parameters[3].valueAsText).catalogPath

        for param in parameters:
            self.describeParameter(messages, param)

        dem  = parameters[0].valueAsText
        wb   = parameters[1].valueAsText
        ks   = parameters[2].valueAsText
        poro = parameters[3].valueAsText

        smthf1 = parameters[4].value
        smthc  = parameters[5].value
        fsink  = parameters[6].value
        merge  = parameters[7].value
        smthf2 = parameters[8].valueAsText.split(";")
        smthf2 = [int(i) for i in smthf2]
        usecl = parameters[9].value
        smthc2 = parameters[10].valueAsText.split(";")
        smthc2 = [int(i) for i in smthc2]
        zfact  = parameters[11].value
        smthflimit = parameters[12].value

        velo = parameters[13].valueAsText
        veld = parameters[14].valueAsText
        smth = parameters[15].valueAsText
        grad = parameters[16].valueAsText

        # Okay finally go ahead and do the work.
        try:
            arcpy.AddMessage("Compute Darcy Flow: START")
            GF = DarcyFlow(dem, wb, ks, poro,
                           smthf1, smthc, fsink, merge, smthf2, usecl, smthc2, zfact, smthflimit,
                           velo, veld, smth, grad)
            arcpy.AddMessage("Compute Darcy Flow: FINISH")
            GF.calculateDarcyFlow()
            current_time = time.strftime("%H:%M:%S", time.localtime())
            arcpy.AddMessage(f"{current_time} Compute Darcy Flow: FINISH")
        except Exception as e:
            current_time = time.strftime("%H:%M:%S", time.localtime())
            arcpy.AddError(f"{current_time} Fail. %s" % e)
        return

    def describeParameter(self, m, p):
        if p.enabled:
            m.addMessage("Parameter: %s \"%s\"" % (p.name, p.displayName))
            m.addMessage("  Value \"%s\"" % p.valueAsText)

    @staticmethod
    def is_file_path(input_string):
        return os.path.sep in input_string


# =============================================================================
if __name__ == "__main__":

    class Messenger(object):
        def addMessage(self, message):
            print(message)

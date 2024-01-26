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
                                  displayName="Input DEM [L] (raster)",  # shown in Geoprocessing pane
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
                                  displayName="Input Hydraulic conductivity [L/T] (raster)",
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

        param5 = arcpy.Parameter(name="Z-Factor",
                                 displayName="Z-Factor",
                                 datatype="GPLong",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 )
        param5.value = 1

        outfile0 = arcpy.Parameter(name="Velocity Magnitude",
                                   displayName="Output Velocity Magnitude [L/T]",
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

        return [infile0, infile1, infile2, infile3,
                param0, param1, param2, param3, param4, param5,
                outfile0, outfile1, outfile2, outfile3]

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
        else:
            parameters[8].enabled = False
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        if parameters[0].altered:
            dem = parameters[0].value
            desc = arcpy.Describe(dem)
            band_count = desc.bandCount
            crs1 = desc.spatialReference
            xsize = desc.meanCellWidth
            ysize = desc.meanCellHeight
            if band_count != 1:
                parameters[0].setErrorMessage("Input DEM must have only one band.")
            if xsize != ysize:
                parameters[0].setErrorMessage("Input DEM must be square cells.")

        if parameters[1].altered:
            wb = parameters[1].value
            desc = arcpy.Describe(wb)
            crs3 = desc.spatialReference

        if parameters[2].altered:
            ks = parameters[2].value
            desc = arcpy.Describe(ks)
            band_count = desc.bandCount
            crs2 = desc.spatialReference
            if band_count != 1:
                parameters[2].setErrorMessage("Input Hydraulic conductivity must have only one band.")

        if parameters[3].altered:
            poro = parameters[3].value
            desc = arcpy.Describe(poro)
            band_count = desc.bandCount
            crs4 = desc.spatialReference
            if band_count != 1:
                parameters[3].setErrorMessage("Input porosity must have only one band.")

        if parameters[0].altered and parameters[1].altered and parameters[2].altered and parameters[3].altered:
            if crs1.name != crs2.name or crs1.name != crs3.name or crs1.name != crs4.name:
                parameters[0].setErrorMessage("All input files must have the same coordinate system.")
                parameters[1].setErrorMessage("All input files must have the same coordinate system.")
                parameters[2].setErrorMessage("All input files must have the same coordinate system.")
                parameters[3].setErrorMessage("All input files must have the same coordinate system.")

        if parameters[4].value is not None and parameters[4].value < 0:
            parameters[4].setErrorMessage("The Smoothing Factor must be greater than 0.")
        if parameters[4].value is not None and parameters[4].value > 200:
            parameters[4].setWarningMessage("The Smoothing Factor may be too large.")
        if parameters[5].value is not None and parameters[5].value < 0:
            parameters[5].setErrorMessage("The Smoothing Cell must be greater than 0.")
        if parameters[5].value is not None and parameters[5].value >= 0 and parameters[5].value % 2 == 0:
            parameters[5].setWarningMessage("The Smoothing Cell is recommended to be an odd number.")
        if parameters[9].value is not None and parameters[9].value < 0:
            parameters[9].setErrorMessage("The Z-Factor must be greater than 0.")

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

        if parameters[10].altered and parameters[10].value is not None:
            if ".img" in parameters[10].valueAsText and (
                    ".gdb" in parameters[10].valueAsText or ".mdb" in parameters[10].valueAsText):
                parameters[10].setErrorMessage(
                    "When storing a raster dataset in a geodatabase, "
                    "do not add a file extension to the name of the raster dataset.")
        if parameters[11].altered and parameters[11].value is not None:
            if ".img" in parameters[11].valueAsText and (
                    ".gdb" in parameters[11].valueAsText or ".mdb" in parameters[11].valueAsText):
                parameters[11].setErrorMessage(
                    "When storing a raster dataset in a geodatabase, "
                    "do not add a file extension to the name of the raster dataset.")
        if parameters[12].altered and parameters[12].value is not None:
            if ".img" in parameters[12].valueAsText and (
                    ".gdb" in parameters[12].valueAsText or ".mdb" in parameters[12].valueAsText):
                parameters[12].setErrorMessage(
                    "When storing a raster dataset in a geodatabase, "
                    "do not add a file extension to the name of the raster dataset.")
        if parameters[13].altered and parameters[13].value is not None:
            if ".img" in parameters[13].valueAsText and (
                    ".gdb" in parameters[13].valueAsText or ".mdb" in parameters[13].valueAsText):
                parameters[13].setErrorMessage(
                    "When storing a raster dataset in a geodatabase, "
                    "do not add a file extension to the name of the raster dataset.")
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
        zfact  = parameters[9].value

        velo = parameters[10].valueAsText
        veld = parameters[11].valueAsText
        smth = parameters[12].valueAsText
        grad = parameters[13].valueAsText

        # Okay finally go ahead and do the work.
        try:
            arcpy.AddMessage("Compute Darcy Flow: START")
            GF = DarcyFlow(dem, wb, ks, poro,
                           smthf1, smthc, fsink, merge, smthf2, zfact,
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


    # Get an instance of the tool.
    update_datestamp = InterfaceGroundwaterFlow()
    # Read its default parameters.
    params = update_datestamp.getParameterInfo()

    # Set some test values into the instance
    arcpy.env.workspace = '.\\test_pro'
    params[0].value = os.path.join(arcpy.env.workspace, "lakeshore")
    params[1].value = os.path.join(arcpy.env.workspace, "hydr_cond.img")
    params[2].value = os.path.join(arcpy.env.workspace, "waterbodies.shp")
    params[3].value = os.path.join(arcpy.env.workspace, "porosity.img")
    params[10].value = os.path.join(arcpy.env.workspace, "veldemo")
    params[11].value = os.path.join(arcpy.env.workspace, "veldirdemo")

    update_datestamp.updateParameters(params)
    update_datestamp.execute(params, Messenger())

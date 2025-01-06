"""
Python code that implements an ArcGIS Tool,
to be included in an ArcGIS Python Toolbox.

@author: Wei Mao <wm23a@fsu.edu>， Michael Core <mcore@fsu.edu>, Ming Ye <mye@fsu.edu>
            The Department of Earth, Ocean, and Atmospheric Science, Florida State University
@ last modified date: 2023-11-27
"""

import os
import arcpy
import time
import importlib
import tool0_preprocessing
importlib.reload(tool0_preprocessing)

from tool0_preprocessing import Preprocessing


class InterfacePreprocessing(object):
    """This class has the methods to define the interface of the tool."""

    def __init__(self) -> None:
        """Define the tool.
        """
        self.label = "0-Preprocessing"
        self.description = """Preprocessing module."""
        self.category = "ArcNLET"

    def getParameterInfo(self):
        """Define parameter definitions.
        """
        infile0 = arcpy.Parameter(name="Study Area",
                                  displayName="Study Area (polygon)",
                                  datatype="GPFeatureLayer",
                                  parameterType="Required",
                                  direction="Input")
        infile0.filter.list = ["Polygon"]

        input0 = arcpy.Parameter(name="Projected Coordinate System",
                                 displayName="Projected Coordinate System [m]",
                                 datatype="GPCoordinateSystem",
                                 parameterType="Required",
                                 direction="Input")
        input0.parameterDependencies = [infile0.name]

        input1 = arcpy.Parameter(name="Top Depth",
                                 displayName="Top Depth [cm]",
                                 datatype="GPDouble",
                                 parameterType="Required",
                                 direction="Input")
        input1.value = 0

        input2 = arcpy.Parameter(name="Bottom Depth",
                                 displayName="Bottom Depth [cm]",
                                 datatype="GPDouble",
                                 parameterType="Required",
                                 direction="Input")
        input2.value = 200

        input3 = arcpy.Parameter(name="Extraction Method",
                                 displayName="Extraction Method",
                                 datatype="String",
                                 parameterType="Required",
                                 direction="Input")
        choices = ["Harmonic mean for Ks", "Weighted Average", "Dominant Component (Numeric)", "Min", "Max"]
        input3.filter.list = choices
        input3.value = choices[0]

        input4 = arcpy.Parameter(name="Raster Cell Size",
                                 displayName="Raster Cell Size [m]",
                                 datatype="GPDouble",
                                 parameterType="Required",
                                 direction="Input")
        input4.value = 10

        outfile0 = arcpy.Parameter(name="Output Hydraulic Conductivity (Raster)",
                                   displayName="Output Hydraulic Conductivity [m/d] (Raster)",
                                   datatype=["GPRasterLayer"],
                                   parameterType="Required",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )

        outfile1 = arcpy.Parameter(name="Output Porosity (Raster)",
                                   displayName="Output Porosity (Raster)",
                                   datatype=["GPRasterLayer"],
                                   parameterType="Required",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )

        outfile2 = arcpy.Parameter(name="Output Soil Texture (Raster)",
                                   displayName="(Optional) Output Soil type (VZMOD required)",
                                   datatype=["GPRasterLayer"],
                                   parameterType="Optional",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )

        outfile3 = arcpy.Parameter(name="Output Spatial SSURGO Data (Shapefile)",
                                   displayName="(Optional) Output Spatial SSURGO Data (Shapefile)",
                                   datatype=["GPFeatureLayer"],
                                   parameterType="Optional",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )

        return [infile0, input0, input1, input2, input3, input4,
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
        if parameters[0].altered:
            if not parameters[0].hasBeenValidated:
                area = arcpy.Describe(parameters[0].valueAsText).catalogPath
                desc = arcpy.Describe(area)
                spatial_reference = desc.spatialReference
                parameters[1].value = spatial_reference.factoryCode
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        if parameters[0].altered:
            area = arcpy.Describe(parameters[0].valueAsText).catalogPath
            feature_count = arcpy.management.GetCount(area).getOutput(0)
            if int(feature_count) > 1:
                parameters[0].setErrorMessage("Input area should be a single polygon.")
                return

            total_points = 0
            with arcpy.da.UpdateCursor(area, ["SHAPE@"]) as cursor:
                for row in cursor:
                    if row[0].isMultipart:
                        parameters[0].setErrorMessage("Input area should not be multipart polygon.")
                        return

                    for part in row[0]:
                        total_points += len(part)

            if total_points > 15000:
                parameters[0].setErrorMessage(
                    f"Input area exceeds the maximum point limit (15000).\n"
                    f"Current point count: {total_points}.\n"
                    "Excessive points may cause SSURGO Database to return incorrect results."
                )
                return

        if parameters[1].altered:
            wkt = parameters[1].value
            sr = arcpy.SpatialReference()
            sr.loadFromString(wkt)
            arcpy.AddMessage(wkt)
            arcpy.AddMessage(type(wkt))
            if sr.type == "Geographic":
                parameters[1].setErrorMessage("Input coordinate system must be projected, not geographic.")
            if sr.linearUnitName != "Meter":
                parameters[1].setErrorMessage(
                    "Input coordinate system is recommended to use meters. \n"
                    "The reason is that ArcNLET has some default values in VZMOD module and solute transport module, "
                    "and the default values are in units meter per day, such as nitrification/denitrification rate "
                    "and dispersivity of transport. \n")

        if parameters[2].value is not None and parameters[2].value < 0:
            parameters[2].setErrorMessage("Top depth must be greater than 0.")
        if parameters[3].value is not None and parameters[3].value < 0:
            parameters[3].setErrorMessage("Bottom depth must be greater than 0.")
        if parameters[2].value is not None and parameters[3].value is not None:
            if parameters[2].value > parameters[3].value:
                parameters[3].setErrorMessage("Bottom depth must be greater than top depth.")
        if parameters[5].value is not None and parameters[5].value < 0:
            parameters[5].setErrorMessage("Cell size must be greater than 0.")

        if parameters[0].altered and parameters[0].value is not None:
            filedir = arcpy.Describe(parameters[0].valueAsText).catalogPath
            if parameters[6].altered and parameters[6].value is not None:
                if self.is_file_path(parameters[6].valueAsText):
                    if ".gdb" in parameters[6].valueAsText or ".mdb" in parameters[6].valueAsText:
                        filename = os.path.basename(parameters[6].valueAsText)
                        if "." in filename:
                            parameters[6].setErrorMessage(
                                "When storing a raster dataset in a geodatabase, "
                                "do not add a file extension to the name of the raster dataset. ")
                else:
                    if ".gdb" in filedir or ".mdb" in filedir:
                        filename = parameters[6].valueAsText
                        if "." in filename:
                            parameters[6].setErrorMessage(
                                "When storing a raster dataset in a geodatabase, "
                                "do not add a file extension to the name of the raster dataset. "
                                "The default output location is same as Study Area shapefile")

            if parameters[7].altered and parameters[7].value is not None:
                if self.is_file_path(parameters[7].valueAsText):
                    if ".gdb" in parameters[7].valueAsText or ".mdb" in parameters[7].valueAsText:
                        filename = os.path.basename(parameters[7].valueAsText)
                        if "." in filename:
                            parameters[7].setErrorMessage(
                                "When storing a raster dataset in a geodatabase, "
                                "do not add a file extension to the name of the raster dataset. ")
                else:
                    if ".gdb" in filedir or ".mdb" in filedir:
                        filename = parameters[7].valueAsText
                        if "." in filename:
                            parameters[7].setErrorMessage(
                                "When storing a raster dataset in a geodatabase, "
                                "do not add a file extension to the name of the raster dataset. "
                                "The default output location is same as Study Area shapefile")

            if parameters[8].altered and parameters[8].value is not None:
                if self.is_file_path(parameters[8].valueAsText):
                    if ".gdb" in parameters[8].valueAsText or ".mdb" in parameters[8].valueAsText:
                        filename = os.path.basename(parameters[8].valueAsText)
                        if "." in filename:
                            parameters[8].setErrorMessage(
                                "When storing a raster dataset in a geodatabase, "
                                "do not add a file extension to the name of the raster dataset. ")
                else:
                    if ".gdb" in filedir or ".mdb" in filedir:
                        filename = parameters[8].valueAsText
                        if "." in filename:
                            parameters[8].setErrorMessage(
                                "When storing a raster dataset in a geodatabase, "
                                "do not add a file extension to the name of the raster dataset. "
                                "The default output location is same as Study Area shapefile")

            if parameters[9].altered and parameters[9].value is not None:
                if self.is_file_path(parameters[9].valueAsText):
                    if ".gdb" in parameters[9].valueAsText or ".mdb" in parameters[9].valueAsText:
                        filename = os.path.basename(parameters[9].valueAsText)
                        if "." in filename:
                            parameters[9].setErrorMessage(
                                "When storing a raster dataset in a geodatabase, "
                                "do not add a file extension to the name of the raster dataset. ")
                else:
                    if ".gdb" in filedir or ".mdb" in filedir:
                        filename = parameters[9].valueAsText
                        if "." in filename:
                            parameters[9].setErrorMessage(
                                "When storing a raster dataset in a geodatabase, "
                                "do not add a file extension to the name of the raster dataset. "
                                "The default output location is same as Study Area shapefile")
        return

    def execute(self, parameters, messages) -> None:
        """This is the code that executes when you click the "Run" button."""

        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage(f"{current_time} Preprocessing: START")
        for param in parameters:
            self.describeParameter(messages, param)

        study_area  = parameters[0].valueAsText
        proj_coord  = parameters[1].valueAsText
        top_depth   = parameters[2].valueAsText
        bot_depth   = parameters[3].valueAsText
        method      = parameters[4].valueAsText
        cell_size   = parameters[5].valueAsText

        hydr = parameters[6].valueAsText
        poro = parameters[7].valueAsText
        text = parameters[8].valueAsText
        spat = parameters[9].valueAsText

        # Okay finally go ahead and do the work.
        try:
            # current_time = time.strftime("%H:%M:%S", time.localtime())
            # arcpy.AddMessage(f"{current_time} Preprocessing: START")
            PP = Preprocessing(study_area, proj_coord, top_depth, bot_depth, method, cell_size,
                               hydr, poro, text, spat)
            PP.main()
            current_time = time.strftime("%H:%M:%S", time.localtime())
            arcpy.AddMessage(f"{current_time} Preprocessing: FINISH")
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

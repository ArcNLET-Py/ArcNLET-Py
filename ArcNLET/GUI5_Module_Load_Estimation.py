"""
Python code that implements an ArcGIS Tool,
to be included in an ArcGIS Python Toolbox.

@author: Wei Mao <wm23a@fsu.edu>， Michael Core <mcore@fsu.edu>, Ming Ye <mye@fsu.edu>
            The Department of Earth, Ocean, and Atmospheric Science, Florida State University
@date: 2023-11-07
"""

import os
import time
import arcpy

import importlib
import tool5_load_estimation
importlib.reload(tool5_load_estimation)
from tool5_load_estimation import LoadEstimation


class InterfaceLoadEstimation(object):
    """This class has the methods to define the interface of the tool."""

    def __init__(self) -> None:
        """Define the tool. """
        self.label = "5-Load Estimation"
        self.description = """Load Estimation."""
        self.category = "ArcNLET"

    def getParameterInfo(self) -> list:
        """Define parameter definitions.
        """
        param0 = arcpy.Parameter(name="Consideration of NH\u2084",
                                 displayName="Consideration of NH\u2084",
                                 datatype="GPBoolean",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 )
        param0.value = 0

        param1 = arcpy.Parameter(name="Risk Factor",
                                 displayName="Risk Factor",
                                 datatype="GPDouble",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 )
        param1.value = 1.0

        infile1 = arcpy.Parameter(name="Input Plumes NO\u2083 info",
                                  displayName="Input Plumes NO\u2083 info (Point)",
                                  datatype="GPFeatureLayer",
                                  parameterType="Required",
                                  direction="Input")
        infile1.filter.list = ["Point"]

        infile2 = arcpy.Parameter(name="Input Plumes NH\u2084 info",
                                  displayName="Input Plumes NH\u2084 info (Point)",
                                  datatype="GPFeatureLayer",
                                  parameterType="Required",
                                  direction="Input")
        infile2.filter.list = ["Point"]
        # infile2.parameterDependencies = [param0.name]

        outfile1 = arcpy.Parameter(name="Output Results for NO\u2083",
                                   displayName="Output Results for NO\u2083",
                                   datatype="DEFile",
                                   parameterType="required",
                                   direction="Output")

        outfile2 = arcpy.Parameter(name="Output Results for NH\u2084",
                                   displayName="Output Results for NH\u2084",
                                   datatype="DEFile",
                                   parameterType="Optional",
                                   direction="Output")
        # outfile2.parameterDependencies = [param0.name]

        return [param0, param1, infile1, infile2, outfile1, outfile2]

    def isLicensed(self) -> bool:
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters) -> None:
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[0].altered:
            if parameters[0].value:
                parameters[3].enabled = True
                parameters[5].enabled = True
            else:
                parameters[3].enabled = False
                parameters[5].enabled = False

        if parameters[2].altered and parameters[2].value is not None:
            if not parameters[2].hasBeenValidated:
                ppath = arcpy.Describe(parameters[2].valueAsText).catalogPath if not self.is_file_path(
                    parameters[2].valueAsText) else parameters[2].valueAsText
                filename, file_extension = os.path.splitext(ppath)
                dfilename = filename + ".csv"
                parameters[4].value = dfilename

        if parameters[3].altered and parameters[3].value is not None:
            if not parameters[3].hasBeenValidated:
                ppath = arcpy.Describe(parameters[3].valueAsText).catalogPath if not self.is_file_path(
                    parameters[3].valueAsText) else parameters[3].valueAsText
                filename, file_extension = os.path.splitext(ppath)
                dfilename = filename + ".csv"
                parameters[5].value = dfilename
        return

    def updateMessages(self, parameters) -> None:
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        if parameters[1].value is not None and parameters[1].value < 0:
            parameters[1].setErrorMessage("Risk Factor should be greater than 0.")

        if parameters[2].value is not None:
            desc = arcpy.Describe(parameters[2].valueAsText)
            fields = desc.fields
            if not any(field.name == "massInRate" for field in fields):
                parameters[2].setErrorMessage("massInRate field is missing.")
            if not any(field.name == "massDNRate" for field in fields):
                parameters[2].setErrorMessage("massDNRate field is missing.")
            if not any(field.name == "WBId_plume" for field in fields):
                parameters[2].setErrorMessage("WBId_plume field is missing.")

        if parameters[0].value:
            if parameters[3].value is not None:
                desc = arcpy.Describe(parameters[3].valueAsText)
                fields = desc.fields
                if not any(field.name == "massInRate" for field in fields):
                    parameters[3].setErrorMessage("massInRate field is missing.")
                if not any(field.name == "massDNRate" for field in fields):
                    parameters[3].setErrorMessage("massDNRate field is missing.")
                if not any(field.name == "WBId_plume" for field in fields):
                    parameters[3].setErrorMessage("WBId_plume field is missing.")

        if parameters[4].value is not None:
            filename, file_extension = os.path.splitext(parameters[4].valueAsText)
            if file_extension != ".csv":
                parameters[4].setErrorMessage("Please use a .csv file.")

        if parameters[5].value is not None:
            filename, file_extension = os.path.splitext(parameters[5].valueAsText)
            if file_extension != ".csv":
                parameters[5].setErrorMessage("Please use a .csv file.")
        return

    def execute(self, parameters, messages) -> None:
        """This is the code that executes when you click the "Run" button."""

        messages.addMessage("Load Estimation Module.")

        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage(f"{current_time} Load Estimation: START")

        if not self.is_file_path(parameters[2].valueAsText):
            parameters[2].value = arcpy.Describe(parameters[2].valueAsText).catalogPath
        if parameters[0].value:
            if not self.is_file_path(parameters[3].valueAsText):
                parameters[3].value = arcpy.Describe(parameters[3].valueAsText).catalogPath

        for param in parameters:
            self.describeParameter(messages, param)
        
        whethernh4 = parameters[0].valueAsText
        riskfactor = parameters[1].value
        plumesno3 = parameters[2].valueAsText
        outfileno3 = parameters[4].valueAsText
        if parameters[0].value:
            plumesnh4 = parameters[3].valueAsText
            outfilenh4 = parameters[5].valueAsText
        else:
            plumesnh4 = None
            outfilenh4 = None

        try:
            LE = LoadEstimation(whethernh4, riskfactor, plumesno3, outfileno3, plumesnh4, outfilenh4)
            LE.calculate_load_estimation()
            current_time = time.strftime("%H:%M:%S", time.localtime())
            arcpy.AddMessage(f"{current_time} Load Estimation: FINISH")
        except Exception as e:
            current_time = time.strftime("%H:%M:%S", time.localtime())
            arcpy.AddMessage(f"{current_time} Fail. {e}")
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

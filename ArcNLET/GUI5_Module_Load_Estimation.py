"""
Python code that implements implements an ArcGIS Tool,
to be included in an ArcGIS Python Toolbox.

@author: Wei Mao <wm23a@fsu.edu>
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
        self.label = "5 Load Estimation"
        self.description = """Load Estimation."""
        self.category = "ArcNLET"

    def getParameterInfo(self) -> list:
        """Define parameter definitions.
        """
        param0 = arcpy.Parameter(name="whether NH4",
                                 displayName="Consideration of NH\u2084",
                                 datatype="GPBoolean",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 )
        param0.value = 0

        param1 = arcpy.Parameter(name="RiskFactor",
                                 displayName="Risk Factor",
                                 datatype="GPDouble",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 )
        param1.value = 1.0

        infile1 = arcpy.Parameter(name="PlumesNO3",
                                  displayName="Plumes NO\u2083 info (Point)",
                                  datatype="GPFeatureLayer",
                                  parameterType="Required",
                                  direction="Input")
        infile1.filter.list = ["Point"]

        infile2 = arcpy.Parameter(name="PlumesNH4",
                                  displayName="Plumes NH\u2084 info (Point)",
                                  datatype="GPFeatureLayer",
                                  parameterType="Required",
                                  direction="Optional")
        infile2.filter.list = ["Point"]
        infile2.parameterDependencies = [param0.name]

        return [param0, param1, infile1, infile2]

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
            else:
                parameters[3].enabled = False
        return

    def updateMessages(self, parameters) -> None:
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        if parameters[1].value is not None and parameters[1].value < 0:
            parameters[1].setErrorMessage("Risk Factor should be greater than 0.")
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
        riskfactor = parameters[1].valueAsText
        plumesno3 = parameters[2].valueAsText
        if parameters[0].value:
            plumesnh4 = parameters[3].valueAsText
        else:
            plumesnh4 = None

        try:
            LE = LoadEstimation(whethernh4, riskfactor, plumesno3, plumesnh4)
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
            m.addMessage("  Path \"%s\"" % p.valueAsText)

    @staticmethod
    def is_file_path(input_string):
        return os.path.sep in input_string

    
# =============================================================================
if __name__ == "__main__":

    class Messenger(object):
        def addMessage(self, message):
            print(message)

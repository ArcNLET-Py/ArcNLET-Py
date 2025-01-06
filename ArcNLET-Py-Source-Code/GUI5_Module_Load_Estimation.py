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
        inputop = arcpy.Parameter(name="Types of contaminants",
                                  displayName="Types of contaminants",
                                  datatype="String",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  )
        choices = ["Nitrogen", "Phosphorus", "Nitrogen and Phosphorus"]
        inputop.filter.list = choices
        inputop.value = "Nitrogen"

        param0 = arcpy.Parameter(name="Consideration of NH\u2084-N",
                                 displayName="Consideration of NH\u2084-N",
                                 datatype="GPBoolean",
                                 parameterType="Optional",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 )
        param0.enabled = True
        param0.value = 0

        param1 = arcpy.Parameter(name="Risk Factor",
                                 displayName="Risk Factor",
                                 datatype="GPDouble",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 )
        param1.value = 1.0

        infile1 = arcpy.Parameter(name="Input Plumes NO\u2083-N info",
                                  displayName="Input Plumes NO\u2083-N info (Point)",
                                  datatype="GPFeatureLayer",
                                  parameterType="Optional",
                                  direction="Input")
        infile1.filter.list = ["Point"]

        infile2 = arcpy.Parameter(name="Input Plumes NH\u2084-N info",
                                  displayName="Input Plumes NH\u2084-N info (Point)",
                                  datatype="GPFeatureLayer",
                                  parameterType="Optional",
                                  direction="Input")
        infile2.filter.list = ["Point"]
        infile2.enabled = False
        # infile2.parameterDependencies = [param0.name]

        infile3 = arcpy.Parameter(name="Input Plumes PO\u2084-P info",
                                  displayName="Input Plumes PO\u2084-P info (Point)",
                                  datatype="GPFeatureLayer",
                                  parameterType="Optional",
                                  direction="Input")
        infile3.filter.list = ["Point"]
        infile3.enabled = False

        outfile1 = arcpy.Parameter(name="Output Results for NO\u2083-N",
                                   displayName="Output Results for NO\u2083-N",
                                   datatype="DEFile",
                                   parameterType="Optional",
                                   direction="Output")
        # outfile1.value = "NO3N_loading.csv"

        outfile2 = arcpy.Parameter(name="Output Results for NH\u2084-N",
                                   displayName="Output Results for NH\u2084-N",
                                   datatype="DEFile",
                                   parameterType="Optional",
                                   direction="Output")
        outfile2.enabled = False
        # outfile2.parameterDependencies = [param0.name]
        # outfile2.value = "NH4N_loading.csv"

        outfile3 = arcpy.Parameter(name="Output Results for PO\u2084-P",
                                   displayName="Output Results for PO\u2084-P",
                                   datatype="DEFile",
                                   parameterType="Optional",
                                   direction="Output")
        outfile3.enabled = False
        # outfile3.value = "PO4P_loading.csv"

        return [inputop, param0, param1, infile1, infile2, infile3, outfile1, outfile2, outfile3]

    def isLicensed(self) -> bool:
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters) -> None:
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[0].altered:
            if parameters[0].value == "Nitrogen and Phosphorus":
                parameters[1].enabled = True
                parameters[3].enabled = True
                parameters[5].enabled = True
                parameters[6].enabled = True
                parameters[8].enabled = True
                if parameters[1].altered:
                    if parameters[1].value:
                        parameters[4].enabled = True
                        parameters[7].enabled = True
                    else:
                        parameters[4].enabled = False
                        parameters[7].enabled = False
            elif parameters[0].value == "Nitrogen":
                parameters[1].enabled = True
                parameters[3].enabled = True
                parameters[5].enabled = False
                parameters[6].enabled = True
                parameters[8].enabled = False
                if parameters[1].altered:
                    if parameters[1].value:
                        parameters[4].enabled = True
                        parameters[7].enabled = True
                    else:
                        parameters[4].enabled = False
                        parameters[7].enabled = False
            elif parameters[0].value == "Phosphorus":
                parameters[1].enabled = False
                parameters[3].enabled = False
                parameters[4].enabled = False
                parameters[5].enabled = True
                parameters[6].enabled = False
                parameters[7].enabled = False
                parameters[8].enabled = True

        if parameters[3].altered and parameters[3].value is not None:
            if not parameters[3].hasBeenValidated:
                ppath = arcpy.Describe(parameters[3].valueAsText).catalogPath if not self.is_file_path(
                    parameters[3].valueAsText) else parameters[3].valueAsText
                filename, file_extension = os.path.splitext(ppath)
                dfilename = filename + ".csv"
                parameters[6].value = dfilename

        if parameters[4].altered and parameters[4].value is not None:
            if not parameters[4].hasBeenValidated:
                ppath = arcpy.Describe(parameters[4].valueAsText).catalogPath if not self.is_file_path(
                    parameters[4].valueAsText) else parameters[4].valueAsText
                filename, file_extension = os.path.splitext(ppath)
                dfilename = filename + ".csv"
                parameters[7].value = dfilename

        if parameters[5].altered and parameters[5].value is not None:
            if not parameters[5].hasBeenValidated:
                ppath = arcpy.Describe(parameters[5].valueAsText).catalogPath if not self.is_file_path(
                    parameters[5].valueAsText) else parameters[5].valueAsText
                filename, file_extension = os.path.splitext(ppath)
                dfilename = filename + ".csv"
                parameters[8].value = dfilename
        return

    def updateMessages(self, parameters) -> None:
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        if parameters[2].value is not None and parameters[2].value < 0:
            parameters[2].setErrorMessage("Risk Factor should be greater than 0.")

        if parameters[0].value == "Nitrogen and Phosphorus" or parameters[0].value == "Nitrogen":
            if parameters[3].value is not None:
                desc = arcpy.Describe(parameters[3].valueAsText)
                fields = desc.fields
                if not any(field.name == "massInRate" for field in fields):
                    parameters[3].setErrorMessage("massInRate field is missing.")
                if not any(field.name == "massRMRate" for field in fields):
                    parameters[3].setErrorMessage("massRMRate field is missing.")
                if not any(field.name == "WBId_plume" for field in fields):
                    parameters[3].setErrorMessage("WBId_plume field is missing.")
            if parameters[1].value:
                if parameters[4].value is not None:
                    desc = arcpy.Describe(parameters[4].valueAsText)
                    fields = desc.fields
                    if not any(field.name == "massInRate" for field in fields):
                        parameters[4].setErrorMessage("massInRate field is missing.")
                    if not any(field.name == "massRMRate" for field in fields):
                        parameters[4].setErrorMessage("massRMRate field is missing.")
                    if not any(field.name == "WBId_plume" for field in fields):
                        parameters[4].setErrorMessage("WBId_plume field is missing.")

        if parameters[0].value == "Nitrogen and Phosphorus" or parameters[0].value == "Phosphorus":
            if parameters[5].value is not None:
                desc = arcpy.Describe(parameters[5].valueAsText)
                fields = desc.fields
                if not any(field.name == "massInRate" for field in fields):
                    parameters[5].setErrorMessage("massInRate field is missing.")
                if not any(field.name == "massRMRate" for field in fields):
                    parameters[5].setErrorMessage("massRMRate field is missing.")
                if not any(field.name == "WBId_plume" for field in fields):
                    parameters[5].setErrorMessage("WBId_plume field is missing.")

        if parameters[6].value is not None:
            filename, file_extension = os.path.splitext(parameters[6].valueAsText)
            if file_extension != ".csv":
                parameters[6].setErrorMessage("Please use a .csv file.")

        if parameters[7].value is not None:
            filename, file_extension = os.path.splitext(parameters[7].valueAsText)
            if file_extension != ".csv":
                parameters[7].setErrorMessage("Please use a .csv file.")

        if parameters[8].value is not None:
            filename, file_extension = os.path.splitext(parameters[8].valueAsText)
            if file_extension != ".csv":
                parameters[8].setErrorMessage("Please use a .csv file.")
        return

    def execute(self, parameters, messages) -> None:
        """This is the code that executes when you click the "Run" button."""

        messages.addMessage("Load Estimation Module.")

        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage(f"{current_time} Load Estimation: START")

        if parameters[0].value == "Nitrogen and Phosphorus":
            if not self.is_file_path(parameters[3].valueAsText):
                parameters[3].value = arcpy.Describe(parameters[3].valueAsText).catalogPath
            if parameters[1].value:
                if not self.is_file_path(parameters[4].valueAsText):
                    parameters[4].value = arcpy.Describe(parameters[4].valueAsText).catalogPath
            if not self.is_file_path(parameters[5].valueAsText):
                parameters[5].value = arcpy.Describe(parameters[5].valueAsText).catalogPath
        elif parameters[0].value == "Nitrogen":
            if not self.is_file_path(parameters[3].valueAsText):
                parameters[3].value = arcpy.Describe(parameters[3].valueAsText).catalogPath
            if parameters[1].value:
                if not self.is_file_path(parameters[4].valueAsText):
                    parameters[4].value = arcpy.Describe(parameters[4].valueAsText).catalogPath
        elif parameters[0].value == "Phosphorus":
            if not self.is_file_path(parameters[5].valueAsText):
                parameters[5].value = arcpy.Describe(parameters[5].valueAsText).catalogPath

        for param in parameters:
            self.describeParameter(messages, param)
        
        type_of_contaminants = parameters[0].value
        whethernh4 = parameters[1].valueAsText
        riskfactor = parameters[2].value
        plumesno3 = parameters[3].valueAsText
        plumesnh4 = parameters[4].valueAsText
        plumesp = parameters[5].valueAsText
        outfileno3 = parameters[6].valueAsText
        outfilenh4 = parameters[7].valueAsText
        outfilep = parameters[8].valueAsText

        if type_of_contaminants == "Nitrogen":
            if not whethernh4:
                plumesnh4 = None
                outfilenh4 = None
            plumesp = None
            outfilep = None
        elif type_of_contaminants == "Phosphorus":
            plumesno3 = None
            outfileno3 = None
            plumesnh4 = None
            outfilenh4 = None

        try:
            LE = LoadEstimation(type_of_contaminants, whethernh4, riskfactor,
                                plumesno3, outfileno3,
                                plumesnh4, outfilenh4,
                                plumesp, outfilep)
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


"""
Python code that implements implements an ArcGIS Tool,
to be included in an ArcGIS Python Toolbox.

@author: Wei Mao <wm23a@fsu.edu>
"""

import os
import arcpy
from datetime import datetime

# This is for development, so that you can edit code while running in ArcGIS Pro.
import importlib
import tool4_load_estimation
importlib.reload(tool4_load_estimation)

from tool4_load_estimation import LoadEstimation


class InterfaceLoadEstimation(object):
    """This class has the methods to define the interface of the tool."""

    def __init__(self) -> None:
        """Define the tool. """
        self.label = "Load Estimation"
        self.description = """Smoothing DEM to obtain an approximation of the groundwater table."""
        self.canRunInBackground = False
        self.category = "ArcNLET"

    def getParameterInfo(self) -> list:
        """Define parameter definitions.
Refer to https://pro.arcgis.com/en/pro-app/latest/arcpy/geoprocessing_and_python/defining-parameters-in-a-python-toolbox.htm
        """       

        infile0 = arcpy.Parameter(name="dem",
                                  displayName="DEM surface elevation map [L] (raster)",
                                  datatype=["DERasterDataset"],
                                  parameterType="Required", # Required|Optional|Derived
                                  direction="Input", # Input|Output
                                  )

        param0 = arcpy.Parameter(name="smthf",
                                 displayName="Smoothing factor",
                                 datatype="GPLong",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input", # Input|Output
                                  )
        param0.value = 20

        return [infile0, param0]

    def isLicensed(self) -> bool:
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters) -> None:
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[0].altered:
            if not arcpy.Exists(parameters[0].value):
                parameters[0].setErrorMessage("Feature class could not be opened.")
        return

    def execute(self, parameters, messages) -> None:
        """This is the code that executes when you click the "Run" button."""
        
        # Let's dump out what we know here.
        messages.addMessage("This is a test of your tool.")
        for param in parameters:
            self.describeParameter(messages,param)
        
        # Get the parameters from our parameters list,
        # then call a generic python function.
        #
        # This separates the code doing the work from all
        # the crazy code required to talk to ArcGIS.
        
        # See http://resources.arcgis.com/en/help/main/10.2/index.html#//018z00000063000000
        input_fc  = parameters[0].valueAsText
        # fieldname = parameters[1].valueAsText
        # datestamp = parameters[2].valueAsText
        # number    = parameters[3].value
        # depnumber = parameters[4].value
        # output_fc = parameters[5].valueAsText
        
        # Okay finally go ahead and do the work.
        try:
            LoadEstimationTool(input_fc)
            messages.addMessage("Success.")
        except Exception as e:
            arcpy.AddError("Fail. %s" % e)
        return

    def describeParameter(self, m, p):
        m.addMessage("===Parameter=== %s \"%s\"" % (p.name, p.displayName))
        m.addMessage("  altered? %s" % p.altered)
        m.addMessage("  value \"%s\"" % p.valueAsText)
        m.addMessage("  datatype %s" % p.datatype)
        m.addMessage("  filter %s" % p.filter)

    
# =============================================================================
if __name__ == "__main__":
    # This is an example of how you could set up a unit test for this tool.
    # You can run this tool from a debugger or from the command line
    # to check it for errors before you try it in ArcGIS.
    
    class Messenger(object):
        def addMessage(self, message):
            print(message)

    # Get an instance of the tool.
    update_datestamp = Tool_Interface()
    # Read its default parameters.
    params = update_datestamp.getParameterInfo()

    # Set some test values into the instance
    arcpy.env.workspace = '.\\test_pro\\demo.gdb'
    params[0].value = os.path.join(arcpy.env.workspace, "lakeshore")
    # params[1].value = os.path.join(arcpy.env.workspace, "hydr_cond")
    # params[2].value = os.path.join(arcpy.env.workspace, "waterbodies")
    # params[3].value = os.path.join(arcpy.env.workspace, "porosity")
    # params[8].value = os.path.join(arcpy.env.workspace, "veldemo")
    # params[9].value = os.path.join(arcpy.env.workspace, "veldirdemo")
    
    # Run it.
    update_datestamp.execute(params, Messenger())

# That's all

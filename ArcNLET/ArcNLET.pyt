"""
Python Toolbox Template (a ".pyt" file)

This tool is developed based on ArcGIS Pro 3.1, please reference the link:
https://pro.arcgis.com/en/pro-app/latest/arcpy/geoprocessing_and_python/creating-a-new-python-toolbox.htm
(Open date 7/27/2023)

@author: Wei Mao <wm23a@fsu.edu>
"""
import arcpy

# This is for development, so that you can edit code while running in ArcGIS Pro.
import importlib
import GUI1_Module_Groundwater_Flow
import GUI2_Module_Particle_Tracking
import GUI3_Module_Transport
import GUI4_Module_Load_Estimation
importlib.reload(GUI1_Module_Groundwater_Flow)
importlib.reload(GUI2_Module_Particle_Tracking)
importlib.reload(GUI3_Module_Transport)
importlib.reload(GUI4_Module_Load_Estimation)

# Import all the tool classes that will be included in this toolbox.
from GUI1_Module_Groundwater_Flow  import InterfaceGroundwaterFlow
from GUI2_Module_Particle_Tracking import InterfaceParticleTracking
from GUI3_Module_Transport         import InterfaceTransport
from GUI4_Module_Load_Estimation   import InterfaceLoadEstimation


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of this .pyt file)."""
        self.label = "ArcNLET Python Toolbox"
        self.alias = ""  # no special characters including spaces!
        self.description = """ArcNLET python toolbox for ArcGIS Pro!"""

        # List of tool classes associated with this toolbox
        self.tools = [
            InterfaceGroundwaterFlow,
            InterfaceParticleTracking,
            InterfaceTransport,
            InterfaceLoadEstimation
        ]

def list_tools():
    toolbox = Toolbox()
    print("toolbox:", toolbox.label)
    print("description:", toolbox.description)
    print("tools:")
    for t in toolbox.tools:
        tool = t()
        print('  ', tool.label)
        print('   description:', tool.description)
        for param in tool.getParameterInfo():
            print('    ',param.name,':',param.displayName)
        print()


if __name__ == "__main__":
    # Running this as a standalone script lists information about the toolbox and each tool.
    list_tools()

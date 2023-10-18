"""
Python code that implements implements an ArcGIS Tool,
to be included in an ArcGIS Python Toolbox.

@author: Wei Mao <wm23a@fsu.edu>
"""

import importlib
import os
import time
import arcpy
import tool3_transport
importlib.reload(tool3_transport)
from tool3_transport import Transport


class InterfaceTransport(object):
    """This class has the methods to define the interface of the tool."""

    def __init__(self) -> None:
        """Define the tool. """
        self.label = "3 Transport"
        self.description = """Transport module."""
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

        infile0 = arcpy.Parameter(name="Source locations (point)",
                                  displayName="Input Source locations (point)",
                                  datatype="GPFeatureLayer",
                                  parameterType="Required",
                                  direction="Input")
        infile0.filter.list = ["Point"]

        infile1 = arcpy.Parameter(name="Waterbodies",
                                  displayName="Input Water bodies (polygon)",
                                  datatype="GPFeatureLayer",
                                  parameterType="Required",
                                  direction="Input")
        infile1.filter.list = ["Polygon"]

        infile2 = arcpy.Parameter(name="Particle path",
                                  displayName="Input Particle Paths (polyline)",
                                  datatype="GPFeatureLayer",
                                  parameterType="Required",
                                  direction="Input")
        infile2.filter.list = ["Polyline"]

        outfile0 = arcpy.Parameter(name="Plumes_NO3",
                                   displayName="Plumes of NO\u2083 (raster)",
                                   datatype=["GPRasterLayer"],
                                   parameterType="Required",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )

        outfile1 = arcpy.Parameter(name="Plumes_NH4",
                                   displayName="Plumes of NH\u2084 (raster)",
                                   datatype=["GPRasterLayer"],
                                   parameterType="Optional",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )
        outfile1.parameterDependencies = [param0.name]

        option0 = arcpy.Parameter(name="Solution_type",
                                  displayName="Solution type",
                                  datatype="String",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  category="Options",  # Category
                                  )
        choices = ['DomenicoRobbinsSS2D', 'DomenicoRobbinsSSDecay2D']
        option0.filter.type = "ValueList"
        option0.filter.list = choices
        option0.value = choices[1]

        option1 = arcpy.Parameter(name="Plume_point",
                                  displayName="Plume warping control point spacing [Cells]",
                                  datatype="Long",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  category="Options",  # Category
                                  )
        option1.value = 48

        option2 = arcpy.Parameter(name="Plume_method",
                                  displayName="Plume warping method",
                                  datatype="String",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  category="Options",  # Category
                                  )
        choices = ['Spline', 'Polyorder1', 'Polyorder2']
        option2.filter.type = "ValueList"
        option2.filter.list = choices
        option2.value = choices[2]

        option3 = arcpy.Parameter(name="threshold",
                                  displayName="Threshold Concentration [M/L\u00B3]",
                                  datatype="Double",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  category="Options",  # Category
                                  )
        option3.value = 0.000001

        option4 = arcpy.Parameter(name="postprocessing",
                                  displayName="Post processing",
                                  datatype="String",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  category="Options",  # Category
                                  )
        choices = ['None', 'Medium', 'Full']
        option4.filter.type = "ValueList"
        option4.filter.list = choices
        option4.value = choices[1]

        option5 = arcpy.Parameter(name="Demenico",
                                  displayName="Domenico Bdy.",
                                  datatype="String",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  category="Options",  # Category
                                  )
        choices = ['Specified Input Mass Rate', 'Specified Z']
        option5.filter.type = "ValueList"
        option5.filter.list = choices
        option5.value = choices[0]

        param1 = arcpy.Parameter(name="Mass_input",
                                 displayName="Mass input [M/T]",
                                 datatype="Double",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",  # Category
                                 )
        param1.value = 20000

        param2 = arcpy.Parameter(name="Y",
                                 displayName="Source Dimension Y [L]",
                                 datatype="Double",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",  # Category
                                 )
        param2.value = 6

        param3 = arcpy.Parameter(name="Z",
                                 displayName="Source Dimension Z [L]",
                                 datatype="Double",
                                 parameterType="Optional",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",  # Category
                                 )
        param3.enabled = False
        param3.value = 1.5

        param4 = arcpy.Parameter(name="Use_maxZ",
                                  displayName="Maximum Z [L]",
                                  datatype="GPBoolean",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  category="Parameters",  # Category
                                  )
        param4.value = 1

        param5 = arcpy.Parameter(name="Zmax",
                                 displayName="Zmax [L]",
                                 datatype="Double",
                                 parameterType="Optional",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",  # Category
                                 )
        param5.value = 3.0

        param6 = arcpy.Parameter(name="Plumecellsize",
                                 displayName="Plume cell size [L]",
                                 datatype="Double",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",  # Category
                                 )
        param6.value = 0.4

        no3param0 = arcpy.Parameter(name="NO3Co",
                                    displayName="NO\u2083 Concentration [M/L\u00B3]",
                                    datatype="Double",
                                    parameterType="Required",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        no3param0.value = 40

        no3param1 = arcpy.Parameter(name="no3DispersivitiesaL",
                                    displayName="NO\u2083 Dispersivity \u03B1L [L]",
                                    datatype="Double",
                                    parameterType="Required",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        no3param1.value = 2.113

        no3param2 = arcpy.Parameter(name="no3DispersivitiesaTH",
                                    displayName="NO\u2083 Dispersivity \u03B1TH [L]",
                                    datatype="Double",
                                    parameterType="Required",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        no3param2.value = 0.234

        no3param3 = arcpy.Parameter(name="DenitriDecay",
                                    displayName="Denitrification Decay Rate [1/T]",
                                    datatype="Double",
                                    parameterType="Required",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        no3param3.value = 0.008

        no3param4 = arcpy.Parameter(name="VolConverFactor",
                                    displayName="Volume Conversion Factor",
                                    datatype="Double",
                                    parameterType="Required",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        no3param4.value = 1000

        nh4param0 = arcpy.Parameter(name="NH4Co",
                                    displayName="NH\u2084 Concentration [M/L\u00B3]",
                                    datatype="Double",
                                    parameterType="Optional",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        nh4param0.value = 10

        nh4param1 = arcpy.Parameter(name="nh4DispersivitiesaL",
                                    displayName="NH\u2084 Dispersivity \u03B1L [L]",
                                    datatype="Double",
                                    parameterType="Optional",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        nh4param1.value = 2.113

        nh4param2 = arcpy.Parameter(name="nh4DispersivitiesaTH",
                                    displayName="NH\u2084 Dispersivity \u03B1TH [L]",
                                    datatype="Double",
                                    parameterType="Optional",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        nh4param2.value = 0.234

        nh4param3 = arcpy.Parameter(name="NitriDecay",
                                    displayName="Nitrification Decay Rate [1/T]",
                                    datatype="Double",
                                    parameterType="Optional",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        nh4param3.value = 0.0001

        nh4param4 = arcpy.Parameter(name="BulDens",
                                    displayName="Bulk Density [M/L\u00B3]",
                                    datatype="Double",
                                    parameterType="Optional",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        nh4param4.value = 1.42

        nh4param5 = arcpy.Parameter(name="Adsorption",
                                    displayName="Adsorption coefficient [L\u00B3/M]",
                                    datatype="Double",
                                    parameterType="Optional",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        nh4param5.value = 2

        return [param0, infile0, infile1, infile2, outfile0, outfile1,  # 0 - 5
                option0, option1, option2, option3, option4, option5,  # 6 - 11
                param1, param2, param3, param4, param5, param6,  # 12 - 17
                no3param0, no3param1, no3param2, no3param3, no3param4,  # 18 - 22
                nh4param0, nh4param1, nh4param2, nh4param3, nh4param4, nh4param5]  # 23 - 28

    def isLicensed(self) -> bool:
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters) -> None:
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[0].altered:
            if parameters[0].value:
                parameters[5].enabled = True
                parameters[23].enabled = True
                parameters[24].enabled = True
                parameters[25].enabled = True
                parameters[26].enabled = True
                parameters[27].enabled = True
                parameters[28].enabled = True
            else:
                parameters[5].enabled = False
                parameters[23].enabled = False
                parameters[24].enabled = False
                parameters[25].enabled = False
                parameters[26].enabled = False
                parameters[27].enabled = False
                parameters[28].enabled = False

        if parameters[1].altered:
            source_location = parameters[1].value
            if not arcpy.Exists(source_location):
                arcpy.AddMessage("The specified source location does not exist.")
            desc = arcpy.Describe(source_location)
            crs1 = desc.spatialReference

            field_list = desc.fields
            no3_exists = any(field.name.lower() == "no3_conc" for field in field_list)
            parameters[18].enabled = True
            if not no3_exists:
                if parameters[18].altered:
                    if parameters[18].value < 0:
                        arcpy.AddMessage("NO3 initial concentration must be a positive number.")
            else:
                parameters[18].enabled = False
                with arcpy.da.SearchCursor(source_location, ["NO3_Conc"]) as cursor:
                    for row in cursor:
                        no3 = float(row[0])
                        if no3 < 0:
                            arcpy.AddMessage("NO3 initial concentration must be a positive number.")
            if parameters[0].value:
                nh4_exists = any(field.name.lower() == "nh4_conc" for field in field_list)
                parameters[23].enabled = True
                if not nh4_exists:
                    if parameters[23].altered:
                        if parameters[23].value < 0:
                            arcpy.AddMessage("NH4 initial concentration must be a positive number.")
                else:
                    parameters[23].enabled = False
                    with arcpy.da.SearchCursor(source_location, ["NH4_Conc"]) as cursor:
                        for row in cursor:
                            nh4 = float(row[0])
                            if nh4 < 0:
                                arcpy.AddMessage("NH4 initial concentration must be a positive number.")

        if parameters[2].altered:
            wb = parameters[2].value
            if not arcpy.Exists(wb):
                arcpy.AddMessage("The specified shapefile does not exist.")
            desc = arcpy.Describe(wb)
            crs2 = desc.spatialReference

        if parameters[3].altered:
            ppath = parameters[3].value
            if not arcpy.Exists(ppath):
                arcpy.AddMessage("The specified shapefile does not exist.")
            desc = arcpy.Describe(ppath)
            crs3 = desc.spatialReference

        if parameters[1].altered and parameters[2].altered and parameters[3].altered:
            if crs1.name != crs2.name or crs1.name != crs3.name:
                arcpy.AddMessage("All input files must have the same coordinate system.")

        if parameters[6].altered:
            if parameters[6].value == "DomenicoRobbinsSS2D":
                parameters[21].enabled = False
            elif parameters[6].value == "DomenicoRobbinsSSDecay2D":
                parameters[21].enabled = True

        if parameters[7].altered:
            if parameters[7].value < 0:
                arcpy.AddMessage("Plume warping control points must be a positive integer.")
        if parameters[9].altered:
            if parameters[9].value < 0:
                arcpy.AddMessage("Threshold concentration must be a positive number.")
            elif parameters[9].value > 0.1:
                arcpy.AddMessage("Threshold concentration is large than 0.1. Maybe it is too large.")

        if parameters[11].altered:
            if parameters[11].value == 'Specified Z':
                parameters[12].enabled = False
                parameters[14].enabled = True
                parameters[15].enabled = False
                parameters[16].enabled = False
                if parameters[14].altered:
                    if parameters[14].value < 0:
                        arcpy.AddMessage("Z must be a positive number.")
            else:
                parameters[12].enabled = True
                parameters[14].enabled = False
                parameters[15].enabled = True
                if parameters[12].altered:
                    if parameters[12].value < 0:
                        arcpy.AddMessage("Mass input must be a positive number.")
                if parameters[15].altered:
                    if parameters[15].value == 0:
                        parameters[16].enabled = False
                    else:
                        parameters[16].enabled = True
                if parameters[16].value < 0:
                    arcpy.AddMessage("Zmax must be a positive number.")

        if parameters[13].altered:
            if parameters[13].value < 0:
                arcpy.AddMessage("Y must be a positive number.")

        if parameters[17].altered:
            if parameters[17].value < 0:
                arcpy.AddMessage("Plume cell size must be a positive number.")
        # parameters[17].value = parameters[13].value / 15

        if parameters[19].altered:
            if parameters[19].value < 0:
                arcpy.AddMessage("NO3 dispersivity alphaL must be a positive number.")
        if parameters[20].altered:
            if parameters[20].value < 0:
                arcpy.AddMessage("NO3 dispersivity alphaTH must be a positive number.")
        if parameters[21].altered:
            if parameters[21].value < 0:
                arcpy.AddMessage("NO3 decay rate must be a positive number.")
        if parameters[22].altered:
            if parameters[22].value < 0:
                arcpy.AddMessage("NO3 volume conversion factor must be a positive number.")
        if parameters[24].altered:
            if parameters[24].value < 0:
                arcpy.AddMessage("NH4 dispersivity alphaL must be a positive number.")
        if parameters[25].altered:
            if parameters[25].value < 0:
                arcpy.AddMessage("NH4 dispersivity alphaTH must be a positive number.")
        if parameters[26].altered:
            if parameters[26].value < 0:
                arcpy.AddMessage("NH4 decay rate must be a positive number.")
        if parameters[27].altered:
            if parameters[27].value < 0:
                arcpy.AddMessage("Bulk density must be a positive number.")
        if parameters[28].altered:
            if parameters[28].value < 0:
                arcpy.AddMessage("NH4 adsorption coefficient must be a positive number.")

    def execute(self, parameters, messages) -> None:
        """This is the code that executes when you click the "Run" button."""

        messages.addMessage("Solute transport module.")

        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage(f"{current_time} Transport: START")

        if not self.is_file_path(parameters[1].valueAsText):
            parameters[1].value = arcpy.Describe(parameters[1].valueAsText).catalogPath
        if not self.is_file_path(parameters[2].valueAsText):
            parameters[2].value = arcpy.Describe(parameters[2].valueAsText).catalogPath
        if not self.is_file_path(parameters[3].valueAsText):
            parameters[3].value = arcpy.Describe(parameters[3].valueAsText).catalogPath

        for param in parameters:
            self.describeParameter(messages, param)

        whethernh4 = parameters[0].valueAsText
        sourcelocation = parameters[1].valueAsText
        waterbodies = parameters[2].valueAsText
        particlepath = parameters[3].valueAsText
        no3output = parameters[4].valueAsText
        nh4output = parameters[5].valueAsText
        option0 = parameters[6].valueAsText
        option1 = parameters[7].valueAsText
        option2 = parameters[8].valueAsText
        option3 = parameters[9].valueAsText
        option4 = parameters[10].valueAsText
        option5 = parameters[11].valueAsText
        param1 = parameters[12].valueAsText
        param2 = parameters[13].valueAsText
        param3 = parameters[14].valueAsText
        param4 = parameters[15].valueAsText
        param5 = parameters[16].valueAsText
        param6 = parameters[17].valueAsText
        no3param0 = parameters[18].valueAsText
        no3param1 = parameters[19].valueAsText
        no3param2 = parameters[20].valueAsText
        no3param3 = parameters[21].valueAsText
        no3param4 = parameters[22].valueAsText
        nh4param0 = parameters[23].valueAsText
        nh4param1 = parameters[24].valueAsText
        nh4param2 = parameters[25].valueAsText
        nh4param3 = parameters[26].valueAsText
        nh4param4 = parameters[27].valueAsText
        nh4param5 = parameters[28].valueAsText

        # Okay finally go ahead and do the work.
        try:
            TP = Transport(whethernh4, sourcelocation, waterbodies, particlepath, no3output, nh4output,
                           option0, option1, option2, option3, option4, option5,
                           param1, param2, param3, param4, param5, param6,
                           no3param0, no3param1, no3param2, no3param3, no3param4,
                           nh4param0, nh4param1, nh4param2, nh4param3, nh4param4, nh4param5)
            TP.calculate_plumes()
            current_time = time.strftime("%H:%M:%S", time.localtime())
            arcpy.AddMessage(f"{current_time} Transport: FINISH")
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

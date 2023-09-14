"""
Python code that implements implements an ArcGIS Tool,
to be included in an ArcGIS Python Toolbox.

@author: Wei Mao <wm23a@fsu.edu>
"""

# This is for development, so that you can edit code while running in ArcGIS Pro.
import importlib
import os
import arcpy
import tool3_transport
importlib.reload(tool3_transport)
from tool3_transport import Transport


class InterfaceTransport(object):
    """This class has the methods to define the interface of the tool."""

    def __init__(self) -> None:
        """Define the tool. """
        self.label = "Transport"
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

        infile0 = arcpy.Parameter(name="Source locations",
                                  displayName="Input Source locations (point)",
                                  datatype=["DEFeatureClass"],
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  )

        infile1 = arcpy.Parameter(name="Waterbodies",
                                  displayName="Input Water bodies (polygon)",
                                  datatype=["DEFeatureClass"],
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  )

        infile2 = arcpy.Parameter(name="Particle path",
                                  displayName="Input Particle Paths (Polyline)",
                                  datatype=["DEFeatureClass"],
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  )

        outfile0 = arcpy.Parameter(name="Plumes_NO3",
                                   displayName="Plumes of NO\u2083 (raster)",
                                   datatype=["DERasterDataset"],
                                   parameterType="Required",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )

        outfile1 = arcpy.Parameter(name="Plumes_NH4",
                                   displayName="Plumes of NH\u2084 (raster)",
                                   datatype=["DERasterDataset"],
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
        choices = ['Spline', 'Polynomial1', 'Polynomial2']
        option2.filter.type = "ValueList"
        option2.filter.list = choices
        option2.value = choices[2]

        option3 = arcpy.Parameter(name="Use_approximate",
                                  displayName="Use approximate solution",
                                  datatype="GPBoolean",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  category="Options",  # Category
                                  )
        option3.value = 1

        option4 = arcpy.Parameter(name="threshold",
                                  displayName="Threshold Concentration [M/L\u00B3]",
                                  datatype="Double",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  category="Options",  # Category
                                  )
        option4.value = 0.000001

        option5 = arcpy.Parameter(name="postprocessing",
                                  displayName="Post processing",
                                  datatype="String",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  category="Options",  # Category
                                  )
        choices = ['None', 'Medium', 'Full']
        option5.filter.type = "ValueList"
        option5.filter.list = choices
        option5.value = choices[1]

        option6 = arcpy.Parameter(name="Demenico",
                                  displayName="Domenico Bdy.",
                                  datatype="String",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  category="Options",  # Category
                                  )
        choices = ['Specified Input Mass Rate', 'Specified Z']
        option6.filter.type = "ValueList"
        option6.filter.list = choices
        option6.value = choices[0]

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

        param4 = arcpy.Parameter(name="Zmax",
                                 displayName="Zmax [L]",
                                 datatype="Double",
                                 parameterType="Optional",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",  # Category
                                 )
        param4.value = 3.0

        param5 = arcpy.Parameter(name="Plumecellsize",
                                 displayName="Plume cell size [L]",
                                 datatype="Double",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",  # Category
                                 )
        param5.value = 0.4

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

        nh4param6 = arcpy.Parameter(name="Avetheta",
                                    displayName="Average Theta",
                                    datatype="Double",
                                    parameterType="Optional",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        nh4param6.value = 0.5

        return [param0, infile0, infile1, infile2, outfile0, outfile1,  # 0 - 5
                option0, option1, option2, option3, option4, option5, option6,  # 6 - 12
                param1, param2, param3, param4, param5,  # 13 - 17
                no3param0, no3param1, no3param2, no3param3, no3param4,  # 18 - 22
                nh4param0, nh4param1, nh4param2, nh4param3, nh4param4, nh4param5, nh4param6]  # 23 - 29

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
                parameters[29].enabled = True
            else:
                parameters[5].enabled = False
                parameters[23].enabled = False
                parameters[24].enabled = False
                parameters[25].enabled = False
                parameters[26].enabled = False
                parameters[27].enabled = False
                parameters[28].enabled = False
                parameters[29].enabled = False

        if parameters[1].altered:
            source_location = parameters[1].value
            if not arcpy.Exists(source_location):
                raise arcpy.ParameterError("The specified source location does not exist.")
            desc = arcpy.Describe(source_location)
            crs1 = desc.spatialReference
            if desc.shapeType != "Point":
                raise arcpy.ParameterError("Input source location must be a point feature.")
            field_list = desc.fields
            no3_exists = any(field.name.lower() == "no3_conc" for field in field_list)
            parameters[18].enabled = True
            if not no3_exists:
                if parameters[18].altered:
                    if parameters[18].value < 0:
                        raise arcpy.ParameterError("NO3 initial concentration must be a positive number.")
            else:
                parameters[18].enabled = False
                with arcpy.da.SearchCursor(source_location, ["NO3_Conc"]) as cursor:
                    for row in cursor:
                        no3 = float(row[0])
                        if no3 < 0:
                            raise arcpy.ParameterError("NO3 initial concentration must be a positive number.")
            if parameters[0].value:
                nh4_exists = any(field.name.lower() == "nh4_conc" for field in field_list)
                parameters[23].enabled = True
                if not nh4_exists:
                    if parameters[23].altered:
                        if parameters[23].value < 0:
                            raise arcpy.ParameterError("NH4 initial concentration must be a positive number.")
                else:
                    parameters[23].enabled = False
                    with arcpy.da.SearchCursor(source_location, ["NH4_Conc"]) as cursor:
                        for row in cursor:
                            nh4 = float(row[0])
                            if nh4 < 0:
                                raise arcpy.ParameterError("NH4 initial concentration must be a positive number.")

        if parameters[2].altered:
            wb = parameters[2].value
            if not arcpy.Exists(wb):
                raise arcpy.ParameterError("The specified shapefile does not exist.")
            desc = arcpy.Describe(wb)
            crs2 = desc.spatialReference
            if desc.dataType == "FeatureClass" and desc.shapeType == "Polygon":
                arcpy.AddMessage("Input waterbodies is a polygon feature.")
            elif desc.dataType == "RasterDataset":
                arcpy.AddMessage("Input waterbodies is a raster dataset.")
            else:
                raise arcpy.ParameterError("Input waterbodies must be either a polygon feature or a raster dataset.")

        if parameters[3].altered:
            ppath = parameters[3].value
            if not arcpy.Exists(ppath):
                raise arcpy.ParameterError("The specified shapefile does not exist.")
            desc = arcpy.Describe(ppath)
            crs3 = desc.spatialReference
            if desc.shapeType != "Polyline":
                raise arcpy.ParameterError("Input particle path must be a polyline feature.")

        if parameters[1].altered and parameters[2].altered and parameters[3].altered:
            if crs1.name != crs2.name or crs1.name != crs3.name:
                raise arcpy.ParameterError("All input files must have the same coordinate system.")

        if parameters[7].altered:
            if parameters[7].value < 0:
                raise arcpy.ParameterError("Plume warping control points must be a positive integer.")
        if parameters[10].altered:
            if parameters[10].value < 0:
                raise arcpy.ParameterError("Threshold concentration must be a positive number.")
            elif parameters[10].value > 0.1:
                arcpy.AddMessage("Threshold concentration is large than 0.1. Maybe it is too large.")

        if parameters[12].altered:
            if parameters[12].value == 'Specified Z':
                parameters[13].enabled = False
                parameters[15].enabled = True
                parameters[16].enabled = False
                if parameters[15].altered:
                    if parameters[15].value < 0:
                        raise arcpy.ParameterError("Z must be a positive number.")
            else:
                parameters[13].enabled = True
                parameters[15].enabled = False
                parameters[16].enabled = True
                if parameters[13].altered:
                    if parameters[13].value < 0:
                        raise arcpy.ParameterError("Mass input must be a positive number.")
                if parameters[16].altered:
                    if parameters[16].value < 0:
                        raise arcpy.ParameterError("Zmax must be a positive number.")

        if parameters[14].altered:
            if parameters[14].value < 0:
                raise arcpy.ParameterError("Y must be a positive number.")
            parameters[17].value = int(parameters[14].value / 15)
            if parameters[17].altered:
                if parameters[14].value % parameters[17].value != 0:
                    raise arcpy.ParameterError("Y must be a multiple of plume cell size.")
                if parameters[14].value / parameters[17].value > 30 or parameters[14].value / parameters[17].value < 5:
                    arcpy.AddMessage(
                        "Y or plume cell size is not in the recommended range.\n"
                        "Y is recommended to be [5L, 30L] times of plume cell size.")

        if parameters[19].altered:
            if parameters[19].value < 0:
                raise arcpy.ParameterError("NO3 dispersivity alphaL must be a positive number.")
        if parameters[20].altered:
            if parameters[20].value < 0:
                raise arcpy.ParameterError("NO3 dispersivity alphaTH must be a positive number.")
        if parameters[21].altered:
            if parameters[21].value < 0:
                raise arcpy.ParameterError("NO3 decay rate must be a positive number.")
        if parameters[22].altered:
            if parameters[22].value < 0:
                raise arcpy.ParameterError("NO3 volume conversion factor must be a positive number.")
        if parameters[24].altered:
            if parameters[24].value < 0:
                raise arcpy.ParameterError("NH4 dispersivity alphaL must be a positive number.")
        if parameters[25].altered:
            if parameters[25].value < 0:
                raise arcpy.ParameterError("NH4 dispersivity alphaTH must be a positive number.")
        if parameters[26].altered:
            if parameters[26].value < 0:
                raise arcpy.ParameterError("NH4 decay rate must be a positive number.")
        if parameters[27].altered:
            if parameters[27].value < 0:
                raise arcpy.ParameterError("Bulk density must be a positive number.")
        if parameters[28].altered:
            if parameters[28].value < 0:
                raise arcpy.ParameterError("NH4 adsorption coefficient must be a positive number.")
        if parameters[29].altered:
            if parameters[29].value < 0:
                raise arcpy.ParameterError("Average theta must be a positive number.")

    def execute(self, parameters, messages) -> None:
        """This is the code that executes when you click the "Run" button."""
        
        # Let's dump out what we know here.
        messages.addMessage("Solute transport module.")
        for param in parameters:
            self.describeParameter(messages, param)
        
        # Get the parameters from our parameters list,
        # then call a generic python function.
        #
        # This separates the code doing the work from all
        # the crazy code required to talk to ArcGIS.
        
        # See http://resources.arcgis.com/en/help/main/10.2/index.html#//018z00000063000000
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
        option6 = parameters[12].valueAsText
        param1 = parameters[13].valueAsText
        param2 = parameters[14].valueAsText
        param3 = parameters[15].valueAsText
        param4 = parameters[16].valueAsText
        param5 = parameters[17].valueAsText
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
        nh4param6 = parameters[29].valueAsText
        
        # Okay finally go ahead and do the work.
        try:
            TP = Transport(whethernh4, sourcelocation, waterbodies, particlepath, no3output, nh4output,
                           option0, option1, option2, option3, option4, option5, option6,
                           param1, param2, param3, param4, param5,
                           no3param0, no3param1, no3param2, no3param3, no3param4,
                           nh4param0, nh4param1, nh4param2, nh4param3, nh4param4, nh4param5, nh4param6)
            TP.run()
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

"""
Python code that implements an ArcGIS Tool,
to be included in an ArcGIS Python Toolbox.

@author: Wei Mao <wm23a@fsu.edu>， Michael Core <mcore@fsu.edu>, Ming Ye <mye@fsu.edu>
            The Department of Earth, Ocean, and Atmospheric Science, Florida State University
@date: 2023-11-07
"""

import importlib
import os
import time
import arcpy
import tool4_transport
importlib.reload(tool4_transport)
from tool4_transport import Transport


class InterfaceTransport(object):
    """This class has the methods to define the interface of the tool."""

    def __init__(self) -> None:
        """Define the tool. """
        self.label = "4-Transport"
        self.description = """Transport module."""
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

        infile0 = arcpy.Parameter(name="Source locations (point)",
                                  displayName="Input Source locations (point)",
                                  datatype="GPFeatureLayer",
                                  parameterType="Required",
                                  direction="Input")
        infile0.filter.list = ["Point"]

        infile1 = arcpy.Parameter(name="Water bodies",
                                  displayName="Input Water bodies (polygon)",
                                  datatype="GPFeatureLayer",
                                  parameterType="Required",
                                  direction="Input")
        infile1.filter.list = ["Polygon"]

        infile2 = arcpy.Parameter(name="Particle paths",
                                  displayName="Input Particle Paths (polyline)",
                                  datatype="GPFeatureLayer",
                                  parameterType="Required",
                                  direction="Input")
        infile2.filter.list = ["Polyline"]

        outfile0 = arcpy.Parameter(name="Output Plumes of NO\u2083",
                                   displayName="Output Plumes of NO\u2083 (raster)",
                                   datatype=["GPRasterLayer"],
                                   parameterType="Required",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )

        outfile1 = arcpy.Parameter(name="Output Plumes of NH\u2084",
                                   displayName="Output Plumes of NH\u2084 (raster)",
                                   datatype=["GPRasterLayer"],
                                   parameterType="Optional",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )
        outfile1.parameterDependencies = [param0.name]

        outfile2 = arcpy.Parameter(name="Output Plumes info of NO\u2083",
                                   displayName="Output Plumes info of NO\u2083 (point)",
                                   datatype=["GPFeatureLayer"],
                                   parameterType="Optional",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )
        outfile2.enabled = False

        outfile3 = arcpy.Parameter(name="Output Plumes info of NH\u2084",
                                   displayName="Output Plumes info of NH\u2084 (point)",
                                   datatype=["GPFeatureLayer"],
                                   parameterType="Optional",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )
        outfile3.enabled = False
        outfile3.parameterDependencies = [param0.name]

        option0 = arcpy.Parameter(name="Solution type",
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

        option1 = arcpy.Parameter(name="Plume warping control point spacing",
                                  displayName="Plume warping control point spacing [Cells]",
                                  datatype="Long",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  category="Options",  # Category
                                  )
        option1.value = 48

        option2 = arcpy.Parameter(name="Plume warping method",
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

        option3 = arcpy.Parameter(name="Threshold Concentration",
                                  displayName="Threshold Concentration [mg/l]",
                                  datatype="Double",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  category="Options",  # Category
                                  )
        option3.value = 0.000001

        option4 = arcpy.Parameter(name="Postprocessing",
                                  displayName="Postprocessing",
                                  datatype="String",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  category="Options",  # Category
                                  )
        choices = ['None', 'Medium', 'Full']
        option4.filter.type = "ValueList"
        option4.filter.list = choices
        option4.value = choices[1]

        option5 = arcpy.Parameter(name="Demenico Bdy.",
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

        param1 = arcpy.Parameter(name="Mass input",
                                 displayName="Mass input [mg/d]",
                                 datatype="Double",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",  # Category
                                 )
        param1.value = 20000

        param2 = arcpy.Parameter(name="Source Dimension Y",
                                 displayName="Source Dimension Y [m]",
                                 datatype="Double",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",  # Category
                                 )
        param2.value = 12

        param3 = arcpy.Parameter(name="Source Dimension Z",
                                 displayName="Source Dimension Z [m]",
                                 datatype="Double",
                                 parameterType="Optional",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",  # Category
                                 )
        param3.enabled = False
        param3.value = 1.5

        param4 = arcpy.Parameter(name="Maximum Z",
                                  displayName="Maximum Z [m]",
                                  datatype="GPBoolean",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  category="Parameters",  # Category
                                  )
        param4.value = 1

        param5 = arcpy.Parameter(name="Zmax",
                                 displayName="Zmax [m]",
                                 datatype="Double",
                                 parameterType="Optional",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",  # Category
                                 )
        param5.value = 3.0

        param6 = arcpy.Parameter(name="Plume cell size",
                                 displayName="Plume cell size [m]",
                                 datatype="Double",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",  # Category
                                 )
        param6.value = 0.8

        no3param0 = arcpy.Parameter(name="NO\u2083 Concentration",
                                    displayName="NO\u2083 Concentration [mg/l]",
                                    datatype="Double",
                                    parameterType="Required",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        no3param0.value = 40

        no3param1 = arcpy.Parameter(name="NO\u2083 Dispersivity \u03B1L",
                                    displayName="NO\u2083 Dispersivity \u03B1L [m]",
                                    datatype="Double",
                                    parameterType="Required",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        no3param1.value = 2.113

        no3param2 = arcpy.Parameter(name="NO\u2083 Dispersivity \u03B1TH",
                                    displayName="NO\u2083 Dispersivity \u03B1TH [m]",
                                    datatype="Double",
                                    parameterType="Required",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        no3param2.value = 0.234

        no3param3 = arcpy.Parameter(name="Denitrification Decay Rate",
                                    displayName="Denitrification Decay Rate [1/d]",
                                    datatype="Double",
                                    parameterType="Required",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        no3param3.value = 0.008

        no3param4 = arcpy.Parameter(name="Volume Conversion Factor",
                                    displayName="Volume Conversion Factor",
                                    datatype="Double",
                                    parameterType="Required",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        no3param4.value = 1000

        nh4param0 = arcpy.Parameter(name="NH\u2084 Concentration",
                                    displayName="NH\u2084 Concentration [mg/l]",
                                    datatype="Double",
                                    parameterType="Optional",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        nh4param0.value = 10

        nh4param1 = arcpy.Parameter(name="NH\u2084 Dispersivity \u03B1L",
                                    displayName="NH\u2084 Dispersivity \u03B1L [m]",
                                    datatype="Double",
                                    parameterType="Optional",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        nh4param1.value = 2.113

        nh4param2 = arcpy.Parameter(name="NH\u2084 Dispersivity \u03B1TH",
                                    displayName="NH\u2084 Dispersivity \u03B1TH [m]",
                                    datatype="Double",
                                    parameterType="Optional",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        nh4param2.value = 0.234

        nh4param3 = arcpy.Parameter(name="Nitrification Decay Rate",
                                    displayName="Nitrification Decay Rate [1/d]",
                                    datatype="Double",
                                    parameterType="Optional",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        nh4param3.value = 0.0001

        nh4param4 = arcpy.Parameter(name="Bulk Density",
                                    displayName="Bulk Density [g/cm\u00B3]",
                                    datatype="Double",
                                    parameterType="Optional",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        nh4param4.value = 1.42

        nh4param5 = arcpy.Parameter(name="Adsorption coefficient",
                                    displayName="Adsorption coefficient [cm\u00B3/g]",
                                    datatype="Double",
                                    parameterType="Optional",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Parameters",  # Category
                                    )
        nh4param5.value = 2

        maxnum = arcpy.Parameter(name="Maximum plumes of continuous calculation for one time",
                                 displayName="Maximum plumes of continuous calculation for one time",
                                 datatype="Long",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Options",  # Category
                                 )
        maxnum.value = 500

        return [param0, infile0, infile1, infile2, outfile0, outfile1, outfile2, outfile3,   # 0 - 7
                option0, option1, option2, option3, option4, option5, maxnum,                # 8 - 14
                param1, param2, param3, param4, param5, param6,                              # 15 - 20
                no3param0, no3param1, no3param2, no3param3, no3param4,                       # 21 - 25
                nh4param0, nh4param1, nh4param2, nh4param3, nh4param4, nh4param5]            # 26 - 31

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
                parameters[26].enabled = True
                parameters[27].enabled = True
                parameters[28].enabled = True
                parameters[29].enabled = True
                parameters[30].enabled = True
                parameters[31].enabled = True
            else:
                parameters[5].enabled = False
                parameters[26].enabled = False
                parameters[27].enabled = False
                parameters[28].enabled = False
                parameters[29].enabled = False
                parameters[30].enabled = False
                parameters[31].enabled = False

        if parameters[1].altered:
            source_location = parameters[1].value
            desc = arcpy.Describe(source_location)
            crs1 = desc.spatialReference
            field_list = desc.fields
            no3_exists = any(field.name.lower() == "no3_conc" for field in field_list)
            if not no3_exists:
                parameters[21].enabled = True
            else:
                parameters[21].enabled = False

            if parameters[0].value:
                nh4_exists = any(field.name.lower() == "nh4_conc" for field in field_list)
                if not nh4_exists:
                    parameters[26].enabled = True
                else:
                    parameters[26].enabled = False

        if parameters[8].altered:
            if parameters[8].value == "DomenicoRobbinsSS2D":
                parameters[24].enabled = False
            elif parameters[8].value == "DomenicoRobbinsSSDecay2D":
                parameters[24].enabled = True

        if parameters[13].altered:
            if parameters[13].value == 'Specified Z':
                parameters[15].enabled = False
                parameters[17].enabled = True
                parameters[18].enabled = False
                parameters[19].enabled = False

            else:
                parameters[15].enabled = True
                parameters[17].enabled = False
                parameters[18].enabled = True
                if parameters[18].altered:
                    if parameters[18].value == 0:
                        parameters[19].enabled = False
                    else:
                        parameters[19].enabled = True

        if parameters[16].altered:
            if not parameters[16].hasBeenValidated:
                parameters[20].value = parameters[16].value / 15
        return

    def updateMessages(self, parameters) -> None:
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        if parameters[1].altered:
            source_location = parameters[1].value
            desc = arcpy.Describe(source_location)
            crs1 = desc.spatialReference
            field_list = desc.fields
            no3_exists = any(field.name.lower() == "no3_conc" for field in field_list)
            if crs1.linearUnitName != "Meter":
                parameters[1].setErrorMessage("The linear unit of the source location must be meter.")
            if no3_exists:
                with arcpy.da.SearchCursor(source_location, ["NO3_Conc"]) as cursor:
                    for row in cursor:
                        no3 = float(row[0])
                        if no3 < 0:
                            parameters[1].setErrorMessage("NO3 initial concentration must be a positive number.")
            if parameters[0].value:
                nh4_exists = any(field.name.lower() == "nh4_conc" for field in field_list)
                if nh4_exists:
                    with arcpy.da.SearchCursor(source_location, ["NH4_Conc"]) as cursor:
                        for row in cursor:
                            nh4 = float(row[0])
                            if nh4 < 0:
                                parameters[1].setErrorMessage("NH4 initial concentration must be a positive number.")

        if parameters[2].altered:
            wb = parameters[2].value
            desc = arcpy.Describe(wb)
            crs2 = desc.spatialReference
            if crs2.linearUnitName != "Meter":
                parameters[2].setErrorMessage("The linear unit of the water bodies must be meter.")
        if parameters[3].altered:
            ppath = parameters[3].value
            desc = arcpy.Describe(ppath)
            crs3 = desc.spatialReference
            if crs3.linearUnitName != "Meter":
                parameters[3].setErrorMessage("The linear unit of the particle paths must be meter.")

        if parameters[1].altered and parameters[2].altered and parameters[3].altered:
            if crs1.name != crs2.name or crs1.name != crs3.name:
                parameters[1].setErrorMessage("All input files must have the same coordinate system. \n"
                                              + "\n" +
                                              "Source locations projected coordinate system : {} \n".format(crs1.name)
                                              + "Water bodies projected coordinate system : {} \n".format(crs2.name)
                                              + "Particle paths projected coordinate system : {} \n".format(crs3.name))
                parameters[2].setErrorMessage("All input files must have the same coordinate system. \n"
                                              + "\n" +
                                              "Source locations projected coordinate system : {} \n".format(crs1.name)
                                              + "Water bodies projected coordinate system : {} \n".format(crs2.name)
                                              + "Particle paths projected coordinate system : {} \n".format(crs3.name))
                parameters[3].setErrorMessage("All input files must have the same coordinate system. \n"
                                              + "\n" +
                                              "Source locations projected coordinate system : {} \n".format(crs1.name)
                                              + "Water bodies projected coordinate system : {} \n".format(crs2.name)
                                              + "Particle paths projected coordinate system : {} \n".format(crs3.name))

        if parameters[4].altered and parameters[4].value is not None:
            if ".gdb" in parameters[4].valueAsText or ".mdb" in parameters[4].valueAsText:
                parameters[4].setErrorMessage(
                    "Storing the results in a geodatabase will cause an error during calculation")
            else:
                filename, fileext = os.path.splitext(parameters[4].valueAsText)
                parameters[6].value = os.path.basename(filename) + "_info"
        if parameters[5].altered and parameters[5].value is not None:
            if ".gdb" in parameters[5].valueAsText or ".mdb" in parameters[5].valueAsText:
                parameters[5].setErrorMessage(
                    "Storing the results in a geodatabase will cause an error during calculation")
            else:
                filename, fileext = os.path.splitext(parameters[5].valueAsText)
                parameters[7].value = os.path.basename(filename) + "_info"

        if parameters[9].value is not None and parameters[9].value < 0:
            parameters[9].setErrorMessage("Plume warping control points must be a positive integer.")
        if parameters[11].value is not None:
            if parameters[11].value < 0:
                parameters[11].setErrorMessage("Threshold concentration must be a positive number.")
            elif parameters[11].value > 0.1:
                parameters.setErrorMessage("Threshold concentration is large than 0.1. Maybe it is too large.")

        if parameters[15].value is not None and parameters[15].value < 0:
            parameters[15].setErrorMessage("Mass input must be a positive number.")
        if parameters[16].value is not None and parameters[16].value < 0:
            parameters[16].setErrorMessage("Y must be a positive number.")
        if parameters[17].value is not None and parameters[17].value < 0:
            parameters[17].setErrorMessage("Z must be a positive number.")
        if parameters[19].value is not None and parameters[19].value < 0:
            parameters[19].setErrorMessage("Zmax must be a positive number.")
        if parameters[20].value is not None and parameters[20].value < 0:
            parameters[20].setErrorMessage("Plume cell size must be a positive number.")

        if parameters[21].value is not None and parameters[21].value < 0:
            parameters[21].setErrorMessage("NO3 initial concentration must be a positive number.")
        if parameters[22].value is not None and parameters[22].value < 0:
            parameters[22].setErrorMessage("NO3 dispersivity alphaL must be a positive number.")
        if parameters[23].value is not None and parameters[23].value < 0:
            parameters[23].setErrorMessage("NO3 dispersivity alphaTH must be a positive number.")
        if parameters[24].value is not None and parameters[24].value < 0:
            parameters[24].setErrorMessage("NO3 decay rate must be a positive number.")
        if parameters[25].value is not None and parameters[25].value < 0:
            parameters[25].setErrorMessage("NO3 volume conversion factor must be a positive number.")
        if parameters[26].value is not None and parameters[26].value < 0:
            parameters[26].setErrorMessage("NH4 initial concentration must be a positive number.")
        if parameters[27].value is not None and parameters[27].value < 0:
            parameters[27].setErrorMessage("NH4 dispersivity alphaL must be a positive number.")
        if parameters[28].value is not None and parameters[28].value < 0:
            parameters[28].setErrorMessage("NH4 dispersivity alphaTH must be a positive number.")
        if parameters[29].value is not None and parameters[29].value < 0:
            parameters[29].setErrorMessage("NH4 decay rate must be a positive number.")
        if parameters[30].value is not None and parameters[30].value < 0:
            parameters[30].setErrorMessage("Bulk density must be a positive number.")
        if parameters[31].value is not None and parameters[31].value < 0:
            parameters[31].setErrorMessage("NH4 adsorption coefficient must be a positive number.")
        return

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

        whethernh4 = parameters[0].value
        sourcelocation = parameters[1].valueAsText
        waterbodies = parameters[2].valueAsText
        particlepath = parameters[3].valueAsText
        no3output = parameters[4].valueAsText
        nh4output = parameters[5].valueAsText
        no3outputinfo = parameters[6].valueAsText
        nh4outputinfo = parameters[7].valueAsText
        option0 = parameters[8].valueAsText
        option1 = parameters[9].value
        option2 = parameters[10].valueAsText
        option3 = parameters[11].value
        option4 = parameters[12].valueAsText
        option5 = parameters[13].valueAsText
        maxnum = parameters[14].value

        param1 = parameters[15].value
        param2 = parameters[16].value
        param3 = parameters[17].value
        param4 = parameters[18].value
        param5 = parameters[19].value
        param6 = parameters[20].value
        no3param0 = parameters[21].value
        no3param1 = parameters[22].value
        no3param2 = parameters[23].value
        no3param3 = parameters[24].value
        no3param4 = parameters[25].value
        nh4param0 = parameters[26].value
        nh4param1 = parameters[27].value
        nh4param2 = parameters[28].value
        nh4param3 = parameters[29].value
        nh4param4 = parameters[30].value
        nh4param5 = parameters[31].value

        # Okay finally go ahead and do the work.
        try:
            TP = Transport(whethernh4, sourcelocation, waterbodies, particlepath,
                           no3output, nh4output, no3outputinfo, nh4outputinfo,
                           option0, option1, option2, option3, option4, option5, maxnum,
                           param1, param2, param3, param4, param5, param6,
                           no3param0, no3param1, no3param2, no3param3, no3param4,
                           nh4param0, nh4param1, nh4param2, nh4param3, nh4param4, nh4param5)

            TP.main()
            current_time = time.strftime("%H:%M:%S", time.localtime())
            arcpy.AddMessage(f"{current_time} Transport: FINISH")
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

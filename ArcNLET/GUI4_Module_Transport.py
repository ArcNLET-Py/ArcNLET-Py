"""
Python code that implements an ArcGIS Tool,
to be included in an ArcGIS Python Toolbox.

@author: Wei Mao <wm23a@fsu.edu>， Michael Core <mcore@fsu.edu>, Ming Ye <mye@fsu.edu>
            The Department of Earth, Ocean, and Atmospheric Science, Florida State University
@date: 2023-11-07
"""

import importlib
import re
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
        inputop = arcpy.Parameter(name="Types of contaminants",
                                  displayName="Types of contaminants",
                                  datatype="String",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  )
        choices = ["Nitrogen", "Phosphorus", "Nitrogen and Phosphorus"]
        inputop.filter.list = choices
        inputop.value = "Nitrogen"

        whenh4 = arcpy.Parameter(name="Consideration of NH\u2084-N",
                                 displayName="Consideration of NH\u2084-N",
                                 datatype="GPBoolean",
                                 parameterType="Optional",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 )
        whenh4.enable = True
        whenh4.value = 0

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

        outfile0 = arcpy.Parameter(name="Output Plumes of NO\u2083-N",
                                   displayName="Output Plumes of NO\u2083-N (raster)",
                                   datatype=["GPRasterLayer"],
                                   parameterType="Required",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )
        outfile0.value = None

        outfile1 = arcpy.Parameter(name="Output Plumes of NH\u2084-N",
                                   displayName="Output Plumes of NH\u2084-N (raster)",
                                   datatype=["GPRasterLayer"],
                                   parameterType="Optional",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )
        outfile1.value = None

        outfile2 = arcpy.Parameter(name="Output Plumes info of NO\u2083-N",
                                   displayName="Output Plumes info of NO\u2083-N (point)",
                                   datatype=["GPFeatureLayer"],
                                   parameterType="Optional",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )
        outfile2.enabled = False
        outfile2.value = None

        outfile3 = arcpy.Parameter(name="Output Plumes info of NH\u2084-N",
                                   displayName="Output Plumes info of NH\u2084-N (point)",
                                   datatype=["GPFeatureLayer"],
                                   parameterType="Optional",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )
        outfile3.enabled = False
        outfile3.value = None

        outfile4 = arcpy.Parameter(name="Output Plumes of PO\u2084-P",
                                   displayName="Output Plumes of PO\u2084-P (raster)",
                                   datatype=["GPRasterLayer"],
                                   parameterType="Optional",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )
        outfile4.enabled = False
        outfile4.value = None

        outfile5 = arcpy.Parameter(name="Output Plumes info of PO\u2084-P",
                                   displayName="Output Plumes info of PO\u2084-P (point)",
                                   datatype=["GPFeatureLayer"],
                                   parameterType="Optional",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )
        outfile5.enabled = False
        outfile5.value = None

        option0 = arcpy.Parameter(name="Solution type",
                                  displayName="Solution type",
                                  datatype="String",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  category="Solution Options",  # Category
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
                                  category="Solution Options",  # Category
                                  )
        option1.value = 48

        option2 = arcpy.Parameter(name="Plume warping method",
                                  displayName="Plume warping method",
                                  datatype="String",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  category="Solution Options",  # Category
                                  )
        choices = ['Spline', 'Polyorder1', 'Polyorder2']
        option2.filter.type = "ValueList"
        option2.filter.list = choices
        option2.value = choices[0]

        option3 = arcpy.Parameter(name="Threshold Concentration",
                                  displayName="Threshold Concentration [mg/l]",
                                  datatype="Double",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  category="Solution Options",  # Category
                                  )
        option3.value = 0.000001

        option4 = arcpy.Parameter(name="Postprocessing",
                                  displayName="Postprocessing",
                                  datatype="String",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  category="Solution Options",  # Category
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
                                  category="Solution Options",  # Category
                                  )
        choices = ['Specified Input Mass Rate', 'Specified Z']
        option5.filter.type = "ValueList"
        option5.filter.list = choices
        option5.value = choices[0]

        option6 = arcpy.Parameter(name="Maximum plumes of continuous calculation for one time",
                                  displayName="Maximum plumes of continuous calculation for one time",
                                  datatype="Long",
                                  parameterType="Optional",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  category="Solution Options",  # Category
                                  )
        option6.value = 400

        param0 = arcpy.Parameter(name="Mass input of nitrogen [mg/d]",
                                 displayName="Mass input of nitrogen [mg/d]",
                                 datatype="Double",
                                 parameterType="Optional",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Source Plane Parameters",  # Category
                                 )
        param0.enabled = True
        param0.value = 20000

        param1 = arcpy.Parameter(name="Mass input of phosphorus [mg/d]",
                                 displayName="Mass input of phosphorus [mg/d]",
                                 datatype="Double",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Source Plane Parameters",  # Category
                                 )
        param1.enabled = False
        param1.value = 1000

        param2 = arcpy.Parameter(name="Source Dimension Y",
                                 displayName="Source Dimension Y [m]",
                                 datatype="Double",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Source Plane Parameters",  # Category
                                 )
        param2.value = 12

        param3 = arcpy.Parameter(name="Source Dimension Z",
                                 displayName="Source Dimension Z [m]",
                                 datatype="Double",
                                 parameterType="Optional",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Source Plane Parameters",  # Category
                                 )
        param3.enabled = False
        param3.value = 1.5

        param4 = arcpy.Parameter(name="Maximum Z",
                                  displayName="Maximum Z [m]",
                                  datatype="GPBoolean",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  category="Source Plane Parameters",  # Category
                                  )
        param4.value = 1

        param5 = arcpy.Parameter(name="Zmax",
                                 displayName="Zmax [m]",
                                 datatype="Double",
                                 parameterType="Optional",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Source Plane Parameters",  # Category
                                 )
        param5.value = 3.0

        param6 = arcpy.Parameter(name="Plume cell size",
                                 displayName="Plume cell size [m]",
                                 datatype="Double",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Source Plane Parameters",  # Category
                                 )
        param6.value = 0.8

        param7 = arcpy.Parameter(name="Volume Conversion Factor",
                                 displayName="Volume Conversion Factor",
                                 datatype="Double",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Source Plane Parameters",  # Category
                                 )
        param7.value = 1000

        param8 = arcpy.Parameter(name="Bulk Density",
                                 displayName="Bulk Density [g/cm\u00B3]",
                                 datatype="Double",
                                 parameterType="Optional",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Source Plane Parameters",  # Category
                                 )
        param8.value = 1.42

        no3param0 = arcpy.Parameter(name="Concentration of NO\u2083-N",
                                    displayName="Concentration of NO\u2083-N [mg/l]",
                                    datatype="Double",
                                    parameterType="Required",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Nitrogen Parameters",  # Category
                                    )
        no3param0.value = 40

        no3param1 = arcpy.Parameter(name="NO\u2083-N Dispersivity \u03B1L",
                                    displayName="NO\u2083-N Dispersivity \u03B1L [m]",
                                    datatype="Double",
                                    parameterType="Required",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Nitrogen Parameters",  # Category
                                    )
        no3param1.value = 2.113

        no3param2 = arcpy.Parameter(name="NO\u2083-N Dispersivity \u03B1TH",
                                    displayName="NO\u2083-N Dispersivity \u03B1TH [m]",
                                    datatype="Double",
                                    parameterType="Required",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Nitrogen Parameters",  # Category
                                    )
        no3param2.value = 0.234

        no3param3 = arcpy.Parameter(name="Denitrification Decay Rate",
                                    displayName="Denitrification Decay Rate [1/d]",
                                    datatype="Double",
                                    parameterType="Required",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Nitrogen Parameters",  # Category
                                    )
        no3param3.value = 0.008

        nh4param0 = arcpy.Parameter(name="Concentration of NH\u2084-N",
                                    displayName="Concentration of NH\u2084-N [mg/l]",
                                    datatype="Double",
                                    parameterType="Optional",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Nitrogen Parameters",  # Category
                                    )
        nh4param0.value = 10

        nh4param1 = arcpy.Parameter(name="NH\u2084-N Dispersivity \u03B1L",
                                    displayName="NH\u2084-N Dispersivity \u03B1L [m]",
                                    datatype="Double",
                                    parameterType="Optional",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Nitrogen Parameters",  # Category
                                    )
        nh4param1.value = 2.113

        nh4param2 = arcpy.Parameter(name="NH\u2084-N Dispersivity \u03B1TH",
                                    displayName="NH\u2084-N Dispersivity \u03B1TH [m]",
                                    datatype="Double",
                                    parameterType="Optional",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Nitrogen Parameters",  # Category
                                    )
        nh4param2.value = 0.234

        nh4param3 = arcpy.Parameter(name="Nitrification Decay Rate",
                                    displayName="Nitrification Decay Rate [1/d]",
                                    datatype="Double",
                                    parameterType="Optional",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Nitrogen Parameters",  # Category
                                    )
        nh4param3.value = 0.0001

        nh4param5 = arcpy.Parameter(name="kd for NH\u2084-N",
                                    displayName="kd for NH\u2084-N [cm\u00B3/g]",
                                    datatype="Double",
                                    parameterType="Optional",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Nitrogen Parameters",  # Category
                                    )
        nh4param5.value = 2

        phosparam0 = arcpy.Parameter(name="Concentration of PO\u2084-P [mg/l]",
                                     displayName="Concentration of PO\u2084-P [mg/l]",
                                     datatype="Double",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input",  # Input|Output
                                     category="Phosphorus Parameters",  # Category
                                     )
        phosparam0.value = 2

        phosparam1 = arcpy.Parameter(name="PO\u2084-P Dispersivity \u03B1L [m]",
                                     displayName="PO\u2084-P Dispersivity \u03B1L [m]",
                                     datatype="Double",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input",  # Input|Output
                                     category="Phosphorus Parameters",  # Category
                                     )
        phosparam1.value = 2.113

        phosparam2 = arcpy.Parameter(name="PO\u2084-P Dispersivity \u03B1TH [m]",
                                     displayName="PO\u2084-P Dispersivity \u03B1TH [m]",
                                     datatype="Double",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input",  # Input|Output
                                     category="Phosphorus Parameters",  # Category
                                     )
        phosparam2.value = 0.234

        phosparam3 = arcpy.Parameter(name="Precipitation rate [mg/kg 1/day]",
                                     displayName="Rprecip [mg/kg 1/day]",
                                     datatype="GPDouble",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input",
                                     category="Phosphorus Parameters")
        phosparam3.value = 0.0002

        phosparam4 = arcpy.Parameter(name="Sorption isotherm",
                                     displayName="Sorption isotherm",
                                     datatype="String",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input",
                                     category="Phosphorus Parameters")
        phoschoices = ["Linear", "Langmuir"]
        phosparam4.filter.list = phoschoices
        phosparam4.value = "Linear"

        phosparam5 = arcpy.Parameter(name="Linear distribution coefficient [L/kg]",
                                     displayName="Linear distribution coefficient [L/kg]",
                                     datatype="GPDouble",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input",
                                     category="Phosphorus Parameters")
        phosparam5.value = 15.1

        phosparam6 = arcpy.Parameter(name="The coefficient in langmuir equation [L/mg]",
                                     displayName="Langmuir coefficient [L/mg]",
                                     datatype="GPDouble",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input",
                                     category="Phosphorus Parameters")
        phosparam6.value = 0.2

        phosparam7 = arcpy.Parameter(name="Maximum sorption capacity [mg P / kg]",
                                     displayName="Maximum sorption capacity [mg P / kg]",
                                     datatype="GPDouble",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input",
                                     category="Phosphorus Parameters")
        phosparam7.value = 237

        return [inputop, whenh4, infile0, infile1, infile2,                              # 0 - 4
                outfile0, outfile1, outfile2, outfile3, outfile4, outfile5,              # 5 - 10
                option0, option1, option2, option3, option4, option5, option6,           # 11 - 17
                param0, param1, param2, param3, param4, param5, param6, param7, param8,  # 18 - 26
                no3param0, no3param1, no3param2, no3param3,                              # 27 - 30
                nh4param0, nh4param1, nh4param2, nh4param3, nh4param5,                   # 31 - 35
                phosparam0, phosparam1, phosparam2, phosparam3, phosparam4, phosparam5,  # 36 - 41
                phosparam6, phosparam7]                                                  # 42 - 43

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
                parameters[5].enabled = True
                parameters[6].enabled = True
                parameters[9].enabled = True
                parameters[27].enabled = True
                parameters[28].enabled = True
                parameters[29].enabled = True
                parameters[30].enabled = True
                parameters[31].enabled = True
                parameters[32].enabled = True
                parameters[33].enabled = True
                parameters[34].enabled = True
                parameters[35].enabled = True
                parameters[36].enabled = True
                parameters[37].enabled = True
                parameters[38].enabled = True
                parameters[39].enabled = True
                parameters[40].enabled = True
                if parameters[40].altered:
                    if parameters[40].value == "Langmuir":
                        parameters[42].enabled = True
                        parameters[43].enabled = True
                        parameters[41].enabled = False
                    elif parameters[40].value == "Linear":
                        parameters[42].enabled = False
                        parameters[43].enabled = False
                        parameters[41].enabled = True
            elif parameters[0].value == "Nitrogen":
                parameters[1].enabled = True
                parameters[5].enabled = True
                parameters[6].enabled = True
                parameters[9].enabled = False
                parameters[19].enabled = False
                parameters[27].enabled = True
                parameters[28].enabled = True
                parameters[29].enabled = True
                parameters[30].enabled = True
                parameters[31].enabled = True
                parameters[32].enabled = True
                parameters[33].enabled = True
                parameters[34].enabled = True
                parameters[35].enabled = True
                parameters[36].enabled = False
                parameters[37].enabled = False
                parameters[38].enabled = False
                parameters[39].enabled = False
                parameters[40].enabled = False
                parameters[41].enabled = False
                parameters[42].enabled = False
                parameters[43].enabled = False
            elif parameters[0].value == "Phosphorus":
                parameters[1].enabled = False
                parameters[5].enabled = False
                parameters[6].enabled = False
                parameters[9].enabled = True
                parameters[18].enabled = False
                parameters[27].enabled = False
                parameters[28].enabled = False
                parameters[29].enabled = False
                parameters[30].enabled = False
                parameters[31].enabled = False
                parameters[32].enabled = False
                parameters[33].enabled = False
                parameters[34].enabled = False
                parameters[35].enabled = False
                parameters[36].enabled = True
                parameters[37].enabled = True
                parameters[38].enabled = True
                parameters[39].enabled = True
                parameters[40].enabled = True
                if parameters[40].altered:
                    if parameters[40].value == "Langmuir":
                        parameters[42].enabled = True
                        parameters[43].enabled = True
                        parameters[41].enabled = False
                    elif parameters[40].value == "Linear":
                        parameters[42].enabled = False
                        parameters[43].enabled = False
                        parameters[41].enabled = True
        if parameters[1].altered:
            if parameters[1].value:
                parameters[6].enabled = True
                parameters[31].enabled = True
                parameters[32].enabled = True
                parameters[33].enabled = True
                parameters[34].enabled = True
                parameters[35].enabled = True
            else:
                parameters[6].enabled = False
                parameters[31].enabled = False
                parameters[32].enabled = False
                parameters[33].enabled = False
                parameters[34].enabled = False
                parameters[35].enabled = False
        if parameters[1].value or parameters[0].value == "Nitrogen and Phosphorus" or parameters[0].value == "Phosphorus":
            parameters[26].enabled = True
        else:
            parameters[26].enabled = False

        if parameters[2].altered:
            source_location = parameters[2].value
            desc = arcpy.Describe(source_location)
            crs1 = desc.spatialReference
            field_list = desc.fields
            if parameters[0].value == "Nitrogen and Phosphorus" or parameters[0].value == "Nitrogen":
                no3_exists = any(field.name.lower() == "no3_conc" for field in field_list)
                if not no3_exists:
                    parameters[27].enabled = True
                else:
                    parameters[27].enabled = False

                if parameters[1].value:
                    nh4_exists = any(field.name.lower() == "nh4_conc" for field in field_list)
                    if not nh4_exists:
                        parameters[31].enabled = True
                    else:
                        parameters[31].enabled = False
            if parameters[0].value == "Nitrogen and Phosphorus" or parameters[0].value == "Phosphorus":
                phos_exists = any(field.name.lower() == "p_conc" for field in field_list)
                if not phos_exists:
                    parameters[36].enabled = True
                else:
                    parameters[36].enabled = False

        if parameters[11].altered:
            if parameters[11].value == "DomenicoRobbinsSS2D":
                parameters[30].enabled = False
            elif parameters[11].value == "DomenicoRobbinsSSDecay2D":
                if parameters[0].value == "Nitrogen and Phosphorus" or parameters[0].value == "Nitrogen":
                    parameters[30].enabled = True

        if parameters[16].altered:
            if parameters[16].value == 'Specified Z':
                parameters[18].enabled = False
                parameters[19].enabled = False
                parameters[21].enabled = True
                parameters[22].enabled = False
                parameters[23].enabled = False

            else:
                if parameters[0].value == "Nitrogen and Phosphorus" or parameters[0].value == "Nitrogen":
                    parameters[18].enabled = True
                if parameters[0].value == "Nitrogen and Phosphorus" or parameters[0].value == "Phosphorus":
                    parameters[19].enabled = True
                parameters[21].enabled = False
                parameters[22].enabled = True
                if parameters[22].altered:
                    if parameters[22].value == 0:
                        parameters[23].enabled = False
                    else:
                        parameters[23].enabled = True

        if parameters[20].altered:
            if not parameters[20].hasBeenValidated:
                parameters[24].value = parameters[20].value / 15

        return

    def updateMessages(self, parameters) -> None:
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        if parameters[2].altered:
            source_location = parameters[2].value
            desc = arcpy.Describe(source_location)
            crs1 = desc.spatialReference
            field_list = desc.fields
            if crs1.linearUnitName != "Meter":
                parameters[2].setErrorMessage("The linear unit of the source location must be meter.")
            if parameters[0].value == "Nitrogen and Phosphorus" or parameters[0].value == "Nitrogen":
                no3_exists = any(field.name.lower() == "no3_conc" for field in field_list)
                if no3_exists:
                    with arcpy.da.SearchCursor(source_location, ["no3_conc"]) as cursor:
                        for row in cursor:
                            no3 = float(row[0])
                            if no3 < 0:
                                parameters[1].setErrorMessage("NO3 initial concentration must be a positive number.")
                if parameters[1].value:
                    nh4_exists = any(field.name.lower() == "nh4_conc" for field in field_list)
                    if nh4_exists:
                        with arcpy.da.SearchCursor(source_location, ["nh4_conc"]) as cursor:
                            for row in cursor:
                                nh4 = float(row[0])
                                if nh4 < 0:
                                    parameters[2].setErrorMessage("NH4 initial concentration must be a positive number.")
            if parameters[0].value == "Nitrogen and Phosphorus" or parameters[0].value == "Phosphorus":
                phos_exists = any(field.name.lower() == "p_conc" for field in field_list)
                if phos_exists:
                    with arcpy.da.SearchCursor(source_location, ["P_conc"]) as cursor:
                        for row in cursor:
                            p = float(row[0])
                            if p < 0:
                                parameters[2].setErrorMessage("P initial concentration must be a positive number.")

        if parameters[3].altered:
            wb = parameters[3].value
            desc = arcpy.Describe(wb)
            crs2 = desc.spatialReference
            if crs2.linearUnitName != "Meter":
                parameters[3].setErrorMessage("The linear unit of the water bodies must be meter.")
        if parameters[4].altered:
            ppath = parameters[4].value
            desc = arcpy.Describe(ppath)
            crs3 = desc.spatialReference
            if crs3.linearUnitName != "Meter":
                parameters[4].setErrorMessage("The linear unit of the particle paths must be meter.")

        if parameters[2].altered and parameters[3].altered and parameters[4].altered:
            if crs1.name != crs2.name or crs1.name != crs3.name:
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
                parameters[4].setErrorMessage("All input files must have the same coordinate system. \n"
                                              + "\n" +
                                              "Source locations projected coordinate system : {} \n".format(crs1.name)
                                              + "Water bodies projected coordinate system : {} \n".format(crs2.name)
                                              + "Particle paths projected coordinate system : {} \n".format(crs3.name))

        if parameters[0].value == "Nitrogen and Phosphorus" or parameters[0].value == "Nitrogen":
            if parameters[5].altered and parameters[5].value is not None:
                if ".gdb" in parameters[5].valueAsText or ".mdb" in parameters[5].valueAsText:
                    parameters[5].setErrorMessage(
                        "Storing the results in a geodatabase will cause an error during calculation")
                else:
                    filename, fileext = os.path.splitext(parameters[5].valueAsText)
                    parameters[7].value = os.path.basename(filename) + "_info"

                filename = os.path.basename(parameters[5].valueAsText)
                if not self.check_name_validity(filename):
                    parameters[5].setErrorMessage("Invalid output file name.")

            if parameters[6].altered and parameters[6].value is not None:
                if ".gdb" in parameters[6].valueAsText or ".mdb" in parameters[6].valueAsText:
                    parameters[6].setErrorMessage(
                        "Storing the results in a geodatabase will cause an error during calculation")
                else:
                    filename, fileext = os.path.splitext(parameters[6].valueAsText)
                    parameters[8].value = os.path.basename(filename) + "_info"

                filename = os.path.basename(parameters[6].valueAsText)
                if not self.check_name_validity(filename):
                    parameters[6].setErrorMessage("Invalid output file name.")

        if parameters[0].value == "Nitrogen and Phosphorus" or parameters[0].value == "Phosphorus":
            if parameters[9].altered and parameters[9].value is not None:
                if ".gdb" in parameters[9].valueAsText or ".mdb" in parameters[9].valueAsText:
                    parameters[9].setErrorMessage(
                        "Storing the results in a geodatabase will cause an error during calculation")
                else:
                    filename, fileext = os.path.splitext(parameters[9].valueAsText)
                    parameters[10].value = os.path.basename(filename) + "_info"

                filename = os.path.basename(parameters[9].valueAsText)
                if not self.check_name_validity(filename):
                    parameters[9].setErrorMessage("Invalid output file name.")

        if parameters[12].value is not None and parameters[12].value < 0:
            parameters[12].setErrorMessage("Plume warping control points must be a positive integer.")
        if parameters[14].value is not None:
            if parameters[14].value < 0:
                parameters[14].setErrorMessage("Threshold concentration must be a positive number.")
            elif parameters[14].value > 0.1:
                parameters.setErrorMessage("Threshold concentration is large than 0.1. Maybe it is too large.")

        if parameters[18].value is not None and parameters[18].value < 0:
            parameters[18].setErrorMessage("Mass input of nitrogen must be a positive number.")
        if parameters[19].value is not None and parameters[19].value < 0:
            parameters[19].setErrorMessage("Mass input of phosphorus must be a positive number.")
        if parameters[20].value is not None and parameters[20].value < 0:
            parameters[20].setErrorMessage("Y must be a positive number.")
        if parameters[21].value is not None and parameters[21].value < 0:
            parameters[21].setErrorMessage("Z must be a positive number.")
        if parameters[23].value is not None and parameters[23].value < 0:
            parameters[23].setErrorMessage("Zmax must be a positive number.")
        if parameters[24].value is not None and parameters[24].value < 0:
            parameters[24].setErrorMessage("Plume cell size must be a positive number.")
        if parameters[25].value is not None and parameters[25].value < 0:
            parameters[25].setErrorMessage("Volume conversion factor must be a positive number.")
        if parameters[26].value is not None and parameters[26].value < 0:
            parameters[26].setErrorMessage("Bulk density must be a positive number.")

        if parameters[27].value is not None and parameters[27].value < 0:
            parameters[27].setErrorMessage("NO3 initial concentration must be a positive number.")
        if parameters[28].value is not None and parameters[28].value < 0:
            parameters[28].setErrorMessage("NO3 dispersivity alphaL must be a positive number.")
        if parameters[29].value is not None and parameters[29].value < 0:
            parameters[29].setErrorMessage("NO3 dispersivity alphaTH must be a positive number.")
        if parameters[30].value is not None and parameters[30].value < 0:
            parameters[30].setErrorMessage("NO3 decay rate must be a positive number.")

        if parameters[31].value is not None and parameters[31].value < 0:
            parameters[31].setErrorMessage("NH4 initial concentration must be a positive number.")
        if parameters[32].value is not None and parameters[32].value < 0:
            parameters[32].setErrorMessage("NH4 dispersivity alphaL must be a positive number.")
        if parameters[33].value is not None and parameters[33].value < 0:
            parameters[33].setErrorMessage("NH4 dispersivity alphaTH must be a positive number.")
        if parameters[34].value is not None and parameters[34].value < 0:
            parameters[34].setErrorMessage("NH4 decay rate must be a positive number.")
        if parameters[35].value is not None and parameters[35].value < 0:
            parameters[35].setErrorMessage("NH4 adsorption coefficient must be a positive number.")
        if parameters[36].value is not None and parameters[36].value < 0:
            parameters[36].setErrorMessage("P initial concentration must be a positive number.")
        if parameters[37].value is not None and parameters[37].value < 0:
            parameters[37].setErrorMessage("P dispersivity alphaL must be a positive number.")
        if parameters[38].value is not None and parameters[38].value < 0:
            parameters[38].setErrorMessage("P dispersivity alphaTH must be a positive number.")
        if parameters[39].value is not None and parameters[39].value < 0:
            parameters[39].setErrorMessage("P precipitation rate must be a positive number.")
        if parameters[42].value is not None and parameters[42].value < 0:
            parameters[42].setErrorMessage("Langmuir coefficient must be a positive number.")
        if parameters[43].value is not None and parameters[43].value < 0:
            parameters[43].setErrorMessage("Maximum sorption capacity must be a positive number.")
        if parameters[41].value is not None and parameters[41].value < 0:
            parameters[41].setErrorMessage("Linear distribution coefficient must be a positive number.")
        return

    def execute(self, parameters, messages) -> None:
        """This is the code that executes when you click the "Run" button."""

        messages.addMessage("Solute transport module.")

        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage(f"{current_time} Transport: START")

        if not self.is_file_path(parameters[2].valueAsText):
            parameters[2].value = arcpy.Describe(parameters[2].valueAsText).catalogPath
        if not self.is_file_path(parameters[3].valueAsText):
            parameters[3].value = arcpy.Describe(parameters[3].valueAsText).catalogPath
        if not self.is_file_path(parameters[4].valueAsText):
            parameters[4].value = arcpy.Describe(parameters[4].valueAsText).catalogPath

        for param in parameters:
            self.describeParameter(messages, param)

        types_of_contaminants = parameters[0].valueAsText
        whethernh4 = parameters[1].value
        sourcelocation = parameters[2].valueAsText
        waterbodies = parameters[3].valueAsText
        particlepath = parameters[4].valueAsText
        no3output = parameters[5].valueAsText
        nh4output = parameters[6].valueAsText
        no3outputinfo = parameters[7].valueAsText
        nh4outputinfo = parameters[8].valueAsText
        poutput = parameters[9].valueAsText
        poutputinfo = parameters[10].valueAsText

        option0 = parameters[11].valueAsText
        option1 = parameters[12].value
        option2 = parameters[13].valueAsText
        option3 = parameters[14].value
        option4 = parameters[15].valueAsText
        option5 = parameters[16].valueAsText
        option6 = parameters[17].value

        param0 = parameters[18].value
        param1 = parameters[19].value
        param2 = parameters[20].value
        param3 = parameters[21].value
        param4 = parameters[22].value
        param5 = parameters[23].value
        param6 = parameters[24].value
        param7 = parameters[25].value
        param8 = parameters[26].value
        no3param0 = parameters[27].value
        no3param1 = parameters[28].value
        no3param2 = parameters[29].value
        no3param3 = parameters[30].value
        nh4param0 = parameters[31].value
        nh4param1 = parameters[32].value
        nh4param2 = parameters[33].value
        nh4param3 = parameters[34].value
        nh4param4 = parameters[35].value
        phoparam0 = parameters[36].value
        phoparam1 = parameters[37].value
        phoparam2 = parameters[38].value
        phoparam3 = parameters[39].value
        phoparam4 = parameters[40].value
        phoparam5 = parameters[41].value
        phoparam6 = parameters[42].value
        phoparam7 = parameters[43].value

        # Okay finally go ahead and do the work.
        try:
            TP = Transport(types_of_contaminants, whethernh4, sourcelocation, waterbodies, particlepath,
                           no3output, nh4output, no3outputinfo, nh4outputinfo,
                           option0, option1, option2, option3, option4, option5, option6,
                           param0, param1, param2, param3, param4, param5, param6, param7, param8,
                           no3param0, no3param1, no3param2, no3param3,
                           nh4param0, nh4param1, nh4param2, nh4param3, nh4param4,
                           poutput, poutputinfo, phoparam0, phoparam1, phoparam2, phoparam3, phoparam4, phoparam5,
                           phoparam6, phoparam7)

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

    @staticmethod
    def check_name_validity(name):
        if not name[0].isalpha():
            return False
        if not re.match(r'^[a-zA-Z0-9_]+$', name):
            return False
        if ' ' in name:
            return False
        if name[0].isdigit():
            return False
        if len(name) > 13:
            return False
        return True
# =============================================================================
if __name__ == "__main__":

    class Messenger(object):
        def addMessage(self, message):
            print(message)

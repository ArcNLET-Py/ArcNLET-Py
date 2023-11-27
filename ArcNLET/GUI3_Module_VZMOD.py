"""
Python code that implements an ArcGIS Tool,
to be included in an ArcGIS Python Toolbox.

@author: Wei Mao <wm23a@fsu.edu>， Michael Core <mcore@fsu.edu>, Ming Ye <mye@fsu.edu>
            The Department of Earth, Ocean, and Atmospheric Science, Florida State University
@date: 2023-11-13
"""

import os
import time
import arcpy
import importlib
import tool3_VZMOD
importlib.reload(tool3_VZMOD)
from tool3_VZMOD import VZMOD


hydraulic_default = {"Clay":            [2.0, 0.015, 14.75,  0.098, 0.459, 1.260],
                     "Clay Loam":       [2.0, 0.016, 8.180,  0.079, 0.442, 1.415],
                     "Loam":            [2.0, 0.011, 12.04,  0.061, 0.399, 1.474],
                     "Loamy Sand":      [2.0, 0.035, 105.12, 0.049, 0.390, 1.747],
                     "Sand":            [2.0, 0.035, 642.98, 0.053, 0.375, 3.180],
                     "Sandy Clay":      [2.0, 0.033, 11.35,  0.117, 0.385, 1.207],
                     "Sandy Clay Loam": [2.0, 0.021, 13.19,  0.063, 0.384, 1.330],
                     "Sandy Loam":      [2.0, 0.027, 38.25,  0.039, 0.387, 1.448],
                     "Silt":            [2.0, 0.007, 43.74,  0.050, 0.489, 1.677],
                     "Silty Clay":      [2.0, 0.016, 9.61,   0.111, 0.481, 1.321],
                     "Silty Clay Loam": [2.0, 0.008, 11.11,  0.090, 0.482, 1.520],
                     "Silty Loam":      [2.0, 0.005, 18.26,  0.065, 0.439, 1.663]}

nitrification_default = {"Clay":            [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809],
                         "Clay Loam":       [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809],
                         "Loam":            [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809],
                         "Loamy Sand":      [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809],
                         "Sand":            [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809],
                         "Sandy Clay":      [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809],
                         "Sandy Clay Loam": [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809],
                         "Sandy Loam":      [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809],
                         "Silt":            [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809],
                         "Silty Clay":      [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809],
                         "Silty Clay Loam": [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809],
                         "Silty Loam":      [2.9, 25.0, 0.347, 2.267, 1.104, 0.0, 0.0, 0.154, 0.665, 0.809]}

denitrification_default = {"Clay":            [0.025, 26.0, 0.347, 3.774, 0.0],
                           "Clay Loam":       [0.025, 26.0, 0.347, 3.774, 0.0],
                           "Loam":            [0.025, 26.0, 0.347, 3.774, 0.0],
                           "Loamy Sand":      [0.025, 26.0, 0.347, 2.865, 0.0],
                           "Sand":            [0.025, 26.0, 0.347, 2.865, 0.0],
                           "Sandy Clay":      [0.025, 26.0, 0.347, 2.865, 0.0],
                           "Sandy Clay Loam": [0.025, 26.0, 0.347, 2.865, 0.0],
                           "Sandy Loam":      [0.025, 26.0, 0.347, 2.865, 0.0],
                           "Silt":            [0.025, 26.0, 0.347, 3.867, 0.0],
                           "Silty Clay":      [0.025, 26.0, 0.347, 3.867, 0.0],
                           "Silty Clay Loam": [0.025, 26.0, 0.347, 3.867, 0.0],
                           "Silty Loam":      [0.025, 26.0, 0.347, 3.867, 0.0]}

adsorption_default = {"Clay":            [1.46, 1.50],
                      "Clay Loam":       [1.46, 1.50],
                      "Loam":            [0.35, 1.50],
                      "Loamy Sand":      [0.35, 1.50],
                      "Sand":            [0.35, 1.50],
                      "Sandy Clay":      [1.46, 1.50],
                      "Sandy Clay Loam": [1.46, 1.50],
                      "Sandy Loam":      [0.35, 1.50],
                      "Silt":            [0.35, 1.50],
                      "Silty Clay":      [1.46, 1.50],
                      "Silty Clay Loam": [1.46, 1.50],
                      "Silty Loam":      [0.35, 1.50]}


class InterfaceVZMOD(object):
    """This class has the methods to define the interface of the tool."""

    def __init__(self) -> None:
        """Define the tool. """
        self.label = "3-VZMOD (Optional)"
        self.description = """VZMOD (Optional)."""
        self.category = "ArcNLET"

    def getParameterInfo(self) -> list:
        """Define parameter definitions.
        """
        Option = arcpy.Parameter(name="Soil types",
                                 displayName="Soil types",
                                 datatype="String",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 )
        choices = ["Clay", "Clay Loam", "Loam", "Loamy Sand", "Sand", "Sandy Clay", "Sandy Clay Loam", "Sandy Loam",
                   "Silt", "Silty Clay", "Silty Clay Loam", "Silty Loam"]
        Option.filter.list = choices
        Option.value = "Clay"

        hydroparam0 = arcpy.Parameter(name="Hydraulic Loading Rate",
                                      displayName="Hydraulic Loading Rate (cm/d)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Hydraulic Params"
                                      )
        hydroparam0.parameterDependencies = [Option.value]
        hydroparam0.value = hydraulic_default[Option.value][0]

        hydroparam1 = arcpy.Parameter(name="\u0251",
                                      displayName="\u0251 (-)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Hydraulic Params"
                                      )
        hydroparam1.parameterDependencies = [Option.value]
        hydroparam1.value = hydraulic_default[Option.value][1]

        hydroparam2 = arcpy.Parameter(name="Ks",
                                      displayName="Ks (cm/d)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Hydraulic Params"
                                      )
        hydroparam2.parameterDependencies = [Option.value]
        hydroparam2.value = hydraulic_default[Option.value][2]

        hydroparam3 = arcpy.Parameter(name="\u03B8r",
                                      displayName="\u03B8r (-)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Hydraulic Params"
                                      )
        hydroparam3.value = 0.098

        hydroparam4 = arcpy.Parameter(name="\u03B8s",
                                      displayName="\u03B8s (-)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Hydraulic Params"
                                      )
        hydroparam4.value = 0.459

        hydroparam5 = arcpy.Parameter(name="n",
                                      displayName="n (-)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Hydraulic Params"
                                      )
        hydroparam5.value = 1.26

        nitriparam0 = arcpy.Parameter(name="Knit",
                                      displayName="Knit (1/d)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam0.value = 2.9

        nitriparam1 = arcpy.Parameter(name="Topt-nit",
                                      displayName="Topt-nit (\u2103)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam1.value = 25.0

        nitriparam2 = arcpy.Parameter(name="\u03B2nit",
                                      displayName="\u03B2nit (-)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam2.value = 0.347

        nitriparam3 = arcpy.Parameter(name="e2",
                                      displayName="e2 (-)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam3.value = 2.267

        nitriparam4 = arcpy.Parameter(name="e3",
                                      displayName="e3 (-)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam4.value = 1.104

        nitriparam5 = arcpy.Parameter(name="fs",
                                      displayName="fs (-)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam5.value = 0.0

        nitriparam6 = arcpy.Parameter(name="fwp",
                                      displayName="fwp (-)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam6.value = 0.0

        nitriparam7 = arcpy.Parameter(name="Swp",
                                      displayName="Swp (-)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam7.value = 0.154

        nitriparam8 = arcpy.Parameter(name="Sl",
                                      displayName="Sl (-)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam8.value = 0.665

        nitriparam9 = arcpy.Parameter(name="Sh",
                                      displayName="Sh (-)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam9.value = 0.809

        denitparam0 = arcpy.Parameter(name="Kdnt",
                                      displayName="Kdnt (1/d)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Denitrification Params"
                                      )
        denitparam0.value = 0.025

        denitparam1 = arcpy.Parameter(name="Topt-dnt",
                                      displayName="Topt-dnt (/u2103)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Denitrification Params"
                                      )
        denitparam1.value = 26.0

        denitparam2 = arcpy.Parameter(name="\u03B2dnt",
                                      displayName="\u03B2dnt (-)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Denitrification Params"
                                      )
        denitparam2.value = 0.347

        denitparam3 = arcpy.Parameter(name="e1",
                                      displayName="e1 (-)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Denitrification Params"
                                      )
        denitparam3.value = 3.774

        denitparam4 = arcpy.Parameter(name="Sdnt",
                                      displayName="Sdnt (-)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Denitrification Params"
                                      )
        denitparam4.value = 0.0

        adsorparam0 = arcpy.Parameter(name="kd",
                                      displayName="kd (cm\u00B3/g)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Adsorption Params"
                                      )
        adsorparam0.value = 1.46

        adsorparam1 = arcpy.Parameter(name="\u03C1",
                                      displayName="\u03C1 (g/cm\u00B3)",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Adsorption Params"
                                      )
        adsorparam1.value = 1.50

        Tempparam0 = arcpy.Parameter(name="Temperature Parameter",
                                     displayName="Temperature param (\u2103)",
                                     datatype="GPDouble",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input",  # Input|Output
                                     category="Temperature and Transport Params"
                                     )
        Tempparam0.value = 25.5

        Tempparam1 = arcpy.Parameter(name="Transport Parameter",
                                     displayName="Transport param (cm\u00B2/d)",
                                     datatype="GPDouble",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input",  # Input|Output
                                     category="Temperature and Transport Params"
                                     )
        Tempparam1.value = 4.32

        Initparam0 = arcpy.Parameter(name="Concentration of NH\u2084",
                                     displayName="Concentration of NH\u2084 (mg/L)",
                                     datatype="GPDouble",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        Initparam0.value = 60.0

        Initparam1 = arcpy.Parameter(name="Concentration of NO\u2083",
                                     displayName="Concentration of NO\u2083 (mg/L)",
                                     datatype="GPDouble",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        Initparam1.value = 1.0

        Initparam2 = arcpy.Parameter(name="Depth to Water Table",
                                     displayName="Depth to water table (cm)",
                                     datatype="GPDouble",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        Initparam2.value = 150

        Initparam3 = arcpy.Parameter(name="Distance",
                                     displayName="Distance (cm)",
                                     datatype="GPDouble",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        Initparam3.value = 0
        Initparam3.enabled = False

        outputfile0 = arcpy.Parameter(name="Output folder",
                                      displayName="Output folder",
                                      datatype="DEFolder",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input"  # Input|Output
                                      )

        inputfile0 = arcpy.Parameter(name="Single or multiple OSTDS",
                                     displayName="Single or multiple OSTDS",
                                     datatype="String",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        choices = ["Single OSTDS", "Multiple OSTDS"]
        inputfile0.filter.list = choices
        inputfile0.value = "Single OSTDS"

        inputfile1 = arcpy.Parameter(name="Heterogeneous Ks and \u03B8s",
                                     displayName="Heterogeneous Ks and \u03B8s",
                                     datatype="GPBoolean",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        inputfile1.value = 0
        inputfile1.parameterDependencies = [inputfile0.name]

        inputfile2 = arcpy.Parameter(name="Calculate depth to water table",
                                     displayName="Calculate depth to water table",
                                     datatype="GPBoolean",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        inputfile2.value = 0
        inputfile2.parameterDependencies = [inputfile0.name]

        inputfile3 = arcpy.Parameter(name="Multiple soil types",
                                     displayName="Multiple soil types",
                                     datatype="GPBoolean",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        inputfile3.value = 0
        inputfile3.parameterDependencies = [inputfile0.name]

        inputfile4 = arcpy.Parameter(name="Septic tank sources (point)",
                                     displayName="Septic tank sources (point)",
                                     datatype="GPFeatureLayer",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        inputfile4.filter.list = ["Point"]
        inputfile4.parameterDependencies = [inputfile0.name]

        inputfile5 = arcpy.Parameter(name="Hydraulic conductivity (raster)",
                                     displayName="Hydraulic conductivity (raster)",
                                     datatype="GPRasterLayer",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )

        inputfile6 = arcpy.Parameter(name="Soil porosity (raster)",
                                     displayName="Soil porosity (raster)",
                                     datatype="GPRasterLayer",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )

        inputfile7 = arcpy.Parameter(name="DEM file (raster)",
                                     displayName="DEM file (raster)",
                                     datatype="GPRasterLayer",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )

        inputfile8 = arcpy.Parameter(name="Smoothed DEM (raster)",
                                     displayName="Smoothed DEM (raster)",
                                     datatype="GPRasterLayer",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )

        inputfile9 = arcpy.Parameter(name="Soil types (raster)",
                                     displayName="Soil types (raster)",
                                     datatype="GPRasterLayer",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )

        return [inputfile0, inputfile1, inputfile2, inputfile3, inputfile4,                            # 0 - 4
                inputfile5, inputfile6, inputfile7, inputfile8, inputfile9,                            # 5 - 9
                Option, hydroparam0, hydroparam1, hydroparam2, hydroparam3, hydroparam4, hydroparam5,  # 10 - 16
                nitriparam0, nitriparam1, nitriparam2, nitriparam3, nitriparam4,                       # 17 - 21
                nitriparam5, nitriparam6, nitriparam7, nitriparam8, nitriparam9,                       # 22 - 26
                denitparam0, denitparam1, denitparam2, denitparam3, denitparam4,                       # 27 - 31
                adsorparam0, adsorparam1, Tempparam0, Tempparam1,                                      # 32 - 35
                Initparam0, Initparam1, Initparam2, Initparam3, outputfile0]                           # 36 - 40

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

    def updateParameters(self, parameters) -> None:
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[10].altered:
            if not parameters[10].hasBeenValidated:
                parameters[11].value = hydraulic_default[parameters[10].valueAsText][0]
                parameters[12].value = hydraulic_default[parameters[10].valueAsText][1]
                parameters[13].value = hydraulic_default[parameters[10].valueAsText][2]
                parameters[14].value = hydraulic_default[parameters[10].valueAsText][3]
                parameters[15].value = hydraulic_default[parameters[10].valueAsText][4]
                parameters[16].value = hydraulic_default[parameters[10].valueAsText][5]
                parameters[17].value = nitrification_default[parameters[10].valueAsText][0]
                parameters[18].value = nitrification_default[parameters[10].valueAsText][1]
                parameters[19].value = nitrification_default[parameters[10].valueAsText][2]
                parameters[20].value = nitrification_default[parameters[10].valueAsText][3]
                parameters[21].value = nitrification_default[parameters[10].valueAsText][4]
                parameters[22].value = nitrification_default[parameters[10].valueAsText][5]
                parameters[23].value = nitrification_default[parameters[10].valueAsText][6]
                parameters[24].value = nitrification_default[parameters[10].valueAsText][7]
                parameters[25].value = nitrification_default[parameters[10].valueAsText][8]
                parameters[26].value = nitrification_default[parameters[10].valueAsText][9]
                parameters[27].value = denitrification_default[parameters[10].valueAsText][0]
                parameters[28].value = denitrification_default[parameters[10].valueAsText][1]
                parameters[29].value = denitrification_default[parameters[10].valueAsText][2]
                parameters[30].value = denitrification_default[parameters[10].valueAsText][3]
                parameters[31].value = denitrification_default[parameters[10].valueAsText][4]
                parameters[32].value = adsorption_default[parameters[10].valueAsText][0]
                parameters[33].value = adsorption_default[parameters[10].valueAsText][1]
        else:
            parameters[11].value = None
            parameters[12].value = None
            parameters[13].value = None
            parameters[14].value = None
            parameters[15].value = None
            parameters[16].value = None
            parameters[17].value = None
            parameters[18].value = None
            parameters[19].value = None
            parameters[20].value = None
            parameters[21].value = None
            parameters[22].value = None
            parameters[23].value = None
            parameters[24].value = None
            parameters[25].value = None
            parameters[26].value = None
            parameters[27].value = None
            parameters[28].value = None
            parameters[29].value = None
            parameters[30].value = None
            parameters[31].value = None
            parameters[32].value = None
            parameters[33].value = None

        if parameters[0].altered:
            if parameters[0].value == "Multiple OSTDS":
                parameters[1].enabled = True
                parameters[2].enabled = True
                parameters[3].enabled = True
                parameters[4].enabled = True
                if parameters[1].altered and parameters[1].value:
                    parameters[5].enabled = True
                    parameters[6].enabled = True
                    parameters[13].enabled = False
                    parameters[15].enabled = False
                else:
                    parameters[5].enabled = False
                    parameters[6].enabled = False
                    parameters[13].enabled = True
                    parameters[15].enabled = True
                if parameters[2].altered and parameters[2].value:
                    parameters[7].enabled = True
                    parameters[8].enabled = True
                    parameters[38].enabled = False
                    parameters[39].enabled = True
                else:
                    parameters[7].enabled = False
                    parameters[8].enabled = False
                    parameters[38].enabled = True
                    parameters[39].enabled = False
                if parameters[3].altered and parameters[3].value:
                    parameters[9].enabled = True
                    parameters[10].enabled = False
                    parameters[12].enabled = False
                    parameters[13].enabled = False
                    parameters[14].enabled = False
                    parameters[15].enabled = False
                    parameters[16].enabled = False
                    parameters[30].enabled = False
                    parameters[32].enabled = False
                else:
                    parameters[9].enabled = False
                    parameters[10].enabled = True
                    parameters[12].enabled = True
                    parameters[13].enabled = True
                    parameters[14].enabled = True
                    parameters[15].enabled = True
                    parameters[16].enabled = True
                    parameters[30].enabled = True
                    parameters[32].enabled = True
            else:
                parameters[1].enabled = False
                parameters[2].enabled = False
                parameters[3].enabled = False
                parameters[4].enabled = False
                parameters[5].enabled = False
                parameters[6].enabled = False
                parameters[7].enabled = False
                parameters[8].enabled = False
                parameters[9].enabled = False
                parameters[10].enabled = True
                parameters[12].enabled = True
                parameters[13].enabled = True
                parameters[14].enabled = True
                parameters[15].enabled = True
                parameters[16].enabled = True
                parameters[30].enabled = True
                parameters[32].enabled = True
                parameters[38].enabled = True
                parameters[39].enabled = False
        return

    def updateMessages(self, parameters) -> None:
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        if parameters[11].value is not None and parameters[11].value < 0:
            parameters[11].setErrorMessage("Hydraulic loading rate must be greater than 0.")
        if parameters[12].value is not None and parameters[12].value < 0:
            parameters[12].setErrorMessage("Alpha must be greater than 0.")
        if parameters[13].value is not None and parameters[13].value < 0:
            parameters[13].setErrorMessage("Ks must be greater than 0.")
        if parameters[14].value is not None:
            if parameters[14].value < 0:
                parameters[14].setErrorMessage("Theta_r must be greater than 0.")
            elif parameters[14].value > 1:
                parameters[14].setErrorMessage("Theta_r must be less than 1.")
        if parameters[15].value is not None:
            if parameters[15].value < 0:
                parameters[15].setErrorMessage("Theta_s must be greater than 0.")
            elif parameters[15].value > 1:
                parameters[15].setErrorMessage("Theta_s must be less than 1.")
        if parameters[16].value is not None and parameters[16].value < 0:
            parameters[16].setErrorMessage("n must be greater than 0.")

        if parameters[17].value is not None and parameters[17].value < 0:
            parameters[17].setErrorMessage("Knit must be greater than 0.")
        if parameters[24].value is not None and parameters[24].value < 0:
            parameters[24].setErrorMessage("Swp must be greater than 0.")
        if parameters[25].value is not None and parameters[25].value < 0:
            parameters[25].setErrorMessage("Sl must be greater than 0.")
        if parameters[26].value is not None and parameters[26].value < 0:
            parameters[26].setErrorMessage("Sh must be greater than 0.")

        if parameters[27].value is not None and parameters[27].value < 0:
            parameters[27].setErrorMessage("Kdnt must be greater than 0.")
        if parameters[31].value is not None and parameters[31].value < 0:
            parameters[31].setErrorMessage("Sdnt must be greater than 0.")

        if parameters[32].value is not None and parameters[32].value < 0:
            parameters[32].setErrorMessage("kd must be greater than 0.")
        if parameters[33].value is not None and parameters[33].value < 0:
            parameters[33].setErrorMessage("rho must be greater than 0.")
        if parameters[35].value is not None and parameters[35].value < 0:
            parameters[35].setErrorMessage("Transport parameter must be greater than 0.")

        if parameters[36].value is not None and parameters[36].value < 0:
            parameters[36].setErrorMessage("NH4 must be greater than 0.")
        if parameters[37].value is not None and parameters[37].value < 0:
            parameters[37].setErrorMessage("NO3 must be greater than 0.")

    def execute(self, parameters, messages) -> None:
        """This is the code that executes when you click the "Run" button."""

        messages.addMessage("VZMOD Module.")

        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage(f"{current_time} VZMOD: START")

        for param in parameters:
            self.describeParameter(messages, param)

        if parameters[0].value == "Multiple OSTDS":
            options = True
        elif parameters[0].value == "Single OSTDS":
            options = False
        hetero_Ks_thetas = parameters[1].value
        calc_DTW = parameters[2].value
        multi_soil_type = parameters[3].value

        septic_tank = parameters[4].valueAsText
        hydraulic_conductivity = parameters[5].valueAsText
        soil_porosity = parameters[6].valueAsText
        DEM = parameters[7].valueAsText
        smoothed_DEM = parameters[8].valueAsText
        soiltypefile = parameters[9].valueAsText

        soiltype = parameters[10].valueAsText
        hlr = parameters[11].value
        alpha = parameters[12].value
        ks = parameters[13].value
        thetar = parameters[14].value
        thetas = parameters[15].value
        n = parameters[16].value

        knit = parameters[17].value
        toptnit = parameters[18].value
        beltanit = parameters[19].value
        e2 = parameters[20].value
        e3 = parameters[21].value
        fs = parameters[22].value
        fwp = parameters[23].value
        Swp = parameters[24].value
        Sl = parameters[25].value
        Sh = parameters[26].value

        kdnt = parameters[27].value
        toptdnt = parameters[28].value
        beltadnt = parameters[29].value
        e1 = parameters[30].value
        Sdnt = parameters[31].value

        kd = parameters[32].value
        rho = parameters[33].value

        Temp = parameters[34].value
        Tran = parameters[35].value

        NH4 = parameters[36].value
        NO3 = parameters[37].value
        DTW = parameters[38].value
        dist = parameters[39].value

        output_folder = parameters[40].valueAsText

        try:
            vzmod = VZMOD(soiltype, hlr, alpha, ks, thetar, thetas, n, knit, toptnit, beltanit, e2, e3, fs, fwp, Swp,
                          Sl, Sh, kdnt, toptdnt, beltadnt, e1, Sdnt, kd, rho, Temp, Tran, NH4, NO3, DTW, dist,
                          options, output_folder, hetero_Ks_thetas, calc_DTW, multi_soil_type,
                          septic_tank, hydraulic_conductivity, soil_porosity, DEM, smoothed_DEM, soiltypefile)
            vzmod.runVZMOD()
            current_time = time.strftime("%H:%M:%S", time.localtime())
            arcpy.AddMessage(f"{current_time} VZMOD: FINISH")
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

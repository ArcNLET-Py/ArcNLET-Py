"""
Python code that implements implements an ArcGIS Tool,
to be included in an ArcGIS Python Toolbox.

@author: Wei Mao <wm23a@fsu.edu>
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
        self.label = "3 VZMOD (Optional)"
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

        hydroparam0 = arcpy.Parameter(name="HLR",
                                      displayName="Hydraulic Loading Rate",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Hydraulic Params"
                                      )
        hydroparam0.parameterDependencies = [Option.value]
        hydroparam0.value = hydraulic_default[Option.value][0]

        hydroparam1 = arcpy.Parameter(name="alpha",
                                      displayName="\u0251",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Hydraulic Params"
                                      )
        hydroparam1.parameterDependencies = [Option.value]
        hydroparam1.value = hydraulic_default[Option.value][1]

        hydroparam2 = arcpy.Parameter(name="Ks",
                                      displayName="Ks",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Hydraulic Params"
                                      )
        hydroparam2.parameterDependencies = [Option.value]
        hydroparam2.value = hydraulic_default[Option.value][2]

        hydroparam3 = arcpy.Parameter(name="thetar",
                                      displayName="\u03B8r",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Hydraulic Params"
                                      )
        hydroparam3.value = 0.098

        hydroparam4 = arcpy.Parameter(name="thetas",
                                      displayName="\u03B8s",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Hydraulic Params"
                                      )
        hydroparam4.value = 0.459

        hydroparam5 = arcpy.Parameter(name="n",
                                      displayName="n",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Hydraulic Params"
                                      )
        hydroparam5.value = 1.26

        nitriparam0 = arcpy.Parameter(name="Knit",
                                      displayName="Knit",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam0.value = 2.9

        nitriparam1 = arcpy.Parameter(name="Topt-nit",
                                      displayName="Topt-nit",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam1.value = 25.0

        nitriparam2 = arcpy.Parameter(name="beltanit",
                                      displayName="\u03B2nit",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam2.value = 0.347

        nitriparam3 = arcpy.Parameter(name="e2",
                                      displayName="e2",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam3.value = 2.267

        nitriparam4 = arcpy.Parameter(name="e3",
                                      displayName="e3",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam4.value = 1.104

        nitriparam5 = arcpy.Parameter(name="fs",
                                      displayName="fs",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam5.value = 0.0

        nitriparam6 = arcpy.Parameter(name="fwp",
                                      displayName="fwp",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam6.value = 0.0

        nitriparam7 = arcpy.Parameter(name="Swp",
                                      displayName="Swp",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam7.value = 0.154

        nitriparam8 = arcpy.Parameter(name="Sl",
                                      displayName="Sl",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam8.value = 0.665

        nitriparam9 = arcpy.Parameter(name="Sh",
                                      displayName="Sh",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam9.value = 0.809

        denitparam0 = arcpy.Parameter(name="Kdnt",
                                      displayName="Kdnt",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Denitrification Params"
                                      )
        denitparam0.value = 0.025

        denitparam1 = arcpy.Parameter(name="Topt-dnt",
                                      displayName="Topt-dnt",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Denitrification Params"
                                      )
        denitparam1.value = 26.0

        denitparam2 = arcpy.Parameter(name="beltadnt",
                                      displayName="\u03B2dnt",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Denitrification Params"
                                      )
        denitparam2.value = 0.347

        denitparam3 = arcpy.Parameter(name="e1",
                                      displayName="e1",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Denitrification Params"
                                      )
        denitparam3.value = 3.774

        denitparam4 = arcpy.Parameter(name="Sdnt",
                                      displayName="Sdnt",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Denitrification Params"
                                      )
        denitparam4.value = 0.0

        adsorparam0 = arcpy.Parameter(name="kd",
                                      displayName="kd",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Adsorption Params"
                                      )
        adsorparam0.value = 1.46

        adsorparam1 = arcpy.Parameter(name="rho",
                                      displayName="\u03C1",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Adsorption Params"
                                      )
        adsorparam1.value = 1.50

        Tempparam0 = arcpy.Parameter(name="Temp",
                                     displayName="Temperature param",
                                     datatype="GPDouble",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input",  # Input|Output
                                     category="Temperature and Transport Params"
                                     )
        Tempparam0.value = 25.5

        Tempparam1 = arcpy.Parameter(name="Transport",
                                     displayName="Transport param",
                                     datatype="GPDouble",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input",  # Input|Output
                                     category="Temperature and Transport Params"
                                     )
        Tempparam1.value = 4.32

        Initparam0 = arcpy.Parameter(name="NH4",
                                     displayName="Concentration of NH\u2084",
                                     datatype="GPDouble",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        Initparam0.value = 60.0

        Initparam1 = arcpy.Parameter(name="NO3",
                                     displayName="Concentration of NO\u2083",
                                     datatype="GPDouble",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        Initparam1.value = 1.0

        Initparam2 = arcpy.Parameter(name="DTW",
                                     displayName="Depth to water table (cm)",
                                     datatype="GPDouble",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        Initparam2.value = 150

        Initparam3 = arcpy.Parameter(name="Distance",
                                     displayName="Distance",
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

        inputfile0 = arcpy.Parameter(name="Multiple sources",
                                     displayName="Multiple sources",
                                     datatype="GPBoolean",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        inputfile0.value = 0

        inputfile1 = arcpy.Parameter(name="Distributed Ks and thetas",
                                     displayName="Distributed Ks and \u03B8s",
                                     datatype="GPBoolean",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        inputfile1.value = 0
        inputfile1.parameterDependencies = [inputfile1.name]

        inputfile2 = arcpy.Parameter(name="Calculate depth to water table",
                                     displayName="Calculate depth to water table",
                                     datatype="GPBoolean",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        inputfile2.value = 0
        inputfile2.parameterDependencies = [inputfile1.name]

        inputfile3 = arcpy.Parameter(name="Multiple soil type",
                                     displayName="Multiple soil type",
                                     datatype="GPBoolean",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        inputfile3.value = 0
        inputfile2.parameterDependencies = [inputfile1.name]

        inputfile4 = arcpy.Parameter(name="Septic tank sources (point)",
                                     displayName="Septic tank sources (point)",
                                     datatype="GPFeatureLayer",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        inputfile4.filter.list = ["Point"]
        inputfile4.parameterDependencies = [inputfile1.name]

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

        inputfile9 = arcpy.Parameter(name="Soil type (raster)",
                                     displayName="Soil type (raster)",
                                     datatype="GPRasterLayer",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )

        return [inputfile0, inputfile1, inputfile2, inputfile3, inputfile4,                            # 31 - 35
                inputfile5, inputfile6, inputfile7, inputfile8, inputfile9,
                Option, hydroparam0, hydroparam1, hydroparam2, hydroparam3, hydroparam4, hydroparam5,  # 0 - 6
                nitriparam0, nitriparam1, nitriparam2, nitriparam3, nitriparam4,                       # 7 - 11
                nitriparam5, nitriparam6, nitriparam7, nitriparam8, nitriparam9,                       # 12 - 16
                denitparam0, denitparam1, denitparam2, denitparam3, denitparam4,                       # 17 - 21
                adsorparam0, adsorparam1, Tempparam0, Tempparam1,                                      # 22 - 25
                Initparam0, Initparam1, Initparam2, Initparam3, outputfile0]

    def isLicensed(self) -> bool:
        """Set whether tool is licensed to execute."""
        return True

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
            if parameters[0].value:
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
                parameters[39].enabled = True
        return

    def updateMessages(self, parameters) -> None:
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        if parameters[1].value is not None and parameters[1].value < 0:
            parameters[1].setErrorMessage("Hydraulic loading rate must be greater than 0.")
        if parameters[2].value is not None and parameters[2].value < 0:
            parameters[2].setErrorMessage("Alpha must be greater than 0.")
        if parameters[3].value is not None and parameters[3].value < 0:
            parameters[3].setErrorMessage("Ks must be greater than 0.")
        if parameters[4].value is not None:
            if parameters[4].value < 0:
                parameters[4].setErrorMessage("Theta_r must be greater than 0.")
            elif parameters[4].value > 1:
                parameters[4].setErrorMessage("Theta_r must be less than 1.")
        if parameters[5].value is not None:
            if parameters[5].value < 0:
                parameters[5].setErrorMessage("Theta_s must be greater than 0.")
            elif parameters[5].value > 1:
                parameters[5].setErrorMessage("Theta_s must be less than 1.")
        if parameters[6].value is not None and parameters[6].value < 0:
            parameters[6].setErrorMessage("n must be greater than 0.")

        if parameters[7].value is not None and parameters[7].value < 0:
            parameters[7].setErrorMessage("Knit must be greater than 0.")
        if parameters[14].value is not None and parameters[14].value < 0:
            parameters[14].setErrorMessage("Swp must be greater than 0.")
        if parameters[15].value is not None and parameters[15].value < 0:
            parameters[15].setErrorMessage("Sl must be greater than 0.")
        if parameters[16].value is not None and parameters[16].value < 0:
            parameters[16].setErrorMessage("Sh must be greater than 0.")

        if parameters[17].value is not None and parameters[17].value < 0:
            parameters[17].setErrorMessage("Kdnt must be greater than 0.")
        if parameters[21].value is not None and parameters[21].value < 0:
            parameters[21].setErrorMessage("Sdnt must be greater than 0.")

        if parameters[22].value is not None and parameters[22].value < 0:
            parameters[22].setErrorMessage("kd must be greater than 0.")
        if parameters[23].value is not None and parameters[23].value < 0:
            parameters[23].setErrorMessage("rho must be greater than 0.")
        if parameters[25].value is not None and parameters[25].value < 0:
            parameters[25].setErrorMessage("Transport parameter must be greater than 0.")

        if parameters[26].value is not None and parameters[26].value < 0:
            parameters[26].setErrorMessage("NH4 must be greater than 0.")
        if parameters[27].value is not None and parameters[27].value < 0:
            parameters[27].setErrorMessage("NO3 must be greater than 0.")

    def execute(self, parameters, messages) -> None:
        """This is the code that executes when you click the "Run" button."""

        messages.addMessage("Load Estimation Module.")

        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage(f"{current_time} Load Estimation: START")

        for param in parameters:
            self.describeParameter(messages, param)

        soiltypes = parameters[0].valueAsText
        hlr = parameters[1].valueAsText
        alpha = parameters[2].valueAsText
        ks = parameters[3].valueAsText
        thetar = parameters[4].valueAsText
        thetas = parameters[5].valueAsText
        n = parameters[6].valueAsText

        knit = parameters[7].valueAsText
        toptnit = parameters[8].valueAsText
        beltanit = parameters[9].valueAsText
        e2 = parameters[10].valueAsText
        e3 = parameters[11].valueAsText
        fs = parameters[12].valueAsText
        fwp = parameters[13].valueAsText
        Swp = parameters[14].valueAsText
        Sl = parameters[15].valueAsText
        Sh = parameters[16].valueAsText

        kdnt = parameters[17].valueAsText
        toptdnt = parameters[18].valueAsText
        beltadnt = parameters[19].valueAsText
        e1 = parameters[20].valueAsText
        Sdnt = parameters[21].valueAsText

        kd = parameters[22].valueAsText
        rho = parameters[23].valueAsText
        Temp = parameters[24].valueAsText
        Tran = parameters[25].valueAsText

        NH4 = parameters[26].valueAsText
        NO3 = parameters[27].valueAsText
        DTW = parameters[28].valueAsText
        dist = parameters[29].valueAsText

        output_folder = parameters[30].valueAsText

        multi_sources = parameters[31].valueAsText
        hetero_Ks_thetas = parameters[32].valueAsText
        calc_DTW = parameters[33].valueAsText
        multi_soil_type = parameters[34].valueAsText

        septic_tank = parameters[35].valueAsText
        hydraulic_conductivity = parameters[36].valueAsText
        soil_porosity = parameters[37].valueAsText
        DEM = parameters[38].valueAsText
        smoothed_DEM = parameters[39].valueAsText
        soil_type = parameters[40].valueAsText

        try:
            vzmod = VZMOD(soiltypes, hlr, alpha, ks, thetar, thetas, n, knit, toptnit, beltanit, e2, e3, fs, fwp, Swp,
                          Sl, Sh, kdnt, toptdnt, beltadnt, e1, Sdnt, kd, rho, Temp, Tran, NH4, NO3, DTW, dist,
                          multi_sources, output_folder, hetero_Ks_thetas, calc_DTW, multi_soil_type,
                          septic_tank, hydraulic_conductivity, soil_porosity, DEM, smoothed_DEM, soil_type)
            vzmod.runVZMOD()
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

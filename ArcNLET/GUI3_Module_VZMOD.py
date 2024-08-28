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
                                      displayName="Hydraulic Loading Rate [cm/d]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Hydraulic Params"
                                      )
        hydroparam0.parameterDependencies = [Option.value]
        hydroparam0.value = hydraulic_default[Option.value][0]

        hydroparam1 = arcpy.Parameter(name="\u0251",
                                      displayName="\u0251 [-]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Hydraulic Params"
                                      )
        hydroparam1.parameterDependencies = [Option.value]
        hydroparam1.value = hydraulic_default[Option.value][1]

        hydroparam2 = arcpy.Parameter(name="Ks",
                                      displayName="Ks [cm/d]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Hydraulic Params"
                                      )
        hydroparam2.parameterDependencies = [Option.value]
        hydroparam2.value = hydraulic_default[Option.value][2]

        hydroparam3 = arcpy.Parameter(name="\u03B8r",
                                      displayName="\u03B8r [-]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Hydraulic Params"
                                      )
        hydroparam3.value = 0.098

        hydroparam4 = arcpy.Parameter(name="\u03B8s",
                                      displayName="\u03B8s [-]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Hydraulic Params"
                                      )
        hydroparam4.value = 0.459

        hydroparam5 = arcpy.Parameter(name="n",
                                      displayName="n [-]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Hydraulic Params"
                                      )
        hydroparam5.value = 1.26

        nitriparam0 = arcpy.Parameter(name="Knit",
                                      displayName="Knit [1/d]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam0.value = 2.9

        nitriparam1 = arcpy.Parameter(name="Topt-nit",
                                      displayName="Topt-nit [\u2103]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam1.value = 25.0

        nitriparam2 = arcpy.Parameter(name="\u03B2nit",
                                      displayName="\u03B2nit [-]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam2.value = 0.347

        nitriparam3 = arcpy.Parameter(name="e2",
                                      displayName="e2 [-]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam3.value = 2.267

        nitriparam4 = arcpy.Parameter(name="e3",
                                      displayName="e3 [-]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam4.value = 1.104

        nitriparam5 = arcpy.Parameter(name="fs",
                                      displayName="fs [-]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam5.value = 0.0

        nitriparam6 = arcpy.Parameter(name="fwp",
                                      displayName="fwp [-]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam6.value = 0.0

        nitriparam7 = arcpy.Parameter(name="Swp",
                                      displayName="Swp [-]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam7.value = 0.154

        nitriparam8 = arcpy.Parameter(name="Sl",
                                      displayName="Sl [-]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam8.value = 0.665

        nitriparam9 = arcpy.Parameter(name="Sh",
                                      displayName="Sh [-]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Nitrification Params"
                                      )
        nitriparam9.value = 0.809

        denitparam0 = arcpy.Parameter(name="Kdnt",
                                      displayName="Kdnt [1/d]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Denitrification Params"
                                      )
        denitparam0.value = 0.025

        denitparam1 = arcpy.Parameter(name="Topt-dnt",
                                      displayName="Topt-dnt [\u2103]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Denitrification Params"
                                      )
        denitparam1.value = 26.0

        denitparam2 = arcpy.Parameter(name="\u03B2dnt",
                                      displayName="\u03B2dnt [-]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Denitrification Params"
                                      )
        denitparam2.value = 0.347

        denitparam3 = arcpy.Parameter(name="e1",
                                      displayName="e1 [-]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Denitrification Params"
                                      )
        denitparam3.value = 3.774

        denitparam4 = arcpy.Parameter(name="Sdnt",
                                      displayName="Sdnt [-]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Denitrification Params"
                                      )
        denitparam4.value = 0.0

        nadsorparam = arcpy.Parameter(name="kd for NH\u2084-N",
                                      displayName="kd for NH\u2084-N [cm\u00B3/g]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="NH\u2084-N Adsorption Params"
                                      )
        nadsorparam.value = 1.46

        nDispparam = arcpy.Parameter(name="Dispersion coefficient",
                                     displayName="Dispersion coefficient [cm\u00B2/d]",
                                     datatype="GPDouble",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input",  # Input|Output
                                     category="Dispersion, Bulk Density and Temperature"
                                     )
        nDispparam.value = 4.32

        bulkdensity = arcpy.Parameter(name="\u03C1",
                                      displayName="\u03C1 [g/cm\u00B3]",
                                      datatype="GPDouble",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Input",  # Input|Output
                                      category="Dispersion, Bulk Density and Temperature"
                                      )
        bulkdensity.value = 1.50

        Tempparam = arcpy.Parameter(name="Temperature",
                                    displayName="Temperature [\u2103]",
                                    datatype="GPDouble",
                                    parameterType="Required",  # Required|Optional|Derived
                                    direction="Input",  # Input|Output
                                    category="Dispersion, Bulk Density and Temperature"
                                    )
        Tempparam.value = 25.5

        phosparam0 = arcpy.Parameter(name="Precipitation rate [mg/kg 1/day]",
                                     displayName="Rprecip [mg/kg 1/day]",
                                     datatype="GPDouble",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input",
                                     category="Phosphorus Params")
        phosparam0.value = 0.0002

        phosparam1 = arcpy.Parameter(name="Sorption isotherm",
                                     displayName="Sorption isotherm",
                                     datatype="String",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input",
                                     category="Phosphorus Params")
        phoschoices = ["Linear", "Langmuir"]
        phosparam1.filter.list = phoschoices
        phosparam1.value = "Linear"

        phosparam2 = arcpy.Parameter(name="The coefficient in langmuir equation [L/mg]",
                                     displayName="Langmuir coefficient [L/mg]",
                                     datatype="GPDouble",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input",
                                     category="Phosphorus Params")
        phosparam2.value = 0.2

        phosparam3 = arcpy.Parameter(name="Maximum sorption capacity [mg P / kg]",
                                     displayName="Maximum sorption capacity [mg P / kg]",
                                     datatype="GPDouble",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input",
                                     category="Phosphorus Params")
        phosparam3.value = 237

        phosparam4 = arcpy.Parameter(name="Linear distribution coefficient [L/kg]",
                                     displayName="Linear distribution coefficient [L/kg]",
                                     datatype="GPDouble",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input",
                                     category="Phosphorus Params")
        phosparam4.value = 15.1

        Initparam0 = arcpy.Parameter(name="Concentration of NH\u2084-N",
                                     displayName="Concentration of NH\u2084-N [mg/L]",
                                     datatype="GPDouble",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        Initparam0.value = 60.0

        Initparam1 = arcpy.Parameter(name="Concentration of NO\u2083-N",
                                     displayName="Concentration of NO\u2083-N [mg/L]",
                                     datatype="GPDouble",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        Initparam1.value = 1.0

        Initparam2 = arcpy.Parameter(name="Concentration of PO\u2084-P [mg/L]",
                                     displayName="Concentration of PO\u2084-P [mg/L]",
                                     datatype="GPDouble",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        Initparam2.value = 10.0

        Initparam3 = arcpy.Parameter(name="Depth to Water Table",
                                     displayName="Depth to water table [cm]",
                                     datatype="GPDouble",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        Initparam3.value = 150

        Initparam4 = arcpy.Parameter(name="Distance",
                                     displayName="Distance [cm]",
                                     datatype="GPDouble",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        Initparam4.value = 0
        Initparam4.enabled = False

        outputfile0 = arcpy.Parameter(name="Output profile results",
                                      displayName="Output profile results (text file)",
                                      datatype="DEFile",
                                      parameterType="Required",  # Required|Optional|Derived
                                      direction="Output"  # Input|Output
                                      )
        outputfile0.value = os.path.join(os.getcwd(), "Results.txt")
        outputfile0.enabled = True

        inputfile0 = arcpy.Parameter(name="Types of contaminants",
                                 displayName="Types of contaminants",
                                 datatype="String",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 )
        choices = ["Nitrogen", "Phosphorus", "Nitrogen and Phosphorus"]
        inputfile0.filter.list = choices
        inputfile0.value = "Nitrogen"

        inputfile1 = arcpy.Parameter(name="Single or multiple OSTDS",
                                     displayName="Single or multiple OSTDS",
                                     datatype="String",
                                     parameterType="Required",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        choices = ["Single OSTDS", "Multiple OSTDS"]
        inputfile1.filter.list = choices
        inputfile1.value = "Single OSTDS"

        inputfile2 = arcpy.Parameter(name="Heterogeneous Ks and \u03B8s",
                                     displayName="Heterogeneous Ks and \u03B8s",
                                     datatype="GPBoolean",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        inputfile2.value = 0
        inputfile2.parameterDependencies = [inputfile1.name]

        inputfile3 = arcpy.Parameter(name="Calculate depth to water table",
                                     displayName="Calculate depth to water table",
                                     datatype="GPBoolean",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        inputfile3.value = 0
        inputfile3.parameterDependencies = [inputfile1.name]

        inputfile4 = arcpy.Parameter(name="Multiple soil types",
                                     displayName="Multiple soil types",
                                     datatype="GPBoolean",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        inputfile4.value = 0
        inputfile4.parameterDependencies = [inputfile1.name]

        inputfile5 = arcpy.Parameter(name="Septic tank sources (point)",
                                     displayName="Septic tank sources (point)",
                                     datatype="GPFeatureLayer",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )
        inputfile5.filter.list = ["Point"]
        inputfile5.parameterDependencies = [inputfile1.name]

        inputfile6 = arcpy.Parameter(name="Hydraulic conductivity (raster)",
                                     displayName="Hydraulic conductivity (raster)",
                                     datatype="GPRasterLayer",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )

        inputfile7 = arcpy.Parameter(name="Soil porosity (raster)",
                                     displayName="Soil porosity (raster)",
                                     datatype="GPRasterLayer",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )

        inputfile8 = arcpy.Parameter(name="DEM file (raster)",
                                     displayName="DEM file (raster)",
                                     datatype="GPRasterLayer",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )

        inputfile9 = arcpy.Parameter(name="Smoothed DEM (raster)",
                                     displayName="Smoothed DEM (raster)",
                                     datatype="GPRasterLayer",
                                     parameterType="Optional",  # Required|Optional|Derived
                                     direction="Input"  # Input|Output
                                     )

        inputfile10 = arcpy.Parameter(name="Soil types (raster)",
                                      displayName="Soil types (raster)",
                                      datatype="GPRasterLayer",
                                      parameterType="Optional",  # Required|Optional|Derived
                                      direction="Input"  # Input|Output
                                      )

        return [inputfile0, inputfile1, inputfile2, inputfile3, inputfile4,                            # 0 - 4
                inputfile5, inputfile6, inputfile7, inputfile8, inputfile9, inputfile10,               # 5 - 10
                Option, hydroparam0, hydroparam1, hydroparam2, hydroparam3, hydroparam4, hydroparam5,  # 11 - 17
                nitriparam0, nitriparam1, nitriparam2, nitriparam3, nitriparam4,                       # 18 - 22
                nitriparam5, nitriparam6, nitriparam7, nitriparam8, nitriparam9,                       # 23 - 27
                denitparam0, denitparam1, denitparam2, denitparam3, denitparam4,                       # 28 - 32
                nadsorparam, nDispparam, bulkdensity, Tempparam,                                       # 33 - 36
                phosparam0, phosparam1, phosparam2, phosparam3, phosparam4,                            # 37 - 41
                Initparam0, Initparam1, Initparam2, Initparam3, Initparam4, outputfile0]               # 42 - 47

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
        if parameters[0].altered:
            if parameters[0].value == "Nitrogen and Phosphorus":
                parameters[18].enabled = True
                parameters[19].enabled = True
                parameters[20].enabled = True
                parameters[21].enabled = True
                parameters[22].enabled = True
                parameters[23].enabled = True
                parameters[24].enabled = True
                parameters[25].enabled = True
                parameters[26].enabled = True
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
                parameters[38].enabled = True
                if parameters[38].altered:
                    if parameters[38].value == "Langmuir":
                        parameters[37].enabled = True
                        parameters[39].enabled = True
                        parameters[40].enabled = True
                        parameters[41].enabled = False
                    elif parameters[38].value == "Linear":
                        parameters[37].enabled = True
                        parameters[39].enabled = False
                        parameters[40].enabled = False
                        parameters[41].enabled = True
                parameters[42].enabled = True
                parameters[43].enabled = True
                parameters[44].enabled = True
                parameters[45].enabled = True
            elif parameters[0].value == "Nitrogen":
                parameters[18].enabled = True
                parameters[19].enabled = True
                parameters[20].enabled = True
                parameters[21].enabled = True
                parameters[22].enabled = True
                parameters[23].enabled = True
                parameters[24].enabled = True
                parameters[25].enabled = True
                parameters[26].enabled = True
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
                parameters[37].enabled = False
                parameters[38].enabled = False
                parameters[39].enabled = False
                parameters[40].enabled = False
                parameters[41].enabled = False
                parameters[42].enabled = True
                parameters[43].enabled = True
                parameters[44].enabled = False
                parameters[45].enabled = True
            elif parameters[0].value == "Phosphorus":
                parameters[18].enabled = False
                parameters[19].enabled = False
                parameters[20].enabled = False
                parameters[21].enabled = False
                parameters[22].enabled = False
                parameters[23].enabled = False
                parameters[24].enabled = False
                parameters[25].enabled = False
                parameters[26].enabled = False
                parameters[27].enabled = False
                parameters[28].enabled = False
                parameters[29].enabled = False
                parameters[30].enabled = False
                parameters[31].enabled = False
                parameters[32].enabled = False
                parameters[33].enabled = False
                parameters[34].enabled = True
                parameters[35].enabled = True
                parameters[36].enabled = False
                parameters[38].enabled = True
                if parameters[38].altered:
                    if parameters[38].value == "Langmuir":
                        parameters[37].enabled = True
                        parameters[39].enabled = True
                        parameters[40].enabled = True
                        parameters[41].enabled = False
                    elif parameters[38].value == "Linear":
                        parameters[37].enabled = True
                        parameters[39].enabled = False
                        parameters[40].enabled = False
                        parameters[41].enabled = True
                parameters[42].enabled = False
                parameters[43].enabled = False
                parameters[44].enabled = True
                parameters[45].enabled = True

        if parameters[11].altered:
            if not parameters[11].hasBeenValidated:
                parameters[12].value = hydraulic_default[parameters[11].valueAsText][0]
                parameters[13].value = hydraulic_default[parameters[11].valueAsText][1]
                parameters[14].value = hydraulic_default[parameters[11].valueAsText][2]
                parameters[15].value = hydraulic_default[parameters[11].valueAsText][3]
                parameters[16].value = hydraulic_default[parameters[11].valueAsText][4]
                parameters[17].value = hydraulic_default[parameters[11].valueAsText][5]
                parameters[18].value = nitrification_default[parameters[11].valueAsText][0]
                parameters[19].value = nitrification_default[parameters[11].valueAsText][1]
                parameters[20].value = nitrification_default[parameters[11].valueAsText][2]
                parameters[21].value = nitrification_default[parameters[11].valueAsText][3]
                parameters[22].value = nitrification_default[parameters[11].valueAsText][4]
                parameters[23].value = nitrification_default[parameters[11].valueAsText][5]
                parameters[24].value = nitrification_default[parameters[11].valueAsText][6]
                parameters[25].value = nitrification_default[parameters[11].valueAsText][7]
                parameters[26].value = nitrification_default[parameters[11].valueAsText][8]
                parameters[27].value = nitrification_default[parameters[11].valueAsText][9]
                parameters[28].value = denitrification_default[parameters[11].valueAsText][0]
                parameters[29].value = denitrification_default[parameters[11].valueAsText][1]
                parameters[30].value = denitrification_default[parameters[11].valueAsText][2]
                parameters[31].value = denitrification_default[parameters[11].valueAsText][3]
                parameters[32].value = denitrification_default[parameters[11].valueAsText][4]
                parameters[33].value = adsorption_default[parameters[11].valueAsText][0]
                parameters[35].value = adsorption_default[parameters[11].valueAsText][1]
        else:
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
            parameters[35].value = None

        if parameters[1].altered:
            if parameters[1].value == "Multiple OSTDS":
                parameters[2].enabled = True
                parameters[3].enabled = True
                parameters[4].enabled = True
                parameters[5].enabled = True
                # if parameters[5].altered and parameters[5].value:
                #     if not parameters[47].hasBeenValidated:
                #         parameters[47].value = os.path.join(os.path.dirname(parameters[5].valueAsText), "Results.txt")
                if parameters[2].altered and parameters[2].value:
                    parameters[6].enabled = True
                    parameters[7].enabled = True
                    parameters[14].enabled = False
                    parameters[16].enabled = False
                else:
                    parameters[6].enabled = False
                    parameters[7].enabled = False
                    parameters[14].enabled = True
                    parameters[16].enabled = True
                if parameters[3].altered and parameters[3].value:
                    parameters[8].enabled = True
                    parameters[9].enabled = True
                    parameters[45].enabled = False
                    parameters[46].enabled = True
                else:
                    parameters[8].enabled = False
                    parameters[9].enabled = False
                    parameters[45].enabled = True
                    parameters[46].enabled = False
                if parameters[4].altered and parameters[4].value:
                    parameters[10].enabled = True
                    parameters[11].enabled = False
                    parameters[13].enabled = False
                    parameters[14].enabled = False
                    parameters[15].enabled = False
                    parameters[16].enabled = False
                    parameters[17].enabled = False
                    parameters[31].enabled = False
                    parameters[33].enabled = False
                else:
                    parameters[10].enabled = False
                    parameters[11].enabled = True
                    parameters[13].enabled = True
                    parameters[14].enabled = True
                    parameters[15].enabled = True
                    parameters[16].enabled = True
                    parameters[17].enabled = True
                    if parameters[2].altered and parameters[2].value:
                        parameters[14].enabled = False
                        parameters[16].enabled = False
                    if parameters[0].value == "Nitrogen" or parameters[0].value == "Nitrogen and Phosphorus":
                        parameters[31].enabled = True
                        parameters[33].enabled = True
            else:
                parameters[2].enabled = False
                parameters[3].enabled = False
                parameters[4].enabled = False
                parameters[5].enabled = False
                parameters[6].enabled = False
                parameters[7].enabled = False
                parameters[8].enabled = False
                parameters[9].enabled = False
                parameters[10].enabled = False
                parameters[11].enabled = True
                parameters[13].enabled = True
                parameters[14].enabled = True
                parameters[15].enabled = True
                parameters[16].enabled = True
                parameters[17].enabled = True
                if parameters[0].value == "Nitrogen" or parameters[0].value == "Nitrogen and Phosphorus":
                    parameters[31].enabled = True
                    parameters[33].enabled = True
                parameters[45].enabled = True
                parameters[46].enabled = False
        return

    def updateMessages(self, parameters) -> None:
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        if parameters[12].value is not None and parameters[12].value < 0:
            parameters[12].setErrorMessage("Hydraulic loading rate must be greater than 0.")
        if parameters[13].value is not None and parameters[13].value < 0:
            parameters[13].setErrorMessage("\u0251 must be greater than 0.")
        if parameters[14].value is not None and parameters[14].value < 0:
            parameters[14].setErrorMessage("Ks must be greater than 0.")
        if parameters[15].value is not None:
            if parameters[15].value < 0:
                parameters[15].setErrorMessage("\u03B8r must be greater than 0.")
            elif parameters[15].value > 1:
                parameters[15].setErrorMessage("\u03B8r must be less than 1.")
        if parameters[16].value is not None:
            if parameters[16].value < 0:
                parameters[16].setErrorMessage("\u03B8s must be greater than 0.")
            elif parameters[16].value > 1:
                parameters[16].setErrorMessage("\u03B8s must be less than 1.")
        if parameters[17].value is not None and parameters[17].value < 0:
            parameters[17].setErrorMessage("n must be greater than 0.")

        if parameters[18].value is not None and parameters[18].value < 0:
            parameters[18].setErrorMessage("Knit must be greater than 0.")
        if parameters[25].value is not None and parameters[25].value < 0:
            parameters[25].setErrorMessage("Swp must be greater than 0.")
        if parameters[26].value is not None and parameters[26].value < 0:
            parameters[27].setErrorMessage("Sl must be greater than 0.")
        if parameters[27].value is not None and parameters[27].value < 0:
            parameters[27].setErrorMessage("Sh must be greater than 0.")

        if parameters[28].value is not None and parameters[28].value < 0:
            parameters[28].setErrorMessage("Kdnt must be greater than 0.")
        if parameters[32].value is not None and parameters[32].value < 0:
            parameters[32].setErrorMessage("Sdnt must be greater than 0.")

        if parameters[33].value is not None and parameters[33].value < 0:
            parameters[33].setErrorMessage("kd must be greater than 0.")
        if parameters[34].value is not None and parameters[34].value < 0:
            parameters[34].setErrorMessage("Dispersion coefficient must be greater than 0.")
        if parameters[35].value is not None and parameters[35].value < 0:
            parameters[35].setErrorMessage("\u03C1 must be greater than 0.")

        if parameters[37].value is not None and parameters[37].value < 0:
            parameters[37].setErrorMessage("Rprecip must be greater than 0.")
        if parameters[39].value is not None and parameters[39].value < 0:
            parameters[39].setErrorMessage("Langmuir coefficient must be greater than 0.")
        if parameters[40].value is not None and parameters[40].value < 0:
            parameters[40].setErrorMessage("Maximum sorption capacity must be greater than 0.")

        if parameters[42].value is not None and parameters[42].value < 0:
            parameters[42].setErrorMessage("NH4-N concentration must be greater than 0.")
        if parameters[43].value is not None and parameters[43].value < 0:
            parameters[43].setErrorMessage("NO3-N concentration must be greater than 0.")
        if parameters[44].value is not None and parameters[44].value < 0:
            parameters[44].setErrorMessage("Phosphate concentration must be greater than 0.")

    def execute(self, parameters, messages) -> None:
        """This is the code that executes when you click the "Run" button."""

        messages.addMessage("VZMOD Module.")

        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage(f"{current_time} VZMOD: START")

        for param in parameters:
            self.describeParameter(messages, param)

        types_of_contaminants = parameters[0].valueAsText
        options = None
        if parameters[1].value == "Multiple OSTDS":
            options = True
        elif parameters[1].value == "Single OSTDS":
            options = False
        hetero_Ks_thetas = parameters[2].value
        calc_DTW = parameters[3].value
        multi_soil_type = parameters[4].value

        septic_tank = parameters[5].valueAsText
        hydraulic_conductivity = parameters[6].valueAsText
        soil_porosity = parameters[7].valueAsText
        DEM = parameters[8].valueAsText
        smoothed_DEM = parameters[9].valueAsText
        soiltypefile = parameters[10].valueAsText

        soiltype = parameters[11].valueAsText
        hlr = parameters[12].value
        alpha = parameters[13].value
        ks = parameters[14].value
        thetar = parameters[15].value
        thetas = parameters[16].value
        n = parameters[17].value

        knit = parameters[18].value
        toptnit = parameters[19].value
        beltanit = parameters[20].value
        e2 = parameters[21].value
        e3 = parameters[22].value
        fs = parameters[23].value
        fwp = parameters[24].value
        Swp = parameters[25].value
        Sl = parameters[26].value
        Sh = parameters[27].value

        kdnt = parameters[28].value
        toptdnt = parameters[29].value
        beltadnt = parameters[30].value
        e1 = parameters[31].value
        Sdnt = parameters[32].value

        kd = parameters[33].value
        dispn = parameters[34].value

        rho = parameters[35].value
        Temp = parameters[36].value

        phoschoice = parameters[38].value
        rprep = parameters[37].value
        kl = parameters[39].value
        pmax = parameters[40].value
        phoskd = parameters[41].value

        NH4 = parameters[42].value
        NO3 = parameters[43].value
        phos = parameters[44].value
        DTW = parameters[45].value
        dist = parameters[46].value

        output_file = parameters[47].valueAsText

        try:
            vzmod = VZMOD(types_of_contaminants, soiltype, hlr, alpha, ks, thetar, thetas, n,
                          knit, toptnit, beltanit, e2, e3, fs, fwp, Swp, Sl, Sh, kdnt, toptdnt, beltadnt, e1, Sdnt,
                          kd, rho, Temp, dispn, NH4, NO3, DTW, dist,
                          phoschoice, rprep, kl, pmax, phoskd, phos,
                          options, output_file, hetero_Ks_thetas, calc_DTW, multi_soil_type,
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

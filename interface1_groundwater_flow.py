"""
Python code that implements an ArcGIS Tool to be included in an ArcGIS Python Toolbox.

This is the interface file between the ArcGIS Pro and the computational code.

https://pro.arcgis.com/en/pro-app/latest/arcpy/geoprocessing_and_python/defining-a-tool-in-a-python-toolbox.htm

@author: Wei Mao <wm23a@fsu.edu>
"""

import os
import arcpy

import importlib
import tool1_groundwater_flow

importlib.reload(tool1_groundwater_flow)

from tool1_groundwater_flow import DarcyFlow


class InterfaceGroundwaterFlow(object):
    """This class has the methods to define the interface of the tool."""

    def __init__(self) -> None:
        """Define the tool.
        """
        self.label = "Groundwater Flow"
        self.description = """Groundwater flow module."""
        self.category = "ArcNLET"

    def getParameterInfo(self):
        """Define parameter definitions.
        """

        infile0 = arcpy.Parameter(name="DEM",
                                  displayName="Input DEM surface elevation map [L] (raster)",  # shown in Geoprocessing pane
                                  datatype=["DERasterDataset"],
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input")  # Input|Output

        infile1 = arcpy.Parameter(name="Hydraulic Conductivity",
                                  displayName="Input Hydraulic conductivity [L/T] (raster)",
                                  datatype=["DERasterDataset"],
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  )

        infile2 = arcpy.Parameter(name="Waterbodies",
                                  displayName="Input Water bodies (polygon)",
                                  datatype=["DEFeatureClass"],
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  )

        infile3 = arcpy.Parameter(name="Porosity",
                                  displayName="Input Soil porosity (raster)",
                                  datatype=["DERasterDataset"],
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  )

        param0 = arcpy.Parameter(name="Smoothing Factor",
                                 displayName="Smoothing Factor",
                                 datatype="GPLong",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 )
        param0.value = 20

        param1 = arcpy.Parameter(name="Smoothing cell",
                                 displayName="Smoothing Cell",
                                 datatype="GPLong",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 )
        param1.value = 7
        param2 = arcpy.Parameter(name="Fill Sinks",
                                 displayName="Fill Sinks",
                                 datatype="GPBoolean",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 )
        param2.value = 0

        param3 = arcpy.Parameter(name="Merge Waterbodies",
                                 displayName="Merge Waterbodies",
                                 datatype="GPBoolean",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 )
        param3.value = 0

        param4 = arcpy.Parameter(name="Smoothing Factor after Merging",
                                 displayName="Smoothing Factor after Merging",
                                 datatype="GPLong",
                                 parameterType="Optional",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 multiValue=True,
                                 )
        param4.value = 2
        param4.parameterDependencies = [param3.name]

        param5 = arcpy.Parameter(name="Z-Factor",
                                 displayName="Z-Factor",
                                 datatype="GPLong",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 )
        param5.value = 1

        outfile0 = arcpy.Parameter(name="Velocity",
                                   displayName="Output Velocity Magnitude [L/T]",
                                   datatype=["DERasterDataset"],
                                   parameterType="Required",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )
        # outfile0.symbology = os.path.join(os.path.dirname(__file__),
        #                                   'Aspect_out_raster.lyrx')

        outfile1 = arcpy.Parameter(name="Velocity Direction",
                                   displayName="Output Velocity Direction [°wrt N]",
                                   datatype=["DERasterDataset"],
                                   parameterType="Required",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )

        outfile2 = arcpy.Parameter(name="Gradient",
                                   displayName="Output Hydraulic Gradient",
                                   datatype=["DERasterDataset"],
                                   parameterType="Optional",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )

        outfile3 = arcpy.Parameter(name="Smoothed DEM",
                                   displayName="Output Smoothed DEM",
                                   datatype=["DERasterDataset"],
                                   parameterType="Optional",  # Required|Optional|Derived
                                   direction="Output",  # Input|Output
                                   )

        return [infile0, infile1, infile2, infile3,
                param0, param1, param2, param3, param4, param5,
                outfile0, outfile1, outfile2, outfile3]

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

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed. This method is called whenever a parameter
        has been changed."""
        if parameters[0].altered:
            dem = parameters[0].value
            if not arcpy.Exists(dem):
                raise arcpy.ParameterError("The specified raster does not exist.")
            desc = arcpy.Describe(dem)
            band_count = desc.bandCount
            crs1 = desc.spatialReference
            xsize = desc.meanCellWidth
            ysize = desc.meanCellHeight
            if band_count != 1:
                raise arcpy.ParameterError("Input DEM must have only one band.")
            if xsize != ysize:
                raise arcpy.ParameterError("Input DEM must be square cells.")

        if parameters[1].altered:
            ks = parameters[1].value
            if not arcpy.Exists(ks):
                raise arcpy.ParameterError("The specified raster does not exist.")
            desc = arcpy.Describe(ks)
            band_count = desc.bandCount
            crs2 = desc.spatialReference
            if band_count != 1:
                raise arcpy.ParameterError("Input Hydraulic conductivity must have only one band.")

        if parameters[2].altered:
            wb = parameters[2].value
            if not arcpy.Exists(wb):
                raise arcpy.ParameterError("The specified shapefile does not exist.")
            desc = arcpy.Describe(wb)
            crs3 = desc.spatialReference
            if desc.shapeType != "Polygon":
                raise arcpy.ParameterError("Input shapefile must be a polygon feature.")

        if parameters[3].altered:
            poro = parameters[3].value
            if not arcpy.Exists(poro):
                raise arcpy.ParameterError("The specified raster does not exist.")
            desc = arcpy.Describe(poro)
            band_count = desc.bandCount
            crs4 = desc.spatialReference
            if band_count != 1:
                raise arcpy.ParameterError("Input porosity must have only one band.")

        if parameters[0].altered and parameters[1].altered and parameters[2].altered and parameters[3].altered:
            if crs1.name != crs2.name or crs1.name != crs3.name or crs1.name != crs4.name:
                raise arcpy.ParameterError("All input files must have the same coordinate system.")

        if parameters[4].altered:
            if parameters[4].value is not None and parameters[4].value < 0:
                raise arcpy.ParameterError("The Smoothing Factor must be greater than 0.")
        if parameters[5].altered:
            if parameters[5].value is not None and parameters[5].value < 0:
                raise arcpy.ParameterError("The Smoothing Cell must be greater than 0.")
        if parameters[9].altered:
            if parameters[9].value is not None and parameters[9].value < 0:
                raise arcpy.ParameterError("The Z-Factor must be greater than 0.")

        if parameters[7].value:
            parameters[8].enabled = True
            if parameters[8].altered:
                values_list = parameters[8].valueAsText.split(";")
                try:
                    values_list = [int(i) for i in values_list]
                    values_greater_than_zero = all(val >= 0 for val in values_list)
                except ValueError:
                    values_greater_than_zero = False
                if not values_greater_than_zero:
                    raise arcpy.ParameterError("The Smoothing Cell must be greater than 0.")
        else:
            parameters[8].enabled = False
        return

    def execute(self, parameters, messages) -> None:
        """This is the code that executes when you click the "Run" button."""

        # Let's dump out what we know here.
        messages.addMessage("Smoothing DEM to obtain an approximation of the groundwater table.")
        for param in parameters:
            self.describeParameter(messages, param)

        # Get the parameters from our parameters list,
        # then call a generic python function.
        #
        # This separates the code doing the work from all
        # the crazy code required to talk to ArcGIS.

        # See http://resources.arcgis.com/en/help/main/10.2/index.html#//018z00000063000000
        dem  = parameters[0].valueAsText
        ks   = parameters[1].valueAsText
        wb   = parameters[2].valueAsText
        poro = parameters[3].valueAsText

        smthf1 = parameters[4].value
        smthc  = parameters[5].value
        fsink  = parameters[6].value
        merge  = parameters[7].value
        smthf2 = parameters[8].valueAsText.split(";")
        smthf2 = [int(i) for i in smthf2]
        zfact  = parameters[9].value

        velo = parameters[10].valueAsText
        veld = parameters[11].valueAsText
        grad = parameters[12].valueAsText
        smth = parameters[13].valueAsText

        # Okay finally go ahead and do the work.
        try:
            GF = DarcyFlow(dem, ks, wb, poro,
                           smthf1, smthc, fsink, merge, smthf2, zfact,
                           velo, veld, grad, smth)
            GF.calculateDarcyFlow()
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
    update_datestamp = InterfaceGroundwaterFlow()
    # Read its default parameters.
    params = update_datestamp.getParameterInfo()

    # Set some test values into the instance
    arcpy.env.workspace = '.\\test_pro'
    params[0].value = os.path.join(arcpy.env.workspace, "lakeshore")
    params[1].value = os.path.join(arcpy.env.workspace, "hydr_cond.img")
    params[2].value = os.path.join(arcpy.env.workspace, "waterbodies.shp")
    params[3].value = os.path.join(arcpy.env.workspace, "porosity.img")
    params[10].value = os.path.join(arcpy.env.workspace, "veldemo")
    params[11].value = os.path.join(arcpy.env.workspace, "veldirdemo")

    # Run it.
    update_datestamp.updateParameters(params)
    update_datestamp.execute(params, Messenger())

# That's all

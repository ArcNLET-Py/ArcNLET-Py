"""
Python code that implements an ArcGIS Tool,
to be included in an ArcGIS Python Toolbox.

@author: Wei Mao <wm23a@fsu.edu>
"""

import os
import arcpy
import time
import importlib
import tool2_particle_tracking

importlib.reload(tool2_particle_tracking)

from tool2_particle_tracking import ParticleTracking


class InterfaceParticleTracking(object):
    """This class has the methods to define the interface of the tool."""

    def __init__(self) -> None:
        """Define the tool. """
        self.label = "Particle Tracking"
        self.description = """Particle Tracking module."""
        self.category = "ArcNLET"

    def getParameterInfo(self) -> list:
        """Define parameter definitions.
        """

        infile0 = arcpy.Parameter(name="Source locations (point)",
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

        infile2 = arcpy.Parameter(name="Velocity",
                                  displayName="Input Velocity Magnitude [L/T] (raster)",
                                  datatype=["DERasterDataset"],
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  )

        infile3 = arcpy.Parameter(name="Velocity Direction",
                                  displayName="Input Velocity Direction [°wrt N] (raster)",
                                  datatype=["DERasterDataset"],
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  )

        infile4 = arcpy.Parameter(name="Porosity",
                                  displayName="Input Soil porosity (raster)",
                                  datatype=["DERasterDataset"],
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  )

        option = arcpy.Parameter(name="ClippingOption",
                                 displayName="Clipping and alignment option",
                                 datatype="GPBoolean",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 )
        option.value = False

        param0 = arcpy.Parameter(name="WBRasterRes",
                                 displayName="WB Raster Resolution [L]",
                                 datatype="GPLong",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 )
        param0.value = 10
        param0.parameterDependencies = [infile3.name]

        param1 = arcpy.Parameter(name="Stepsize",
                                 displayName="Step Size [L]",
                                 datatype="GPLong",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 )
        param1.value = 10
        param1.parameterDependencies = [param0.name]

        param2 = arcpy.Parameter(name="Maxsteps",
                                 displayName="Max Steps",
                                 datatype="GPLong",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 )
        param2.value = 1000

        outfile = arcpy.Parameter(name="Particlepath",
                                  displayName="Output Particle Paths (Polyline)",
                                  datatype=["DEFeatureClass"],
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Output",  # Input|Output
                                  )

        return [infile0, infile1, infile2, infile3, infile4, option,
                param0, param1, param2, outfile]

    def isLicensed(self) -> bool:
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters) -> None:
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        if parameters[0].altered:
            source_location = parameters[0].value
            if not arcpy.Exists(source_location):
                raise arcpy.ParameterError("The specified source location does not exist.")
            desc = arcpy.Describe(source_location)
            crs1 = desc.spatialReference
            if desc.shapeType != "Point":
                raise arcpy.ParameterError("Input source location must be a point feature.")

        if parameters[1].altered:
            wb = parameters[1].value
            if not arcpy.Exists(wb):
                raise arcpy.ParameterError("The specified shapefile does not exist.")
            desc = arcpy.Describe(wb)
            crs2 = desc.spatialReference
            if desc.shapeType != "Polygon":
                raise arcpy.ParameterError("Input waterbodies must be a polygon feature.")

        if parameters[2].altered:
            velo = parameters[2].value
            if not arcpy.Exists(velo):
                raise arcpy.ParameterError("The specified raster does not exist.")
            desc = arcpy.Describe(velo)
            band_count = desc.bandCount
            crs3 = desc.spatialReference
            if band_count != 1:
                raise arcpy.ParameterError("Input velocity must have only one band.")

        if parameters[3].altered:
            veld = parameters[3].value
            if not arcpy.Exists(veld):
                raise arcpy.ParameterError("The specified raster does not exist.")
            desc = arcpy.Describe(veld)
            band_count = desc.bandCount
            xsize = desc.meanCellWidth
            crs4 = desc.spatialReference
            if band_count != 1:
                raise arcpy.ParameterError("Input porosity must have only one band.")
            parameters[6].value = xsize / 2
            # parameters[6].value = xsize / 2

        if parameters[4].altered:
            poro = parameters[4].value
            if not arcpy.Exists(poro):
                raise arcpy.ParameterError("The specified raster does not exist.")
            desc = arcpy.Describe(poro)
            band_count = desc.bandCount
            crs5 = desc.spatialReference
            if band_count != 1:
                raise arcpy.ParameterError("Input porosity must have only one band.")

        if parameters[0].altered and parameters[1].altered and parameters[2].altered and parameters[3].altered and \
                parameters[4].altered:
            if crs1.name != crs2.name or crs1.name != crs3.name or crs1.name != crs4.name or crs1.name != crs5.name:
                raise arcpy.ParameterError("All input files must have the same coordinate system.")

        if parameters[6].altered:
            if parameters[6].value is not None and parameters[6].value < 0:
                raise arcpy.ParameterError("The WB Raster Res. must be greater than 0.")
        if parameters[7].altered:
            if parameters[7].value is not None and parameters[7].value < 0:
                raise arcpy.ParameterError("The Step Size must be greater than 0.")
        if parameters[8].altered:
            if parameters[8].value is not None and parameters[8].value < 0:
                raise arcpy.ParameterError("The Max Steps must be greater than 0.")

        return

    def execute(self, parameters, messages) -> None:
        """This is the code that executes when you click the "Run" button."""

        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage(f"{current_time} Particle Tracking: START")

        for param in parameters:
            self.describeParameter(messages, param)

        source_location = parameters[0].valueAsText
        water_bodies = parameters[1].valueAsText
        velocity = parameters[2].valueAsText
        velocity_dir = parameters[3].valueAsText
        poro = parameters[4].valueAsText

        option = parameters[5].value
        resolution = parameters[6].value
        step_size = parameters[7].value
        max_steps = parameters[8].value

        output_fc = parameters[9].valueAsText

        try:
            PT = ParticleTracking(source_location, water_bodies, velocity, velocity_dir, poro, option,
                                  resolution, step_size, max_steps, output_fc)
            PT.track()
            # messages.addMessage("Success.")
            current_time = time.strftime("%H:%M:%S", time.localtime())
            arcpy.AddMessage(f"{current_time} Particle Tracking: FINISH")
        except Exception as e:
            current_time = time.strftime("%H:%M:%S", time.localtime())
            arcpy.AddError(f"{current_time} Fail. {e}")
        return

    def describeParameter(self, m, p):
        m.addMessage("Parameter: %s \"%s\"" % (p.name, p.displayName))
        m.addMessage("  Value \"%s\"" % p.valueAsText)


# =============================================================================
if __name__ == "__main__":

    class Messenger(object):
        def addMessage(self, message):
            print(message)

    # Get an instance of the tool.
    update_datestamp = InterfaceParticleTracking()
    # Read its default parameters.
    params = update_datestamp.getParameterInfo()

    # Set some test values into the instance
    arcpy.env.workspace = '.\\test_pro'
    params[0] = os.path.join(arcpy.env.workspace, "PotentialSepticTankLocationS.shp")
    params[1] = os.path.join(arcpy.env.workspace, "waterbodies")
    params[2] = os.path.join(arcpy.env.workspace, "11vel")
    params[3] = os.path.join(arcpy.env.workspace, "11veld")
    params[4] = os.path.join(arcpy.env.workspace, "porosity.img")

    params[9] = "C:\\path.shp"
    update_datestamp.updateParameters(params)
    update_datestamp.execute(params, Messenger())

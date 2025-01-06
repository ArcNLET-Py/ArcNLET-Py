"""
Python code that implements an ArcGIS Tool,
to be included in an ArcGIS Python Toolbox.

@author: Wei Mao <wm23a@fsu.edu>， Michael Core <mcore@fsu.edu>, Ming Ye <mye@fsu.edu>
            The Department of Earth, Ocean, and Atmospheric Science, Florida State University
@date: 2023-11-07
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
        self.label = "2-Particle Tracking"
        self.description = """Particle Tracking module."""
        self.category = "ArcNLET"

    def getParameterInfo(self) -> list:
        """Define parameter definitions.
        """

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

        infile2 = arcpy.Parameter(name="Velocity Magnitude",
                                  displayName="Input Velocity Magnitude [m/d] (raster)",
                                  datatype=["GPRasterLayer"],
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  )

        infile3 = arcpy.Parameter(name="Velocity Direction",
                                  displayName="Input Velocity Direction [°wrt N] (raster)",
                                  datatype=["GPRasterLayer"],
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  )

        infile4 = arcpy.Parameter(name="Porosity",
                                  displayName="Input Soil porosity (raster)",
                                  datatype=["GPRasterLayer"],
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input",  # Input|Output
                                  )

        option = arcpy.Parameter(name="Flow Path Truncation",
                                 displayName="Flow Path Truncation",
                                 datatype="GPBoolean",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 )
        option.value = False

        param0 = arcpy.Parameter(name="WB Raster Resolution",
                                 displayName="WB Raster Resolution [m]",
                                 datatype="GPLong",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 )
        param0.value = 10
        param0.parameterDependencies = [infile3.name]

        param1 = arcpy.Parameter(name="Step Size",
                                 displayName="Step Size [m]",
                                 datatype="Double",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 )
        param1.value = 10
        param1.parameterDependencies = [param0.name]

        param2 = arcpy.Parameter(name="Max Steps",
                                 displayName="Max Steps",
                                 datatype="GPLong",
                                 parameterType="Required",  # Required|Optional|Derived
                                 direction="Input",  # Input|Output
                                 category="Parameters",
                                 )
        param2.value = 1000

        outfile = arcpy.Parameter(name="Particle Paths",
                                  displayName="Output Particle Paths (Polyline)",
                                  datatype=["GPFeatureLayer"],
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
        if parameters[3].altered:
            if not parameters[3].hasBeenValidated:
                veld = parameters[3].value
                desc = arcpy.Describe(veld)
                xsize = desc.meanCellWidth
                parameters[6].value = xsize

                parameters[7].value = round(xsize / 2, 4)
        return

    def updateMessages(self, parameters) -> None:
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        if parameters[0].altered:
            source_location = parameters[0].value
            desc = arcpy.Describe(source_location)
            crs1 = desc.spatialReference
            if crs1.linearUnitName != 'Meter':
                parameters[0].setErrorMessage("The source locations must be in meters.")
            pointfile = arcpy.management.GetCount(desc.catalogPath)
            point_count = int(pointfile.getOutput(0))

        if parameters[1].altered:
            wb = parameters[1].value
            desc = arcpy.Describe(wb)
            crs2 = desc.spatialReference
            if crs2.linearUnitName != 'Meter':
                parameters[1].setErrorMessage("The water bodies must be in meters.")

        if parameters[2].altered:
            velo = parameters[2].value
            desc = arcpy.Describe(velo)
            band_count = desc.bandCount
            crs3 = desc.spatialReference
            if band_count != 1:
                parameters[2].setErrorMessage("Input velocity must have only one band.")
            if crs3.linearUnitName != 'Meter':
                parameters[2].setErrorMessage("The velocity magnitude must be in meters.")

        if parameters[3].altered:
            veld = parameters[3].value
            desc = arcpy.Describe(veld)
            band_count = desc.bandCount
            crs4 = desc.spatialReference
            if band_count != 1:
                parameters[3].setErrorMessage("Input porosity must have only one band.")
            if crs4.linearUnitName != 'Meter':
                parameters[3].setErrorMessage("The velocity direction must be in meters.")

        if parameters[4].altered:
            poro = parameters[4].value
            desc = arcpy.Describe(poro)
            band_count = desc.bandCount
            crs5 = desc.spatialReference
            if band_count != 1:
                parameters[4].setErrorMessage("Input porosity must have only one band.")
            if crs5.linearUnitName != 'Meter':
                parameters[4].setErrorMessage("The porosity must be in meters.")

        if parameters[0] and parameters[5].value:
            if point_count > 1000:
                parameters[5].setWarningMessage(
                                                "The 'Flow Path Truncation' function is not recommended because a large "
                                                "number of points can significantly reduce calculation efficiency."
                                                )

        if parameters[0].altered and parameters[1].altered and parameters[2].altered and parameters[3].altered and \
                parameters[4].altered:
            if crs1.name != crs2.name or crs1.name != crs3.name or crs1.name != crs4.name or crs1.name != crs5.name:
                parameters[0].setErrorMessage("All input files must have the same coordinate system. \n"
                                              + "\n" +
                                              "Source locations projected coordinate system : {} \n".format(crs1.name)
                                              + "Water bodies projected coordinate system : {} \n".format(crs2.name)
                                              + "Velocity magnitude projected coordinate system : {} \n".format(crs3.name)
                                              + "Velocity direction projected coordinate system : {} \n".format(crs4.name)
                                              + "Porosity projected coordinate system : {} \n".format(crs5.name))
                parameters[1].setErrorMessage("All input files must have the same coordinate system. \n"
                                              + "\n" +
                                              "Source locations projected coordinate system : {} \n".format(crs1.name)
                                              + "Water bodies projected coordinate system : {} \n".format(crs2.name)
                                              + "Velocity magnitude projected coordinate system : {} \n".format(crs3.name)
                                              + "Velocity direction projected coordinate system : {} \n".format(crs4.name)
                                              + "Porosity projected coordinate system : {} \n".format(crs5.name))
                parameters[2].setErrorMessage("All input files must have the same coordinate system. \n"
                                              + "\n" +
                                              "Source locations projected coordinate system : {} \n".format(crs1.name)
                                              + "Water bodies projected coordinate system : {} \n".format(crs2.name)
                                              + "Velocity magnitude projected coordinate system : {} \n".format(crs3.name)
                                              + "Velocity direction projected coordinate system : {} \n".format(crs4.name)
                                              + "Porosity projected coordinate system : {} \n".format(crs5.name))
                parameters[3].setErrorMessage("All input files must have the same coordinate system. \n"
                                              + "\n" +
                                              "Source locations projected coordinate system : {} \n".format(crs1.name)
                                              + "Water bodies projected coordinate system : {} \n".format(crs2.name)
                                              + "Velocity magnitude projected coordinate system : {} \n".format(crs3.name)
                                              + "Velocity direction projected coordinate system : {} \n".format(crs4.name)
                                              + "Porosity projected coordinate system : {} \n".format(crs5.name))
                parameters[4].setErrorMessage("All input files must have the same coordinate system. \n"
                                              + "\n" +
                                              "Source locations projected coordinate system : {} \n".format(crs1.name)
                                              + "Water bodies projected coordinate system : {} \n".format(crs2.name)
                                              + "Velocity magnitude projected coordinate system : {} \n".format(crs3.name)
                                              + "Velocity direction projected coordinate system : {} \n".format(crs4.name)
                                              + "Porosity projected coordinate system : {} \n".format(crs5.name))

        if parameters[6].value is not None and parameters[6].value < 0:
            parameters[6].setErrorMessage("The WB Raster Res. must be greater than 0.")
        if parameters[7].value is not None and parameters[7].value < 0:
            parameters[7].setErrorMessage("The Step Size must be greater than 0.")
        if parameters[8].value is not None and parameters[8].value < 0:
            parameters[8].setErrorMessage("The Max Steps must be greater than 0.")

        if parameters[2].altered and parameters[2].value is not None:
            if parameters[9].altered and parameters[9].value is not None:
                if self.is_file_path(parameters[9].valueAsText):
                    if ".gdb" in parameters[9].valueAsText or 'mdb' in parameters[9].valueAsText:
                        filename = os.path.basename(parameters[9].valueAsText)
                        if "." in filename:
                            parameters[9].setErrorMessage(
                                "When storing a shapefile in a geodatabase, "
                                "do not add a file extension to the name of the shapefile.")
                else:
                    basefile = arcpy.Describe(parameters[2].valueAsText).CatalogPath
                    if ".gdb" in basefile or 'mdb' in basefile:
                        filename = parameters[9].valueAsText
                        if "." in filename:
                            parameters[9].setErrorMessage(
                                "When storing a shapefile in a geodatabase, "
                                "do not add a file extension to the name of the shapefile."
                                "The default output location is same as the velocity magnitude raster.")

        return

    def execute(self, parameters, messages) -> None:
        """This is the code that executes when you click the "Run" button."""

        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage(f"{current_time} Particle Tracking: START")

        if not self.is_file_path(parameters[0].valueAsText):
            parameters[0].value = arcpy.Describe(parameters[0].valueAsText).catalogPath
        if not self.is_file_path(parameters[1].valueAsText):
            parameters[1].value = arcpy.Describe(parameters[1].valueAsText).catalogPath
        if not self.is_file_path(parameters[2].valueAsText):
            parameters[2].value = arcpy.Describe(parameters[2].valueAsText).catalogPath
        if not self.is_file_path(parameters[3].valueAsText):
            parameters[3].value = arcpy.Describe(parameters[3].valueAsText).catalogPath
        if not self.is_file_path(parameters[4].valueAsText):
            parameters[4].value = arcpy.Describe(parameters[4].valueAsText).catalogPath

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

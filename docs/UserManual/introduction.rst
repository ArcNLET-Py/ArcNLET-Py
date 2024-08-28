.. _introduction:

======================================================================================================
ArcNLET-Py: A Python Version of ArcGIS-Based Nitrogen Load Estimation Toolbox Developed for ArcGIS Pro
======================================================================================================


   User’s Manual

   Manuscript Completed: December 2023

   Prepared by

   Michael Core(mcore@fsu.edu), Wei Mao (wm23a@fsu.edu), and Ming Ye
   (mye@fsu.edu)

   Department of Earth, Ocean, and Atmospheric Science, Florida State
   University, Tallahassee, FL 32306

**Prepared for Florida Department of Environmental Protection
Tallahassee, FL**

Introduction
============

The original ArcNLET (ArcGIS-based Nitrogen Load Estimation Toolbox) was
developed using the Visual Basic programming language for ArcMap. Since
ESRI stopped supporting Visual Basic programming for ArcGIS and ArcGIS
Pro is the current ArcGIS platform, we developed a new version of
ArcNLET for ArcGIS Pro. In addition, the new version was written in
Python, and the Python source codes are open to the public through
GitHub. This new version is referred to as **ArcNLET-Py**. It has all
the features of ArcNLET, with several new features that will be
discussed in the manual later on. Since the graphic user interface of
ArcNLET-Py is entirely different from ArcNLET, we developed this manual
for using ArcNLET-Py. The numerical simulation behind ArcNLET-Py is
similar to ArcNLET, and it should be conceptually straightforward for
ArcNLET users to use ArcNLET-Py.

ArcNLET-Py simulates the fate and transport of nitrogen (including both
ammonium and nitrate) and phosphorus (as phosphate, PO\ :sub:`4`\ :sup:`3-`) in a surficial
groundwater aquifer originating from onsite sewage treatment and disposal
systems (OSTDS), a.k.a., septic tanks. ArcNLET-Py produces estimated
values of ammonium, nitrate, and phosphate load to specified surface
water bodies. The primary functions performed by ArcNLET-Py are to:

-  Aid in preparing data that represents the soil hydraulic properties
   (e.g., hydraulic conductivity and porosity) within the domain
   boundary.

-  Simulate reactive transport of ammonium and nitrate in the vertical
   direction at the distance between an OSTDS drainfield and groundwater
   table.

-  Evaluate the groundwater flow directions and magnitudes at discrete
   points (i.e., OSTDS locations) of a domain of interest.

-  Determine the flow paths along which nitrogen travels from an OSTDS
   to its receiving water body.

-  Estimate the nitrogen plumes originating from OSTDS and ending at
   receiving surface water bodies.

-  Calculate nitrate-nitrogen loss due to denitrification during nitrate
   transport and calculate the final nitrate load to target water
   bodies.

-  Simulate reactive transport of phosphorus in the vertical direction
   from an OSTDS drainfield to the groundwater table and estimate the
   subsequent phosphate load reaching surface water bodies.

The impetus behind developing the original ArcNLET and ArcNLET-Py is to
have a simplified nitrogen and phosphorus transformation and transport
model that is easy to implement, integrated into a geographic information
system (GIS) for ease of data management, and uses input data that are
available in the public domain. Traditional numerical models for
groundwater flow and contaminant transport, such as the Modular
Three-Dimensional Finite-Difference Groundwater Flow Model (MODFLOW),
Modular Three-Dimensional Particle Tracking Model (MODPATH), and Modular
Three-Dimensional Multispecies Transport Model for Simulation (MT3DMS),
can simulate nitrogen and phosphorus fate and transport under complicated
field conditions and produce simulated results that may agree well with
field measurements. Developing these models and generating such
agreement requires extensive data collection of the study area and an
experienced modeler. An approach involving traditional modeling tools
may not be ideal for obtaining quick but realistic estimates of
nitrogen and phosphorus loads to surface water bodies since traditional
modeling processes can be difficult and time-consuming. Additionally,
traditional tools do not integrate well with GIS. As a result, a
simplified model is developed to address the concerns with traditional
modeling software. An outcome of the simplified model is that it
becomes possible to integrate the modeling toolbox effectively within
the GIS framework and to use the advanced spatial analysis tools made
available by the GIS.

The model is implemented as a Python Toolbox for ArcGIS Pro from the
Environmental Systems Research Institute, Inc. (Esri). Integrating this
model with ArcGIS Pro makes it easy to incorporate the spatial nature of
data, such as the locations of individual OSTDS and spatially variable
hydraulic conductivity and porosity. Finally, embedding the model within
ArcGIS facilitates data pre- and post-processing and the visualization
of results.

1. Please keep in mind that ArcNLET-Py uses shapefiles stored in folders
   on your local machine.

2. ArcNLET-Py is compatible neither with the Esri feature class nor with
   any of the Esri geodatabases (i.e., file geodatabase, personal
   geodatabase, or enterprise geodatabase).

The model is controlled via the Geoprocessing Pane and accessed as tools
in the content pane or Catalog View of ArcGIS Pro. A point-and-click
approach facilitates user interaction, as it is more user-friendly than
the input file-oriented interaction used in traditional groundwater
modeling software such as MODFLOW and MT3DMS.

This manual describes the practical usage of the toolbox. The underlying
model of nitrogen fate and transport and the associated algorithmic
implementation are described in detail in the technical manual (Rios et
al., 2011). Readers of this manual should be familiar with ArcGIS Pro
3.2.0 and basic scientific and hydrological terminology.

.. contents:: Table of Contents
   :local:
   :depth: 2

1.1 Organization of the Manual
1.2 Acronyms and Abbreviations

Organization of the Manual
--------------------------

The structure of the manual is as follows: the manual begins with an
abbreviated description of the simplified model used in this toolbox,
followed by a discussion of the assumptions employed in the model with a
detailed description of each module’s data inputs, outputs, and
parameters. After a brief overview of the simplified model, the focus
turns to installation requirements for the toolbox and instructions for
accessing the tools within. After learning to access the tool, there is
a detailed breakdown for finding and preparing data inputs for OSTDS
locations, groundwater modeling, and particle tracking. Once comfortable
with preparing data inputs, the manual explains the theory and practice
of sensitivity analysis and model calibration within the toolbox.
Finally, an example problem (referred to as Lakeshore example) for
preparing the input files and executing each module is provided.

The measurement units used in this manual may vary between metric and
imperial units. However, required units are always explicitly stated.
For clarification, it is best to use the units of meters and the
projection coordinate system of North American Datum (NAD) 1983
Universal Transverse Mercator (UTM) Zone 17 North (N), identified by the
European Petroleum Survey Group (EPSG) via the Well-Known ID (WKID) of
26917. To make this manual more straightforward to read, a specific
typographic convention has been adopted as follows:

-  Model inputs and parameters are in **bold** in the document text and
   are surrounded by [brackets] in the Lakeshore example. Names of
   attributes (i.e., field names) in attribute tables are always shown
   in the Courier New font.

Acronyms and Abbreviations
--------------------------

   In this manual, abbreviated acronyms or terms are spelled out in full
   the first time they appear. Table 1 is a list of acronyms and
   abbreviations used in this manual:

.. raw:: html

   <div style="text-align:center;">
      Table 1: Abbreviations
   </div>
   <br></br>

+-------------+--------------------------------------------------------+
|             |    ArcGIS Pro Nitrogen Loading and Estimation Toolbox  |
|  ArcNLET-Py |    for Python                                          |
+=============+========================================================+
|    CPU      |    Central Processing Unit                             |
+-------------+--------------------------------------------------------+
|    CSV      |    Comma-Separated Values text file                    |
+-------------+--------------------------------------------------------+
|    DEM      |    Digital Elevation Model                             |
+-------------+--------------------------------------------------------+
|    DTW      |    Depth to Water Table                                |
+-------------+--------------------------------------------------------+
|    Esri     |    Environmental Systems Research Institute, Inc.      |
+-------------+--------------------------------------------------------+
|    FDEP     |    Florida Department of Environmental Protection      |
+-------------+--------------------------------------------------------+
|    FID      |    Feature ID                                          |
+-------------+--------------------------------------------------------+
|    GIS      |    Geographic Information System.                      |
+-------------+--------------------------------------------------------+
|    GUI      |    Graphical User Interface                            |
+-------------+--------------------------------------------------------+
|    MODFLOW  |    Modular Three-Dimensional Finite-Difference         |
|             |    Groundwater Flow Model                              |
+-------------+--------------------------------------------------------+
|    MODPATH  |    Modular Three-Dimensional Particle Tracking Model   |
+-------------+--------------------------------------------------------+
|    MT3DMS   |    Modular Three-Dimensional Multispecies Transport    |
|             |    Model for Simulation                                |
+-------------+--------------------------------------------------------+
|    NED      |    National Elevation Dataset                          |
+-------------+--------------------------------------------------------+
|    NH4      |    Ammonium                                            |
+-------------+--------------------------------------------------------+
|    NHD      |    National Hydrography dataset                        |
+-------------+--------------------------------------------------------+
|    NO3      |    Nitrate                                             |
+-------------+--------------------------------------------------------+
|    OSTDS    |    Onsite Sewage Treatment and Disposal System. A      |
|             |    septic tank is an example of an OSTDS.              |
+-------------+--------------------------------------------------------+
|    RAM      |    Randon Access Memory                                |
+-------------+--------------------------------------------------------+
|    PO4      |    Phosphate                                           |
+-------------+--------------------------------------------------------+
|    SA       |    Spatial Analyst (extension for ArcGIS)              |
+-------------+--------------------------------------------------------+
|    STU      |    Soil Treatment Unit                                 |
+-------------+--------------------------------------------------------+
|    STUMOD   |    Spreadsheet-Based Analytical Flow and Transport     |
|             |    Model                                               |
+-------------+--------------------------------------------------------+
|    SSURGO   |    Soil Survey Geographic Database                     |
+-------------+--------------------------------------------------------+
|    TNM      |    USGS The National Map Download v2.0                 |
+-------------+--------------------------------------------------------+
|    VZMOD    |    Vadose Zone Model                                   |
+-------------+--------------------------------------------------------+

See also:
- :ref:`simplifiedmodel` for details on the simplified model.
- :ref:`installationandrequirements` for installation requirements.
- :ref:`preparinginputdata` for information on preparing input data.
- :ref:`lakeshoeexample` for the lakeshore example.
- :ref:`sensitivityandcalibration` for sensitivity analysis and calibration.
- :ref:`references` for the references section.

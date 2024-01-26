.. _simplifiedmodel:

Simplified Model of Nitrogen Transformation and Transport
=========================================================

The simplified model consists of three components (flow model, transport
model, and nitrogen (nitrate (NO\ :sub:`3`) and ammonium (NH\ :sub:`4`))
load estimation) implemented in six separate modules as follows:

-  The proto-module (0-Preprocessing) aids in preparing soil datasets
   derived from the Soil Survey Geographic Database (SSURGO), which
   includes hydraulic conductivity, porosity, texture, and spatial
   distribution.

-  The first module (1-Groundwater Flow) consists of a simplified flow
   model that uses smoothed topography to approximate the water table
   and calculate the magnitude and direction of groundwater seepage
   velocity.

-  The second module (2-Particle Tracking) calculates flow paths based
   on the first module's results of velocity direction and magnitude
   results.

-  The third module, the Vadose Zone MODel (3-VZMOD), is optional and
   estimates the vertical soil flow and nitrification and
   denitrification of ammonium (NH\ :sub:`4`) and nitrate (NO\ :sub:`3`)
   within the Vadose Zone below the OSTDS based on the number of OSTDS
   points, soil conditions, and depth between the drainfield and the
   water table.

-  The fourth module (4-Transport) uses an analytical solution to the
   advection-dispersion equation to simulate the movement of
   NH\ :sub:`4` and/or NO\ :sub:`3` plumes. The Transport Module warps
   plumes along their paths.

-  The fifth module (5-Load Estimation) calculates the NH\ :sub:`4`
   and/or NO\ :sub:`3` mass load-input, -output, and -removal for both
   surface water bodies and plumes that fall short of water features.

The modules are each described in detail below.

Subsections:
- :ref:`preprocessing` for preprocessing steps.
- :ref:`groundwaterflow` for understanding groundwater flow.
- :ref:`particletracking` on particle tracking.
- :ref:`vzmod` for vertical zone modeling.
- :ref:`transport` for transport modeling.
- :ref:`loadestimation` for load estimation techniques.


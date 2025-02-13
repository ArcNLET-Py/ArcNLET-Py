# Brief Introduction to the Training Materials

## Training Presentations

- **Background_ArcNLET-Py**  
  This section provides the background and concepts of ArcNLET-Py with a brief introduction.

- **Practical_Application_TurkeyCreek**  
  A practical example based on the Turkey Creek study area.

- **NO3_Modelling_Lakeshore**  
  This example aligns with the lakeshore scenario from the VB.NET version of the ArcNLET model. It utilizes the groundwater module, particle tracking module, transport module, and load estimation module to estimate the load of NO₃-N from groundwater to surface water. NH₄-N and vadose zone processes are not included in this example.

- **NO3+NH4_Modelling_Lakeshore**  
  An expanded version of the lakeshore example using all six modules of ArcNLET-Py to estimate the loads of NO₃-N and NH₄-N from groundwater to surface water. This includes vadose zone and groundwater processes, but excludes phosphate modeling.

- **NO3+NH4+PO4_Modelling_Lakeshore**  
  Similar to the previous example, but includes phosphate modeling.

- **Guide_Smoothing_Merging_Waterbody**  
  A quick guide for using the "Merge Waterbody" function in ArcNLET-Py.

- **Guide_Module0_SoilProcessing**  
  A quick guide on using "Module 0: Preprocessing" to extract soil data (regional scale hydraulic conductivity, porosity, and soil types) from the online SSURGO database.

- **Tips_SmoothingFactor_PlumeCalculation**  
  Users may encounter memory issues during calculations when using the Groundwater Flow or Transport module. This tip offers a solution to help resolve these problems.

## Training Data

- **lakeshore_example.zip**  
  This folder contains three examples:
  1. **Subfolder 1**: NO₃ modeling for lakeshore
  2. **Subfolder 2**: NO₃+NH₄ modeling for lakeshore
  3. **Subfolder 3**: NO₃+NH₄+PO₄ modeling for lakeshore

  Each example contains multiple subfolders, numbered to match the steps in the respective example. For instance, **Folder 2 in Example 1**, which represents the particle tracking module, corresponds to the second step in the process. It's crucial to open the folders in sequence, as the results from earlier modules are required for later steps. Within each subfolder, you will find additional subfolders for inputs and outputs, containing the files used and generated for each step. Additionally, a screenshot of the module setup, showing all the settings and parameters used to run the module, is included. Red boxes identify modified parameters, while those not marked are the default values.

- **turkeycreek_example.zip**  
  This folder contains the example for the Turkey Creek study area.

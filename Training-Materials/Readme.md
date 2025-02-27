# Brief Introduction to the Training Materials

## Training Presentations

- **Background_ArcNLET-Py**  
  This section provides the background and concepts of ArcNLET-Py with a brief introduction.  

- **Practical_Application_TurkeyCreek**  
  A practical example based on the Turkey Creek study area.  
  **Video:** [Watch the Practical_Application_TurkeyCreek video](https://www.youtube.com/watch?v=NLeYeUUXcj0&t=1254s&ab_channel=MingYe)

- **NO3_Modelling_Lakeshore**  
  This example aligns with the lakeshore scenario from the VB.NET version of the ArcNLET model. It utilizes the groundwater module, particle tracking module, transport module, and load estimation module to estimate the load of NO₃-N from groundwater to surface water. NH₄-N and vadose zone processes are not included in this example.  
  **Video:** [Watch the NO3_Modelling_Lakeshore video](https://www.youtube.com/watch?v=eDgjHmFEEN8&t=7s&ab_channel=MingYe)

- **NO3+NH4_Modelling_Lakeshore**  
  An expanded version of the lakeshore example using all six modules of ArcNLET-Py to estimate the loads of NO₃-N and NH₄-N from groundwater to surface water. This includes vadose zone and groundwater processes, but excludes phosphate modeling.  
  **Video:** [Watch the NO3+NH4_Modelling_Lakeshore video](https://www.youtube.com/watch?v=GZNDaH6TJ3U&ab_channel=MingYe)

- **NO3+NH4+PO4_Modelling_Lakeshore**  
  Similar to the previous example, but includes phosphate modeling.  
  **Video:** [Watch the NO3+NH4+PO4_Modelling_Lakeshore video](https://www.youtube.com/watch?v=nz28jB8KQQ0&ab_channel=MingYe)

- **Guide_Smoothing_Merging_Waterbody**  
  A quick guide for using the "Merge Waterbody" function in ArcNLET-Py.  
  **Video:** [Watch the Guide_Smoothing_Merging_Waterbody video](https://www.youtube.com/watch?v=h8Da7uWfCT0&t=1s&ab_channel=MingYe)

- **Guide_Module0_SoilProcessing**  
  A quick guide on using "Module 0: Preprocessing" to extract soil data (regional scale hydraulic conductivity, porosity, and soil types) from the online SSURGO database.  
  **Video:** [Watch the Guide_Module0_SoilProcessing video](https://www.youtube.com/watch?v=TfUKjmSuaPo&ab_channel=MingYe)

- **Tips_SmoothingFactor_PlumeCalculation**  
  Users may encounter memory issues during calculations when using the Groundwater Flow or Transport module. This tip offers a solution to help resolve these problems.  
  **Video:** [Watch the Tips_SmoothingFactor_PlumeCalculation video](https://www.youtube.com/watch?v=Qxkt40PH5_M&ab_channel=MingYe)

- **Guide_Postprocessing_in_Transport_Module**  
  This presentation explains the three postprocessing options in Tranposrt module.  
  **Video:** [Watch the Tips_SmoothingFactor_PlumeCalculation video](https://www.youtube.com/watch?v=6853VG00lME&t=7s&ab_channel=MingYe)

## Training Data

- **lakeshore_example.zip**  
  This folder contains three examples:  
  1. **Example 1**: NO₃ modeling for lakeshore  
  2. **Example 2**: NO₃+NH₄ modeling for lakeshore  
  3. **Example 3**: NO₃+NH₄+PO₄ modeling for lakeshore  
- **turkeycreek_example.zip**  

  Each example contains multiple subfolders, numbered to match the steps in the respective example. For instance, **Folder 2 in Example 1**, which represents the particle tracking module, corresponds to the second step in the process. It's crucial to open the folders in sequence, as the results from earlier modules are required for later steps. Within each subfolder, you will find additional subfolders for inputs and

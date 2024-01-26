.. _installationandrequirements:

Installation and Requirements
=============================

.. contents:: Table of Contents
   :local:
   :depth: 2

3.1 System Requirements
3.2 Install ArcGIS Pro
3.3 ArcGIS Pro Project File
3.4 ArcNLET-Py from GitHub
3.5 ArcNLET-Py Installation
3.6 Run ArcNLET-Py in ArcGIS Pro

System Requirements
-------------------

The following requirements must be met to use the ArcNLET-Py for ArcGIS
Pro:

-  A Microsoft Windows 10 or 11 Home, Pro, or Enterprise, or Windows
   Server 2016, 2019, or 2022 Standard Datacenter (64-bit) that meets
   the minimum requirements for ArcGIS Pro 3.2.0

-  Active ArcGIS Pro License

-  SA (Spatial Analyst) extension for ArcGIS Pro

-  Microsoft .NET Desktop Runtime 6.0.5 or a later patch release (6.0.6)
   is required using a Windows x64 installer. The presence of Microsoft
   .NET Desktop Runtime 7 or later is inconsequential.

These are the exact requirements of running ArcGIS Pro. In other words,
ArcNLET-Py can be installed on a computer running ArcGIS Pro without
difficulty.

It is recommended to have a computer with:

-  A central processing unit (CPU) with 4 cores and simultaneous
   multithreading

-  32 GB of free solid-state storage space

-  32 GB of memory/random access memory (RAM)

   a. ArcNLET functions with the minimum memory requirement for ArcGIS
      Pro, which is 8 GB of RAM.

The ArcNLET-Py needs a number of Python scripts and other files to
function. These files and folders are stored in your ArcGIS Pro Project
Folder or other local machine location as determined by you. Using a
network drive or network location such as OneDrive, Dropbox, or Google
Drive with ArcGIS Pro is not recommended because of schema locks, file
deletion, and file update errors that ArcGIS Pro can occur on your local
machine but not on a network location. Storing your project in these
network locations mentioned above can cause unwarranted and intermittent
errors when running the ArcNLET-Py modules.

Install ArcGIS Pro
------------------

To begin, you must have an ArcGIS Pro license and complete the ArcGIS
Pro software suite installation on your local or network computer. If
you do not have ArcGIS Pro, please follow Esri’s instructions at the
following link:
https://pro.arcgis.com/en/pro-app/latest/get-started/install-and-sign-in-to-arcgis-pro.htm

ArcGIS Pro Project File
-----------------------

For running ArcNLET-Py, you need a new ArcGIS Pro Project File in a
folder directory on your local computer. If you are unfamiliar with
creating an ArcGIS Pro Project File, please see the Esri tutorial:
https://pro.arcgis.com/en/pro-app/latest/get-started/create-a-project.htm.

1. To create a new Project File, start ArcGIS Pro.
2. Click [Map] (Figure 3‑1).

.. figure:: ./media/installationandrequirementsMedia/media/image1.png
   :align: center
   :alt: A group of icons with text Description automatically generated
   :width: 6.5in
   :height: 1.68958in

   Figure 3‑1: ArcGIS Pro – New Project selection.

3. In the [Create a New Project] (Figure 3‑2) dialog box, name your
   Project File, such as [ArcNLET_YYYY_MM_DD], and set the [Location] to
   a new folder on your local or network computer for which you have
   read and write access.
4. Ensure the box is NOT checked for [Create a new folder for this
   project], then click [OK].

.. figure:: ./media/installationandrequirementsMedia/media/image2.png
   :align: center
   :alt: A screenshot of a computer Description automatically generated
   :width: 6.17602in
   :height: 2.08246in
   
   Figure 3‑2: The ArcGIS Pro Create a New Project dialog box.

5. Go to your newly created file folder directory (Figure 3‑3) to see
   the ArcGIS Pro Project File.

.. figure:: ./media/installationandrequirementsMedia/media/image3.png
   :align: center
   :alt: A screenshot of a computer Description automatically generated
   :width: 6.11078in
   :height: 2.61667in
   
   Figure 3‑3: ArcGIS Pro in the Windows File Explorer.

ArcNLET-Py from GitHub
----------------------

GitHub is a web-based platform allowing users to collaborate on projects
involving code or text-based files. It is built on Git, a version
control system that keeps track of changes and versions, making it
easier to work with multiple people simultaneously. GitHub also supports
Markdown, a lightweight markup language that enables users to create
rich text documents, such as documentation, manuals, or websites.
Moreover, GitHub offers practical tools for project management, such as
issue tracking, project boards, and action automation. GitHub is widely
used for software development and open-source projects, but it can also
benefit non-developers who wish to contribute or access the latest
versions of the projects (GitHub, Inc. 2023). Examples of successful
GitHub stories are QGIS, an open-source GIS, and FloPy, a Python library
for working with MODFLOW-based models. GitHub helps both developers and
users of these projects by providing a platform for collaboration,
contribution, and version control.

1. Open a web browser such as Chrome, Firefox, or Edge, and go to
   https://github.com/ArcNLET-Py/ArcNLET-Py.
2. Click the green [< > Code Button] shown in Figure 3‑4.

.. rst-class:: center 

|image1|

.. raw:: html

   <div  style="text-align:center;">
   3‑4: The GitHub < > Code button.Figure
   </div>
   <br> <!-- Add a line break here --></br>

3. Click [Download ZIP] in the local submenu, as seen below in Figure
   3‑5.

.. figure:: ./media/installationandrequirementsMedia/media/image5.png
   :align: center
   :alt: A screenshot of a computer Description automatically generated
   :width: 4.31667in
   :height: 3.98327in

   Figure 3‑5: The GitHub Download ZIP.

4. Download the zip file to your [Downloads] folder. When downloading
   the file, you should receive a notification (Figure 3‑6). If the
   download does not begin, then please check your pop-up blocker.

.. figure:: ./media/installationandrequirementsMedia/media/image6.png
   :align: center
   :alt: A screenshot of a computer Description automatically generated
   :width: 4.03172in
   :height: 2.14185in

   Figure 3‑6: The download notification for ArcNLET-Py-main.zip.

ArcNLET-Py Installation
-----------------------

1. Locate the zip file, [ArcNLET-Py-main.zip], in your [Download] folder
   and move (Copy and Paste) the file to the location on your computer
   where your current ArcGIS Pro Project File (Figure 3‑7) was saved
   in the Create an ArcGIS Pro Project File in the Section 3.3.

.. figure:: ./media/installationandrequirementsMedia/media/image7.png
   :align: center
   :alt: A screenshot of a computer Description automatically generated
   :width: 6.17646in
   :height: 3.17083in

   Figure 3‑7: ArcNLET-Py-main.zip in the Windows File Explorer.

2. Right-click the [ArcNLET-Py-main.zip] zip file and select [Extract
   All...] as seen in Figure 3‑8.

.. figure:: ./media/installationandrequirementsMedia/media/image8.png
   :align: center
   :alt: A screenshot of a computer Description automatically generated
   :width: 3.52531in
   :height: 6.26721in

   Figure 3‑8: The Extract All option in the right-click submenu.

3. Click [Extract] in the [Extract Compressed (Zipped) Folders] menu, as
   seen below in Figure 3‑9. This process extracts all the contents in
   the [ArcNLET-Py-main.zip] file to a folder called [ArcNLET-Py-main]
   in your current ArcGIS Pro Project folder.

.. figure:: ./media/installationandrequirementsMedia/media/image9.png
   :align: center
   :alt: A screenshot of a computer Description automatically generated
   :width: 5.98385in
   :height: 4.99615in

   Figure 3‑9: The Extract Compressed (Zipped) Folders window for ArcNLET-Py-main.zip.

Run ArcNLET-Py in ArcGIS Pro
----------------------------

1. Open your ArcGIS Pro Project File by double-clicking the .aprx file
   in the folder directory. For this manual, the Project File is called
   [ArcNLET_2023_09_28.aprx] (Figure 3‑3).
2. Once your ArcGIS Pro Project File is open, navigate to
   the [Catalog Pane] or [Catalog View], click the expand arrow for
   [Folders], and you may notice there are two [ArcNLET-Py-main]
   folders (…\\\\ArcNLET-Py-main\\ArcNLET-Py-main). The folder
   structure is due to how GitHub extracts the repository (Figure
   3‑10).

.. figure:: ./media/installationandrequirementsMedia/media/image10.png
   :align: center
   :alt: A screenshot of a computer Description automatically generated
   :width: 6.13256in
   :height: 3.15101in

   Figure 3‑10: The extracted ArcNLET-Py-main folder in the Windows File Explorer.

3. In ArcGIS Pro, in the second [ArcNLET-Py-main] folder, look for the
   [ArcNLET] folder that contains the [ArcNLET.pyt] ArcGIS Pro Python
   Toolbox. By clicking the expand arrow next to the toolbox, you can
   access the ArcNLET Toolset, which includes the following modules:
   0-Preprocessing, 1-Groundwater Flow, 2-Particle Tracking, 3-VZMOD,
   4-Transport, and 5-Load Estimation as shown in Figure 3‑11 and
   Figure 3‑12.

.. figure:: ./media/installationandrequirementsMedia/media/image11.png
   :align: center
   :alt: A screenshot of a computer Description automatically generated
   :width: 7.20833in
   :height: 2.29444in

   Figure 3‑11: The ArcNLET-Py Python Toolset in the Catalog View in ArcGIS Pro.

.. figure:: ./media/installationandrequirementsMedia/media/image12.png
   :align: center
   :alt: A screenshot of a computer Description automatically generated
   :width: 4.92777in
   :height: 6.51133in

   Figure 3‑12: The ArcNLET-Py Python Toolset in the Catalog Pane in ArcGIS Pro.

4. Take a moment to click each toolset or module to read the metadata.
   The [Metadata Pane] includes parameter information for the data sets
   needed for the Preprocessing Module (Figure 3‑13), Groundwater Flow
   Module (Figure 3‑14), Particle Tracking Module (Figure 3‑15), VZMOD
   Module (Figure 3‑16), transportation module (Figure 3‑17), and the
   Load Estimation Module (Figure 3‑18) in ArcNLET-Py.

.. figure:: ./media/installationandrequirementsMedia/media/image13.png
   :align: center
   :alt: A screenshot of a computer Description automatically generated
   :width: 7.20833in
   :height: 5.84444in

   Figure 3‑13: The ArcNLET-Py Preprocessing Module Metadata Pane in ArcGIS Pro.

.. figure:: ./media/installationandrequirementsMedia/media/image14.png
   :align: center
   :alt: A screenshot of a computer Description automatically generated
   :width: 7.20833in
   :height: 6.1125in

   Figure 3‑14: The ArcNLET-Py Groundwater Flow Module Metadata Pane in ArcGIS Pro.

.. figure:: ./media/installationandrequirementsMedia/media/image15.png
   :align: center
   :alt: A screenshot of a computer Description automatically generated
   :width: 7.20833in
   :height: 6.10069in

   Figure 3‑15: The ArcNLET-Py Particle Tracking Module Metadata Pane in ArcGIS Pro.

.. figure:: ./media/installationandrequirementsMedia/media/image16.png
   :align: center
   :alt: A screenshot of a computer Description automatically generated
   :width: 7.20833in
   :height: 6.11806in

   Figure 3‑16: The ArcNLET-Py VZMOD Module Metadata Pane in ArcGIS Pro.

.. figure:: ./media/installationandrequirementsMedia/media/image17.png
   :align: center
   :alt: A screenshot of a computer Description automatically generated
   :width: 7.20833in
   :height: 6.12431in

   Figure 3‑17: The ArcNLET-Py Transport Module Metadata Pane in ArcGIS Pro.

.. figure:: ./media/installationandrequirementsMedia/media/image18.png
   :align: center
   :alt: A screenshot of a computer Description automatically generated
   :width: 7.20833in
   :height: 6.07847in

   Figure 3‑18: The ArcNLET-Py Load Estimation Module Metadata Pane in ArcGIS Pro.

.. |image1| image:: ./media/installationandrequirementsMedia/media/image4.png
   :align: middle
   :width: 6.5in
   :height: 0.49375in

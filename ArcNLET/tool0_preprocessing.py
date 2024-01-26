"""
This script contains the Preprocessing module of ArcNLET model in the ArcGIS Python Toolbox.

The users provide a polygon shapefile of the study area, and the code will extract the soil properties from the SSURGO
The soil properties include hydraulic conductivity, porosity, and soil type.

@author: Wei Mao <wm23a@fsu.edu>， Michael Core <mcore@fsu.edu>, Ming Ye <mye@fsu.edu>
            The Department of Earth, Ocean, and Atmospheric Science, Florida State University
@date: 2023-11-27
"""

import os
import time
import arcpy
import json
import requests
import numpy as np
import pandas as pd
from json.decoder import JSONDecodeError
from requests import exceptions
import soiltexture

__version__ = "V1.0.0"
arcpy.env.parallelProcessingFactor = "100%"
arcpy.env.overwriteOutput = True


class Preprocessing(object):
    def __init__(self, c_area, c_pcs, c_top, c_bot, c_method, c_cellsize,
                 c_hydr_cond, c_porosity, c_soiltexture=None, c_spatial=None):
        # input files
        self.area = arcpy.Describe(c_area).catalogPath if not self.is_file_path(c_area) else c_area
        # self.projected_coordinate_system = arcpy.SpatialReference.loadFromString(c_pcs)
        self.projected_coordinate_system = c_pcs
        self.top = c_top
        self.bot = c_bot
        self.method = c_method
        self.cellsize = c_cellsize

        self.workdir = os.path.dirname(self.area)

        if self.is_file_path(c_hydr_cond):
            self.hydr_cond_name = os.path.basename(c_hydr_cond)
            self.hydr_cond_dir = os.path.dirname(c_hydr_cond)
        else:
            self.hydr_cond_name = os.path.basename(c_hydr_cond)
            self.hydr_cond_dir = self.workdir
        if self.is_file_path(c_porosity):
            self.porosity_name = os.path.basename(c_porosity)
            self.porosity_dir = os.path.dirname(c_porosity)
        else:
            self.porosity_name = os.path.basename(c_porosity)
            self.porosity_dir = self.workdir
        if c_soiltexture is not None:
            if self.is_file_path(c_soiltexture):
                self.soiltexture_name = os.path.basename(c_soiltexture)
                self.soiltexture_dir = os.path.dirname(c_soiltexture)
            else:
                self.soiltexture_name = os.path.basename(c_soiltexture)
                self.soiltexture_dir = self.workdir
        else:
            self.soiltexture_name = None
        if c_spatial is not None:
            if self.is_file_path(c_spatial):
                self.spatial_name = os.path.basename(c_spatial)
                self.spatial_dir = os.path.dirname(c_spatial)
            else:
                self.spatial_name = os.path.basename(c_spatial)
                self.spatial_dir = self.workdir
        else:
            self.spatial_name = None
        self.hydr_cond = os.path.join(self.hydr_cond_dir, self.hydr_cond_name)
        self.porosity = os.path.join(self.porosity_dir, self.porosity_name)
        self.soiltexture = os.path.join(self.soiltexture_dir, self.soiltexture_name) if self.soiltexture_name else None
        self.spatial = os.path.join(self.spatial_dir, self.spatial_name) if self.spatial_name else None

    def main(self):
        """main calculation function
        """
        arcpy.env.workspace = os.path.abspath(self.workdir)
        wgs84 = arcpy.SpatialReference(4326)

        # convert to WGS84
        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage(f"{current_time}     Preprocessing: Convert to WGS84")
        if arcpy.Describe(self.area).spatialReference.name != "GCS_WGS_1984":
            area_wgs84 = r"memory\area_wgs84"
            arcpy.management.Project(self.area, area_wgs84, wgs84)
            area = area_wgs84
        else:
            area = self.area

        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage(f"{current_time}     Request spatial data from SSURGO")
        q = Preprocessing.request_spatial(area)
        spatial_df = Preprocessing.fetch_ssurgodata(q)

        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage(f"{current_time}     Request tabular data from SSURGO")
        q = Preprocessing.request_tabular(df=spatial_df, method=self.method, top=self.top, bottom=self.bot)
        tabular_df = Preprocessing.fetch_ssurgodata(q)

        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage(f"{current_time}     Merge spatial and tabular data")
        merged_df = pd.merge(spatial_df, tabular_df, on=['mukey', 'areasymbol', 'muname', 'musym'], how='inner')
        new_column_names = {'wsatiated_l': 'wsat_l', 'wsatiated_r': 'wsat_r', 'wsatiated_h': 'wsat_h',
                            'dbovendry_l': 'dbo_l', 'dbovendry_r': 'dbo_r', 'dbovendry_h': 'dbo_h',
                            'partdensity': 'part_d', 'claytotal_r': 'clay_r', 'silttotal_r': 'silt_r',
                            'sandtotal_r': 'sand_r'}
        merged_df.rename(columns=new_column_names, inplace=True)

        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage(f"{current_time}     Convert units and calculate soil type")
        merged_df['ksat_l'] = merged_df['ksat_l'].astype('float64') / 1000000 * 86400
        merged_df['ksat_r'] = merged_df['ksat_r'].astype('float64') / 1000000 * 86400
        merged_df['ksat_h'] = merged_df['ksat_h'].astype('float64') / 1000000 * 86400
        merged_df['wsat_l'] = merged_df['wsat_l'].astype('float64') / 100
        merged_df['wsat_r'] = merged_df['wsat_r'].astype('float64') / 100
        merged_df['wsat_h'] = merged_df['wsat_h'].astype('float64') / 100
        columns_to_convert = ['dbo_l', 'dbo_r', 'dbo_h', 'part_d', 'clay_r', 'silt_r', 'sand_r']
        merged_df[columns_to_convert] = merged_df[columns_to_convert].astype('float64')
        merged_df['poro'] = 1 - merged_df['dbo_r'] / 2.65
        merged_df.loc[merged_df['wsat_r'].isnull(), 'wsat_r'] = merged_df.loc[merged_df['wsat_r'].isnull(), 'poro']

        total = merged_df['sand_r'] + merged_df['silt_r'] + merged_df['clay_r']
        merged_df['sand_r'] = merged_df['sand_r'] / total * 100
        merged_df['silt_r'] = merged_df['silt_r'] / total * 100
        merged_df['clay_r'] = merged_df['clay_r'] / total * 100
        merged_df['texture'] = soiltexture.getTextures(merged_df['sand_r'], merged_df['clay_r'], classification='USDA')
        soil_map = {"clay": 1, "clay loam": 2, "loam": 3, "loamy sand": 4, "sand": 5, "sandy clay": 6,
                    "sandy clay loam": 7, "sandy loam": 8, "silt": 9, "silt clay": 10,
                    "silt clay loam": 11, "silt loam": 12}
        merged_df['soiltype'] = merged_df['texture'].map(soil_map)
        merged_df['soiltype'].fillna(0, inplace=True)
        merged_df['soiltype'].replace([np.inf, -np.inf], 0, inplace=True)
        merged_df['soiltype'] = merged_df['soiltype'].astype(int)

        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage(f"{current_time}     Export to shapefile")
        output_shapefile = "spatial.shp"
        arcpy.management.CreateFeatureclass(arcpy.env.workspace, output_shapefile, "POLYGON",
                                            spatial_reference=wgs84)

        field_name = list(merged_df.columns)
        field_name.remove('geom')
        for field in field_name:
            field_type = "TEXT" if merged_df[field].dtype == 'object' else "DOUBLE"
            arcpy.management.AddField(output_shapefile, field, field_type)

        no_data_value = -9999
        with arcpy.da.InsertCursor(output_shapefile, ["SHAPE@"] + field_name) as cursor:
            for index, row in merged_df.iterrows():
                polygon_wkt = row['geom']
                polygon = arcpy.FromWKT(polygon_wkt, wgs84)
                row_values = [polygon] + [val if pd.notnull(val) else no_data_value for val in row[field_name].tolist()]
                cursor.insertRow(row_values)

        arcpy.management.Project(output_shapefile, self.spatial, self.projected_coordinate_system)
        arcpy.management.Delete(output_shapefile)

        current_time = time.strftime("%H:%M:%S", time.localtime())
        arcpy.AddMessage(f"{current_time}     Export to raster")
        arcpy.conversion.PolygonToRaster(self.spatial, 'ksat_r', self.hydr_cond, cell_assignment='MAXIMUM_AREA',
                                         cellsize=self.cellsize)
        output_hydraulic_conductivity = arcpy.sa.SetNull(self.hydr_cond, self.hydr_cond, 'VALUE = -9999')
        output_hydraulic_conductivity.save(self.hydr_cond)

        arcpy.conversion.PolygonToRaster(self.spatial, 'poro', self.porosity, cell_assignment='MAXIMUM_AREA',
                                         cellsize=self.cellsize)
        output_porosity = arcpy.sa.SetNull(self.porosity, self.porosity, 'VALUE = -9999')
        output_porosity.save(self.porosity)

        if self.soiltexture is not None:
            arcpy.conversion.PolygonToRaster(self.spatial, 'soiltype', self.soiltexture, cell_assignment='MAXIMUM_AREA',
                                             cellsize=self.cellsize)
            output_soil_texture = arcpy.sa.SetNull(self.soiltexture, self.soiltexture, 'VALUE = -9999')
            output_soil_texture.save(self.soiltexture)

            arcpy.management.BuildRasterAttributeTable(self.soiltexture, "Overwrite")
            arcpy.management.AddField(self.soiltexture, "SOILTYPE", "TEXT", field_length=50)
            with arcpy.da.UpdateCursor(self.soiltexture, ["VALUE", "SOILTYPE"]) as cursor:
                for row in cursor:
                    if row[0] in soil_map.values():
                        row[1] = list(soil_map.keys())[list(soil_map.values()).index(row[0])]
                    else:
                        row[1] = "NA"
                    cursor.updateRow(row)

        if self.spatial is None:
            arcpy.management.Delete(self.spatial)

    @staticmethod
    def request_spatial(area):
        wkt_str = "POLYGON (("
        with arcpy.da.SearchCursor(area, ['SHAPE@']) as cursor:
            for row in cursor:
                polygon = row[0]
                for part in polygon:
                    for pnt in part:
                        if pnt:
                            wkt_str += "{} {}, ".format(pnt.X, pnt.Y)
        wkt_str = wkt_str[:-2] + "))"

        q = """~DeclareGeometry(@aoi)~

        select @aoi = geometry::STPolyFromText('""" + wkt_str + """' , 4326)

        ~DeclareIdGeomTable(@outtable)~
        ~GetClippedMapunits(@aoi,polygon,geo,@outtable)~

        select *
        into #temp
        from @outtable;

        select areasymbol, areaname, muname, musym, mukey, nationalmusym as nat_musym, geom
        from #temp, legend, mapunit
        where #temp.id = mapunit.mukey and mapunit.lkey = legend.lkey"""
        return q

    @staticmethod
    def request_tabular(df, method, top, bottom):
        column = 'mukey'
        df[column] = df[column].astype('string')
        key_list = pd.Series(df[column].unique()).to_list()
        keys = ",".join(map("'{0}'".format, key_list))

        tDep = str(top)
        bDep = str(bottom)

        prop = ["ksat_l", "ksat_r", "ksat_h", "wsatiated_l", "wsatiated_r", "wsatiated_h",
                "dbovendry_l", "dbovendry_r", "dbovendry_h", "partdensity",
                "claytotal_r", "silttotal_r", "sandtotal_r"]

        if method.lower() == "weighted average":
            q = ("""
            SELECT areasymbol, musym, muname, mukey
                INTO #kitchensink
                FROM legend
                INNER JOIN mapunit ON mapunit.lkey = legend.lkey AND mapunit.mukey IN(""" + keys + """)
            SELECT mapunit.mukey, cokey, comppct_r, compkind, majcompflag,
                    SUM (comppct_r) OVER (PARTITION BY mapunit.mukey) AS SUM_COMP_PCT
                INTO #comp_temp
                FROM legend AS legend
                INNER JOIN mapunit ON mapunit.lkey = legend.lkey AND mapunit.mukey IN(""" + keys + """)
                INNER JOIN component ON component.mukey = mapunit.mukey AND component.majcompflag = 'Yes'
            SELECT cokey, compkind, majcompflag, SUM_COMP_PCT,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) / 
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT1,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT2,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT3,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT4,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT5,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT6,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT7,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT8,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT9,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT10,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT11,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT12,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT13
                INTO #comp_temp3
                FROM #comp_temp
            SELECT mapunit.mukey, areasymbol, musym, muname, component.cokey AS cokey, chorizon.chkey/1 AS chkey,
                    compname, compkind, hzname, hzdept_r, hzdepb_r, CASE WHEN hzdept_r < """
                 + tDep + " THEN " + tDep + """ ELSE hzdept_r END AS hzdept_r_ADJ,
                    CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep + """ ELSE hzdepb_r END AS hzdepb_r_ADJ,
                    CASE WHEN ksat_l is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep + " THEN " + tDep +
                 """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_ksat_l,
                    CASE WHEN ksat_r is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep + " THEN " + tDep +
                 """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_ksat_r,
                    CASE WHEN ksat_h is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep + " THEN " + tDep +
                 """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_ksat_h,
                    CASE WHEN wsatiated_l is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_wsatiated_l,
                    CASE WHEN wsatiated_r is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_wsatiated_r,
                    CASE WHEN wsatiated_h is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_wsatiated_h,
                    CASE WHEN dbovendry_l is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_dbovendry_l,
                    CASE WHEN dbovendry_r is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_dbovendry_r,
                    CASE WHEN dbovendry_h is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_dbovendry_h,
                    CASE WHEN partdensity is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_partdensity,
                    CASE WHEN claytotal_r is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_claytotal_r,
                    CASE WHEN silttotal_r is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_silttotal_r,
                    CASE WHEN sandtotal_r is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_sandtotal_r,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN ksat_l is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN ksat_l is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) OVER 
                 (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_ksat_l,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN ksat_r is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN ksat_r is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) 
                 OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_ksat_r,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN ksat_h is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN ksat_h is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) 
                 OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_ksat_h,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN wsatiated_l is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN wsatiated_l is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) 
                 OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_wsatiated_l,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN wsatiated_r is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN wsatiated_r is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) 
                 OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_wsatiated_r,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN wsatiated_h is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN wsatiated_h is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) 
                 OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_wsatiated_h,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN dbovendry_l is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN dbovendry_l is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) 
                 OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_dbovendry_l,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN dbovendry_r is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN dbovendry_r is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) 
                 OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_dbovendry_r,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN dbovendry_h is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN dbovendry_h is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) 
                 OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_dbovendry_h,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN partdensity is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN partdensity is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) 
                 OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_partdensity,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN claytotal_r is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN claytotal_r is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) 
                 OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_claytotal_r,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN silttotal_r is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN silttotal_r is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) 
                 OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_silttotal_r,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN sandtotal_r is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN sandtotal_r is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) 
                 OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_sandtotal_r,
                    comppct_r, ksat_l, ksat_r, ksat_h, wsatiated_l, wsatiated_r, wsatiated_h, dbovendry_l, dbovendry_r,
                    dbovendry_h, partdensity, claytotal_r, silttotal_r, sandtotal_r
                INTO #main
                FROM legend
                INNER JOIN mapunit ON mapunit.lkey = legend.lkey AND mapunit.mukey IN(""" + keys + """)
                INNER JOIN component ON component.mukey = mapunit.mukey  AND component.compkind != 'Miscellaneous area'
                INNER JOIN chorizon ON chorizon.cokey = component.cokey AND hzdepb_r > """ + tDep +
                 """ AND hzdept_r <= """ + bDep + """
                WHERE chorizon.hzdept_r IS NOT NULL
                ORDER BY mapunit.mukey, areasymbol, musym, muname, comppct_r DESC, cokey, hzdept_r, hzdepb_r
            SELECT #main.mukey, #main.areasymbol, #main.musym, #main.muname, #main.cokey, #main.chkey, #main.compname,
                    #main.compkind, hzname, hzdept_r, hzdepb_r, hzdept_r_ADJ, hzdepb_r_ADJ, 
                    (CASE WHEN ISNULL(sum_thickness_ksat_l, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT1 END) AS
                        CORRECT_COMP_PCT1,
                    (CASE WHEN ISNULL(sum_thickness_ksat_r, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT2 END) AS
                        CORRECT_COMP_PCT2,
                    (CASE WHEN ISNULL(sum_thickness_ksat_h, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT3 END) AS
                        CORRECT_COMP_PCT3,
                    (CASE WHEN ISNULL(sum_thickness_wsatiated_l, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT4 END) AS
                        CORRECT_COMP_PCT4,
                    (CASE WHEN ISNULL(sum_thickness_wsatiated_r, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT5 END) AS
                        CORRECT_COMP_PCT5,
                    (CASE WHEN ISNULL(sum_thickness_wsatiated_h, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT6 END) AS
                        CORRECT_COMP_PCT6,
                    (CASE WHEN ISNULL(sum_thickness_dbovendry_l, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT7 END) AS
                        CORRECT_COMP_PCT7,
                    (CASE WHEN ISNULL(sum_thickness_dbovendry_r, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT8 END) AS
                        CORRECT_COMP_PCT8,
                    (CASE WHEN ISNULL(sum_thickness_dbovendry_h, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT9 END) AS
                        CORRECT_COMP_PCT9,
                    (CASE WHEN ISNULL(sum_thickness_partdensity, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT10 END) AS
                        CORRECT_COMP_PCT10,
                    (CASE WHEN ISNULL(sum_thickness_claytotal_r, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT11 END) AS
                        CORRECT_COMP_PCT11,
                    (CASE WHEN ISNULL(sum_thickness_silttotal_r, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT12 END) AS
                        CORRECT_COMP_PCT12,
                    (CASE WHEN ISNULL(sum_thickness_sandtotal_r, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT13 END) AS
                        CORRECT_COMP_PCT13,
                    ISNULL(thickness_wt_ksat_l, 0) AS thickness_wt_ksat_l, sum_thickness_ksat_l, 
                    ISNULL(thickness_wt_ksat_r, 0) AS thickness_wt_ksat_r, sum_thickness_ksat_r,
                    ISNULL(thickness_wt_ksat_h, 0) AS thickness_wt_ksat_h, sum_thickness_ksat_h,
                    ISNULL(thickness_wt_wsatiated_l, 0) AS thickness_wt_wsatiated_l, sum_thickness_wsatiated_l,
                    ISNULL(thickness_wt_wsatiated_r, 0) AS thickness_wt_wsatiated_r, sum_thickness_wsatiated_r,
                    ISNULL(thickness_wt_wsatiated_h, 0) AS thickness_wt_wsatiated_h, sum_thickness_wsatiated_h,
                    ISNULL(thickness_wt_dbovendry_l, 0) AS thickness_wt_dbovendry_l, sum_thickness_dbovendry_l,
                    ISNULL(thickness_wt_dbovendry_r, 0) AS thickness_wt_dbovendry_r, sum_thickness_dbovendry_r,
                    ISNULL(thickness_wt_dbovendry_h, 0) AS thickness_wt_dbovendry_h, sum_thickness_dbovendry_h,
                    ISNULL(thickness_wt_partdensity, 0) AS thickness_wt_partdensity, sum_thickness_partdensity,
                    ISNULL(thickness_wt_claytotal_r, 0) AS thickness_wt_claytotal_r, sum_thickness_claytotal_r,
                    ISNULL(thickness_wt_silttotal_r, 0) AS thickness_wt_silttotal_r, sum_thickness_silttotal_r,
                    ISNULL(thickness_wt_sandtotal_r, 0) AS thickness_wt_sandtotal_r, sum_thickness_sandtotal_r,
                    comppct_r, SUM_COMP_PCT, ksat_l, ksat_r, ksat_h, wsatiated_l, wsatiated_r, wsatiated_h, dbovendry_l,
                    dbovendry_r, dbovendry_h, partdensity, claytotal_r, silttotal_r, sandtotal_r, 
                    ((thickness_wt_ksat_l / (CASE WHEN sum_thickness_ksat_l = 0 THEN 1 ELSE 
                        sum_thickness_ksat_l END)) * ksat_l) AS DEPTH_WEIGHTED_AVERAGE1,
                    ((thickness_wt_ksat_r / (CASE WHEN sum_thickness_ksat_r = 0 THEN 1 ELSE 
                        sum_thickness_ksat_r END)) * ksat_r) AS DEPTH_WEIGHTED_AVERAGE2,
                    ((thickness_wt_ksat_h / (CASE WHEN sum_thickness_ksat_h = 0 THEN 1 ELSE 
                        sum_thickness_ksat_h END)) * ksat_h) AS DEPTH_WEIGHTED_AVERAGE3,
                    ((thickness_wt_wsatiated_l / (CASE WHEN sum_thickness_wsatiated_l = 0 THEN 1 ELSE 
                        sum_thickness_wsatiated_l END)) * wsatiated_l) AS DEPTH_WEIGHTED_AVERAGE4,
                    ((thickness_wt_wsatiated_r / (CASE WHEN sum_thickness_wsatiated_r = 0 THEN 1 ELSE 
                        sum_thickness_wsatiated_r END)) * wsatiated_r) AS DEPTH_WEIGHTED_AVERAGE5,
                    ((thickness_wt_wsatiated_h / (CASE WHEN sum_thickness_wsatiated_h = 0 THEN 1 ELSE 
                        sum_thickness_wsatiated_h END)) * wsatiated_h) AS DEPTH_WEIGHTED_AVERAGE6,
                    ((thickness_wt_dbovendry_l / (CASE WHEN sum_thickness_dbovendry_l = 0 THEN 1 ELSE 
                        sum_thickness_dbovendry_l END)) * dbovendry_l) AS DEPTH_WEIGHTED_AVERAGE7,
                    ((thickness_wt_dbovendry_r / (CASE WHEN sum_thickness_dbovendry_r = 0 THEN 1 ELSE 
                        sum_thickness_dbovendry_r END)) * dbovendry_r) AS DEPTH_WEIGHTED_AVERAGE8,
                    ((thickness_wt_dbovendry_h / (CASE WHEN sum_thickness_dbovendry_h = 0 THEN 1 ELSE 
                        sum_thickness_dbovendry_h END)) * dbovendry_h) AS DEPTH_WEIGHTED_AVERAGE9,
                    ((thickness_wt_partdensity / (CASE WHEN sum_thickness_partdensity = 0 THEN 1 ELSE 
                        sum_thickness_partdensity END)) * partdensity) AS DEPTH_WEIGHTED_AVERAGE10,
                    ((thickness_wt_claytotal_r / (CASE WHEN sum_thickness_claytotal_r = 0 THEN 1 ELSE 
                        sum_thickness_claytotal_r END)) * claytotal_r) AS DEPTH_WEIGHTED_AVERAGE11,
                    ((thickness_wt_silttotal_r / (CASE WHEN sum_thickness_silttotal_r = 0 THEN 1 ELSE 
                        sum_thickness_silttotal_r END)) * silttotal_r) AS DEPTH_WEIGHTED_AVERAGE12,
                    ((thickness_wt_sandtotal_r / (CASE WHEN sum_thickness_sandtotal_r = 0 THEN 1 ELSE 
                        sum_thickness_sandtotal_r END)) * sandtotal_r) AS DEPTH_WEIGHTED_AVERAGE13
                INTO #comp_temp2
                FROM #main
                INNER JOIN #comp_temp3 ON #comp_temp3.cokey = #main.cokey
                ORDER BY #main.mukey, comppct_r DESC, #main.cokey, #main.areasymbol, #main.musym, #main.muname,
                    hzdept_r, hzdepb_r
            SELECT DISTINCT #comp_temp2.mukey, #comp_temp2.cokey, CORRECT_COMP_PCT1, CORRECT_COMP_PCT2,
                    CORRECT_COMP_PCT3, CORRECT_COMP_PCT4, CORRECT_COMP_PCT5, CORRECT_COMP_PCT6, CORRECT_COMP_PCT7,
                    CORRECT_COMP_PCT8, CORRECT_COMP_PCT9, CORRECT_COMP_PCT10, CORRECT_COMP_PCT11,
                    CORRECT_COMP_PCT12, CORRECT_COMP_PCT13
                INTO #weights
                FROM #comp_temp2
                    WHERE DEPTH_WEIGHTED_AVERAGE1 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE2 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE3 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE4 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE5 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE6 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE7 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE8 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE9 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE10 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE11 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE12 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE13 IS NOT NULL
            SELECT DISTINCT #weights.mukey, SUM(CORRECT_COMP_PCT1) AS RATED_PCT1, SUM(CORRECT_COMP_PCT2) AS RATED_PCT2, 
                    SUM(CORRECT_COMP_PCT3) AS RATED_PCT3, SUM(CORRECT_COMP_PCT4) AS RATED_PCT4, 
                    SUM(CORRECT_COMP_PCT5) AS RATED_PCT5, SUM(CORRECT_COMP_PCT6) AS RATED_PCT6, 
                    SUM(CORRECT_COMP_PCT7) AS RATED_PCT7, SUM(CORRECT_COMP_PCT8) AS RATED_PCT8, 
                    SUM(CORRECT_COMP_PCT9) AS RATED_PCT9, SUM(CORRECT_COMP_PCT10) AS RATED_PCT10, 
                    SUM(CORRECT_COMP_PCT11) AS RATED_PCT11, SUM(CORRECT_COMP_PCT12) AS RATED_PCT12, 
                    SUM(CORRECT_COMP_PCT13) AS RATED_PCT13
                INTO #weights2
                FROM #weights
                GROUP BY #weights.mukey
            SELECT #comp_temp2.mukey, #comp_temp2.cokey, #weights2.RATED_PCT1, #weights2.RATED_PCT2, 
                    #weights2.RATED_PCT3, #weights2.RATED_PCT4, #weights2.RATED_PCT5, #weights2.RATED_PCT6, 
                    #weights2.RATED_PCT7, #weights2.RATED_PCT8, #weights2.RATED_PCT9, #weights2.RATED_PCT10, 
                    #weights2.RATED_PCT11, #weights2.RATED_PCT12, #weights2.RATED_PCT13, 
                    SUM(CORRECT_COMP_PCT1 * DEPTH_WEIGHTED_AVERAGE1) AS COMP_WEIGHTED_AVERAGE1, 
                    SUM(CORRECT_COMP_PCT2 * DEPTH_WEIGHTED_AVERAGE2) AS COMP_WEIGHTED_AVERAGE2, 
                    SUM(CORRECT_COMP_PCT3 * DEPTH_WEIGHTED_AVERAGE3) AS COMP_WEIGHTED_AVERAGE3, 
                    SUM(CORRECT_COMP_PCT4 * DEPTH_WEIGHTED_AVERAGE4) AS COMP_WEIGHTED_AVERAGE4, 
                    SUM(CORRECT_COMP_PCT5 * DEPTH_WEIGHTED_AVERAGE5) AS COMP_WEIGHTED_AVERAGE5, 
                    SUM(CORRECT_COMP_PCT6 * DEPTH_WEIGHTED_AVERAGE6) AS COMP_WEIGHTED_AVERAGE6, 
                    SUM(CORRECT_COMP_PCT7 * DEPTH_WEIGHTED_AVERAGE7) AS COMP_WEIGHTED_AVERAGE7, 
                    SUM(CORRECT_COMP_PCT8 * DEPTH_WEIGHTED_AVERAGE8) AS COMP_WEIGHTED_AVERAGE8, 
                    SUM(CORRECT_COMP_PCT9 * DEPTH_WEIGHTED_AVERAGE9) AS COMP_WEIGHTED_AVERAGE9, 
                    SUM(CORRECT_COMP_PCT10 * DEPTH_WEIGHTED_AVERAGE10) AS COMP_WEIGHTED_AVERAGE10, 
                    SUM(CORRECT_COMP_PCT11 * DEPTH_WEIGHTED_AVERAGE11) AS COMP_WEIGHTED_AVERAGE11, 
                    SUM(CORRECT_COMP_PCT12 * DEPTH_WEIGHTED_AVERAGE12) AS COMP_WEIGHTED_AVERAGE12, 
                    SUM(CORRECT_COMP_PCT13 * DEPTH_WEIGHTED_AVERAGE13) AS COMP_WEIGHTED_AVERAGE13
                INTO #last_step
                FROM #comp_temp2
                INNER JOIN #weights2 ON #weights2.mukey = #comp_temp2.mukey
                    WHERE DEPTH_WEIGHTED_AVERAGE1 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE2 IS NOT NULL OR 
                        DEPTH_WEIGHTED_AVERAGE3 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE4 IS NOT NULL OR 
                        DEPTH_WEIGHTED_AVERAGE5 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE6 IS NOT NULL OR 
                        DEPTH_WEIGHTED_AVERAGE7 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE8 IS NOT NULL OR 
                        DEPTH_WEIGHTED_AVERAGE9 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE10 IS NOT NULL OR 
                        DEPTH_WEIGHTED_AVERAGE11 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE12 IS NOT NULL OR 
                        DEPTH_WEIGHTED_AVERAGE13 IS NOT NULL
                GROUP BY #comp_temp2.mukey, #comp_temp2.cokey, CORRECT_COMP_PCT1, CORRECT_COMP_PCT2, CORRECT_COMP_PCT3, 
                    CORRECT_COMP_PCT4, CORRECT_COMP_PCT5, CORRECT_COMP_PCT6, CORRECT_COMP_PCT7, CORRECT_COMP_PCT8, 
                    CORRECT_COMP_PCT9, CORRECT_COMP_PCT10, CORRECT_COMP_PCT11, CORRECT_COMP_PCT12, CORRECT_COMP_PCT13, 
                    #weights2.RATED_PCT1, #weights2.RATED_PCT2, #weights2.RATED_PCT3, #weights2.RATED_PCT4, 
                    #weights2.RATED_PCT5, #weights2.RATED_PCT6, #weights2.RATED_PCT7, #weights2.RATED_PCT8, 
                    #weights2.RATED_PCT9, #weights2.RATED_PCT10, #weights2.RATED_PCT11, #weights2.RATED_PCT12, 
                    #weights2.RATED_PCT13, DEPTH_WEIGHTED_AVERAGE1, DEPTH_WEIGHTED_AVERAGE2, DEPTH_WEIGHTED_AVERAGE3, 
                    DEPTH_WEIGHTED_AVERAGE4, DEPTH_WEIGHTED_AVERAGE5, 
                    DEPTH_WEIGHTED_AVERAGE6, DEPTH_WEIGHTED_AVERAGE7,
                    DEPTH_WEIGHTED_AVERAGE8, DEPTH_WEIGHTED_AVERAGE9, 
                    DEPTH_WEIGHTED_AVERAGE10, DEPTH_WEIGHTED_AVERAGE11, 
                    DEPTH_WEIGHTED_AVERAGE12, DEPTH_WEIGHTED_AVERAGE13
            SELECT #kitchensink.mukey, #last_step.cokey, areasymbol, musym, muname, #last_step.RATED_PCT1, 
                    #last_step.RATED_PCT2, #last_step.RATED_PCT3, #last_step.RATED_PCT4, #last_step.RATED_PCT5, 
                    #last_step.RATED_PCT6, #last_step.RATED_PCT7, #last_step.RATED_PCT8, #last_step.RATED_PCT9, 
                    #last_step.RATED_PCT10, #last_step.RATED_PCT11, #last_step.RATED_PCT12, #last_step.RATED_PCT13, 
                    CAST (SUM((CASE WHEN RATED_PCT1 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE1 END) / 
                        (CASE WHEN RATED_PCT1 = 0 THEN 1 ELSE RATED_PCT1 END)) OVER 
                        (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS ksat_l, 
                    CAST (SUM((CASE WHEN RATED_PCT2 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE2 END) / 
                        (CASE WHEN RATED_PCT2 = 0 THEN 1 ELSE RATED_PCT2 END)) OVER 
                        (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS ksat_r, 
                    CAST (SUM((CASE WHEN RATED_PCT3 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE3 END) / 
                        (CASE WHEN RATED_PCT3 = 0 THEN 1 ELSE RATED_PCT3 END)) 
                        OVER (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS ksat_h, 
                    CAST (SUM((CASE WHEN RATED_PCT4 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE4 END) / 
                        (CASE WHEN RATED_PCT4 = 0 THEN 1 ELSE RATED_PCT4 END)) 
                        OVER (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS wsatiated_l, 
                    CAST (SUM((CASE WHEN RATED_PCT5 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE5 END) / 
                        (CASE WHEN RATED_PCT5 = 0 THEN 1 ELSE RATED_PCT5 END)) 
                        OVER (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS wsatiated_r, 
                    CAST (SUM((CASE WHEN RATED_PCT6 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE6 END) / 
                        (CASE WHEN RATED_PCT6 = 0 THEN 1 ELSE RATED_PCT6 END)) 
                        OVER (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS wsatiated_h, 
                    CAST (SUM((CASE WHEN RATED_PCT7 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE7 END) / 
                        (CASE WHEN RATED_PCT7 = 0 THEN 1 ELSE RATED_PCT7 END)) 
                        OVER (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS dbovendry_l, 
                    CAST (SUM((CASE WHEN RATED_PCT8 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE8 END) / 
                        (CASE WHEN RATED_PCT8 = 0 THEN 1 ELSE RATED_PCT8 END)) 
                        OVER (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS dbovendry_r, 
                    CAST (SUM((CASE WHEN RATED_PCT9 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE9 END) / 
                        (CASE WHEN RATED_PCT9 = 0 THEN 1 ELSE RATED_PCT9 END)) 
                        OVER (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS dbovendry_h, 
                    CAST (SUM((CASE WHEN RATED_PCT10 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE10 END) / 
                        (CASE WHEN RATED_PCT10 = 0 THEN 1 ELSE RATED_PCT10 END)) 
                        OVER (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS partdensity, 
                    CAST (SUM((CASE WHEN RATED_PCT11 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE11 END) / 
                        (CASE WHEN RATED_PCT11 = 0 THEN 1 ELSE RATED_PCT11 END)) 
                        OVER (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS claytotal_r, 
                    CAST (SUM((CASE WHEN RATED_PCT12 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE12 END) / 
                        (CASE WHEN RATED_PCT12 = 0 THEN 1 ELSE RATED_PCT12 END)) 
                        OVER (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS silttotal_r, 
                    CAST (SUM((CASE WHEN RATED_PCT13 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE13 END) / 
                    (CASE WHEN RATED_PCT13 = 0 THEN 1 ELSE RATED_PCT13 END)) 
                    OVER (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS sandtotal_r
                INTO #last_step2
                FROM #last_step
                RIGHT OUTER JOIN #kitchensink ON #kitchensink.mukey = #last_step.mukey
                GROUP BY #kitchensink.areasymbol, #kitchensink.musym, #kitchensink.muname, #kitchensink.mukey, 
                    #last_step.RATED_PCT1, #last_step.RATED_PCT2, #last_step.RATED_PCT3, #last_step.RATED_PCT4, 
                    #last_step.RATED_PCT5, #last_step.RATED_PCT6, #last_step.RATED_PCT7, #last_step.RATED_PCT8, 
                    #last_step.RATED_PCT9, #last_step.RATED_PCT10, #last_step.RATED_PCT11, #last_step.RATED_PCT12, 
                    #last_step.RATED_PCT13, COMP_WEIGHTED_AVERAGE1, COMP_WEIGHTED_AVERAGE2, COMP_WEIGHTED_AVERAGE3, 
                    COMP_WEIGHTED_AVERAGE4, COMP_WEIGHTED_AVERAGE5, COMP_WEIGHTED_AVERAGE6, COMP_WEIGHTED_AVERAGE7, 
                    COMP_WEIGHTED_AVERAGE8, COMP_WEIGHTED_AVERAGE9, COMP_WEIGHTED_AVERAGE10, COMP_WEIGHTED_AVERAGE11, 
                    COMP_WEIGHTED_AVERAGE12, COMP_WEIGHTED_AVERAGE13, #last_step.cokey
                ORDER BY #kitchensink.mukey, #kitchensink.areasymbol, #kitchensink.musym, #kitchensink.muname
            SELECT #last_step2.areasymbol, #last_step2.musym, #last_step2.muname, #last_step2.mukey, 
                    #last_step2.ksat_l, #last_step2.ksat_r, #last_step2.ksat_h, #last_step2.wsatiated_l, 
                    #last_step2.wsatiated_r, #last_step2.wsatiated_h, #last_step2.dbovendry_l, 
                    #last_step2.dbovendry_r, #last_step2.dbovendry_h, #last_step2.partdensity, 
                    #last_step2.claytotal_r, #last_step2.silttotal_r, #last_step2.sandtotal_r
                FROM #last_step2
                LEFT OUTER JOIN #last_step ON #last_step.mukey = #last_step2.mukey
                GROUP BY #last_step2.areasymbol, #last_step2.musym, #last_step2.muname, #last_step2.mukey, 
                    #last_step2.ksat_l, #last_step2.ksat_r, #last_step2.ksat_h, #last_step2.wsatiated_l, 
                    #last_step2.wsatiated_r, #last_step2.wsatiated_h, #last_step2.dbovendry_l, 
                    #last_step2.dbovendry_r, #last_step2.dbovendry_h, #last_step2.partdensity, 
                    #last_step2.claytotal_r, #last_step2.silttotal_r, #last_step2.sandtotal_r
                ORDER BY #last_step2.mukey, #last_step2.areasymbol, #last_step2.musym, #last_step2.muname, 
                    #last_step2.ksat_l, #last_step2.ksat_r, #last_step2.ksat_h, #last_step2.wsatiated_l, 
                    #last_step2.wsatiated_r, #last_step2.wsatiated_h, #last_step2.dbovendry_l, 
                    #last_step2.dbovendry_r, #last_step2.dbovendry_h, #last_step2.partdensity, 
                    #last_step2.claytotal_r, #last_step2.silttotal_r, #last_step2.sandtotal_r""")
        elif method.lower() == "harmonic mean for ks":
            q = ("""
            SELECT areasymbol, musym, muname, mukey
                INTO #kitchensink
                FROM legend
                INNER JOIN mapunit ON mapunit.lkey = legend.lkey AND mapunit.mukey IN(""" + keys + """)
            SELECT mapunit.mukey, cokey, comppct_r, compkind, majcompflag,
                    SUM (comppct_r) OVER (PARTITION BY mapunit.mukey) AS SUM_COMP_PCT
                INTO #comp_temp
                FROM legend AS legend
                INNER JOIN mapunit ON mapunit.lkey = legend.lkey AND mapunit.mukey IN(""" + keys + """)
                INNER JOIN component ON component.mukey = mapunit.mukey AND component.majcompflag = 'Yes'
            SELECT cokey, compkind, majcompflag, SUM_COMP_PCT,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) / 
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT1,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT2,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT3,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT4,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT5,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT6,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT7,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT8,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT9,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT10,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT11,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT12,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) /
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT13
                INTO #comp_temp3
                FROM #comp_temp
            SELECT mapunit.mukey, areasymbol, musym, muname, component.cokey AS cokey, chorizon.chkey/1 AS chkey,
                    compname, compkind, hzname, hzdept_r, hzdepb_r, 
                    CASE WHEN hzdept_r < """ + tDep + " THEN " + tDep + """ ELSE hzdept_r END AS hzdept_r_ADJ,
                    CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep + """ ELSE hzdepb_r END AS hzdepb_r_ADJ,
                    CASE WHEN ksat_l is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_ksat_l,
                    CASE WHEN ksat_r is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_ksat_r,
                    CASE WHEN ksat_h is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_ksat_h,
                    CASE WHEN wsatiated_l is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_wsatiated_l,
                    CASE WHEN wsatiated_r is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_wsatiated_r,
                    CASE WHEN wsatiated_h is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_wsatiated_h,
                    CASE WHEN dbovendry_l is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_dbovendry_l,
                    CASE WHEN dbovendry_r is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_dbovendry_r,
                    CASE WHEN dbovendry_h is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_dbovendry_h,
                    CASE WHEN partdensity is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_partdensity,
                    CASE WHEN claytotal_r is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_claytotal_r,
                    CASE WHEN silttotal_r is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_silttotal_r,
                    CASE WHEN sandtotal_r is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_sandtotal_r,
                    CAST( SUM ( CAST ( ( 
                        ( CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep + """ 
                               WHEN ksat_l is NULL THEN NULL ELSE hzdepb_r END - 
                          CASE WHEN hzdept_r < """ + tDep + " THEN " + tDep + """ 
                               WHEN ksat_l is NULL THEN NULL ELSE hzdept_r END ) 
                        )AS decimal(5,2))) OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_ksat_l,
                    CAST( SUM ( CAST ( (
                        ( CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep + """ 
                               WHEN ksat_r is NULL THEN NULL ELSE hzdepb_r END - 
                          CASE WHEN hzdept_r < """ + tDep + " THEN " + tDep + """ 
                               WHEN ksat_r is NULL THEN NULL ELSE hzdept_r END ) 
                        )AS decimal(5,2))) OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_ksat_r,
                    CAST( SUM ( CAST ( (
                        ( CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep + """ 
                               WHEN ksat_h is NULL THEN NULL ELSE hzdepb_r END - 
                          CASE WHEN hzdept_r < """ + tDep + " THEN " + tDep + """ 
                               WHEN ksat_h is NULL THEN NULL ELSE hzdept_r END ) 
                        )AS decimal(5,2))) OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_ksat_h,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN wsatiated_l is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN wsatiated_l is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) 
                 OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_wsatiated_l,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN wsatiated_r is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN wsatiated_r is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) 
                 OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_wsatiated_r,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN wsatiated_h is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN wsatiated_h is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) 
                 OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_wsatiated_h,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN dbovendry_l is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN dbovendry_l is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) 
                 OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_dbovendry_l,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN dbovendry_r is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN dbovendry_r is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) 
                 OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_dbovendry_r,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN dbovendry_h is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN dbovendry_h is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) 
                 OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_dbovendry_h,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN partdensity is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN partdensity is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) 
                 OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_partdensity,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN claytotal_r is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN claytotal_r is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) 
                 OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_claytotal_r,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN silttotal_r is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN silttotal_r is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) 
                 OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_silttotal_r,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN sandtotal_r is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN sandtotal_r is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) 
                 OVER (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_sandtotal_r,
                    comppct_r, ksat_l, ksat_r, ksat_h, wsatiated_l, wsatiated_r, wsatiated_h, dbovendry_l, dbovendry_r,
                    dbovendry_h, partdensity, claytotal_r, silttotal_r, sandtotal_r
                INTO #main
                FROM legend
                INNER JOIN mapunit ON mapunit.lkey = legend.lkey AND mapunit.mukey IN(""" + keys + """)
                INNER JOIN component ON component.mukey = mapunit.mukey  AND component.compkind != 'Miscellaneous area'
                INNER JOIN chorizon ON chorizon.cokey = component.cokey AND hzdepb_r > """ + tDep +
                 """ AND hzdept_r <= """ + bDep + """
                WHERE chorizon.hzdept_r IS NOT NULL
                ORDER BY mapunit.mukey, areasymbol, musym, muname, comppct_r DESC, cokey, hzdept_r, hzdepb_r
            SELECT #main.mukey, #main.areasymbol, #main.musym, #main.muname, #main.cokey, #main.chkey, #main.compname,
                    #main.compkind, hzname, hzdept_r, hzdepb_r, hzdept_r_ADJ, hzdepb_r_ADJ, 
                    (CASE WHEN ISNULL(sum_thickness_ksat_l, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT1 END) AS
                        CORRECT_COMP_PCT1,
                    (CASE WHEN ISNULL(sum_thickness_ksat_r, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT2 END) AS
                        CORRECT_COMP_PCT2,
                    (CASE WHEN ISNULL(sum_thickness_ksat_h, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT3 END) AS
                        CORRECT_COMP_PCT3,
                    (CASE WHEN ISNULL(sum_thickness_wsatiated_l, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT4 END) AS
                        CORRECT_COMP_PCT4,
                    (CASE WHEN ISNULL(sum_thickness_wsatiated_r, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT5 END) AS
                        CORRECT_COMP_PCT5,
                    (CASE WHEN ISNULL(sum_thickness_wsatiated_h, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT6 END) AS
                        CORRECT_COMP_PCT6,
                    (CASE WHEN ISNULL(sum_thickness_dbovendry_l, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT7 END) AS
                        CORRECT_COMP_PCT7,
                    (CASE WHEN ISNULL(sum_thickness_dbovendry_r, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT8 END) AS
                        CORRECT_COMP_PCT8,
                    (CASE WHEN ISNULL(sum_thickness_dbovendry_h, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT9 END) AS
                        CORRECT_COMP_PCT9,
                    (CASE WHEN ISNULL(sum_thickness_partdensity, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT10 END) AS
                        CORRECT_COMP_PCT10,
                    (CASE WHEN ISNULL(sum_thickness_claytotal_r, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT11 END) AS
                        CORRECT_COMP_PCT11,
                    (CASE WHEN ISNULL(sum_thickness_silttotal_r, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT12 END) AS
                        CORRECT_COMP_PCT12,
                    (CASE WHEN ISNULL(sum_thickness_sandtotal_r, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT13 END) AS
                        CORRECT_COMP_PCT13,
                    ISNULL(thickness_wt_ksat_l, 0) AS thickness_wt_ksat_l, sum_thickness_ksat_l, 
                    ISNULL(thickness_wt_ksat_r, 0) AS thickness_wt_ksat_r, sum_thickness_ksat_r,
                    ISNULL(thickness_wt_ksat_h, 0) AS thickness_wt_ksat_h, sum_thickness_ksat_h,
                    ISNULL(thickness_wt_wsatiated_l, 0) AS thickness_wt_wsatiated_l, sum_thickness_wsatiated_l,
                    ISNULL(thickness_wt_wsatiated_r, 0) AS thickness_wt_wsatiated_r, sum_thickness_wsatiated_r,
                    ISNULL(thickness_wt_wsatiated_h, 0) AS thickness_wt_wsatiated_h, sum_thickness_wsatiated_h,
                    ISNULL(thickness_wt_dbovendry_l, 0) AS thickness_wt_dbovendry_l, sum_thickness_dbovendry_l,
                    ISNULL(thickness_wt_dbovendry_r, 0) AS thickness_wt_dbovendry_r, sum_thickness_dbovendry_r,
                    ISNULL(thickness_wt_dbovendry_h, 0) AS thickness_wt_dbovendry_h, sum_thickness_dbovendry_h,
                    ISNULL(thickness_wt_partdensity, 0) AS thickness_wt_partdensity, sum_thickness_partdensity,
                    ISNULL(thickness_wt_claytotal_r, 0) AS thickness_wt_claytotal_r, sum_thickness_claytotal_r,
                    ISNULL(thickness_wt_silttotal_r, 0) AS thickness_wt_silttotal_r, sum_thickness_silttotal_r,
                    ISNULL(thickness_wt_sandtotal_r, 0) AS thickness_wt_sandtotal_r, sum_thickness_sandtotal_r,
                    comppct_r, SUM_COMP_PCT, ksat_l, ksat_r, ksat_h, wsatiated_l, wsatiated_r, wsatiated_h, dbovendry_l,
                    dbovendry_r, dbovendry_h, partdensity, claytotal_r, silttotal_r, sandtotal_r, 
                    thickness_wt_ksat_l / SUM (ISNULL(thickness_wt_ksat_l / ksat_l, 1)) OVER (PARTITION BY #main.cokey)
                     AS DEPTH_WEIGHTED_AVERAGE1, 
                    thickness_wt_ksat_r / SUM (ISNULL(thickness_wt_ksat_r / ksat_r, 1)) OVER (PARTITION BY #main.cokey)
                     AS DEPTH_WEIGHTED_AVERAGE2,
                    thickness_wt_ksat_h / SUM (ISNULL(thickness_wt_ksat_h / ksat_h, 1)) OVER (PARTITION BY #main.cokey)
                     AS DEPTH_WEIGHTED_AVERAGE3,
                    ((thickness_wt_wsatiated_l / (CASE WHEN sum_thickness_wsatiated_l = 0 THEN 1 ELSE 
                        sum_thickness_wsatiated_l END)) * wsatiated_l) AS DEPTH_WEIGHTED_AVERAGE4,
                    ((thickness_wt_wsatiated_r / (CASE WHEN sum_thickness_wsatiated_r = 0 THEN 1 ELSE 
                        sum_thickness_wsatiated_r END)) * wsatiated_r) AS DEPTH_WEIGHTED_AVERAGE5,
                    ((thickness_wt_wsatiated_h / (CASE WHEN sum_thickness_wsatiated_h = 0 THEN 1 ELSE 
                        sum_thickness_wsatiated_h END)) * wsatiated_h) AS DEPTH_WEIGHTED_AVERAGE6,
                    ((thickness_wt_dbovendry_l / (CASE WHEN sum_thickness_dbovendry_l = 0 THEN 1 ELSE 
                        sum_thickness_dbovendry_l END)) * dbovendry_l) AS DEPTH_WEIGHTED_AVERAGE7,
                    ((thickness_wt_dbovendry_r / (CASE WHEN sum_thickness_dbovendry_r = 0 THEN 1 ELSE 
                        sum_thickness_dbovendry_r END)) * dbovendry_r) AS DEPTH_WEIGHTED_AVERAGE8,
                    ((thickness_wt_dbovendry_h / (CASE WHEN sum_thickness_dbovendry_h = 0 THEN 1 ELSE 
                        sum_thickness_dbovendry_h END)) * dbovendry_h) AS DEPTH_WEIGHTED_AVERAGE9,
                    ((thickness_wt_partdensity / (CASE WHEN sum_thickness_partdensity = 0 THEN 1 ELSE 
                        sum_thickness_partdensity END)) * partdensity) AS DEPTH_WEIGHTED_AVERAGE10,
                    ((thickness_wt_claytotal_r / (CASE WHEN sum_thickness_claytotal_r = 0 THEN 1 ELSE 
                        sum_thickness_claytotal_r END)) * claytotal_r) AS DEPTH_WEIGHTED_AVERAGE11,
                    ((thickness_wt_silttotal_r / (CASE WHEN sum_thickness_silttotal_r = 0 THEN 1 ELSE 
                        sum_thickness_silttotal_r END)) * silttotal_r) AS DEPTH_WEIGHTED_AVERAGE12,
                    ((thickness_wt_sandtotal_r / (CASE WHEN sum_thickness_sandtotal_r = 0 THEN 1 ELSE 
                        sum_thickness_sandtotal_r END)) * sandtotal_r) AS DEPTH_WEIGHTED_AVERAGE13
                INTO #comp_temp2
                FROM #main
                INNER JOIN #comp_temp3 ON #comp_temp3.cokey = #main.cokey
                ORDER BY #main.mukey, comppct_r DESC, #main.cokey, #main.areasymbol, #main.musym, #main.muname,
                    hzdept_r, hzdepb_r
            SELECT DISTINCT #comp_temp2.mukey, #comp_temp2.cokey, CORRECT_COMP_PCT1, CORRECT_COMP_PCT2,
                    CORRECT_COMP_PCT3, CORRECT_COMP_PCT4, CORRECT_COMP_PCT5, CORRECT_COMP_PCT6, CORRECT_COMP_PCT7,
                    CORRECT_COMP_PCT8, CORRECT_COMP_PCT9, CORRECT_COMP_PCT10, CORRECT_COMP_PCT11,
                    CORRECT_COMP_PCT12, CORRECT_COMP_PCT13
                INTO #weights
                FROM #comp_temp2
                    WHERE DEPTH_WEIGHTED_AVERAGE1 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE2 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE3 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE4 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE5 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE6 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE7 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE8 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE9 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE10 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE11 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE12 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE13 IS NOT NULL
            SELECT DISTINCT #weights.mukey, SUM(CORRECT_COMP_PCT1) AS RATED_PCT1, SUM(CORRECT_COMP_PCT2) AS RATED_PCT2, 
                    SUM(CORRECT_COMP_PCT3) AS RATED_PCT3, SUM(CORRECT_COMP_PCT4) AS RATED_PCT4, 
                    SUM(CORRECT_COMP_PCT5) AS RATED_PCT5, SUM(CORRECT_COMP_PCT6) AS RATED_PCT6, 
                    SUM(CORRECT_COMP_PCT7) AS RATED_PCT7, SUM(CORRECT_COMP_PCT8) AS RATED_PCT8, 
                    SUM(CORRECT_COMP_PCT9) AS RATED_PCT9, SUM(CORRECT_COMP_PCT10) AS RATED_PCT10, 
                    SUM(CORRECT_COMP_PCT11) AS RATED_PCT11, SUM(CORRECT_COMP_PCT12) AS RATED_PCT12, 
                    SUM(CORRECT_COMP_PCT13) AS RATED_PCT13
                INTO #weights2
                FROM #weights
                GROUP BY #weights.mukey
            SELECT #comp_temp2.mukey, #comp_temp2.cokey, #weights2.RATED_PCT1, #weights2.RATED_PCT2, 
                    #weights2.RATED_PCT3, #weights2.RATED_PCT4, #weights2.RATED_PCT5, #weights2.RATED_PCT6, 
                    #weights2.RATED_PCT7, #weights2.RATED_PCT8, #weights2.RATED_PCT9, #weights2.RATED_PCT10, 
                    #weights2.RATED_PCT11, #weights2.RATED_PCT12, #weights2.RATED_PCT13, 
                    SUM(CORRECT_COMP_PCT1 * DEPTH_WEIGHTED_AVERAGE1) AS COMP_WEIGHTED_AVERAGE1, 
                    SUM(CORRECT_COMP_PCT2 * DEPTH_WEIGHTED_AVERAGE2) AS COMP_WEIGHTED_AVERAGE2, 
                    SUM(CORRECT_COMP_PCT3 * DEPTH_WEIGHTED_AVERAGE3) AS COMP_WEIGHTED_AVERAGE3, 
                    SUM(CORRECT_COMP_PCT4 * DEPTH_WEIGHTED_AVERAGE4) AS COMP_WEIGHTED_AVERAGE4, 
                    SUM(CORRECT_COMP_PCT5 * DEPTH_WEIGHTED_AVERAGE5) AS COMP_WEIGHTED_AVERAGE5, 
                    SUM(CORRECT_COMP_PCT6 * DEPTH_WEIGHTED_AVERAGE6) AS COMP_WEIGHTED_AVERAGE6, 
                    SUM(CORRECT_COMP_PCT7 * DEPTH_WEIGHTED_AVERAGE7) AS COMP_WEIGHTED_AVERAGE7, 
                    SUM(CORRECT_COMP_PCT8 * DEPTH_WEIGHTED_AVERAGE8) AS COMP_WEIGHTED_AVERAGE8, 
                    SUM(CORRECT_COMP_PCT9 * DEPTH_WEIGHTED_AVERAGE9) AS COMP_WEIGHTED_AVERAGE9, 
                    SUM(CORRECT_COMP_PCT10 * DEPTH_WEIGHTED_AVERAGE10) AS COMP_WEIGHTED_AVERAGE10, 
                    SUM(CORRECT_COMP_PCT11 * DEPTH_WEIGHTED_AVERAGE11) AS COMP_WEIGHTED_AVERAGE11, 
                    SUM(CORRECT_COMP_PCT12 * DEPTH_WEIGHTED_AVERAGE12) AS COMP_WEIGHTED_AVERAGE12, 
                    SUM(CORRECT_COMP_PCT13 * DEPTH_WEIGHTED_AVERAGE13) AS COMP_WEIGHTED_AVERAGE13
                INTO #last_step
                FROM #comp_temp2
                INNER JOIN #weights2 ON #weights2.mukey = #comp_temp2.mukey
                    WHERE DEPTH_WEIGHTED_AVERAGE1 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE2 IS NOT NULL OR 
                        DEPTH_WEIGHTED_AVERAGE3 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE4 IS NOT NULL OR 
                        DEPTH_WEIGHTED_AVERAGE5 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE6 IS NOT NULL OR 
                        DEPTH_WEIGHTED_AVERAGE7 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE8 IS NOT NULL OR 
                        DEPTH_WEIGHTED_AVERAGE9 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE10 IS NOT NULL OR 
                        DEPTH_WEIGHTED_AVERAGE11 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE12 IS NOT NULL OR 
                        DEPTH_WEIGHTED_AVERAGE13 IS NOT NULL
                GROUP BY #comp_temp2.mukey, #comp_temp2.cokey, CORRECT_COMP_PCT1, CORRECT_COMP_PCT2, CORRECT_COMP_PCT3, 
                    CORRECT_COMP_PCT4, CORRECT_COMP_PCT5, CORRECT_COMP_PCT6, CORRECT_COMP_PCT7, CORRECT_COMP_PCT8, 
                    CORRECT_COMP_PCT9, CORRECT_COMP_PCT10, CORRECT_COMP_PCT11, CORRECT_COMP_PCT12, CORRECT_COMP_PCT13, 
                    #weights2.RATED_PCT1, #weights2.RATED_PCT2, #weights2.RATED_PCT3, #weights2.RATED_PCT4, 
                    #weights2.RATED_PCT5, #weights2.RATED_PCT6, #weights2.RATED_PCT7, #weights2.RATED_PCT8, 
                    #weights2.RATED_PCT9, #weights2.RATED_PCT10, #weights2.RATED_PCT11, #weights2.RATED_PCT12, 
                    #weights2.RATED_PCT13, DEPTH_WEIGHTED_AVERAGE1, DEPTH_WEIGHTED_AVERAGE2, DEPTH_WEIGHTED_AVERAGE3, 
                    DEPTH_WEIGHTED_AVERAGE4, DEPTH_WEIGHTED_AVERAGE5, 
                    DEPTH_WEIGHTED_AVERAGE6, DEPTH_WEIGHTED_AVERAGE7,
                    DEPTH_WEIGHTED_AVERAGE8, DEPTH_WEIGHTED_AVERAGE9, 
                    DEPTH_WEIGHTED_AVERAGE10, DEPTH_WEIGHTED_AVERAGE11, 
                    DEPTH_WEIGHTED_AVERAGE12, DEPTH_WEIGHTED_AVERAGE13
            SELECT #kitchensink.mukey, #last_step.cokey, areasymbol, musym, muname, #last_step.RATED_PCT1, 
                    #last_step.RATED_PCT2, #last_step.RATED_PCT3, #last_step.RATED_PCT4, #last_step.RATED_PCT5, 
                    #last_step.RATED_PCT6, #last_step.RATED_PCT7, #last_step.RATED_PCT8, #last_step.RATED_PCT9, 
                    #last_step.RATED_PCT10, #last_step.RATED_PCT11, #last_step.RATED_PCT12, #last_step.RATED_PCT13, 
                    CAST (SUM((CASE WHEN RATED_PCT1 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE1 END) / 
                        (CASE WHEN RATED_PCT1 = 0 THEN 1 ELSE RATED_PCT1 END)) OVER 
                        (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS ksat_l, 
                    CAST (SUM((CASE WHEN RATED_PCT2 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE2 END) / 
                        (CASE WHEN RATED_PCT2 = 0 THEN 1 ELSE RATED_PCT2 END)) OVER 
                        (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS ksat_r, 
                    CAST (SUM((CASE WHEN RATED_PCT3 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE3 END) / 
                        (CASE WHEN RATED_PCT3 = 0 THEN 1 ELSE RATED_PCT3 END)) 
                        OVER (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS ksat_h, 
                    CAST (SUM((CASE WHEN RATED_PCT4 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE4 END) / 
                        (CASE WHEN RATED_PCT4 = 0 THEN 1 ELSE RATED_PCT4 END)) 
                        OVER (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS wsatiated_l, 
                    CAST (SUM((CASE WHEN RATED_PCT5 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE5 END) / 
                        (CASE WHEN RATED_PCT5 = 0 THEN 1 ELSE RATED_PCT5 END)) 
                        OVER (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS wsatiated_r, 
                    CAST (SUM((CASE WHEN RATED_PCT6 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE6 END) / 
                        (CASE WHEN RATED_PCT6 = 0 THEN 1 ELSE RATED_PCT6 END)) 
                        OVER (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS wsatiated_h, 
                    CAST (SUM((CASE WHEN RATED_PCT7 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE7 END) / 
                        (CASE WHEN RATED_PCT7 = 0 THEN 1 ELSE RATED_PCT7 END)) 
                        OVER (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS dbovendry_l, 
                    CAST (SUM((CASE WHEN RATED_PCT8 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE8 END) / 
                        (CASE WHEN RATED_PCT8 = 0 THEN 1 ELSE RATED_PCT8 END)) 
                        OVER (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS dbovendry_r, 
                    CAST (SUM((CASE WHEN RATED_PCT9 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE9 END) / 
                        (CASE WHEN RATED_PCT9 = 0 THEN 1 ELSE RATED_PCT9 END)) 
                        OVER (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS dbovendry_h, 
                    CAST (SUM((CASE WHEN RATED_PCT10 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE10 END) / 
                        (CASE WHEN RATED_PCT10 = 0 THEN 1 ELSE RATED_PCT10 END)) 
                        OVER (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS partdensity, 
                    CAST (SUM((CASE WHEN RATED_PCT11 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE11 END) / 
                        (CASE WHEN RATED_PCT11 = 0 THEN 1 ELSE RATED_PCT11 END)) 
                        OVER (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS claytotal_r, 
                    CAST (SUM((CASE WHEN RATED_PCT12 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE12 END) / 
                        (CASE WHEN RATED_PCT12 = 0 THEN 1 ELSE RATED_PCT12 END)) 
                        OVER (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS silttotal_r, 
                    CAST (SUM((CASE WHEN RATED_PCT13 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE13 END) / 
                    (CASE WHEN RATED_PCT13 = 0 THEN 1 ELSE RATED_PCT13 END)) 
                    OVER (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS sandtotal_r
                INTO #last_step2
                FROM #last_step
                RIGHT OUTER JOIN #kitchensink ON #kitchensink.mukey = #last_step.mukey
                GROUP BY #kitchensink.areasymbol, #kitchensink.musym, #kitchensink.muname, #kitchensink.mukey, 
                    #last_step.RATED_PCT1, #last_step.RATED_PCT2, #last_step.RATED_PCT3, #last_step.RATED_PCT4, 
                    #last_step.RATED_PCT5, #last_step.RATED_PCT6, #last_step.RATED_PCT7, #last_step.RATED_PCT8, 
                    #last_step.RATED_PCT9, #last_step.RATED_PCT10, #last_step.RATED_PCT11, #last_step.RATED_PCT12, 
                    #last_step.RATED_PCT13, COMP_WEIGHTED_AVERAGE1, COMP_WEIGHTED_AVERAGE2, COMP_WEIGHTED_AVERAGE3, 
                    COMP_WEIGHTED_AVERAGE4, COMP_WEIGHTED_AVERAGE5, COMP_WEIGHTED_AVERAGE6, COMP_WEIGHTED_AVERAGE7, 
                    COMP_WEIGHTED_AVERAGE8, COMP_WEIGHTED_AVERAGE9, COMP_WEIGHTED_AVERAGE10, COMP_WEIGHTED_AVERAGE11, 
                    COMP_WEIGHTED_AVERAGE12, COMP_WEIGHTED_AVERAGE13, #last_step.cokey
                ORDER BY #kitchensink.mukey, #kitchensink.areasymbol, #kitchensink.musym, #kitchensink.muname
            SELECT #last_step2.areasymbol, #last_step2.musym, #last_step2.muname, #last_step2.mukey, 
                    #last_step2.ksat_l, #last_step2.ksat_r, #last_step2.ksat_h, #last_step2.wsatiated_l, 
                    #last_step2.wsatiated_r, #last_step2.wsatiated_h, #last_step2.dbovendry_l, 
                    #last_step2.dbovendry_r, #last_step2.dbovendry_h, #last_step2.partdensity, 
                    #last_step2.claytotal_r, #last_step2.silttotal_r, #last_step2.sandtotal_r
                FROM #last_step2
                LEFT OUTER JOIN #last_step ON #last_step.mukey = #last_step2.mukey
                GROUP BY #last_step2.areasymbol, #last_step2.musym, #last_step2.muname, #last_step2.mukey, 
                    #last_step2.ksat_l, #last_step2.ksat_r, #last_step2.ksat_h, #last_step2.wsatiated_l, 
                    #last_step2.wsatiated_r, #last_step2.wsatiated_h, #last_step2.dbovendry_l, 
                    #last_step2.dbovendry_r, #last_step2.dbovendry_h, #last_step2.partdensity, 
                    #last_step2.claytotal_r, #last_step2.silttotal_r, #last_step2.sandtotal_r
                ORDER BY #last_step2.mukey, #last_step2.areasymbol, #last_step2.musym, #last_step2.muname, 
                    #last_step2.ksat_l, #last_step2.ksat_r, #last_step2.ksat_h, #last_step2.wsatiated_l, 
                    #last_step2.wsatiated_r, #last_step2.wsatiated_h, #last_step2.dbovendry_l, 
                    #last_step2.dbovendry_r, #last_step2.dbovendry_h, #last_step2.partdensity, 
                    #last_step2.claytotal_r, #last_step2.silttotal_r, #last_step2.sandtotal_r""")
        elif method.lower() == "dominant component (numeric)":
            q = ("""
            SELECT areasymbol, musym, muname, mukey
                INTO #kitchensink
                FROM legend
                INNER JOIN mapunit ON mapunit.lkey = legend.lkey AND mapunit.mukey IN(""" + keys + """)
            SELECT mapunit.mukey, cokey, comppct_r, compkind, majcompflag,
                    SUM (comppct_r) OVER (PARTITION BY mapunit.mukey) AS SUM_COMP_PCT
                INTO #comp_temp
                FROM legend AS legend
                INNER JOIN mapunit ON mapunit.lkey = legend.lkey AND mapunit.mukey IN(""" + keys + """)
                INNER JOIN component ON component.mukey = mapunit.mukey AND component.compkind != 'Miscellaneous area'
                    AND component.cokey = (SELECT TOP 1 c2.cokey FROM component AS c2
                INNER JOIN mapunit AS mm1 ON c2.mukey = mm1.mukey AND c2.mukey = mapunit.mukey
                 AND c2.compkind != 'Miscellaneous area'
                ORDER BY c2.comppct_r DESC, c2.cokey)
            SELECT cokey, compkind, majcompflag, SUM_COMP_PCT,
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) / 
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT1, 
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) / 
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT2, 
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) / 
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT3, 
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) / 
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT4, 
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) / 
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT5, 
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) / 
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT6, 
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) / 
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT7, 
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) / 
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT8, 
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) / 
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT9, 
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) / 
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT10, 
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) / 
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT11, 
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) / 
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT12, 
                    CASE WHEN comppct_r = SUM_COMP_PCT THEN 1 ELSE CAST((#comp_temp.comppct_r) AS decimal(5,2)) / 
                        SUM_COMP_PCT END AS WEIGHTED_COMP_PCT13
                INTO #comp_temp3
                FROM #comp_temp
            SELECT mapunit.mukey, areasymbol, musym, muname, component.cokey AS cokey, chorizon.chkey/1 AS chkey, 
                    compname, compkind, hzname, hzdept_r, hzdepb_r, CASE WHEN hzdept_r < """
                 + tDep + " THEN " + tDep + """ ELSE hzdept_r END AS hzdept_r_ADJ,
                    CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep + """ ELSE hzdepb_r END AS hzdepb_r_ADJ,
                    CASE WHEN ksat_l is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep + " THEN " + tDep +
                 """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_ksat_l,
                    CASE WHEN ksat_r is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep + " THEN " + tDep +
                 """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_ksat_r,
                    CASE WHEN ksat_h is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep + " THEN " + tDep +
                 """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_ksat_h,
                    CASE WHEN wsatiated_l is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_wsatiated_l,
                    CASE WHEN wsatiated_r is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_wsatiated_r,
                    CASE WHEN wsatiated_h is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_wsatiated_h,
                    CASE WHEN dbovendry_l is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_dbovendry_l,
                    CASE WHEN dbovendry_r is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_dbovendry_r,
                    CASE WHEN dbovendry_h is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_dbovendry_h,
                    CASE WHEN partdensity is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_partdensity,
                    CASE WHEN claytotal_r is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_claytotal_r,
                    CASE WHEN silttotal_r is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_silttotal_r,
                    CASE WHEN sandtotal_r is NULL THEN NULL ELSE CAST (CASE WHEN hzdepb_r > """ + bDep +
                 " THEN " + bDep + """ ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ ELSE hzdept_r END AS decimal(5,2)) END AS thickness_wt_sandtotal_r, 
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN ksat_l is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN ksat_l is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) OVER 
                 (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_ksat_l,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN ksat_r is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN ksat_r is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) OVER 
                 (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_ksat_r,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN ksat_h is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN ksat_h is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) OVER 
                 (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_ksat_h,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN wsatiated_l is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN wsatiated_l is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) OVER
                 (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_wsatiated_l,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN wsatiated_r is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN wsatiated_r is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) OVER 
                 (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_wsatiated_r,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN wsatiated_h is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN wsatiated_h is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) OVER 
                 (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_wsatiated_h,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN dbovendry_l is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN dbovendry_l is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) OVER 
                 (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_dbovendry_l,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN dbovendry_r is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN dbovendry_r is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) OVER 
                 (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_dbovendry_r,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN dbovendry_h is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN dbovendry_h is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) OVER 
                 (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_dbovendry_h,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN partdensity is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN partdensity is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) OVER 
                 (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_partdensity,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN claytotal_r is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN claytotal_r is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) OVER 
                 (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_claytotal_r,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN silttotal_r is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN silttotal_r is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) OVER 
                 (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_silttotal_r,
                    CAST (SUM(CAST((CASE WHEN hzdepb_r > """ + bDep + " THEN " + bDep +
                 """ WHEN sandtotal_r is NULL THEN NULL ELSE hzdepb_r END - CASE WHEN hzdept_r < """ + tDep +
                 " THEN " + tDep + """ WHEN sandtotal_r is NULL THEN NULL ELSE hzdept_r END) AS decimal(5,2))) OVER 
                 (PARTITION BY component.cokey) AS decimal(5,2)) AS sum_thickness_sandtotal_r,
                    comppct_r, ksat_l, ksat_r, ksat_h, wsatiated_l, wsatiated_r, wsatiated_h, dbovendry_l, dbovendry_r,
                    dbovendry_h, partdensity, claytotal_r, silttotal_r, sandtotal_r
                INTO #main
                FROM legend
                INNER JOIN mapunit ON mapunit.lkey = legend.lkey AND mapunit.mukey IN(""" + keys + """)
                INNER JOIN component ON component.mukey = mapunit.mukey  AND component.compkind != 'Miscellaneous area'
                INNER JOIN chorizon ON chorizon.cokey = component.cokey AND hzdepb_r > """ + tDep +
                 """ AND hzdept_r <= """ + bDep + """
                    WHERE chorizon.hzdept_r IS NOT NULL
                ORDER BY mapunit.mukey, areasymbol, musym, muname, comppct_r DESC, cokey, hzdept_r, hzdepb_r
            SELECT #main.mukey, #main.areasymbol, #main.musym, #main.muname, #main.cokey, #main.chkey, #main.compname, 
                    #main.compkind, hzname, hzdept_r, hzdepb_r, hzdept_r_ADJ, hzdepb_r_ADJ, 
                    (CASE WHEN ISNULL(sum_thickness_ksat_l, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT1 END) AS 
                        CORRECT_COMP_PCT1, 
                    (CASE WHEN ISNULL(sum_thickness_ksat_r, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT2 END) AS 
                        CORRECT_COMP_PCT2, 
                    (CASE WHEN ISNULL(sum_thickness_ksat_h, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT3 END) AS 
                        CORRECT_COMP_PCT3, 
                    (CASE WHEN ISNULL(sum_thickness_wsatiated_l, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT4 END) AS 
                        CORRECT_COMP_PCT4, 
                    (CASE WHEN ISNULL(sum_thickness_wsatiated_r, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT5 END) AS 
                        CORRECT_COMP_PCT5, 
                    (CASE WHEN ISNULL(sum_thickness_wsatiated_h, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT6 END) AS 
                        CORRECT_COMP_PCT6, 
                    (CASE WHEN ISNULL(sum_thickness_dbovendry_l, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT7 END) AS 
                        CORRECT_COMP_PCT7, 
                    (CASE WHEN ISNULL(sum_thickness_dbovendry_r, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT8 END) AS 
                        CORRECT_COMP_PCT8, 
                    (CASE WHEN ISNULL(sum_thickness_dbovendry_h, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT9 END) AS 
                        CORRECT_COMP_PCT9, 
                    (CASE WHEN ISNULL(sum_thickness_partdensity, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT10 END) AS 
                        CORRECT_COMP_PCT10, 
                    (CASE WHEN ISNULL(sum_thickness_claytotal_r, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT11 END) AS 
                        CORRECT_COMP_PCT11, 
                    (CASE WHEN ISNULL(sum_thickness_silttotal_r, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT12 END) AS 
                        CORRECT_COMP_PCT12, 
                    (CASE WHEN ISNULL(sum_thickness_sandtotal_r, 0) = 0 THEN 0 ELSE WEIGHTED_COMP_PCT13 END) AS 
                        CORRECT_COMP_PCT13, 
                    ISNULL(thickness_wt_ksat_l, 0) AS thickness_wt_ksat_l, sum_thickness_ksat_l, 
                    ISNULL(thickness_wt_ksat_r, 0) AS thickness_wt_ksat_r, sum_thickness_ksat_r, 
                    ISNULL(thickness_wt_ksat_h, 0) AS thickness_wt_ksat_h, sum_thickness_ksat_h, 
                    ISNULL(thickness_wt_wsatiated_l, 0) AS thickness_wt_wsatiated_l, sum_thickness_wsatiated_l, 
                    ISNULL(thickness_wt_wsatiated_r, 0) AS thickness_wt_wsatiated_r, sum_thickness_wsatiated_r, 
                    ISNULL(thickness_wt_wsatiated_h, 0) AS thickness_wt_wsatiated_h, sum_thickness_wsatiated_h, 
                    ISNULL(thickness_wt_dbovendry_l, 0) AS thickness_wt_dbovendry_l, sum_thickness_dbovendry_l, 
                    ISNULL(thickness_wt_dbovendry_r, 0) AS thickness_wt_dbovendry_r, sum_thickness_dbovendry_r, 
                    ISNULL(thickness_wt_dbovendry_h, 0) AS thickness_wt_dbovendry_h, sum_thickness_dbovendry_h, 
                    ISNULL(thickness_wt_partdensity, 0) AS thickness_wt_partdensity, sum_thickness_partdensity, 
                    ISNULL(thickness_wt_claytotal_r, 0) AS thickness_wt_claytotal_r, sum_thickness_claytotal_r, 
                    ISNULL(thickness_wt_silttotal_r, 0) AS thickness_wt_silttotal_r, sum_thickness_silttotal_r, 
                    ISNULL(thickness_wt_sandtotal_r, 0) AS thickness_wt_sandtotal_r, sum_thickness_sandtotal_r, 
                    comppct_r, SUM_COMP_PCT, ksat_l, ksat_r, ksat_h, wsatiated_l, wsatiated_r, wsatiated_h, 
                    dbovendry_l, dbovendry_r, dbovendry_h, partdensity, claytotal_r, silttotal_r, sandtotal_r, 
                    ((thickness_wt_ksat_l / (CASE WHEN sum_thickness_ksat_l = 0 THEN 1 ELSE 
                        sum_thickness_ksat_l END)) * ksat_l) AS DEPTH_WEIGHTED_AVERAGE1, 
                    ((thickness_wt_ksat_r / (CASE WHEN sum_thickness_ksat_r = 0 THEN 1 ELSE 
                        sum_thickness_ksat_r END)) * ksat_r) AS DEPTH_WEIGHTED_AVERAGE2, 
                    ((thickness_wt_ksat_h / (CASE WHEN sum_thickness_ksat_h = 0 THEN 1 ELSE 
                        sum_thickness_ksat_h END)) * ksat_h) AS DEPTH_WEIGHTED_AVERAGE3, 
                    ((thickness_wt_wsatiated_l / (CASE WHEN sum_thickness_wsatiated_l = 0 THEN 1 ELSE 
                        sum_thickness_wsatiated_l END)) * wsatiated_l) AS DEPTH_WEIGHTED_AVERAGE4, 
                    ((thickness_wt_wsatiated_r / (CASE WHEN sum_thickness_wsatiated_r = 0 THEN 1 ELSE 
                        sum_thickness_wsatiated_r END)) * wsatiated_r) AS DEPTH_WEIGHTED_AVERAGE5, 
                    ((thickness_wt_wsatiated_h / (CASE WHEN sum_thickness_wsatiated_h = 0 THEN 1 ELSE 
                        sum_thickness_wsatiated_h END)) * wsatiated_h) AS DEPTH_WEIGHTED_AVERAGE6, 
                    ((thickness_wt_dbovendry_l / (CASE WHEN sum_thickness_dbovendry_l = 0 THEN 1 ELSE 
                        sum_thickness_dbovendry_l END)) * dbovendry_l) AS DEPTH_WEIGHTED_AVERAGE7, 
                    ((thickness_wt_dbovendry_r / (CASE WHEN sum_thickness_dbovendry_r = 0 THEN 1 ELSE 
                        sum_thickness_dbovendry_r END)) * dbovendry_r) AS DEPTH_WEIGHTED_AVERAGE8, 
                    ((thickness_wt_dbovendry_h / (CASE WHEN sum_thickness_dbovendry_h = 0 THEN 1 ELSE 
                        sum_thickness_dbovendry_h END)) * dbovendry_h) AS DEPTH_WEIGHTED_AVERAGE9, 
                    ((thickness_wt_partdensity / (CASE WHEN sum_thickness_partdensity = 0 THEN 1 ELSE 
                        sum_thickness_partdensity END)) * partdensity) AS DEPTH_WEIGHTED_AVERAGE10, 
                    ((thickness_wt_claytotal_r / (CASE WHEN sum_thickness_claytotal_r = 0 THEN 1 ELSE 
                        sum_thickness_claytotal_r END)) * claytotal_r) AS DEPTH_WEIGHTED_AVERAGE11, 
                    ((thickness_wt_silttotal_r / (CASE WHEN sum_thickness_silttotal_r = 0 THEN 1 ELSE 
                        sum_thickness_silttotal_r END)) * silttotal_r) AS DEPTH_WEIGHTED_AVERAGE12, 
                    ((thickness_wt_sandtotal_r / (CASE WHEN sum_thickness_sandtotal_r = 0 THEN 1 ELSE 
                        sum_thickness_sandtotal_r END)) * sandtotal_r) AS DEPTH_WEIGHTED_AVERAGE13
                INTO #comp_temp2
                FROM #main
                INNER JOIN #comp_temp3 ON #comp_temp3.cokey = #main.cokey
                ORDER BY #main.mukey, comppct_r DESC,
                    #main.cokey, #main.areasymbol, #main.musym, #main.muname, hzdept_r, hzdepb_r
            SELECT DISTINCT #comp_temp2.mukey, #comp_temp2.cokey, CORRECT_COMP_PCT1, CORRECT_COMP_PCT2, 
                    CORRECT_COMP_PCT3, CORRECT_COMP_PCT4, CORRECT_COMP_PCT5, CORRECT_COMP_PCT6, 
                    CORRECT_COMP_PCT7, CORRECT_COMP_PCT8, CORRECT_COMP_PCT9, CORRECT_COMP_PCT10, 
                    CORRECT_COMP_PCT11, CORRECT_COMP_PCT12, CORRECT_COMP_PCT13
                INTO #weights
                FROM #comp_temp2
                    WHERE DEPTH_WEIGHTED_AVERAGE1 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE2 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE3 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE4 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE5 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE6 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE7 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE8 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE9 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE10 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE11 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE12 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE13 IS NOT NULL
            SELECT DISTINCT #weights.mukey, SUM(CORRECT_COMP_PCT1) AS RATED_PCT1, SUM(CORRECT_COMP_PCT2) AS RATED_PCT2, 
                    SUM(CORRECT_COMP_PCT3) AS RATED_PCT3, SUM(CORRECT_COMP_PCT4) AS RATED_PCT4, 
                    SUM(CORRECT_COMP_PCT5) AS RATED_PCT5, SUM(CORRECT_COMP_PCT6) AS RATED_PCT6, 
                    SUM(CORRECT_COMP_PCT7) AS RATED_PCT7, SUM(CORRECT_COMP_PCT8) AS RATED_PCT8, 
                    SUM(CORRECT_COMP_PCT9) AS RATED_PCT9, SUM(CORRECT_COMP_PCT10) AS RATED_PCT10, 
                    SUM(CORRECT_COMP_PCT11) AS RATED_PCT11, SUM(CORRECT_COMP_PCT12) AS RATED_PCT12, 
                    SUM(CORRECT_COMP_PCT13) AS RATED_PCT13
                INTO #weights2
                FROM #weights
                GROUP BY #weights.mukey
            SELECT #comp_temp2.mukey, #comp_temp2.cokey, #weights2.RATED_PCT1, #weights2.RATED_PCT2, 
                    #weights2.RATED_PCT3, #weights2.RATED_PCT4, #weights2.RATED_PCT5, #weights2.RATED_PCT6, 
                    #weights2.RATED_PCT7, #weights2.RATED_PCT8, #weights2.RATED_PCT9, #weights2.RATED_PCT10, 
                    #weights2.RATED_PCT11, #weights2.RATED_PCT12, #weights2.RATED_PCT13, 
                    SUM(CORRECT_COMP_PCT1 * DEPTH_WEIGHTED_AVERAGE1) AS COMP_WEIGHTED_AVERAGE1, 
                    SUM(CORRECT_COMP_PCT2 * DEPTH_WEIGHTED_AVERAGE2) AS COMP_WEIGHTED_AVERAGE2, 
                    SUM(CORRECT_COMP_PCT3 * DEPTH_WEIGHTED_AVERAGE3) AS COMP_WEIGHTED_AVERAGE3, 
                    SUM(CORRECT_COMP_PCT4 * DEPTH_WEIGHTED_AVERAGE4) AS COMP_WEIGHTED_AVERAGE4, 
                    SUM(CORRECT_COMP_PCT5 * DEPTH_WEIGHTED_AVERAGE5) AS COMP_WEIGHTED_AVERAGE5, 
                    SUM(CORRECT_COMP_PCT6 * DEPTH_WEIGHTED_AVERAGE6) AS COMP_WEIGHTED_AVERAGE6, 
                    SUM(CORRECT_COMP_PCT7 * DEPTH_WEIGHTED_AVERAGE7) AS COMP_WEIGHTED_AVERAGE7, 
                    SUM(CORRECT_COMP_PCT8 * DEPTH_WEIGHTED_AVERAGE8) AS COMP_WEIGHTED_AVERAGE8, 
                    SUM(CORRECT_COMP_PCT9 * DEPTH_WEIGHTED_AVERAGE9) AS COMP_WEIGHTED_AVERAGE9, 
                    SUM(CORRECT_COMP_PCT10 * DEPTH_WEIGHTED_AVERAGE10) AS COMP_WEIGHTED_AVERAGE10, 
                    SUM(CORRECT_COMP_PCT11 * DEPTH_WEIGHTED_AVERAGE11) AS COMP_WEIGHTED_AVERAGE11, 
                    SUM(CORRECT_COMP_PCT12 * DEPTH_WEIGHTED_AVERAGE12) AS COMP_WEIGHTED_AVERAGE12, 
                    SUM(CORRECT_COMP_PCT13 * DEPTH_WEIGHTED_AVERAGE13) AS COMP_WEIGHTED_AVERAGE13
                INTO #last_step
                FROM #comp_temp2
                INNER JOIN #weights2 ON #weights2.mukey = #comp_temp2.mukey
                    WHERE DEPTH_WEIGHTED_AVERAGE1 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE2 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE3 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE4 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE5 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE6 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE7 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE8 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE9 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE10 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE11 IS NOT NULL OR DEPTH_WEIGHTED_AVERAGE12 IS NOT NULL OR 
                          DEPTH_WEIGHTED_AVERAGE13 IS NOT NULL
                GROUP BY #comp_temp2.mukey, #comp_temp2.cokey, CORRECT_COMP_PCT1, CORRECT_COMP_PCT2, CORRECT_COMP_PCT3, 
                    CORRECT_COMP_PCT4, CORRECT_COMP_PCT5, CORRECT_COMP_PCT6, CORRECT_COMP_PCT7, CORRECT_COMP_PCT8, 
                    CORRECT_COMP_PCT9, CORRECT_COMP_PCT10, CORRECT_COMP_PCT11, CORRECT_COMP_PCT12, CORRECT_COMP_PCT13, 
                    #weights2.RATED_PCT1, #weights2.RATED_PCT2, #weights2.RATED_PCT3, #weights2.RATED_PCT4, 
                    #weights2.RATED_PCT5, #weights2.RATED_PCT6, #weights2.RATED_PCT7, #weights2.RATED_PCT8, 
                    #weights2.RATED_PCT9, #weights2.RATED_PCT10, #weights2.RATED_PCT11, #weights2.RATED_PCT12, 
                    #weights2.RATED_PCT13, DEPTH_WEIGHTED_AVERAGE1, DEPTH_WEIGHTED_AVERAGE2, DEPTH_WEIGHTED_AVERAGE3, 
                    DEPTH_WEIGHTED_AVERAGE4, DEPTH_WEIGHTED_AVERAGE5, 
                    DEPTH_WEIGHTED_AVERAGE6, DEPTH_WEIGHTED_AVERAGE7, 
                    DEPTH_WEIGHTED_AVERAGE8, DEPTH_WEIGHTED_AVERAGE9, 
                    DEPTH_WEIGHTED_AVERAGE10, DEPTH_WEIGHTED_AVERAGE11, 
                    DEPTH_WEIGHTED_AVERAGE12, DEPTH_WEIGHTED_AVERAGE13
            SELECT #kitchensink.mukey, #last_step.cokey, areasymbol, musym, muname, #last_step.RATED_PCT1, 
                    #last_step.RATED_PCT2, #last_step.RATED_PCT3, #last_step.RATED_PCT4, #last_step.RATED_PCT5, 
                    #last_step.RATED_PCT6, #last_step.RATED_PCT7, #last_step.RATED_PCT8, #last_step.RATED_PCT9, 
                    #last_step.RATED_PCT10, #last_step.RATED_PCT11, #last_step.RATED_PCT12, #last_step.RATED_PCT13, 
                    CAST (SUM((CASE WHEN RATED_PCT1 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE1 END) / 
                        (CASE WHEN RATED_PCT1 = 0 THEN 1 ELSE RATED_PCT1 END)) OVER 
                        (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS ksat_l, 
                    CAST (SUM((CASE WHEN RATED_PCT2 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE2 END) / 
                        (CASE WHEN RATED_PCT2 = 0 THEN 1 ELSE RATED_PCT2 END)) OVER 
                        (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS ksat_r, 
                    CAST (SUM((CASE WHEN RATED_PCT3 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE3 END) / 
                        (CASE WHEN RATED_PCT3 = 0 THEN 1 ELSE RATED_PCT3 END)) OVER 
                        (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS ksat_h, 
                    CAST (SUM((CASE WHEN RATED_PCT4 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE4 END) / 
                        (CASE WHEN RATED_PCT4 = 0 THEN 1 ELSE RATED_PCT4 END)) OVER 
                        (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS wsatiated_l, 
                    CAST (SUM((CASE WHEN RATED_PCT5 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE5 END) / 
                        (CASE WHEN RATED_PCT5 = 0 THEN 1 ELSE RATED_PCT5 END)) OVER 
                        (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS wsatiated_r, 
                    CAST (SUM((CASE WHEN RATED_PCT6 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE6 END) / 
                        (CASE WHEN RATED_PCT6 = 0 THEN 1 ELSE RATED_PCT6 END)) OVER 
                        (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS wsatiated_h, 
                    CAST (SUM((CASE WHEN RATED_PCT7 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE7 END) / 
                        (CASE WHEN RATED_PCT7 = 0 THEN 1 ELSE RATED_PCT7 END)) OVER 
                        (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS dbovendry_l, 
                    CAST (SUM((CASE WHEN RATED_PCT8 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE8 END) / 
                        (CASE WHEN RATED_PCT8 = 0 THEN 1 ELSE RATED_PCT8 END)) OVER 
                        (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS dbovendry_r, 
                    CAST (SUM((CASE WHEN RATED_PCT9 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE9 END) / 
                        (CASE WHEN RATED_PCT9 = 0 THEN 1 ELSE RATED_PCT9 END)) OVER 
                        (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS dbovendry_h, 
                    CAST (SUM((CASE WHEN RATED_PCT10 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE10 END) / 
                        (CASE WHEN RATED_PCT10 = 0 THEN 1 ELSE RATED_PCT10 END)) OVER 
                        (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS partdensity, 
                    CAST (SUM((CASE WHEN RATED_PCT11 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE11 END) / 
                        (CASE WHEN RATED_PCT11 = 0 THEN 1 ELSE RATED_PCT11 END)) OVER 
                        (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS claytotal_r, 
                    CAST (SUM((CASE WHEN RATED_PCT12 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE12 END) / 
                        (CASE WHEN RATED_PCT12 = 0 THEN 1 ELSE RATED_PCT12 END)) OVER 
                        (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS silttotal_r, 
                    CAST (SUM((CASE WHEN RATED_PCT13 = 0 THEN NULL ELSE COMP_WEIGHTED_AVERAGE13 END) / 
                        (CASE WHEN RATED_PCT13 = 0 THEN 1 ELSE RATED_PCT13 END)) OVER 
                        (PARTITION BY #kitchensink.mukey) AS decimal(10,2)) AS sandtotal_r
                INTO #last_step2
                FROM #last_step
                RIGHT OUTER JOIN #kitchensink ON #kitchensink.mukey = #last_step.mukey
                GROUP BY #kitchensink.areasymbol, #kitchensink.musym, #kitchensink.muname, #kitchensink.mukey, 
                    #last_step.RATED_PCT1, #last_step.RATED_PCT2, #last_step.RATED_PCT3, #last_step.RATED_PCT4, 
                    #last_step.RATED_PCT5, #last_step.RATED_PCT6, #last_step.RATED_PCT7, #last_step.RATED_PCT8, 
                    #last_step.RATED_PCT9, #last_step.RATED_PCT10, #last_step.RATED_PCT11, #last_step.RATED_PCT12, 
                    #last_step.RATED_PCT13, COMP_WEIGHTED_AVERAGE1, COMP_WEIGHTED_AVERAGE2, COMP_WEIGHTED_AVERAGE3, 
                    COMP_WEIGHTED_AVERAGE4, COMP_WEIGHTED_AVERAGE5, COMP_WEIGHTED_AVERAGE6, COMP_WEIGHTED_AVERAGE7, 
                    COMP_WEIGHTED_AVERAGE8, COMP_WEIGHTED_AVERAGE9, COMP_WEIGHTED_AVERAGE10, COMP_WEIGHTED_AVERAGE11, 
                    COMP_WEIGHTED_AVERAGE12, COMP_WEIGHTED_AVERAGE13, #last_step.cokey
                ORDER BY #kitchensink.mukey, #kitchensink.areasymbol, #kitchensink.musym, #kitchensink.muname
            SELECT #last_step2.areasymbol, #last_step2.musym, #last_step2.muname, #last_step2.mukey, 
                    #last_step2.ksat_l, #last_step2.ksat_r, #last_step2.ksat_h, #last_step2.wsatiated_l, 
                    #last_step2.wsatiated_r, #last_step2.wsatiated_h, #last_step2.dbovendry_l, 
                    #last_step2.dbovendry_r, #last_step2.dbovendry_h, #last_step2.partdensity, 
                    #last_step2.claytotal_r, #last_step2.silttotal_r, #last_step2.sandtotal_r
                FROM #last_step2
                LEFT OUTER JOIN #last_step ON #last_step.mukey = #last_step2.mukey
                GROUP BY #last_step2.areasymbol, #last_step2.musym, #last_step2.muname, #last_step2.mukey, 
                    #last_step2.ksat_l, #last_step2.ksat_r, #last_step2.ksat_h, #last_step2.wsatiated_l, 
                    #last_step2.wsatiated_r, #last_step2.wsatiated_h, #last_step2.dbovendry_l, 
                    #last_step2.dbovendry_r, #last_step2.dbovendry_h, #last_step2.partdensity, 
                    #last_step2.claytotal_r, #last_step2.silttotal_r, #last_step2.sandtotal_r
                ORDER BY #last_step2.mukey, #last_step2.areasymbol, #last_step2.musym, #last_step2.muname, 
                    #last_step2.ksat_l, #last_step2.ksat_r, #last_step2.ksat_h, #last_step2.wsatiated_l, 
                    #last_step2.wsatiated_r, #last_step2.wsatiated_h, #last_step2.dbovendry_l, 
                    #last_step2.dbovendry_r, #last_step2.dbovendry_h, #last_step2.partdensity, 
                    #last_step2.claytotal_r, #last_step2.silttotal_r, #last_step2.sandtotal_r""")
        elif method.lower() == "max":
            q = ("""
            SELECT mapunit.mukey, areasymbol, musym, muname, 
                (SELECT TOP 1 MAX(chm1.ksat_l) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS ksat_l, 
                (SELECT TOP 1 MAX(chm1.ksat_r) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS ksat_r, 
                (SELECT TOP 1 MAX(chm1.ksat_h) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS ksat_h, 
                (SELECT TOP 1 MAX(chm1.wsatiated_l) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS wsatiated_l, 
                (SELECT TOP 1 MAX(chm1.wsatiated_r) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS wsatiated_r, 
                (SELECT TOP 1 MAX(chm1.wsatiated_h) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS wsatiated_h, 
                (SELECT TOP 1 MAX(chm1.dbovendry_l) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS dbovendry_l, 
                (SELECT TOP 1 MAX(chm1.dbovendry_r) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS dbovendry_r, 
                (SELECT TOP 1 MAX(chm1.dbovendry_h) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS dbovendry_h, 
                (SELECT TOP 1 MAX(chm1.partdensity) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS partdensity,
                (SELECT TOP 1 MAX(chm1.claytotal_r) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS claytotal_r, 
                (SELECT TOP 1 MAX(chm1.silttotal_r) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS silttotal_r, 
                (SELECT TOP 1 MAX(chm1.sandtotal_r) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS sandtotal_r
                INTO #funagg
                FROM legend
                INNER JOIN mapunit ON mapunit.lkey = legend.lkey AND mapunit.mukey IN(""" + keys + """)
                LEFT JOIN component ON component.mukey = mapunit.mukey AND component.majcompflag = 'Yes' 
                    AND component.compkind != 'Miscellaneous area'
            SELECT areasymbol, musym, muname, mukey, MAX(ksat_l) AS ksat_l, MAX(ksat_r) AS ksat_r, 
                    MAX(ksat_h) AS ksat_h, MAX(wsatiated_l) AS wsatiated_l, MAX(wsatiated_r) AS wsatiated_r,
                    MAX(wsatiated_h) AS wsatiated_h, MAX(dbovendry_l) AS dbovendry_l, MAX(dbovendry_r) AS dbovendry_r,
                    MAX(dbovendry_h) AS dbovendry_h, MAX(partdensity) AS partdensity, MAX(claytotal_r) AS claytotal_r,
                    MAX(silttotal_r) AS silttotal_r, MAX(sandtotal_r) AS sandtotal_r FROM #funagg
                GROUP BY areasymbol, musym, muname, mukey""")
        elif method.lower() == "min":
            q = ("""
            SELECT mapunit.mukey, areasymbol, musym, muname, 
                (SELECT TOP 1 MIN(chm1.ksat_l) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS ksat_l, 
                (SELECT TOP 1 MIN(chm1.ksat_r) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS ksat_r, 
                (SELECT TOP 1 MIN(chm1.ksat_h) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS ksat_h, 
                (SELECT TOP 1 MIN(chm1.wsatiated_l) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS wsatiated_l, 
                (SELECT TOP 1 MIN(chm1.wsatiated_r) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS wsatiated_r, 
                (SELECT TOP 1 MIN(chm1.wsatiated_h) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS wsatiated_h, 
                (SELECT TOP 1 MIN(chm1.dbovendry_l) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS dbovendry_l, 
                (SELECT TOP 1 MIN(chm1.dbovendry_r) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS dbovendry_r, 
                (SELECT TOP 1 MIN(chm1.dbovendry_h) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                    WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS dbovendry_h, 
                (SELECT TOP 1 MIN(chm1.partdensity) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS partdensity, 
                (SELECT TOP 1 MIN(chm1.claytotal_r) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS claytotal_r, 
                (SELECT TOP 1 MIN(chm1.silttotal_r) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS silttotal_r, 
                (SELECT TOP 1 MIN(chm1.sandtotal_r) FROM component AS cm1 INNER JOIN chorizon AS chm1 ON 
                 cm1.cokey = chm1.cokey AND cm1.cokey = component.cokey AND component.compkind != 'Miscellaneous area'
                 WHERE chm1.hzdept_r BETWEEN """ + tDep + " AND " + bDep + """ OR chm1.hzdepb_r BETWEEN """ + tDep +
                 " AND " + bDep + """ ) AS sandtotal_r
                INTO #funagg
                FROM legend
                INNER JOIN mapunit ON mapunit.lkey = legend.lkey AND mapunit.mukey IN(""" + keys + """)
                LEFT JOIN component ON component.mukey = mapunit.mukey  AND component.majcompflag = 'Yes' 
                        AND component.compkind != 'Miscellaneous area'
            SELECT areasymbol, musym, muname, mukey, MIN(ksat_l) AS ksat_l, MIN(ksat_r) AS ksat_r, 
                    MIN(ksat_h) AS ksat_h, MIN(wsatiated_l) AS wsatiated_l, MIN(wsatiated_r) AS wsatiated_r,
                    MIN(wsatiated_h) AS wsatiated_h, MIN(dbovendry_l) AS dbovendry_l, MIN(dbovendry_r) AS dbovendry_r,
                    MIN(dbovendry_h) AS dbovendry_h, MIN(partdensity) AS partdensity, MIN(claytotal_r) AS claytotal_r,
                    MIN(silttotal_r) AS silttotal_r, MIN(sandtotal_r) AS sandtotal_r FROM #funagg
                GROUP BY areasymbol, musym, muname, mukey""")
        else:
            q = """None"""
        return q

    @staticmethod
    def fetch_ssurgodata(q, meta=False):
        try:
            theURL = "https://sdmdataaccess.nrcs.usda.gov"
            theURL = theURL + "/Tabular/SDMTabularService/post.rest"

            rDic = {}

            if meta:
                rDic["format"] = "JSON+COLUMNNAME+METADATA"
            else:
                rDic["format"] = "JSON+COLUMNNAME"

            rDic["query"] = q
            rData = json.dumps(rDic)

            results = requests.post(data=rData, url=theURL)
            qData = results.json()

            cols = qData.get('Table')[0]
            data = qData.get('Table')[1:]

            df = pd.DataFrame(data, columns=cols)
            return df

        except (exceptions.InvalidURL, exceptions.HTTPError, exceptions.Timeout):
            arcpy.AddError('Requests error, Soil Data Access offline??')

        except JSONDecodeError as err:
            arcpy.AddError('JSON Decode error: ' + err.msg)
            arcpy.AddError('This usually happens when the extent is too large, try smaller extent.')

        except Exception as e:
            arcpy.AddError('Unhandled error')
            arcpy.AddError(e)

    @staticmethod
    def is_file_path(input_string):
        return os.path.sep in input_string


# ======================================================================
# Main program for debugging
if __name__ == '__main__':
    arcpy.env.workspace = "C:\\Users\\Wei\\OneDrive - Florida State University\\Desktop\\lakeshore_example\\OriginalData"
    # arcpy.env.workspace = "E:\\lakeshore_example\\lakeshore_example"
    area = os.path.join(arcpy.env.workspace, "clip.shp")
    pcs = arcpy.SpatialReference(26917)
    top = 0
    bot = 200
    method = "weighted average"
    cell_size = 10

    hydr = os.path.join(arcpy.env.workspace, "hydr")
    poro = os.path.join(arcpy.env.workspace, "poro")
    solt = os.path.join(arcpy.env.workspace, "solt")
    spat = os.path.join(arcpy.env.workspace, "spat.shp")

    start_time = time.time()

    arcpy.AddMessage("starting geoprocessing")
    PP = Preprocessing(area, pcs, top, bot, method, cell_size,
                       hydr, poro, solt, spat)
    PP.main()
    end_time = time.time()
    print("Time elapsed: {} seconds".format(end_time - start_time))
    print("Tests successful!")

"""Create a .ttl file for Maine's aquifers from a .shp file containing fixed aquifer geometries

Under ### INPUT Filenames ###, define
    the name (and path) of the input .shp file
    the name (and path) of the input s2 cells .shp file
Under ### OUTPUT Filenames ###, define
    the name (and path) of the output .shp file (for the processed aquifer layer)
    the name (and path) of the output .ttl file

Required:
    * geopandas
    * pandas
    * shapely (LineString, Point, and Polygon)
    * rdflib (Graph and Literal)
    * rdflib.namespace (GEO, PROV, RDF, RDFS, and XSD)
    * variable (a local .py file with a dictionary of project namespaces)

Functions:
    * namestr - takes an object and returns a string version of its variable name
    * print_gdf_info - takes a GeoDataFrame (gdf) and prints its variable name, column names, EPSG value,
                       and size to the console
    * read_shp_2_gdf - takes a .shp file and returns a gdf
    * filter_flow_rates - takes a gdf, keeps rows with only specified flowrate values, and returns a gdf
    * dissolve_on_attribute - takes a gdf and an attribute name, dissolves on the attribute, and returns a gdf
    * add_index_as_column - takes a gdf and an attribute name, creates a new column from the index, and returns a gdf
    * convert_crs - takes a gdf and an EPSG value and returns a gdf
    * add_area_length - takes a gdf and returns a gdf with feature area and length appended
    * buffer_polygons - takes a gdf and a buffer distance and returns a gdf with buffered features
    * dissolve_spatially - takes a gdf and an EPSG value, dissolves all features spatially, explodes the dissolve,
                           assigns the EPSG (this must be the same as the input gdf), and returns a gdf
    * spatial_join_ids - takes two gdfs and a common attribute name, does a left spatial join on the two gdfs,
                         renames the index from the right gdf, and returns a gdf
    * create_id_dict - takes a gdf and creates a dictionary of dissolved ids to lists of original ids
    * process_aquifers_shp2shp - takes a .shp file, processes it, saves the result as a .shp file, and returns a
                                 dictionary of dissolved ids to lists of original ids
    * initial_kg - takes a dictionary of prefixes and returns an empty RDFLib knowledge graph
    * build_iris - takes an id value and a dictionary of prefixes and returns IRIs for an aquifer and its geometry
    * process_aquifers_shp2ttl - takes two .shp files (aquifers and S2 cells), an output file name, and a dictionary
                                 of dissolved ids to lists of original ids, and creates and saves a .ttl file
"""

import geopandas as gpd
import pandas as pd
from shapely import LineString, Point, Polygon
from rdflib import Graph, Literal
from rdflib.namespace import GEO, OWL, PROV, RDF, RDFS, XSD

import logging
import time
import datetime

import sys
import os

# Modify the system path to find variable.py
sys.path.insert(1, 'G:/My Drive/UMaine Docs from Laptop/SAWGraph/Data Sources')
from variable import _PREFIX, find_s2_intersects_geom

# Set the current directory to this file's directory
os.chdir('G:/My Drive/UMaine Docs from Laptop/SAWGraph/Data Sources/Groundwater')

### INPUT Filenames ###
# mgs_aquifer_shp_path: This is a fixed version of the file from the Maine Geological Survey (MGS)
# s2_file: Level 13 S2 cells that overlap/are within Maine
mgs_aquifer_shp_path = '../Geospatial/Maine_Aquifers-shp/Maine_Aquifers-fixed.shp'
s2_file = '../Geospatial/s2l13_23/s2l13_23.shp'

### OUTPUT Filenames ###
# mgs_aqs_shp_outfile: the final saved output from the .shp processing steps; also the input to triplification
# ttl_file: the resulting (output) .ttl file
mgs_aqs_shp_outfile = '../Geospatial/Maine_Aquifers-shp/Maine_Aquifers-processed.shp'
ttl_file = 'me_mgs_aquifers.ttl'

### VARIABLES ###
# When True, prints column names, epsg value, and size (rows & columns) for each processing step GeoDataFrame
# When False, only a brief statement is printed acknowledging a step is complete
diagnostics = False
# flow_rates is a list of 'SYMBOLOGY' values to keep in the processed aquifer file
# dissolve_attr_1 is the id column for aquifers from MGS
# buffer is used to create overlap among nearly adjacent aquifers to connect them
# dissolve_attr_1 is the id column for the connected aquifers
flow_rates = ['10-50 GPM', '>50 GPM']
dissolve_attr_1 = 'AQUIFERID'
dissolve_attr_2 = 'saw_id'
buffer = 100  # in meters
# epsg_working is an equidistant CRS for working with buffers
# epsg_final is WGS 84, the default CRS for GeoSPARQL
epsg_working = 26919  # UTM zone 19N for Maine
epsg_final = 4326
# aquifer id values are padded with leading zeros so they are all a fixed length
# max_id_length should be set to the maximum expected length of an id value (or longer)
max_id_length = 4

logname = 'log.txt'
logging.basicConfig(filename=logname,
                    filemode='w',
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def namestr(obj, namespace):
    """Return the name of an object

    :param obj: A python object
    :param namespace: The object's namespace [globals() is the typical choice here]
    :return: The object's name; i.e., for some variable storing some object this returns the variable name
    """
    return [name for name in namespace if namespace[name] is obj][0]


def log_gdf_info(gdf, step):
    """Log diagnostic information for a GeoDataFrame

    :param gdf: a GeoDataFrame
    :param step: a text string describing the current processing step
    """
    # print(f'Dataframe: {namestr(gdf, globals())}')
    logger.info(f'Step: {step}')
    logger.info(f'Columns: {gdf.columns}')
    logger.info(f'EPSG: {gdf.crs.to_epsg()}')
    logger.info(f'Rows: {gdf.shape[0]}; Columns: {gdf.shape[1]}\n')


def read_shp_2_gdf(path, diag):
    """Reads a .shp file and converts it to a GeoDataFrame

    :param path: a path to a .shp file
    :param diag: if True the function logs more detailed info than when it is False
    :return: a GeoDataFrame
    """
    gdfout = gpd.read_file(path)
    log_gdf_info(gdfout, 'Shapefile imported') if diag else logger.info('Shapefile imported')
    gdfout.drop(columns=['fid',
                         'QUADNAME',
                         'COMPID',
                         'ATYPE',
                         'DRAW',
                         'SOURCE',
                         'COMMENTS',
                         'AQUIFERHIS',
                         'PUBLISH_DA',
                         'created_us',
                         'created_da',
                         'last_edite',
                         'last_edi_1',
                         'Shape__Are',
                         'Shape__Len'], inplace=True)
    log_gdf_info(gdfout, 'Extra columns dropped') if diag else logger.info('Extra columns dropped')
    return gdfout


def filter_flow_rates(gdfin, rates, diag):
    """Filters a GeoDataFrame based on specified aquifer flow rates

    :param gdfin: a GeoDataFrame
    :param rates: a list of strings representing desired aquifer flow rates
    :param diag: if True the function logs more detailed info than when it is False
    :return: a GeoDataFrame
    """
    gdfout = gdfin[gdfin['SYMBOLOGY'].isin(rates)]
    log_gdf_info(gdfout, 'Flow rate filter') if diag else logger.info('Flow rate filter applied')
    return gdfout


def dissolve_on_attribute(gdfin, attr, diag):
    """Dissolves a GeoDataFrame based on a given attribute

    :param gdfin: a GeoDataFrame
    :param attr: the attribute with values for dissolving on
    :param diag: if True the function logs more detailed info than when it is False
    :return: a GeoDataFrame
    """
    gdfout = gdfin.dissolve(by=attr)
    log_gdf_info(gdfout, f'Dissolve on {attr}') if diag else logger.info(f'Polygons dissolved on {attr}')
    return gdfout


def add_index_as_column(gdf, attr, diag):
    """Creates a new column in a GeoDataFrame with the values of the index column

    :param gdf: a GeoDataFrame
    :param attr: the name for the new column
    :param diag: if True the function logs more detailed info than when it is False
    :return: a GeoDataFrame
    """
    gdf[attr] = gdf.index
    log_gdf_info(gdf, f'Add index as column {attr}') if diag else logger.info(f'Index added as column {attr}')
    return gdf


def convert_crs(gdfin, epsg, diag):
    """Convert a GeoDataFrame to a desired EPSG

    :param gdfin: a GeoDataFrame
    :param epsg: the new EPSG value
    :param diag: if True the function logs more detailed info than when it is False
    :return: a GeoDataFrame
    """
    gdfout = gdfin.to_crs(epsg=epsg)
    log_gdf_info(gdfout, f'Convert to EPSG {epsg}') if diag else logger.info(f'CRS changed to EPSG {epsg}')
    return gdfout


def add_area_length(gdf, diag):
    """Adds area and length columns to a GeoDataFrame of polygons

    :param gdf: a GeoDataFrame
    :param diag: if True the function logs more detailed info than when it is False
    :return: a GeoDataFrame
    """
    gdf['ShapeArea'] = gdf.area
    gdf['ShapeLen'] = gdf.length
    log_gdf_info(gdf, 'Add ShapeArea and ShapeLen columns') if diag else logger.info(
        f'Added ShapeArea and ShapeLen columns')
    return gdf


def buffer_polygons(gdf, buff, diag):
    """Buffers the polygons in a GeoDataFrame

    :param gdf: a GeoDataFrame
    :param buff: buffer distance in meters
    :param diag: if True the function logs more detailed info than when it is False
    :return: a GeoDataFrame
    """
    gdf['geometry'] = gdf.geometry.buffer(buff)
    log_gdf_info(gdf, f'Buffer polygons by {buff} meters') if diag else logger.info(
        f'Polygon layer buffered by {buff} meters')
    return gdf


def dissolve_spatially(gdfin, epsg, diag):
    """Performs a spatial dissolve on a GeoDataFrame of polygons

    :param gdfin: a GeoDataFrame
    :param epsg: the EPSG of the input GeoDataFrame (it is lost during the spatial dissolve and must be reset)
    :param diag: if True the function logs more detailed info than when it is False
    :return: a GeoDataFrame
    """
    gdfout = gpd.GeoDataFrame(geometry=[gdfin.unary_union]).explode(index_parts=False).reset_index()
    gdfout.set_crs(epsg=epsg, inplace=True)
    gdfout.index += 1
    log_gdf_info(gdfout, 'Spatial dissolve') if diag else logger.info(
        f'Polygon layer dissolved spatially, CRS set to EPSG {epsg}')
    return gdfout


def spatial_join_ids(gdf_left, gdf_right, idname, diag):
    """Takes two GeoDataFrames and does a left spatial join based on their intersections

    :param gdf_left: a GeoDataFrame
    :param gdf_right: a GeoDataFrame
    :param idname: name for the index column from the right GeoDataFrame
    :param diag: if True the function logs more detailed info than when it is False
    :return: a GeoDataFrame
    """
    gdfout = gdf_left.sjoin(gdf_right, how='left', predicate='intersects')
    gdfout.drop(columns=['index'], inplace=True)
    gdfout.rename(columns={'index_right': idname}, inplace=True)
    gdfout[idname] = pd.to_numeric(gdfout[idname]).astype('Int64')
    log_gdf_info(gdfout, f'Spatially join {idname}') if diag else logger.info(
        f'Spatial join of new {idname} attribute complete')
    return gdfout


def create_id_dict(gdf):
    """Essentially connects original aquifer ids to dissolved aquifer ids

    :param gdf: a GeoDataFrame
    :return: a dictionary
    """
    dic = {}
    for row in gdf.itertuples():
        if row.saw_id not in dic.keys():
            dic[row.saw_id] = [row.AQUIFERID]
        else:
            dic[row.saw_id].append(row.AQUIFERID)
    logger.info('Dictionary of new versus old IDs created')
    return dic


def process_aquifers_shp2shp(infile, outfile, diag):
    """A function that carries out a complete sequence of geospatial processing on a .shp file
       The result is saved as a .shp file

    :param infile: a path to a .shp file
    :param outfile: a path and name for the resulting .shp file
    :param diag: if True the called functions log more detailed info than when it is False
    :return: a dictionary
    """
    logger.info('\n\nBEGIN PROCESSING THE AQUIFERS SHAPEFILE')
    gdf_initial = read_shp_2_gdf(infile, diag)
    gdf_filtered = filter_flow_rates(gdf_initial, flow_rates, diag)
    gdf_dissolve_1 = dissolve_on_attribute(gdf_filtered, dissolve_attr_1, diag)
    gdf_index2column = add_index_as_column(gdf_dissolve_1, dissolve_attr_1, diag)
    gdf_new_crs = convert_crs(gdf_index2column, epsg_working, diag)
    gdf_with_area_len = add_area_length(gdf_new_crs, diag)
    gdf_buffered = buffer_polygons(gdf_with_area_len, buffer, diag)
    gdf_dissolved_buffers = dissolve_spatially(gdf_buffered, epsg_working, diag)
    gdf_joined = spatial_join_ids(gdf_new_crs, gdf_dissolved_buffers, dissolve_attr_2, diag)
    gdf_dissolve_2 = dissolve_on_attribute(gdf_joined, dissolve_attr_2, diag)
    gdf_final = convert_crs(gdf_dissolve_2, epsg_final, diag)
    gdf_final.to_file(outfile)
    logger.info('AQUIFER SHAPEFILE PROCESSING COMPLETE')
    return create_id_dict(gdf_joined)


def initial_kg(_PREFIX):
    """Create an empty knowledge graph with project namespaces

    :param _PREFIX: a dictionary of project namespaces
    :return: an RDFLib graph
    """
    graph = Graph()
    for prefix in _PREFIX:
        graph.bind(prefix, _PREFIX[prefix])
    logger.info('Intializing the knowledge graph')
    return graph


def build_iris(aqid, _PREFIX):
    """Create IRIs for an aquifer and its geometry

    :param aqid: The aquifer id value for an aquifer
    :param _PREFIX: a dictionary of prefixes
    :return: a tuple with the two IRIs
    """
    return (_PREFIX["me_mgs_data"]['d.MGS-Aquifer.' + str(aqid).zfill(max_id_length)],
            _PREFIX["me_mgs_data"]['d.MGS-Aquifer.Geometry.' + str(aqid).zfill(max_id_length)])


def process_aquifers_shp2ttl(infile, s2file, outfile, ids_dict):
    """Triplifies the aquifer data in a .shp file and saves the result as a .ttl file

    :param infile: a processed .shp file with aquifer data
    :param s2file: Level 13 S2 cells for Maine
    :param outfile: the path and name for the .ttl file
    :param ids_dict: a a dictionary of dissolved ids to lists of original ids
    :return:
    """
    logger.info('BEGIN TRIPLIFYING THE PROCESSED AQUIFERS')
    logger.info('Loading the shapefiles')
    gdf_aquifers = gpd.read_file(infile)
    gdf_s2l13 = gpd.read_file(s2file)
    kg = initial_kg(_PREFIX)
    count = 1
    n = len(gdf_aquifers.index)
    logger.info('Creating the triples')
    for row in gdf_aquifers.itertuples():
        aquiferiri, polyiri = build_iris(row.saw_id, _PREFIX)
        kg.add((aquiferiri, RDF.type, _PREFIX['gwml']['GW_Aquifer']))
        kg.add((aquiferiri, _PREFIX['me_mgs']['SAWidAquifer'], Literal(row.saw_id, datatype=XSD.string)))
        kg.add((aquiferiri, GEO.hasGeometry, polyiri))
        kg.add((aquiferiri, GEO['hasDefaultGeometry'], polyiri))
        kg.add((aquiferiri, PROV.hadPrimarySource, _PREFIX['me_mgs']['MGS']))
        comment = 'Original MGS IDs:'
        for aqid in ids_dict[row.saw_id]:
            comment += ' ' + str(aqid)
        kg.add((aquiferiri, RDFS.comment, Literal(comment, datatype=XSD.string)))
        kg.add((polyiri, GEO.asWKT, Literal(row.geometry, datatype=GEO.wktLiteral)))
        kg.add((polyiri, RDF.type, GEO.Geometry))
        kg.add((polyiri, RDF.type, _PREFIX['sf']['MultiPolygon']))

        s2within, s2overlaps = find_s2_intersects_geom(row.geometry, gdf_s2l13)
        for s2 in s2within:
            kg.add((_PREFIX["kwgr"]['s2.level13.' + s2], _PREFIX["kwg-ont"]['sfWithin'], aquiferiri))
        for s2 in s2overlaps:
            kg.add((_PREFIX["kwgr"]['s2.level13.' + s2], _PREFIX["kwg-ont"]['sfOverlaps'], aquiferiri))

        print(f'Processing row {count:4} of {n} : SAWidAquifer {str(row.saw_id).zfill(max_id_length):5}',
              end='\r',
              flush=True)
        count += 1
    kg.serialize(outfile, format='turtle')
    logger.info('TRIPLIFYING COMPLETE AND .ttl FILE CREATED')


if __name__ == '__main__':
    start_time = time.time()
    ids = process_aquifers_shp2shp(mgs_aquifer_shp_path, mgs_aqs_shp_outfile, diagnostics)
    process_aquifers_shp2ttl(mgs_aqs_shp_outfile, s2_file, ttl_file, ids)
    logger.info(f'Runtime: {str(datetime.timedelta(seconds=time.time() - start_time))} HMS')
    print(f'Runtime: {str(datetime.timedelta(seconds=time.time() - start_time))} HMS')

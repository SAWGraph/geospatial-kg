"""Create a .ttl file for Maine's NHD water bodies from a .shp file

Under ### INPUT Filenames ###, define
    the name (and path) of the input .shp file
    the name (and path) of the input s2 cells .shp file
Under ### OUTPUT Filename ###, define
    the name (and path) of the output .ttl file

Required:
    * geopandas
    * shapely (LineString, Point, and Polygon)
    * rdflib (Graph and Literal)
    * rdflib.namespace (GEO, PROV, RDF, RDFS, and XSD)
    * variable (a local .py file with a dictionary of project namespaces)

Functions:
    * initial_kg - takes a dictionary of prefixes and returns an empty RDFLib knowledge graph
    * build_iris - takes an id value and a dictionary of prefixes and returns IRIs for a waterbody and its geometry
    * process_aquifers_shp2ttl - takes two .shp files (aquifers and S2 cells), an output file name, and a dictionary
                                 of dissolved ids to lists of original ids, and creates and saves a .ttl file
"""

import geopandas as gpd
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
os.chdir('G:/My Drive/UMaine Docs from Laptop/SAWGraph/Data Sources/Surface Water')

### INPUT Filenames ###
# nhd_waterbody_shp_file: Region 1 waterbodies (most of New England including all of Maine)
# s2_file: Level 13 S2 cells that overlap/are within Maine
nhd_waterbody_shp_file = '../Geospatial/NE_01_NHDSnapshot/NHDWaterbody.shp'
s2_file = '../Geospatial/s2l13_23/s2l13_23.shp'

### OUTPUT Filename ###
# ttl_file: the resulting (output) .ttl file
ttl_file = 'me_nhd_waterbody.ttl'

logname = 'log.txt'
logging.basicConfig(filename=logname,
                    filemode='w',
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


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


def build_iris(cid, _PREFIX):
    """Create IRIs for a waterbody and its geometry

    This varies from Geoconnex notation which currently contains no waterbodies beyond mainstems
        They have a mainstem URI; e.g., https://geoconnex.us/ref/mainstems/######
        The connected geometry is a blank node that connects to the geo:asWKT object

    :param cid: The COMID value for a waterbody
    :return: a tuple with the two IRIs
    """
    return _PREFIX["gcx-cid"][str(cid)], _PREFIX["gcx-cid"][str(cid) + '/Geometry']


def process_waterbodies_shp2ttl(infile, s2file, outfile):
    """Triplifies the waterbody data in a .shp file and saves the result as a .ttl file

    :param infile: a .shp file with NHD waterbody data
    :param s2file: Level 13 S2 cells for Maine
    :param outfile: the path and name for the .ttl file
    :return:
    """
    logger.info('\n\nBEGIN TRIPLIFYING NHD WATERBODIES')
    logger.info('Loading the shapefiles')
    gdf_waterbody = gpd.read_file(infile)
    gdf_s2l13 = gpd.read_file(s2file)
    kg = initial_kg(_PREFIX)
    count = 1
    n = len(gdf_waterbody.index)
    logger.info('Creating the triples')
    for row in gdf_waterbody.itertuples():
        bodyiri, geomiri = build_iris(row.COMID, _PREFIX)
        kg.add((bodyiri, RDF.type,
                _PREFIX['hyf']['HY_WaterBody']))  # NOTE: This could be refined later using hyf and/or chyf subclasses
        kg.add((bodyiri, RDFS.label, Literal(f'GNIS_NAME: {row.GNIS_NAME}', datatype=XSD.string)))
        kg.add((bodyiri, RDFS.comment, Literal(f'COMID: {row.COMID}', datatype=XSD.string)))
        kg.add((bodyiri, RDFS.comment, Literal(f'Reachcode: {row.REACHCODE}', datatype=XSD.string)))
        kg.add((bodyiri, RDFS.comment, Literal(f'FTYPE: {row.FTYPE}', datatype=XSD.string)))
        kg.add((bodyiri, GEO.hasGeometry, geomiri))
        kg.add((bodyiri, GEO['hasDefaultGeometry'], geomiri))
        kg.add((geomiri, GEO.asWKT, Literal(row.geometry, datatype=GEO.wktLiteral)))
        kg.add((geomiri, RDF.type, GEO.Geometry))
        kg.add((geomiri, RDF.type, _PREFIX['sf']['MultiPolygon']))

        s2within, s2overlaps = find_s2_intersects_geom(row.geometry, gdf_s2l13)
        for s2 in s2within:
            kg.add((_PREFIX["kwgr"]['s2.level13.' + s2], _PREFIX["kwg-ont"]['sfWithin'], bodyiri))
        for s2 in s2overlaps:
            kg.add((_PREFIX["kwgr"]['s2.level13.' + s2], _PREFIX["kwg-ont"]['sfOverlaps'], bodyiri))

        print(f'Processing row {count:5} of {n} : COMID {str(row.COMID):8}', end='\r', flush=True)
        count += 1
    kg.serialize(outfile, format='turtle')
    logger.info('TRIPLIFYING COMPLETE AND .ttl FILE CREATED')


if __name__ == '__main__':
    start_time = time.time()
    process_waterbodies_shp2ttl(nhd_waterbody_shp_file, s2_file, ttl_file)
    logger.info(f'Runtime: {str(datetime.timedelta(seconds=time.time() - start_time))} HMS')
    print(f'\nRuntime: {str(datetime.timedelta(seconds=time.time() - start_time))} HMS')

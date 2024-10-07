"""Create a .ttl file for a state's county subdivisions

County subdivisions constitute level 3 admin regions per KWG
Under ### Input Filenames ###, define
    the name (and path) of the .shp file of county subdivisions
    the name (and path) of the .shp file of the state's S2 cells
Under ### Output Filename ###, define
    the name (and path) of the output .ttl file

Required:
    * geopandas
    * shapely (LineString, Point, and Polygon)
    * rdflib (Graph and Literal)
    * rdflib.namespace (GEO, RDF, RDFS, and XSD)
    * namespaces (a local .py file with a dictionary of project namespaces)

Functions:
    * initial_kg - initialize an RDFLib knowledge graph with project namespaces
    * build_iris - build IRIs for a given town and its geometries
    * find_s2_intersects_poly - find the S2 cells that are within or overlap a given town
    * main - parse all towns for a given state to the RDFLib graph
"""

import geopandas as gpd
from shapely import LineString, Point, Polygon
from rdflib import Graph, Literal
from rdflib.namespace import GEO, OWL, PROV, RDF, RDFS, SDO, XSD

import logging
import time
import datetime

import sys
import os

# Modify the system path to find namespaces.py
sys.path.insert(1, 'G:/My Drive/UMaine Docs from Laptop/SAWGraph/Data Sources')
from namespaces import _PREFIX

# Set the current directory to this file's directory
os.chdir('G:/My Drive/UMaine Docs from Laptop/SAWGraph/Data Sources/Administrative Regions')

### Input Filenames ###
# cousub_file: a county subdivisions .shp file from the US Census Bureau
#    County subdivision shapefiles: https://www.census.gov/cgi-bin/geo/shapefiles/index.php
cousub_file = '../Geospatial/Illinois/tl_2023_17_cousub/tl_2023_17_cousub.shp'

### Output Filename ###
# ttl_file: the resulting (output) .ttl file
ttl_file = 'ttl_files/il_admin-regions_level-3.ttl'

statename = ', Illinois'

logname = 'logs/log_IL_AdminRegionLevel3-2-ttl.txt'
logging.basicConfig(filename=logname,
                    filemode='a',
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
    return graph


def build_iris(gid):
    """Create IRIs for a town and its geometries

    :param gid: The 10-digit FIPS code for the town is expected as iinput (GEOID)
    :return: a tuple with the three IRIs
    """
    return (_PREFIX["dcgeoid"][gid],
            _PREFIX["saw_geo"]['d.Polygon.administrativeRegion.USA.' + gid],
            _PREFIX["saw_geo"]['d.Point.administrativeRegion.USA.' + gid])


def main():
    """Parse all county subdivisions within a state to an RDFLib knowledge graph

    Major components:
        * Read county subdivision .shp file to a GeoDataFrame
        * Create an empty knowledge graph with project namespaces
        * Iterate through the county subdivisions
            * Create triples with the county subdivision as subject
            * Create triples with the point and polygon geometries as subjects

    :return: a complete knowledge graph
    """
    gdf_towns = gpd.read_file(cousub_file)
    logger.info('Intializing the knowledge graph')
    graph = initial_kg(_PREFIX)
    count = 1
    n = len(gdf_towns.index)
    logger.info('Processing the towns and integrating with S2L13')
    for row in gdf_towns.itertuples():
        name = row.NAMELSAD + statename
        towniri, polyiri, pntiri = build_iris(row.GEOID)

        graph.add((towniri, RDF.type, _PREFIX["kwg-ont"]['AdministrativeRegion_3']))
        graph.add((towniri, RDFS.label, Literal(name, datatype=XSD.string)))
        graph.add((towniri, _PREFIX["kwg-ont"]['administrativePartOf'],
                   _PREFIX["kwgr"]['administrativeRegion.USA.' + row.STATEFP + row.COUNTYFP]))
        graph.add((towniri, _PREFIX["kwg-ont"]['hasFIPS'], Literal(row.GEOID, datatype=XSD.string)))
        graph.add((towniri, _PREFIX["kwg-ont"]['sfWithin'],
                   _PREFIX["kwgr"]['administrativeRegion.USA.' + row.STATEFP + row.COUNTYFP]))
        graph.add((towniri, GEO.hasGeometry, polyiri))
        graph.add((towniri, GEO.defaultGeometry, polyiri))

        graph.add((polyiri, RDF.type, GEO.Geometry))
        graph.add((polyiri, RDF.type, _PREFIX["sf"]['Polygon']))
        graph.add((polyiri, GEO.asWKT, Literal(row.geometry, datatype=GEO.wktLiteral)))
        graph.add((polyiri, RDFS.label, Literal('Geometry of ' + name, datatype=XSD.string)))

        print(f'Row {count:3} of {n} : {name:50}', end='\r', flush=True)
        count += 1
    print()
    return graph


if __name__ == "__main__":
    logger.info('Launching script')
    start_time = time.time()
    kg = main()
    logger.info('Creating the output .ttl file')
    kg.serialize(ttl_file, format='turtle')
    print(f'Runtime: {str(datetime.timedelta(seconds=time.time() - start_time))} HMS')
    logger.info(f'Runtime: {str(datetime.timedelta(seconds=time.time() - start_time))} HMS')

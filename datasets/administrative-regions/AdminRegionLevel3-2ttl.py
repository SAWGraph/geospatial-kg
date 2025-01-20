"""Create a .ttl file for a state's county subdivisions

County subdivisions constitute level 3 admin regions per KWG (kwg-ont:AdministrativeRegion_3)

Global Variables
    User Populated
        state_name:         The name of the current state; e.g., Alabama
        fips_file:          A .tsv file for translating between state names, abbreviations, and FIPS codes
    Automatically Populated
        cousub_affix:       Automatically generated; e.g., ", Alabama"
        input_file_name:    Generated by the get_input_file_name(name, fips) function;
                            e.g., "tl_2023_01_cousub.shp" for Alabama (also includes path info)
        output_file_name:   Generated by the get_output_file_name(abbr, fips) function;
                            e.g., "al_01_admin-regions_level-3.ttl'" for Alabama (also includes path info)

Required Python packages:
    * geopandas
    * pandas
    * rdflib (Graph and Literal)
    * rdflib.namespace (GEO, RDF, RDFS, and XSD)
    * namespaces (a local .py file with a dictionary of project namespaces)
    * datetime, logging, os, sys, time

Functions:
    * get_state_abbr - Takes a state name (e.g., 'Alabama') and returns its abbreviation (e.g., 'AL')
    * get_state_fips - Takes a state name (e.g., 'Alabama') and returns its FIPS code (e.g., '01') as a string
    * get_county_name - Takes a 5-digit county FIPS code (e.g., '23007' and returns its county name (e.g., Franklin County)
    * get_state_identifiers - Takes a state name and returns both its abbreviation (lower case) and its FIPS code
    * get_input_file_name - Takes a state name and its FIPS code and creates a file path/name string
    * get_output_file_name - Takes a state abbreviation and its FIPS code and creates a file path/name string
    * initial_kg - initialize an RDFLib knowledge graph with project namespaces
    * build_iris - build IRIs for a given county subdivision and its geometry
    * county_subs_2ttl - triplify county subdivisions for a given state and write to a .ttl file
"""
import geopandas as gpd
import pandas as pd
from rdflib import Graph, Literal
from rdflib.namespace import GEO, OWL, PROV, RDF, RDFS, SDO, XSD

import logging
import time
import datetime

import sys
import os

# Modify the system path to find namespaces.py
sys.path.insert(1, 'G:/My Drive/Laptop/SAWGraph/Data Sources')
from namespaces import _PREFIX

# Set the current directory to this file's directory
os.chdir('G:/My Drive/Laptop/SAWGraph/Data Sources/Spatial')

### GLOBAL VARIABLES #########################################################################
### State Identifier ###
state_name = 'Rhode Island'
cousub_affix = ', ' + state_name

### Input Filename ###
# see the get_input_file_name() function below
# County subdivision shapefiles: https://www.census.gov/cgi-bin/geo/shapefiles/index.php

### Output Filename ###
# see the get_output_file_name() function below

### State FIPS Info (and more) ###
# Columns: StateFIPS, CountyFIPS_3, CountyName, StateName, CountyFIPS, StateAbbr, STATE-COUNTY
fips_file = 'fips2county.tsv'
################################################################################################

logname = 'logs/log_AdminRegionLevel3-2ttl.txt'
logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info('')
logger.info('LOGGER INITIALIZED')


def get_state_abbr(name: str, df: pd.DataFrame) -> str:
    """Given a state's proper name returns the 2-character abbreviation

    :param name: A state's proper name (eg Alabama)
    :param df: A DataFrame of state and county names, abbreviations, and FIPS codes
    :return: A state's 2-character abbreviation (eg AL)
    """
    state_abbr_df = df[["StateName", "StateAbbr"]].drop_duplicates()
    return state_abbr_df.loc[state_abbr_df["StateName"] == name, "StateAbbr"].values[0]


def get_state_fips(name: str, df: pd.DataFrame) -> str:
    """Given a state's proper name returns the 2-digit FIPS code

    :param name: A state's proper name (eg Alabama)
    :param df: A DataFrame of state and county names, abbreviations, and FIPS codes
    :return: A state's 2-digit FIPS code (eg 01) as a 2-character string
    """
    state_fips_df = df[["StateName", "StateFIPS"]].drop_duplicates()
    return str(state_fips_df.loc[state_fips_df["StateName"] == name, "StateFIPS"].values[0]).zfill(2)


def get_state_identifiers(name: str, df: pd.DataFrame) -> tuple:
    """Given a state's proper name returns the 2-character abbreviation (in lower case) and the 2-digit FIPS code

    :param name: A state's proper name (eg Alabama)
    :param df: A DataFrame of state and county names, abbreviations, and FIPS codes
    :return: A state's 2-character abbreviation (eg AL) and the state's 2-digit FIPS code (eg 01) as a 2-character string
    """
    abbr = get_state_abbr(name, df).lower()
    fips = get_state_fips(name, df)
    return abbr, fips


def get_input_file_name(fips: str):
    """Given a state's FIPS code, returns a path / filename for the input file (user specific)

    :param fips: A state's 2-digit FIPS code (as a string) (e.g., '01')
    :return: The path / filename for an input shape file for a specific state
    """
    return '../Geospatial/CountySubdivisionShpFiles/tl_2023_' + fips + '_cousub/tl_2023_' + fips + '_cousub.shp'


def get_output_file_name(abbr, fips):
    """Given a state's name and FIPS code, returns a path / filename for the output file (user specific)

    :param abbr: A state's two-letter abbreviation (e.g., 'AL' or 'Al' or 'al')0
    :param fips: A state's 2-digit FIPS code as a string (e.g., '01')
    :return: The path / filename for an output .ttl file for a specific state
    """
    return 'ttl_files/AdministrativeRegion_3/' + abbr.lower() + '_' + fips + '_admin-regions_level-3.ttl'


def initial_kg(_PREFIX: dict) -> Graph:
    """Create an empty knowledge graph with project namespaces

    :param _PREFIX: a dictionary of project namespaces
    :return: an RDFLib graph
    """
    graph = Graph()
    for prefix in _PREFIX:
        graph.bind(prefix, _PREFIX[prefix])
    return graph


def build_iris(gid: str) -> tuple:
    """Create IRIs for a town and its geometries

    :param gid: The 10-digit FIPS code for the town is expected as input as a string (GEOID)
    :return: a tuple with the three IRIs
    """
    return _PREFIX["dcgeoid"][gid], _PREFIX["saw_geo"]['d.Polygon.administrativeRegion.USA.' + gid]


def county_subs_2ttl(state: str, infile: str, outfile: str, df: pd.DataFrame) -> None:
    """Parse all county subdivisions within a state to an RDFLib knowledge graph

    :param state: The name of the current state
    :param infile: A string with the path / filename for a Cenusus Bureau .shp file of county subdivisions for a state
    :param outfile: A string with the path / filename for a .ttl file
    :param df: A DataFrame containing 5-digit county FIPS codes and county names
    :return: None
    """
    gdf_towns = gpd.read_file(infile)  # Read the .shp file to a GeoDataframe
    logger.info('Intialize RDFLib Graph')
    graph = initial_kg(_PREFIX)  # Create an empty Graph() with SAWGraph namespaces
    count = 1  # For providing progress updates to the user via the terminal
    n = len(gdf_towns.index)  # For providing progress updates to the user via the terminal
    logger.info(f'Triplify county subdivisions (AdministrativeRegion_3) for {state_name} from {infile}')
    for row in gdf_towns.itertuples():
        county = df.loc[df["CountyFIPS"] == str(row.STATEFP) + str(row.COUNTYFP), "CountyName"].values[0]
        if state in ['Alaska', 'Connecticut', 'District of Columbia', 'Louisiana']:
            name = row.NAMELSAD + ', ' + county + cousub_affix  # Creates a string of the form 'CountySub, County, State'
            # Alaska has Boroughs and Census Areas
            # Connecticut has Planning Regions
            # DC is a single unit
            # Louisiana has Parishes
        else:
            name = row.NAMELSAD + ', ' + county + ' County' + cousub_affix  # Creates a string of the form 'CountySub, County, State'
        # Get IRIs for the current county subdivision and its polygon geometry
        cousub_iri, geo_iri = build_iris(row.GEOID)

        # Triplify basic county subdivision data
        graph.add((cousub_iri, RDF.type, _PREFIX["kwg-ont"]['AdministrativeRegion_3']))
        graph.add((cousub_iri, RDFS.label, Literal(name, datatype=XSD.string)))
        graph.add((cousub_iri, _PREFIX["kwg-ont"]['administrativePartOf'],
                   _PREFIX["kwgr"]['administrativeRegion.USA.' + row.STATEFP + row.COUNTYFP]))
        graph.add((cousub_iri, _PREFIX["kwg-ont"]['hasFIPS'], Literal(row.GEOID, datatype=XSD.string)))

        # Triplify county subdivision geometry data
        graph.add((cousub_iri, GEO.hasGeometry, geo_iri))
        graph.add((cousub_iri, GEO.defaultGeometry, geo_iri))
        graph.add((geo_iri, RDF.type, GEO.Geometry))
        graph.add((geo_iri, GEO.asWKT, Literal(row.geometry, datatype=GEO.wktLiteral)))
        graph.add((geo_iri, RDFS.label, Literal('Geometry of ' + name, datatype=XSD.string)))

        # Provide user progress update
        print(f'Row {count:3} of {n} : {name:50}', end='\r', flush=True)
        count += 1
    print()
    logger.info(f'Write {state} county subdivision triples to {ttl_file}')
    graph.serialize(outfile, format='turtle')  # Write the current state KG to a .ttl file

if __name__ == "__main__":
    logger.info(f'Launching script: State = {state_name}')
    start_time = time.time()
    # Create input and output file names for specified state and a template (user/machine specific)
    df_fips = pd.read_csv(fips_file, sep='\t', header='infer', dtype=str, encoding='latin-1')
    df_fips_county = df_fips[["CountyFIPS", "CountyName"]].drop_duplicates()
    state_abbr, state_fips = get_state_identifiers(state_name, df_fips)
    cousub_file = get_input_file_name(state_fips)
    ttl_file = get_output_file_name(state_abbr, state_fips)
    # Process the specified state's county subdivisions
    county_subs_2ttl(state_name, cousub_file, ttl_file, df_fips_county)
    print(f'Runtime: {str(datetime.timedelta(seconds=time.time() - start_time))} HMS')
    logger.info(f'Runtime: {str(datetime.timedelta(seconds=time.time() - start_time))} HMS')

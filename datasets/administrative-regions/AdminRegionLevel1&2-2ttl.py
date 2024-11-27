"""Create a single .ttl file for all states and create one .ttl file per state for each state's counties

States constitute level 1 admin regions per KWG (kwg-ont:AdministrativeRegion_1)
   The US has 51 including the District of Columbia (territories are ignored)
Counties constitute level 2 admin regions per KWG (kwg-ont:AdministrativeRegion_2)
   The number of counties per state varies substantially

All data is retrieved from KWG (https://stko-kwg.geog.ucsb.edu/graphdb)

Under ### Output Filenames/Paths ###, define
    the name (and path) of the output .ttl file for the US (states)
    the path for the output .ttl files for the states' counties

Required:
    * pandas
    * rdflib (Graph and Literal)
    * rdflib.namespace (GEO, RDF, RDFS, and XSD)
    * SPARQLWrapper (SPARQLWrapper, JSON, GET, DIGEST)
    * sparql_dataframe
    * namespaces (a local .py file with a dictionary of project namespaces)
    * datetime, logging, os, ssl, sys, time

Functions:
    * add_state_abbrev() - Adds two-letter state abbreviations to a dataframe based on state FIPS codes
    * initial_kg - initialize an RDFLib knowledge graph with project namespaces
    * admin_regions_level1_2ttl() - queries KWG for states and creates a .ttl file of the results
    * admin_regions_level2_2ttl() - queries KWG for state county info and creates one .ttl file for each state
"""
import pandas as pd
from rdflib import Graph, Literal
from rdflib.namespace import GEO, OWL, PROV, RDF, RDFS, SDO, XSD
from SPARQLWrapper import SPARQLWrapper, JSON, GET, POST, DIGEST
import sparql_dataframe

import logging
import time
import datetime

import sys
import os
import ssl

# Modify the system path to find namespaces.py
sys.path.insert(1, 'G:/My Drive/Laptop/SAWGraph/Data Sources')
from namespaces import _PREFIX

# Set the current directory to this file's directory
os.chdir('G:/My Drive/Laptop/SAWGraph/Data Sources/Administrative Regions & S2L13')

### Output Filenames/Paths ###
level1_outfile = 'ttl_files/AdministrativeRegion_1/us_admin-regions_level-1.ttl'
level2_outpath = 'ttl_files/AdministrativeRegion_2/'

pd.options.mode.copy_on_write = True
ssl._create_default_https_context = ssl._create_stdlib_context

# KnowWhereGraph (KWG) SPARQL endpoint setup
kwg_endpoint = 'https://stko-kwg.geog.ucsb.edu/graphdb/repositories/KWG'
kwg_sparql = SPARQLWrapper(kwg_endpoint)
kwg_sparql.setHTTPAuth(DIGEST)
kwg_sparql.setMethod(GET)
kwg_sparql.setReturnFormat(JSON)

logname = 'logs/log_AdminRegionLevel1&2-2-ttl.txt'
logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info('')
logger.info('LOGGER INITIALIZED')


def add_state_abbrev(df: pd.DataFrame) -> pd.DataFrame:
    """Takes a dataframe of state data from a query of KWG and adds a colum of two-letter state abbreviations

    :param df: a dataframe of US state info from a KWG query that includes a state_fips column
    :return: the original dataframe with an extra column of two-letter state abbreviations
    """
    df_fips = pd.read_csv('fips2county.tsv', sep='\t', header='infer', dtype=str, encoding='latin-1')
    state_abbr_df = df_fips[["StateFIPS", "StateAbbr"]].drop_duplicates()
    df = df.merge(state_abbr_df, how='left', left_on="state_fips", right_on="StateFIPS")
    df = df.drop(columns=["StateFIPS"])
    return df


def initial_kg(_PREFIX:dict) -> Graph:
    """Create an empty knowledge graph with project namespaces

    :param _PREFIX: a dictionary of project namespaces
    :return: an empty RDFLib graph with project namespaces
    """
    graph = Graph()
    for prefix in _PREFIX:
        graph.bind(prefix, _PREFIX[prefix])
    return graph


def admin_regions_level1_2ttl(endpoint:str, outfile:str) -> list:
    """Creates a single .ttl file of state information from KWG and returns a list of KWG state IRIs

    :param endpoint: the KWG SPARQL endpoint URL
    :param outfile: a path and filename for the output .ttl file
    :return: a list of KWG IRIs for the US states
    """
    # Query to retrieve the state IRIs
    query = """
        PREFIX kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/>
        PREFIX kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

        SELECT * WHERE {
            ?state kwg-ont:administrativePartOf kwgr:administrativeRegion.USA ;
                   rdf:type kwg-ont:AdministrativeRegion_1 ;
        } ORDER BY ?state
        """
    df = sparql_dataframe.get(endpoint, query)  # execute the query and return the results as a dataframe
    state_iris = df['state'].to_list()  # convert the state column to a list
    kg = initial_kg(_PREFIX)  # Create an empty Graph() with SAWGraph namespaces
    # Query each state and add the resulting KWG info to the KG
    for state in state_iris:
        # Query to retrieve state info
        query = """
            PREFIX geo: <http://www.opengis.net/ont/geosparql#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/>
            PREFIX kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/>

            SELECT * WHERE {
                <""" + state + """> rdfs:label ?label ;
                                  kwg-ont:administrativePartOf ?within ;
                                  kwg-ont:hasFIPS ?fips ;
                                  geo:hasGeometry ?geom .
                ?geom rdfs:label ?geom_label ;
                      geo:asWKT ?wkt .
            }
            """
        df_temp = sparql_dataframe.get(endpoint, query)  # execute the query and return the results as a dataframe
        df_temp['fips'] = df_temp['fips'].astype(str)  # convert the fips column to strings
        df_temp['fips'] = df_temp['fips'].str.zfill(2)  # pad single digit fips codes with a leading 0

        # Triplify the current state info if the query returned a single row and it isn't for a territory
        if df_temp.shape[0] == 1 and int(df_temp['fips'].iloc[0]) < 60:
            # Create IRIs
            state_iri = _PREFIX['kwgr'][state.replace('http://stko-kwg.geog.ucsb.edu/lod/resource/', '')]
            usa_iri = _PREFIX['kwgr'][
                df_temp['within'].iloc[0].replace('http://stko-kwg.geog.ucsb.edu/lod/resource/', '')]
            geom_iri = _PREFIX['kwgr'][
                df_temp['geom'].iloc[0].replace('http://stko-kwg.geog.ucsb.edu/lod/resource/', '')]

            # Create triples
            kg.add((state_iri, RDF.type, _PREFIX['kwg-ont']['AdministrativeRegion_1']))
            kg.add((state_iri, RDFS.label, Literal(df_temp['label'].iloc[0], datatype=XSD.string)))
            kg.add((state_iri, _PREFIX['kwg-ont']['administrativePartOf'], usa_iri))
            kg.add((state_iri, _PREFIX['kwg-ont']['hasFIPS'], Literal(df_temp['fips'].iloc[0], datatype=XSD.string)))
            kg.add((state_iri, GEO.defaultGeometry, geom_iri))
            kg.add((state_iri, GEO.hasGeometry, geom_iri))
            kg.add((geom_iri, RDF.type, GEO.Geometry))
            kg.add((geom_iri, RDFS.label, Literal(df_temp['geom_label'].iloc[0], datatype=XSD.string)))
            kg.add((geom_iri, GEO.asWKT, Literal(df_temp['wkt'].iloc[0], datatype=GEO.wktLiteral)))
        # Alert the user if the state query returned more (or less) than one row
        elif df_temp.shape[0] != 1:
            logger.info(f'State query for {df_temp['label'].iloc[0]} returned {df_temp.shape[0]} rows; expected 1')
            print(f'State query for {df_temp['label'].iloc[0]} returned {df_temp.shape[0]} rows; expected 1')
        # Alert the user when a territory is skipped
        else:
            logger.info(f'Skipped {df_temp['label'].iloc[0]}')
            print(f'Skipped {df_temp['label'].iloc[0]}')
    kg.serialize(outfile, format='turtle')    # Write the completed KG to a .ttl file
    return state_iris  # These are needed for processing the counties by state


def admin_regions_level2_2ttl(endpoint:str, outpath:str, iris:list) -> None:
    """Creates one .ttl file per state with that state's county information

    :param endpoint: the KWG SPARQL endpoint URL
    :param outpath: a path for the output .ttl files
    :param iris: a list of KWG state IRIs
    :return: None
    """
    # Process each state's counties one state at a time
    for state in iris:
        kg = initial_kg(_PREFIX)  # Create an empty Graph() with SAWGraph namespaces
        # Query KWG for a state's fips code, name, and counties
        query1 = """
            PREFIX kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/>
            PREFIX kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT * WHERE {
                <""" + state + """> kwg-ont:hasFIPS ?state_fips ;
                                    rdfs:label ?state_label .
                ?county kwg-ont:administrativePartOf <""" + state + """> ;
                        rdf:type kwg-ont:AdministrativeRegion_2 .
            } ORDER BY ?county
            """
        df_county = sparql_dataframe.get(endpoint, query1)  # execute the query and return the results as a dataframe
        # Process the query results if the state is not a territory
        if int(df_county['state_fips'].iloc[0]) < 60:
            df_county['state_fips'] = df_county['state_fips'].astype(str)  # convert the state_fips to strings
            df_county['state_fips'] = df_county['state_fips'].str.zfill(2)  # pad single digit fips with a leading 0
            df_county = add_state_abbrev(df_county)  # add two-letter state abbreviations to the dataframe
            county_iris = df_county['county'].to_list()  # create a list of the current state's counties
            # Process each county in the current state
            for county in county_iris:
                # Query KWG for info on the current county
                query2 = """
                    PREFIX geo: <http://www.opengis.net/ont/geosparql#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    PREFIX kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/>
                    PREFIX kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/>

                    SELECT * WHERE {
                        <""" + county + """> rdfs:label ?label ;
                                          kwg-ont:administrativePartOf ?within ;
                                          kwg-ont:hasFIPS ?fips ;
                                          geo:hasGeometry ?geom .
                        ?geom rdfs:label ?geom_label ;
                              geo:asWKT ?wkt .
                    }
                    """
                df_temp = sparql_dataframe.get(endpoint, query2)  # execute the query and return the results as a dataframe
                df_temp['fips'] = df_temp['fips'].astype(str)  # convert the fips column to strings
                df_temp['fips'] = df_temp['fips'].str.zfill(5)  # pad 4 digit fips codes with a leading 0
                # Triplify the county info as long as only one county was returned
                if df_temp.shape[0] == 1:
                    # Create IRIs
                    county_iri = _PREFIX['kwgr'][county.replace('http://stko-kwg.geog.ucsb.edu/lod/resource/', '')]
                    state_iri = _PREFIX['kwgr'][
                        df_temp['within'].iloc[0].replace('http://stko-kwg.geog.ucsb.edu/lod/resource/', '')]
                    geom_iri = _PREFIX['kwgr'][
                        df_temp['geom'].iloc[0].replace('http://stko-kwg.geog.ucsb.edu/lod/resource/', '')]

                    # Create triples
                    kg.add((county_iri, RDF.type, _PREFIX['kwg-ont']['AdministrativeRegion_2']))
                    kg.add((county_iri, RDFS.label, Literal(df_temp['label'].iloc[0], datatype=XSD.string)))
                    kg.add((county_iri, _PREFIX['kwg-ont']['administrativePartOf'], state_iri))
                    kg.add((county_iri, _PREFIX['kwg-ont']['hasFIPS'],
                            Literal(df_temp['fips'].iloc[0], datatype=XSD.string)))
                    kg.add((county_iri, GEO.defaultGeometry, geom_iri))
                    kg.add((county_iri, GEO.hasGeometry, geom_iri))
                    kg.add((geom_iri, RDF.type, GEO.Geometry))
                    kg.add((geom_iri, RDFS.label, Literal(df_temp['geom_label'].iloc[0], datatype=XSD.string)))
                    kg.add((geom_iri, GEO.asWKT, Literal(df_temp['wkt'].iloc[0], datatype=GEO.wktLiteral)))
                # Alert the user if other than 1 county was returned
                else:
                    print(f'County query for {df_temp['label'].iloc[0]} returned {df_temp.shape[0]} rows; expected 1')
            # Build an output file name from a path, a fips code, an abbreviation, and a template
            state_fips = df_county["state_fips"].iloc[0]
            state_abbr = df_county["StateAbbr"].iloc[0]
            output_file = outpath + state_abbr.lower() + '_' + state_fips + '_admin-regions_level-2.ttl'
            kg.serialize(output_file, format='turtle')  # Write the completed KG to a .ttl file
        # Alert the user if a territory is skipped
        else:
            print(f'Skipped counties for {df_county['state_label'].iloc[0]}')


if __name__ == "__main__":
    logger.info(f'Launching script')
    start_time = time.time()
    logger.info('Triplifying data for 50 US states + DC (1 output file)')
    state_iris = admin_regions_level1_2ttl(kwg_endpoint, level1_outfile)
    logger.info('Triplifying data for the counties in each of the 50 states + DC (51 output files)')
    admin_regions_level2_2ttl(kwg_endpoint, level2_outpath, state_iris)
    print(f'Runtime: {str(datetime.timedelta(seconds=time.time() - start_time))} HMS')
    logger.info(f'Runtime: {str(datetime.timedelta(seconds=time.time() - start_time))} HMS')

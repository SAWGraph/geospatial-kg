"""Creates four .ttl files - one for a state's S2 files,
                             one for the state's S2 integration,
                             one for the state's counties' S2 integration, and
                             one for the state's S2 cell class statements

Under ### STATE OF INTEREST ### enter
    the proper name of the state of interest (e.g., 'Alabama')
Under ### State-County-FIPS Table ### enter
    the path/filename to a .tsv file with State-County-FIPS info
    (see https://towardsdatascience.com/the-ultimate-state-county-fips-tool-1e4c54dc9dff)

Note: Output file path/filename templates are embedded in the ..._2ttl functions

Required:
    * pandas
    * rdflib (Graph and Literal)
    * rdflib.namespace (GEO, RDF, RDFS, and XSD)
    * SPARQLWrapper (SPARQLWrapper, JSON, GET, DIGEST)
    * sparql_dataframe
    * namespaces (a local .py file with a dictionary of project namespaces)
    * datetime, logging, os, ssl, sys, time

Functions:
    * get_state_fips - Takes a state name (e.g., 'Alabama') and returns its FIPS code (e.g., '01') as a string
    * get_state_abbr - Takes a state name (e.g., 'Alabama') and returns its abbreviation (e.g., 'AL')
    * initial_kg - initialize an RDFLib knowledge graph with project namespaces
    * get_state_identifiers - Takes a state name and returns both its abbreviation, FIPS code, KWG IRI, and RDFLib IRI
    * state_s2_cells_2ttl - Queries KWG for the S2 cells that overlap or are within a given state (cell info)
    * state_s2_cell_integration_2ttl - Queries KWG for the S2 cell integration info for a state (relations)
    * county_s2_cell_integration_2ttl - Queries KWG for the S2 cell integration info for a state's counties (relations)
    * state_s2_cell_class_stmts_2ttl - Extracts only the S2 cell class statements from the S2 cell info
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
os.chdir('G:/My Drive/Laptop/SAWGraph/Data Sources/Spatial')

### STATE OF INTEREST #########
state_name = 'Illinois'
### State-County-FIPS Table ###
scf_table = 'fips2county.tsv'
###############################

pd.options.mode.copy_on_write = True
ssl._create_default_https_context = ssl._create_stdlib_context

# KnowWhereGraph (KWG) SPARQL endpoint setup
kwg_endpoint = 'https://stko-kwg.geog.ucsb.edu/graphdb/repositories/KWG'
kwg_sparql = SPARQLWrapper(kwg_endpoint)
kwg_sparql.setHTTPAuth(DIGEST)
kwg_sparql.setMethod(GET)
kwg_sparql.setReturnFormat(JSON)

logname = 'logs/log_S2_Cells&Integration_Levels1&2-2-ttl.txt'
logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info('')
logger.info('LOGGER INITIALIZED')


def get_state_fips(table: str, state_name: str) -> str:
    """Takes a state's proper name and returns the state's 2-digit FIPS code as a string

    :param table: path/filename to a .tsv table of State-County-FIPS info
    :param state_name: a string of a state's proper name (e.g., 'Alabama')
    :return: a 2-digit state FIPS code as a string (e.g., '01')
    """
    df_fips = pd.read_csv(table, sep='\t', header='infer', dtype=str, encoding='latin-1')
    state_fips_df = df_fips[["StateName", "StateFIPS"]].drop_duplicates()
    return str(state_fips_df.loc[state_fips_df["StateName"] == state_name, "StateFIPS"].values[0]).zfill(2)


def get_state_abbr(table: str, state_name: str) -> str:
    """Takes a state's proper name and returns the state's two-letter abbreviation0

    :param table: path/filename to a .tsv table of State-County-FIPS info
    :param state_name: a string of a state's proper name (e.g., 'Alabama')
    :return: a two-letter state abbreviation (e.g., 'AL')
    """
    df_fips = pd.read_csv(table, sep='\t', header='infer', dtype=str, encoding='latin-1')
    state_abbr_df = df_fips[["StateName", "StateAbbr"]].drop_duplicates()
    return state_abbr_df.loc[state_abbr_df["StateName"] == state_name, "StateAbbr"].values[0]


def initial_kg(_PREFIX: dict) -> Graph:
    """Create an empty knowledge graph with project namespaces

    :param _PREFIX: a dictionary of project namespaces
    :return: an RDFLib graph
    """
    graph = Graph()
    for prefix in _PREFIX:
        graph.bind(prefix, _PREFIX[prefix])
    return graph


def get_state_identifiers(table: str, name: str) -> tuple:
    """Given a state's proper name and a table of State-County-FIPS info, returns
          the state's two-letter abbreviation, 2-digit FIPS code (as a string),
          KnowWhereGraph IRI, and RDFLib version of the IRI

    :param table: path/filename to a .tsv table of State-County-FIPS info
    :param name: a string of a state's proper name (e.g., 'Alabama')
    :return: two-letter abbreviation, 2-digit FIPS code, KWG IRI, RDFLib IRI object
    """
    abbr = get_state_abbr(table, name).lower()
    fips = get_state_fips(table, name)
    query_iri = 'kwgr:administrativeRegion.USA.' + fips
    rdflib_iri = _PREFIX['kwgr']['administrativeRegion.USA.' + fips]
    return abbr, fips, query_iri, rdflib_iri


def state_s2_cells_2ttl(name: str, endpoint: str, table: str) -> None:
    """Given a state, SPARQL endpoint, and State-County-FIPS data table,
          writes the S2 cells for the state from KWG as a .ttl file

    :param name: a string of a state's proper name (e.g., 'Alabama')
    :param endpoint: KnowWhereGraph (KWG) SPARQL endpoint url
    :param table: path/filename to a .tsv table of State-County-FIPS info
    :return: None
    """
    # Get two-letter state abbreviaion, 2-digit state FIPS code, KWG IRI, and RDFLib IRI object
    state_abbr, state_fips, state_query_iri, state_rdflib_iri = get_state_identifiers(table, name)

    # Query to retrieve state S2 cells and their data
    query_cells = """
        PREFIX geo: <http://www.opengis.net/ont/geosparql#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/>
        PREFIX kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/>

        SELECT * WHERE {
            ?s2 kwg-ont:sfOverlaps | kwg-ont:sfWithin """ + state_query_iri + """ ;
            	rdf:type kwg-ont:S2Cell_Level13 ;
            	rdfs:label ?label ;
            	kwg-ont:cellID ?id ;
                kwg-ont:sfTouches ?touched ;
            	kwg-ont:sfWithin ?s2_12 ;
            	geo:hasGeometry ?geom ;
            	geo:hasMetricArea ?area .
            ?geom rdfs:label ?glabel ;
            	  geo:asWKT ?wkt .
            ?s2_12 rdf:type kwg-ont:S2Cell_Level12 .
        }
        """
    df = sparql_dataframe.get(endpoint, query_cells)  # execute the query and return the results as a dataframe

    # Create two additional dataframes: one without sfTouches data and one with only S2 IRI and sfTouches data
    df_s2 = df.drop('touched', axis=1)
    df_s2.drop_duplicates(inplace=True)
    df_touched = df[['s2', 'touched']]
    df_touched.drop_duplicates(inplace=True)

    kg = initial_kg(_PREFIX)  # Create an empty Graph() with SAWGraph namespaces
    for row in df_s2.itertuples():
        # Create IRIs
        s2_iri = _PREFIX['kwgr'][row.s2.replace('http://stko-kwg.geog.ucsb.edu/lod/resource/', '')]
        s2_12_iri = _PREFIX['kwgr'][row.s2_12.replace('http://stko-kwg.geog.ucsb.edu/lod/resource/', '')]
        geom_iri = _PREFIX['kwgr'][row.geom.replace('http://stko-kwg.geog.ucsb.edu/lod/resource/', '')]

        # Create S2 triples
        kg.add((s2_iri, RDF.type, _PREFIX['kwg-ont']['S2Cell_Level13']))
        kg.add((s2_iri, RDFS.label, Literal(row.label, datatype=XSD.string)))
        kg.add((s2_iri, _PREFIX['kwg-ont']['cellID'],
                Literal(row.s2.replace('http://stko-kwg.geog.ucsb.edu/lod/resource/s2.level13.', ''),
                        datatype=XSD.integer)))
        kg.add((s2_iri, _PREFIX['kwg-ont']['sfWithin'], s2_12_iri))
        kg.add((s2_12_iri, _PREFIX['kwg-ont']['sfContains'], s2_iri))

        # Create S2 geometry triples
        kg.add((s2_iri, GEO.defaultGeometry, geom_iri))
        kg.add((s2_iri, GEO.hasGeometry, geom_iri))
        kg.add((s2_iri, GEO.hasMetricArea, Literal(row.area, datatype=XSD.float)))
        kg.add((geom_iri, RDF.type, GEO.Geometry))
        kg.add((geom_iri, RDFS.label, Literal(row.glabel, datatype=XSD.string)))
        kg.add((geom_iri, GEO.asWKT, Literal(row.wkt, datatype=GEO.wktLiteral)))

    for row in df_touched.itertuples():
        # Create IRIs
        s2_iri = _PREFIX['kwgr'][row.s2.replace('http://stko-kwg.geog.ucsb.edu/lod/resource/', '')]
        touched_iri = _PREFIX['kwgr'][row.touched.replace('http://stko-kwg.geog.ucsb.edu/lod/resource/', '')]

        # Create triples
        kg.add((s2_iri, _PREFIX['kwg-ont']['sfTouches'], touched_iri))
        kg.add((touched_iri, _PREFIX['kwg-ont']['sfTouches'], s2_iri))

    # Write the completed KG to a .ttl file
    kg.serialize('ttl_files/S2_cells/' + state_abbr + '_' + state_fips + '_s2-l13.ttl', format='turtle')


def state_s2_cell_integration_2ttl(name: str, endpoint: str, table: str) -> None:
    """Given a state, SPARQL endpoint, and State-County-FIPS data table,
          writes the S2 cell integration for the state from KWG as a .ttl file

    :param name: a string of a state's proper name (e.g., 'Alabama')
    :param endpoint: KnowWhereGraph (KWG) SPARQL endpoint url
    :param table: path/filename to a .tsv table of State-County-FIPS info
    :return: None
    """
    # Create IRIs
    state_abbr, state_fips, state_query_iri, state_rdflib_iri = get_state_identifiers(table, name)

    # Query to find S2 cells within a given state's boundary
    query_within = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/>
        PREFIX kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/>

        SELECT * WHERE {
            ?s2 kwg-ont:sfWithin """ + state_query_iri + """ ;
            	rdf:type kwg-ont:S2Cell_Level13 .
        }
        """
    df_within = sparql_dataframe.get(endpoint, query_within)  # execute the query and return the results as a dataframe

    # Query to find S2 cells overlapping a given state's boundary
    query_overlaps = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/>
        PREFIX kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/>

        SELECT * WHERE {
            ?s2 kwg-ont:sfOverlaps """ + state_query_iri + """ ;
            	rdf:type kwg-ont:S2Cell_Level13 .
        }
        """
    df_overlaps = sparql_dataframe.get(endpoint, query_overlaps)  # execute query and return results as a dataframe

    kg = initial_kg(_PREFIX)  # Create an empty Graph() with SAWGraph namespaces
    for row in df_within.itertuples():
        # Create S2 IRI
        s2_iri = _PREFIX['kwgr'][row.s2.replace('http://stko-kwg.geog.ucsb.edu/lod/resource/', '')]

        # Create triples (within and its inverse, contains)
        kg.add((s2_iri, _PREFIX['kwg-ont']['sfWithin'], state_rdflib_iri))
        kg.add((state_rdflib_iri, _PREFIX['kwg-ont']['sfContains'], s2_iri))

    for row in df_overlaps.itertuples():
        # Create S2 IRI
        s2_iri = _PREFIX['kwgr'][row.s2.replace('http://stko-kwg.geog.ucsb.edu/lod/resource/', '')]

        # Create triples (overlaps is reflexive)
        kg.add((s2_iri, _PREFIX['kwg-ont']['sfOverlaps'], state_rdflib_iri))
        kg.add((state_rdflib_iri, _PREFIX['kwg-ont']['sfOverlaps'], s2_iri))

    # Write the completed KG to a .ttl file
    kg.serialize('ttl_files/AdministrativeRegion_1/s2_' + state_abbr + '_' + state_fips + '_admin-regions_level-1.ttl',
                 format='turtle')


def county_s2_cell_integration_2ttl(name: str, endpoint: str, table: str) -> None:
    """Given a state, SPARQL endpoint, and State-County-FIPS data table,
          writes the S2 cell integration for the state's counties from KWG as a .ttl file

    :param name: a string of a state's proper name (e.g., 'Alabama')
    :param endpoint: KnowWhereGraph (KWG) SPARQL endpoint url
    :param table: path/filename to a .tsv table of State-County-FIPS info
    :return: None
    """
    # Create IRIs
    state_abbr, state_fips, state_query_iri, state_rdflib_iri = get_state_identifiers(table, name)
    kg = initial_kg(_PREFIX)  # Create an empty Graph() with SAWGraph namespaces
    # Query for counties within the given state
    query_counties = """
            PREFIX kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/>
            PREFIX kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT * WHERE {
                ?county kwg-ont:administrativePartOf """ + state_query_iri + """ ;
                        rdf:type kwg-ont:AdministrativeRegion_2 .
            } ORDER BY ?county
            """
    df_county = sparql_dataframe.get(endpoint, query_counties)  # execute query and return results as a dataframe
    county_iris = df_county['county'].to_list()  # Create a list of the state's counties' IRIs
    for county in county_iris:
        # Query to find S2 cells within a given county's boundary
        query_within = """
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/>
                PREFIX kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/>

                SELECT * WHERE {
                    ?s2 kwg-ont:sfWithin <""" + county + """> ;
                    	rdf:type kwg-ont:S2Cell_Level13 .
                }
                """
        df_within = sparql_dataframe.get(endpoint, query_within)  # execute query and return results as a dataframe

        # Query to find S2 cells overlapping a given county's boundary
        query_overlaps = """
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/>
                PREFIX kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/>

                SELECT * WHERE {
                    ?s2 kwg-ont:sfOverlaps <""" + county + """> ;
                    	rdf:type kwg-ont:S2Cell_Level13 .
                }
                """
        df_overlaps = sparql_dataframe.get(endpoint, query_overlaps)  # execute query and return results as a dataframe
        county_fips = county[-5:]  # Extract the current county's FIPS code from its IRI
        county_rdflib_iri = _PREFIX['kwgr']['administrativeRegion.USA.' + county_fips]  # Create a county IRI
        for row in df_within.itertuples():
            # Create S2 IRI
            s2_iri = _PREFIX['kwgr'][row.s2.replace('http://stko-kwg.geog.ucsb.edu/lod/resource/', '')]

            # Create triples (within and its inverse, contains)
            kg.add((s2_iri, _PREFIX['kwg-ont']['sfWithin'], county_rdflib_iri))
            kg.add((county_rdflib_iri, _PREFIX['kwg-ont']['sfContains'], s2_iri))
        for row in df_overlaps.itertuples():
            # Create S2 IRI
            s2_iri = _PREFIX['kwgr'][row.s2.replace('http://stko-kwg.geog.ucsb.edu/lod/resource/', '')]

            # Create triples (overlaps is reflexive)
            kg.add((s2_iri, _PREFIX['kwg-ont']['sfOverlaps'], county_rdflib_iri))
            kg.add((county_rdflib_iri, _PREFIX['kwg-ont']['sfOverlaps'], s2_iri))

    # Write the completed KG to a .ttl file
    kg.serialize('ttl_files/AdministrativeRegion_2/s2_' + state_abbr + '_' + state_fips + '_admin-regions_level-2.ttl',
                 format='turtle')


def state_s2_cell_class_stmts_2ttl(name: str, table: str) -> None:
    """Given a state's proper name anda  State-County-FIPS data table,
          writes only the S2 cell class statements for the state to a .ttl file

    :param name: a string of a state's proper name (e.g., 'Alabama')
    :param table: path/filename to a .tsv table of State-County-FIPS info
    :return: None
    """
    abbr = get_state_abbr(table, name).lower()
    fips = get_state_fips(table, name)
    input = 'ttl_files/S2_cells/' + abbr + '_' + fips + '_s2-l13.ttl'
    output = 'ttl_files/class_statements/' + abbr + '_' + fips + '_s2-l13_class-statements.ttl'
    prefixes = ['@prefix kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/> .',
                '@prefix kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/> .',
                '@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .']
    # Create the output .ttl file
    with open(output, 'w') as outfile:
        # Add the prefixes to the output file
        for prefix in prefixes:
            outfile.write(prefix)
            outfile.write('\n')
        outfile.write('\n')
        with open(input, 'r') as infile:
            for line in infile:
                # Finds the class statements for S2Cell_Level13
                if 's2cell_level13' in line.lower():
                    outfile.write(line.replace(';', '.'))  # Making sure syntax is correct


if __name__ == "__main__":
    logger.info(f'Launching script: State = {state_name}')
    start_time = time.time()
    logger.info(f'Triplify {state_name} S2 cells (from KWG)')
    state_s2_cells_2ttl(state_name, kwg_endpoint, scf_table)
    logger.info(f'Triplify {state_name} S2 cell integration (from KWG)')
    state_s2_cell_integration_2ttl(state_name, kwg_endpoint, scf_table)
    logger.info(f'Triplify {state_name} counties S2 cell integration (from KWG)')
    county_s2_cell_integration_2ttl(state_name, kwg_endpoint, scf_table)
    logger.info(f'Triplify {state_name} S2 cell class statements (from KWG)')
    state_s2_cell_class_stmts_2ttl(state_name, scf_table)
    print(f'Runtime: {str(datetime.timedelta(seconds=time.time() - start_time))} HMS')
    logger.info(f'Runtime: {str(datetime.timedelta(seconds=time.time() - start_time))} HMS')

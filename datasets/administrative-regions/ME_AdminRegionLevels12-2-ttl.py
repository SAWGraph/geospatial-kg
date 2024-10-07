"""Create a single .ttl file from a set of .zip files containing .ttl files

Under ### INPUT Filenames ###, define
    the name (and path) of the input .zip files
Under ### OUTPUT Filenames ###, define
    the name (and path) of the output .ttl files

Required:
    * zipfile
    * rdflib (Graph)

Functions:
    * process_zipped_ttl_files - adds the .zip file of .ttl files to an RDFLib knowledge graph
"""

import zipfile
from rdflib import Graph

import time
import datetime
import logging

import sys
import os

# Modify the system path to find namespaces.py
sys.path.insert(1, 'G:/My Drive/UMaine Docs from Laptop/SAWGraph/Data Sources')
from namespaces import _PREFIX

# Set the current directory to this file's directory
os.chdir('G:/My Drive/UMaine Docs from Laptop/SAWGraph/Data Sources/Administrative Regions')

### INPUT Filenames ###
# input_counties: a .zip file of KnowWhereGraph level 2 administrative regions
# input_state: a .zip file of a KnowWhereGraph level 1 administrative region
input_counties = 'ttl_files/maine_counties.zip'
input_state = 'ttl_files/maine_state.zip'

### OUTPUT Filenames ###
# output_file: this is for the resulting .ttl file
county_output_file = 'ttl_files/me_admin-regions_level-2.ttl'
state_output_file = 'ttl_files/me_admin-regions_level-1.ttl'

logname = 'logs/log_ME_AdminRegionLevels12-2-ttl.txt'
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


def process_zipped_ttl_files(infile, graph):
    """Parse all .ttl files in a .zip file to a RDFLib graph.

    :param infile: the name of a .zip file that contains .ttl files
    :param graph: an RDFLIB graph
    :return: an RDFLIB graph
    """
    with zipfile.ZipFile(infile) as myzip:
        file_list = myzip.namelist()
        for file in file_list:
            if '.ttl' in file:
                with myzip.open(file) as content:
                    graph.parse(content)
    return graph


if __name__ == "__main__":
    logger.info('Launching script')
    start_time = time.time()
    # Create an empty knowledge graph
    logger.info('Initializing graph')
    county_kg = initial_kg(_PREFIX)
    state_kg = initial_kg(_PREFIX)
    # Call the process_zipped_ttl_files function to add data to the knowledge graph
    logger.info('Processing the zipped admin region .ttl files')
    county_kg = process_zipped_ttl_files(input_counties, county_kg)
    state_kg = process_zipped_ttl_files(input_state, state_kg)
    # Write the resulting knowledge graph to a .ttl file
    logger.info('Creating the output .ttl file')
    county_kg.serialize(county_output_file, format='ttl')
    state_kg.serialize(state_output_file, format='ttl')
    print(f'Runtime: {str(datetime.timedelta(seconds=time.time() - start_time))} HMS')
    logger.info(f'Runtime: {str(datetime.timedelta(seconds=time.time() - start_time))} HMS')

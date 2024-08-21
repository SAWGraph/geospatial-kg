"""Create a single .ttl file from a set of .zip files containing .ttl files

Under ### INPUT Filename ###, define
    the name (and path) of the input .zip file
Under ### OUTPUT Filename ###, define
    the name (and path) of the output .ttl file

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

### INPUT Filename ###
# input_admin_regions: a zip file of KnowWhereGraph administrative regions
input_admin_regions = 'maine-admin-regions.zip'

### OUTPUT Filename ###
# output_file: this is for the resulting .ttl file
output_file = 'me_admin-regions_kwg.ttl'

logname = 'log_ME_AdminRegions-2-ttl.txt'
logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


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
    kg = Graph()
    # Call the process_zipped_ttl_files function to add data to the knowledge graph
    logger.info('Processing the zipped admin region .ttl files')
    kg = process_zipped_ttl_files(input_admin_regions, kg)
    # Write the resulting knowledge graph to a .ttl file
    logger.info('Creating the output .ttl file')
    kg.serialize(output_file, format='ttl')
    print(f'Runtime: {str(datetime.timedelta(seconds=time.time() - start_time))} HMS')
    logger.info(f'Runtime: {str(datetime.timedelta(seconds=time.time() - start_time))} HMS')
"""Create a .ttl file from a .zip file containing one .ttl file for each S2 cell

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

import logging
import time
import datetime

### INPUT Filename ###
# input_s2_cells: The S2L13 cells from KnowWhereGraph for Maine
#    They include state and county admin regions, county S2 cell relations, and state S2 cell relations.
input_s2_cells = 'maine_s2_level-13.zip'

### OUTPUT Filename ###
# output_file: This is for the resulting .ttl file
output_file = 'me_s2-l13.ttl'

logname = 'log_ME_S2Cells-2-ttl.txt'
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
    logger.info('Initializing graph')
    kg = Graph()
    logger.info('Processing the zipped .ttl files')
    kg = process_zipped_ttl_files(input_s2_cells, kg)
    logger.info('Creating the output .ttl file')
    kg.serialize(output_file, format='ttl')
    print(f'Runtime: {str(datetime.timedelta(seconds=time.time() - start_time))} HMS')
    logger.info(f'Runtime: {str(datetime.timedelta(seconds=time.time() - start_time))} HMS')

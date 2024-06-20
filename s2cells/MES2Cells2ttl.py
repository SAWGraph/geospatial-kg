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

import time
import datetime

### INPUT Filename ###
# input_s2_cells: The S2L13 cells from KnowWhereGraph for Maine
#    They include state and county admin regions, county S2 cell relations, and state S2 cell relations.
input_s2_cells = 'maine_s2_level-13.zip'

### OUTPUT Filename ###
# output_file: This is for the resulting .ttl file
output_file = 'me_s2-l13.ttl'


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
    start_time = time.time()
    kg = Graph()
    kg = process_zipped_ttl_files(input_s2_cells, kg)
    kg.serialize(output_file, format='ttl')
    print(f'Runtime: {str(datetime.timedelta(seconds=time.time() - start_time))} HMS')

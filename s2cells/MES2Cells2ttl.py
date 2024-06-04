"""Create a single .ttl file from .zip file containing one .ttl file for each S2 cell

Define the name (and path) of the input .zip file under ### Input Filename ###
Define the name (and path) of the output .ttl file under ### Output Filename ###
Call the process_zipped_ttl_files function once for each input .zip file
"""

import zipfile

from rdflib import Graph

### Input Filenames ###
# These files come from KnowWhereGraph
# They include state and county admin regions, county S2 cell relations, and state S2 cell relations.
input_s2_cells = 'maine_s2_level-13.zip'

### Output Filename ###
# This is for the resulting .ttl file
output_file = 'me_s2-l13.ttl'


### Functions ###

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
    # Create an empty knowledge graph
    kg = Graph()
    # Call the process_zipped_ttl_files function to add data to the knowledge graph
    kg = process_zipped_ttl_files(input_s2_cells, kg)
    # Write the resulting knowledge graph to a .ttl file
    kg.serialize(output_file, format='ttl')

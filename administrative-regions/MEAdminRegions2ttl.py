"""Create a single .ttl file from a set of .zip files containing .ttl files

Under ### Input Filenames ###, define
    the name (and path) of each input .zip file
Under ### Output Filename ###, define
    the name (and path) of the output .ttl file

Required:
    * zipfile
    * rdflib (Graph)

Functions:
    * process_zipped_ttl_files - adds the .zip file of .ttl files to an RDFLib knowledge graph
"""

import datetime
import time
import zipfile
from rdflib import Graph

### Input Filenames ###
# These files come from KnowWhereGraph
# They include state and county admin regions, county S2 cell relations, and state S2 cell relations.
input_admin_regions = 'maine-admin-regions.zip'
input_counties_s2 = 'maine_counties_s2.zip'
input_state_s2 = 'maine_state_s2.zip'

### Output Filename ###
# This is for the resulting .ttl file
output_file = 'me_admin-regions_kwg.ttl'


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
    start_time = time.time()
    # Create an empty knowledge graph
    kg = Graph()
    # Call the process_zipped_ttl_files function to add data to the knowledge graph
    kg = process_zipped_ttl_files(input_admin_regions, kg)
    kg = process_zipped_ttl_files(input_counties_s2, kg)
    kg = process_zipped_ttl_files(input_state_s2, kg)
    # Write the resulting knowledge graph to a .ttl file
    kg.serialize(output_file, format='ttl')
    print(f'Runtime: {str(datetime.timedelta(seconds=time.time() - start_time))} HMS')

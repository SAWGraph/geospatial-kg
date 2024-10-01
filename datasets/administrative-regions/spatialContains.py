import geopandas
from rdflib import Graph
from rdfpandas.graph import to_dataframe
import logging
from pathlib import Path

def get_region_ttl(source, boundary):
    '''
    Get region (boundary) for a set of two ttl file series with spatial geometry
    '''
    ## initiate log file
    logname = "log"
    logging.basicConfig(filename=logname,
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)

    logging.info(f"Running spatial join for {source} to {boundary}")
    #kg = Initial_KG(_PREFIX)
    kg = Graph()
    #open the file and read data
    with open(boundary,'r') as bound:
        boundary_file = bound.read()
    with open(source, 'r') as src:
        source_file = src.read()
    kg.parse(data=boundary_file, format='turtle')
    q = """
        PREFIX geo: <http://www.opengis.net/ont/geosparql#>
        select * where { 
	        ?s rdf:type geo:Geometry .
	        ?feature geo:hasDefaultGeometry ?s .
	        ?s geo:asWKT ?wkt .
        }
    """
    i=0
    i2=0
    bound_graph = kg.query(q)
    for s, feature, wkt in bound_graph:
        i+=1
    print('boundary features: ', i)

    kg2 = Graph()
    kg2.parse(data=source_file, format='turtle')
    for s, feature, wkt in kg2.query(q):
        i2+=1
    print('source features:', i2)
    df_boundary = to_dataframe(kg)
    #df_boundary = df_boundary[df_boundary['geo:asWKT{Literal}'].dropna()]
    print(df_boundary.info())
    print(df_boundary.head())
def triplify_geom(source, boundary):
    '''

    '''
    logging.info(f"Running triplification for {source} to {boundary}")


if __name__ == '__main__':
    root_folder = Path(__file__).resolve().parent.parent.parent
    print(root_folder)
    get_region_ttl((root_folder / f'datasets/maine/mgs/mgs_wells_located_output.ttl').resolve(),
                   f'me_towns.ttl')
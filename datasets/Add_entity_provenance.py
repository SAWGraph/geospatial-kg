# Use caution running this for S2 cells on a personal PC
#   Processing the S2 cells used over 150GB RAM on SKAILab's c101 server at UMaine and took over an hour to run
#   Wrote 7.4M new triples (750MB)

from rdflib import Graph, Namespace, RDF, RDFS, URIRef, Literal
from pathlib import Path
import zipfile
import sys
import logging

cwd = Path.cwd()

ns_dir = cwd.parent.parent
sys.path.insert(0, str(ns_dir))
from namespaces import _PREFIX

log_dir = cwd / 'logs'
ttl_dir = cwd / 'ttl_files'
ar1_file = ttl_dir / 'AdministrativeRegion_1' / 'us_admin-regions_level-1.ttl'
ar2_file = ttl_dir / 'AdministrativeRegion_2' / 'us_admin-regions_level-2.zip'
ar3_file = ttl_dir / 'AdministrativeRegion_3' / 'us_admin-regions_level-3.zip'
s2_file  = ttl_dir / 'S2_cells' / 'us_s2-l13.zip'
in_files = [ ar1_file, ar2_file, ar3_file, s2_file ]


logname = log_dir / f'log_Add_entity_provenance.txt'
logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.info('')
logger.info('LOGGER INITIALIZED')


def initial_kg(_PREFIX: dict):
    logger.info('  Initialize RDFLib Graph')
    graph = Graph()
    for prefix in _PREFIX:
        graph.bind(prefix, _PREFIX[prefix])
    return graph


def create_prov_file(input_path: Path, _PREFIX: dict) -> None:
    kg_in = initial_kg(_PREFIX)
    if input_path.suffix == '.ttl':
        logger.info(f'  Reading .ttl file')
        kg_in.parse(input_path, format='turtle')
    else:
        logger.info('  Reading .zip file')
        with zipfile.ZipFile(input_path, 'r') as archive:
            for file_info in archive.infolist():
                if file_info.filename.endswith('.ttl'):
                    with archive.open(file_info) as ttl_file:
                        kg_in.parse(source=ttl_file, format='turtle')
    kg_out = initial_kg(_PREFIX)

    KWG = Namespace("http://stko-kwg.geog.ucsb.edu/lod/ontology/")
    ontologyStem = 'http://purl.org/spatialai/spatial/admin-regions'
    ontologyIRI = URIRef(ontologyStem)

    if 'level-1' in input_path.stem:
        TARGET_CLASS = KWG.AdministrativeRegion_1
    elif 'level-2' in input_path.stem:
        TARGET_CLASS = KWG.AdministrativeRegion_2
    elif 'level-3' in input_path.stem:
        TARGET_CLASS = KWG.AdministrativeRegion_3
    else:
        TARGET_CLASS = KWG.S2Cell_Level13
    NEW_PREDICATE = RDFS.isDefinedBy
    NEW_OBJECT = ontologyIRI

    count = 0
    for entity in kg_in.subjects(RDF.type, TARGET_CLASS):
        kg_out.add((entity, NEW_PREDICATE, NEW_OBJECT))
        count += 1

    logger.info(f'  Successfully added new triples to {count} entities from {input_path.stem}{input_path.suffix}')

    output_path = ttl_dir / f'{input_path.stem}_prov.ttl'
    logger.info(f'  Writing to {output_path}')
    kg_out.serialize(destination=output_path, format="turtle")
    logger.info(f'  Successfully written to {output_path}')


if __name__ == "__main__":
    for file in in_files:
        logger.info(f'Processing {file}')
        create_prov_file(file, _PREFIX)
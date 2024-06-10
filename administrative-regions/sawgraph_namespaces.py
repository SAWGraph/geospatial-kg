from rdflib import Namespace
from rdflib.namespace import GEO, OWL, PROV, RDF, RDFS, XSD

SAWGRAPH_NAMESPACE = "http://sawgraph.spatialai.org/v1/"

_PREFIX = {
    "dcgeoid": Namespace(f'https://datacommons.org/browser/geoId/'),
    "kwg-ont": Namespace(f'http://stko-kwg.geog.ucsb.edu/lod/ontology/'),
    "kwgr": Namespace(f'http://stko-kwg.geog.ucsb.edu/lod/resource/'),
    "sawgeo": Namespace(f'{SAWGRAPH_NAMESPACE}sawgeo#'),
    "sf": Namespace(f'http://www.opengis.net/ont/sf#'),
    "geo": GEO,
    "owl": OWL,
    "prov": PROV,
    "rdf": RDF,
    "rdfs": RDFS,
    "xsd": XSD
}


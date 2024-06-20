from rdflib import Namespace
from rdflib.namespace import GEO, OWL, PROV, RDF, RDFS, XSD

SAWGRAPH_NAMESPACE = "http://sawgraph.spatialai.org/v1/"

_PREFIX = {
    "dcgeoid": Namespace(f'https://datacommons.org/browser/geoId/'),
    "gcx-cid": Namespace(f'https://geoconnex.us/nhdplusv2/comid/'),
    "gwml": Namespace(f'http://www.opengis.net/gwml-main/2.2/'),
    "hyf": Namespace(f'https://www.opengis.net/def/schema/hy_features/hyf/'),
    "kwg-ont": Namespace(f'http://stko-kwg.geog.ucsb.edu/lod/ontology/'),
    "kwgr": Namespace(f'http://stko-kwg.geog.ucsb.edu/lod/resource/'),
    "me_mgs": Namespace(f'{SAWGRAPH_NAMESPACE}me_mgs#'),
    "me_mgs_data": Namespace(f'{SAWGRAPH_NAMESPACE}me_mgs_data#'),
    "sawgeo": Namespace(f'{SAWGRAPH_NAMESPACE}sawgeo#'),
    "sf": Namespace(f'http://www.opengis.net/ont/sf#'),
    "geo": GEO,
    "owl": OWL,
    "prov": PROV,
    "rdf": RDF,
    "rdfs": RDFS,
    "xsd": XSD
}


def find_s2_intersects_geom(poly, s2cells):
    """Return the S2 cells within a polygon and the S2 cells overlapping the polygon

    :param poly: A polygon representing the boundary of a feature
    :param s2cells: A GeoDataFrame of S2 cells for the features state
    :return: A list of S2 cells within the feature and a list of S2 cells overlapping the feature
    """
    within = []
    overlaps = []
    for row in s2cells.itertuples():
        if row.geometry.within(poly):
            within.append(row.Name)
        if row.geometry.overlaps(poly):
            overlaps.append(row.Name)
    return within, overlaps

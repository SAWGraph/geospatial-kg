"""A  .py file with the namespaces needed to triplify data for SAWGraph
Modeled after a similar file created by Shirly Stephen

Use:
Most triplification scripts simply need to include
    from namespaces import _PREFIX

A system path must be set to find the file. This can be done within the calling .py file
    import sys
    sys.path.insert(1, '<path to this file>')

It may be necessary to reset the working directory after adjusting the path above
    import os
    os.chdir('<path to working directory>')

Note:
The s2 integration functions at the end are not currently used.
S2 integration is accomplished using a more sophisticated KWG script."""


from rdflib import Namespace
from rdflib.namespace import DC, GEO, DCTERMS, OWL, PROV, RDF, RDFS, SDO, SKOS, XSD
from shapely import LineString, Point, Polygon
import geopandas as gpd

SAWGRAPH_NAMESPACE = "http://sawgraph.spatialai.org/v1/"

_PREFIX = {
    "coso": Namespace(f'http://sawgraph.spatialai.org/v1/contaminoso#'),
    "dcgeoid": Namespace(f'https://datacommons.org/browser/geoId/'),
    "gcx": Namespace(f'https://geoconnex.us/'),
    "gcx-cid": Namespace(f'https://geoconnex.us/nhdplusv2/comid/'),
    "gsmlb": Namespace(f'http://geosciml.org/def/gsmlb#'),
    "gwml2": Namespace(f'http://gwml2.org/def/gwml2#'),
    "hyf": Namespace(f'https://www.opengis.net/def/schema/hy_features/hyf/'),
    "il_isgs": Namespace(f'{SAWGRAPH_NAMESPACE}il_isgs#'),
    "il_isgs_data": Namespace(f'{SAWGRAPH_NAMESPACE}il_isgs_data#'),
    "kwg-ont": Namespace(f'http://stko-kwg.geog.ucsb.edu/lod/ontology/'),
    "kwgr": Namespace(f'http://stko-kwg.geog.ucsb.edu/lod/resource/'),
    "me_egad": Namespace(f'{SAWGRAPH_NAMESPACE}me_egad#'),
    "me_egad_data": Namespace(f'{SAWGRAPH_NAMESPACE}me_egad_data#'),
    "me_mgs": Namespace(f'{SAWGRAPH_NAMESPACE}me_mgs#'),
    "me_mgs_data": Namespace(f'{SAWGRAPH_NAMESPACE}me_mgs_data#'),
    "saw_geo": Namespace(f'{SAWGRAPH_NAMESPACE}saw_geo#'),
    "saw_water": Namespace(f'{SAWGRAPH_NAMESPACE}saw_water#'),
    "sf": Namespace(f'http://www.opengis.net/ont/sf#'),
    "spatial": Namespace(f'http://purl.org/spatialai/spatial/spatial-full#'),
    "wdp": Namespace(f'https://www.wikidata.org/wiki/Property:'),
    "dc": DC,
    "dcterms": DCTERMS,  # or "terms" ?
    "geo": GEO,
    "owl": OWL,
    "prov": PROV,
    "rdf": RDF,
    "rdfs": RDFS,
    "schema": SDO,
    "skos": SKOS,
    "xsd": XSD
}


def find_s2_intersects_poly(poly, s2cells):
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


# def find_s2_intersects_pt(pt, s2cells):
#     """Return the S2 cell that contains a given point
#
#     :param pt: A point representing a feature
#     :param s2cells: A GeoDataFrame of S2 cells for the features state
#     :return: A list of S2 cells within the feature and a list of S2 cells overlapping the feature
#     """
#     intersects = []
#     for row in s2cells.itertuples():
#         if row.geometry.intersects(pt):
#             intersects.append(row.Name)
#     return intersects


def find_s2_intersects_point(point, s2_sindex, s2_cells):
    """Return the S2 cells that intersect a given point

    :param pt: A point representing a feature
    :param s2_index: a spatial index object for the S2 cells GeoDataFrame
    :param s2_cells: A GeoDataFrame of S2 cells for the features state
    :return: A list of S2 cells within the feature and a list of S2 cells overlapping the feature
    """
    bbox = list(point.bounds)
    poly_candidates_idx = list(s2_sindex.intersection(bbox))
    poly_candidates = s2_cells.loc[poly_candidates_idx]
    return poly_candidates.loc[poly_candidates.intersects(point)]

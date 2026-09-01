from __future__ import annotations
from typing import Generator
import os
import argparse
from functools import partial
from multiprocessing import Pool
from pathlib import Path

from rdflib import Graph, DC, DCTERMS, OWL, PROV, RDF, RDFS, SDO, SKOS, XMLNS, XSD, TIME, URIRef
from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.query import ResultRow
from shapely.wkt import loads
from shapely import get_dimensions
from namespaces import _PREFIX

FEATURE_IRI_VARIABLE = "feature_iri"
WKT_VARIABLE = "wkt"

FEATURE_WKT_QUERY = f"""
    PREFIX geo: <http://www.opengis.net/ont/geosparql#>
    SELECT ?{FEATURE_IRI_VARIABLE} ?{WKT_VARIABLE} 
    WHERE {{
        ?{FEATURE_IRI_VARIABLE} geo:hasGeometry ?geometry .
        ?geometry geo:asWKT ?{WKT_VARIABLE} .
    }}
"""

KWG_ENDPOINT = "http://stko-kwg.geog.ucsb.edu/"

KWGR = Namespace(f"{KWG_ENDPOINT}lod/resource/")

SPATIAL_ENDPOINT = "http://purl.org/"


# shortcut namespace that enumerates all those predicates
# used in this script
class KWG_ONT(DefinedNamespace):
    sfEquals: URIRef
    sfContains: URIRef
    sfWithin: URIRef
    sfTouches: URIRef
    sfOverlaps: URIRef
    sfCrosses: URIRef

    _NS = Namespace(f"{KWG_ENDPOINT}lod/ontology/")
    
    
class SPATIAL(DefinedNamespace):
    connectedTo: URIRef
    
    _NS = Namespace(f'{SPATIAL_ENDPOINT}spatialai/spatial/spatial-full#')


# _PREFIX = {
    # "kwgr": KWGR,
    # "kwg-ont": KWG_ONT._NS,
    # "geo": Namespace("http://www.opengis.net/ont/geosparql#"),
    # "geof": Namespace("http://www.opengis.net/def/function/geosparql/"),
    # "sf": Namespace("http://www.opengis.net/ont/sf#"),
    # "wd": Namespace("http://www.wikidata.org/entity/"),
    # "wdt": Namespace("http://www.wikidata.org/prop/direct/"),
    # "rdf": RDF,
    # "rdfs": RDFS,
    # "xsd": XSD,
    # "owl": OWL,
    # "time": TIME,
    # "dbo": Namespace("http://dbpedia.org/ontology/"),
    # "ssn": Namespace("http://www.w3.org/ns/ssn/"),
    # "sosa": Namespace("http://www.w3.org/ns/sosa/"),
    # "qudt": Namespace("http://qudt.org/schema/qudt/")
# }

_PREFIX = {
    "co_cgs": Namespace(f'http://sawgraph.spatialai.org/v1/co-cgs#'),
    "co_cgs_data": Namespace(f'http://sawgraph.spatialai.org/v1/co-cgs-data#'),
    "coso": Namespace(f'http://w3id.org/coso/v1/contaminoso#'),
    "dc": DC,
    "dcgeoid": Namespace(f'https://datacommons.org/browser/geoId/'),
    "dcterms": DCTERMS,  # or "terms" ?
    "epa_frs": Namespace(f'http://w3id.org/fio/v1/epa-frs#'),
    "epa_frs_data": Namespace(f'http://w3id.org/fio/v1/epa-frs-data#'),
    "fio-pfas": Namespace(f'http://w3id.org/fio/v1/pfas#'),
    "fio": Namespace(f'http://w3id.org/fio/v1/fio#'),
    "gcx": Namespace(f'https://geoconnex.us/'),
    "gcx_cid": Namespace(f'https://geoconnex.us/nhdplusv2/comid/'),
    "gcx_ms": Namespace(f'https://geoconnex.us/ref/mainstems/'),
    "gsmlb": Namespace(f'http://geosciml.org/def/gsmlb#'),
    "gwml2": Namespace(f'http://gwml2.org/def/gwml2#'),
    "hyf": Namespace(f'https://www.opengis.net/def/schema/hy_features/hyf/'),
    "hyfo": Namespace(f'http://hyfo.spatialai.org/v1/hyfo#'),
    "il_isgs": Namespace(f'http://sawgraph.spatialai.org/v1/il-isgs#'),
    "il_isgs_data": Namespace(f'http://sawgraph.spatialai.org/v1/il-isgs-data#'),
    "kwg-ont": Namespace(f'http://stko-kwg.geog.ucsb.edu/lod/ontology/'),
    "kwgr": Namespace(f'http://stko-kwg.geog.ucsb.edu/lod/resource/'),
    "me_egad": Namespace(f'http://w3id.org/sawgraph/v1/me-egad#'),
    "me_egad_data": Namespace(f'http://w3id.org/sawgraph/v1/me-egad-data#'),
    "me_mgs": Namespace(f'http://sawgraph.spatialai.org/v1/me-mgs#'),
    "me_mgs_data": Namespace(f'http://sawgraph.spatialai.org/v1/me-mgs-data#'),
    "naics": Namespace(f'http://w3id.org/fio/v1/naics#'),
    "nhdplusv2": Namespace(f'http://nhdplusv2.spatialai.org/v1/nhdplusv2#'),
    "obo": Namespace(f'http://purl.obolibrary.org/obo/'),
    "owl": OWL,
    "pfas": Namespace(f'http://sawgraph.spatialai.org/v1/pfas#'),
    "prov": PROV,
    "quantitykind": Namespace(f'http://qudt.org/vocab/quantitykind/'),
    "qudt": Namespace(f'http://qudt.org/schema/qudt/'),
    "rdf": RDF,
    "rdfs": RDFS,
    "saw_geo": Namespace(f'http://sawgraph.spatialai.org/v1/saw_geo#'),
    "schema": SDO,
    "sf": Namespace(f'http://www.opengis.net/ont/sf#'),
    "skos": SKOS,
    "sosa": Namespace('http://www.w3.org/ns/sosa/'),
    "spatial": Namespace(f'http://purl.org/spatialai/spatial/spatial-full#'),
    "stad": Namespace(f'http://purl.org/spatialai/stad/v2/core/'),
    "time": Namespace(f'http://www.w3.org/2006/time#'),
    "unit": Namespace(f'http://qudt.org/vocab/unit/'),
    "us_sdwis": Namespace(f'http://sawgraph.spatialai.org/v1/us-sdwis#'),
    "usgs": Namespace(f'http://usgs.spatialai.org/v1/usgs#'),
    "usgs_data": Namespace(f'http://usgs.spatialai.org/v1/usgs-data#'),
    "usgwd": Namespace(f'http://w3id.org/hyfo/usgwd/v1/usgwd#'),
    "wbd": Namespace(f'http://wbd.spatialai.org/v1/wbd#'),
    "wbd_data": Namespace(f'http://wbd.spatialai.org/v1/wbd-data#'),
    "wdt": Namespace(f'https://www.wikidata.org/prop/direct/'),
    "xml": XMLNS,
    "xsd": XSD
}

CONDITIONS = [
    {
        "predicate": KWG_ONT.sfEquals,
        "inverse": KWG_ONT.sfEquals,
        "mask": "T*F**FFF*"
    },
    {
        "predicate": KWG_ONT.sfWithin,
        "inverse": KWG_ONT.sfContains,
        "mask": "T*F**F***"
    },
    {
        "predicate": KWG_ONT.sfContains,
        "inverse": KWG_ONT.sfWithin,
        "mask": "T*****FF*"
    },
    {
        "predicate": KWG_ONT.sfTouches,
        "inverse": KWG_ONT.sfTouches,
        "mask": "FT*******"
    },
    {
        "predicate": KWG_ONT.sfTouches,
        "inverse": KWG_ONT.sfTouches,
        "mask": "F**T*****"
    },
    {
        "predicate": KWG_ONT.sfTouches,
        "inverse": KWG_ONT.sfTouches,
        "mask": "F***T****"
    },
]


class RelationString:
    """class to work with DE-9IM string codes
    """

    def __init__(self, relation_str: str):
        self.relation_str = relation_str
        self.bit_mask = self.mask()

    def mask(self) -> int:
        """return a bitmask of the true bits

        Returns:
            int: a bitmask of the true bits
        """
        mask = 0
        for idx, char in enumerate(self.relation_str[::-1]):
            if char in ['0', '1', '2', 'T']:
                mask |= 1 << idx
        return mask

    def matches_boolean_pattern(self, boolean_pattern: str) -> bool:
        """returns true if self matches another boolean pattern

        Args:
            boolean_pattern (str): a boolean pattern to check agains

        Returns:
            bool: the truth value of the match
        """
        for idx, char in enumerate(boolean_pattern[::-1]):
            bit = 1 << idx
            if char == 'T':
                if not self.bit_mask & bit:
                    return False
            elif char == 'F':
                if self.bit_mask & bit:
                    return False
        return True

    def matches_pattern(self, pattern: str) -> bool:
        for idx, char in enumerate(pattern):
            if not char == "*":
                if self.relation_str[idx] != char:
                    return False
        return True


class GeometricFeature:
    def __init__(self, query_solution: ResultRow) -> None:
        self.iri = query_solution[FEATURE_IRI_VARIABLE]
        self.geometry = loads(query_solution[WKT_VARIABLE])

    def yield_relations_with(
            self,
            other: GeometricFeature,
            conditions: list[dict]
    ) -> Generator[tuple[URIRef, URIRef, URIRef], None, None]:
        """yields those triples expressing all the relations with another feature 

        Args:
            other (GeometricFeature): another geometric feature

        Yields:
            Generator[tuple[URIRef, URIRef, URIRef], None, None]: a generator through those 
            triples expressing all the relations with another feature
        """
        relation_string = RelationString(self.geometry.relate(other.geometry))
        s = self.iri
        o = other.iri
        if s == o:
            return
        for condition in conditions:
            mask = condition["mask"]
            if relation_string.matches_boolean_pattern(mask):
                p = condition["predicate"]
                yield (s, p, o)
                i = condition["inverse"]
                yield (o, i, s)
                p = SPATIAL.connectedTo
                yield (s, p, o)
                yield (o, p, s)
        if get_dimensions(self.geometry) == get_dimensions(other.geometry) == 1:
            if relation_string.matches_pattern("0********"):
                p = KWG_ONT.sfCrosses
                yield (s, p, o)
                yield (o, p, s)
                p = SPATIAL.connectedTo
                yield (s, p, o)
                yield (o, p, s)

            if relation_string.matches_pattern("1*T***T**"):
                p = KWG_ONT.sfOverlaps
                yield (s, p, o)
                yield (o, p, s)
                p = SPATIAL.connectedTo
                yield (s, p, o)
                yield (o, p, s)

    def relation_graph_with(
            self,
            features2: list[GeometricFeature],
            conditions: list[dict],
            graph: Graph
    ) -> Graph:
        # graph = Graph()
        for feature2 in features2:
            for triple in self.yield_relations_with(other=feature2, conditions=conditions):
                graph.add(triple)
        return graph


def yield_file_paths(input_dir: str) -> Generator[str, None, None]:
    """yields those file_paths in input_dir except for .DS_Store, 
    which is a file created by walking
    
    Args:
        input_dir (str): the name of the directory hosting graphical data
    
    Yields:
        Generator[str, None, None]: a generator of file paths
    """
    for (path, _, files) in os.walk(input_dir):
        for file in files:
            if not file == ".DS_Store":
                file_path = os.path.join(path, file)
                yield file_path


def yield_geometric_features(path: str) -> Generator[GeometricFeature, None, None]:
    if os.path.isfile(path):
        graph = Graph()
        with open(path, 'r') as read_stream:
            graph.parse(read_stream)
        result = graph.query(FEATURE_WKT_QUERY)
        for query_solution in result:
            geometric_feature = GeometricFeature(query_solution)
            yield geometric_feature
    elif os.path.isdir(path):
        for file_path in yield_file_paths(path):
            for feature in yield_geometric_features(file_path):
                yield feature


def conditions_for_dimension_pair(dim1: int, dim2: int) -> list[dict]:
    if dim1 == 0 and dim2 == 0:
        return

    elif dim1 == 0 and dim2 == 1:
        relations = [
            {
                "predicate": KWG_ONT.sfCrosses,
                "inverse": KWG_ONT.sfCrosses,
                "mask": "T********"
            }
        ]
        return relations

    elif dim1 == 0 and dim2 == 2:
        return

    elif dim1 == 1 and dim2 == 0:
        relations = [
            {
                "predicate": KWG_ONT.sfCrosses,
                "inverse": KWG_ONT.sfCrosses,
                "mask": "T********"
            }
        ]
        return relations

    elif dim1 == 1 and dim2 == 1:
        # these conditions are checked separately in the yield_relations_with function
        return

    elif dim1 == 1 and dim2 == 2:
        relations = [
            {
                "predicate": KWG_ONT.sfCrosses,
                "inverse": KWG_ONT.sfCrosses,
                "mask": "T*T******"
            }
        ]
        return relations

    elif dim1 == 2 and dim2 == 0:
        return

    elif dim1 == 2 and dim2 == 1:
        relations = [
            {
                "predicate": KWG_ONT.sfCrosses,
                "inverse": KWG_ONT.sfCrosses,
                "mask": "T*****T**"
            }
        ]
        return relations

    elif dim1 == 2 and dim2 == 2:
        relations = [
            {
                "predicate": KWG_ONT.sfOverlaps,
                "inverse": KWG_ONT.sfOverlaps,
                "mask": "T*T***T**"
            }
        ]
        return relations

    else:
        msg = f"dimensions should be integers between 0 and 2 inclusive"
        raise ValueError(msg)


def write_all_relations(
        indexed_feature: tuple[int, GeometricFeature],
        features2: list[GeometricFeature],
        conditions: list[dict],
        output_folder: str
) -> Graph:
    graph = Graph()
    idx, feature1 = indexed_feature
    graph = feature1.relation_graph_with(features2, conditions, graph)
    # if graph:
    # for prefix in _PREFIX:
    #     graph.bind(prefix, _PREFIX[prefix])
    # file_name = f"{idx}.ttl"
    # destination = os.path.join(output_folder, file_name)
    # graph.serialize(destination=destination, format="ttl")
    return graph


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path1", type=str, help="path to first file or directory")
    parser.add_argument("dim1", type=int, help="dimension of those features in path1")
    parser.add_argument("path2", type=str, help="path to second file or directory")
    parser.add_argument("dim2", type=int, help="dimension of those features in path2")
    parser.add_argument("output_path", type=str, help="name of the output folder")

    args = parser.parse_args()

    path1 = args.path1
    path2 = args.path2
    output_folder = args.output_path
    # os.makedirs(output_folder, exist_ok=False)

    dim1 = args.dim1
    dim2 = args.dim2
    extra_conditions = conditions_for_dimension_pair(dim1, dim2)
    conditions = CONDITIONS

    if extra_conditions is not None:
        conditions.extend(extra_conditions)

    features2 = list(yield_geometric_features(path2))

    write = partial(
        write_all_relations,
        features2=features2,
        conditions=conditions,
        output_folder=output_folder
    )

    with Pool() as pool:
        graphs = pool.map(write, enumerate(yield_geometric_features(path1)))

    graph = Graph()
    for g in graphs:
        graph += g
    for prefix in _PREFIX:
        graph.bind(prefix, _PREFIX[prefix])
    # file_name = 'cross_int_output.ttl'
    # destination = os.path.join(output_folder, file_name)
    graph.serialize(destination=output_folder, format="ttl")

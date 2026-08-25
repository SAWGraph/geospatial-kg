Ontologies and datasets (triples) produced for this repository are licensed as [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

The [SAWGraph Spatial Ontology](sawgraph-spatial-ontology.ttl) is an extension of the [KnowWhereGraph Spatial Ontology](kwg-spatial-ontology.ttl). To simplify many queries, SAWGraph adds the `spatial:connectedTo' property, a superproperty of 'kwg-ont:sfContains', 'kwg-ont:sfCrosses', 'kwg-ont:sfEquals', 'kwg-ont:sfOverlaps', 'kwg-ont:sfTouches', and 'kwg-ont:sfWithin'.

The lite version comments out superproperties and superclasses that are not needed for effective querying of the data, shrinking the number of inferred triples to improve performance.

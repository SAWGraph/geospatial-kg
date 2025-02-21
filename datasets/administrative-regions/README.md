## S2 Cells
S2 cells are available to SAWGraph via the KnowWhereGraph project. Level 13 are currently in use. The cells, their integration with Level 1 and Level 2 administrative regions, and a smaller "class statement only" version are all processed via the S2 script included here, which supercedes the scripts found in the [s2cells](/datasets/s2cells) folder.

**Script**: *S2_Cells&Integration_Levels1&2-2ttl.py*
* Creates a .ttl file of all S2 cells (Level 13) that overlap or are within a given state. This data is queried from KnowWhereGraph.
* Creates a .ttl file with the S2 integration (Level 13) for the given state. This data is queried from KnowWhereGraph.
* Creates a .ttl file with the S2 integration (Level 13) for all of the counties in the given state. This data is queried from KnowWhereGraph.
* Creates a .ttl file containing only class assignments (*?x* rdf:type kwg-ont:S2Cell_Level13) from the first file above. This can be imported into any SAWGraph repository so federation to the Spatial repository is not required to enforce instances being Level 13 S2 Cells.

## Administrative Regions
Administrative regions are classified according to GADM. SAWGraph uses the first four levels: 0 country (implicit), 1 state, 2 county, and 3 county subdivision.

**Script**: *AdminRegion_state_class-statements_2ttl.py*
* Creates a .ttl file containing only class assignments (*?x* rdf:type kwg-ont:AdministrativeRegion_*#*) from the above files. This can be imported into any SAWGraph repository so federation to the Spatial repository is not required to enforce instances being a specific administrative region level.

### Administrative Regions: Level 1 (KnowWhereGraph)
SAWGraph obtains these from [KnowWhereGraph](https://www.knowwheregraph.org/)) along with their S2 integration.

**Script**: *AdminRegionsLevel1&2-2ttl.py*
* Creates us_admin-regions_level-1.ttl file with US state information queried from [KnowWhereGraph](https://stko-kwg.geog.ucsb.edu/graphdb/sparql).
* Creates a unique .ttl file for each US state with that state's county information queried from KnowWhereGraph.
* Adds an `owl:sameAs` relation to a `dcgeoid` identifier for linking to Data Commons.

### Administrative Regions: Level 2 (KnowWhereGraph)
SAWGraph obtains these from [KnowWhereGraph](https://www.knowwheregraph.org/)) along with their S2 integration.

**Script**: See *AdminRegionsLevel1&2-2ttl.py* above.

### Administrative Regions: Level 3 (US Census Bureau County Subdivisions)
SAWGraph obtains these from [US Census Bureau](https://www.census.gov/cgi-bin/geo/shapefiles/index.php)).
* County subdivisions are often townships but can also correspond to towns, especially in New England.
* This is as deep as the US Census Bureau goes with municipal subdivisions.
* Actual towns and cities tend to be noncontiguous leaving a patchwork of gaps.
* SAWGraph currently uses the 2023 versions of the County Subdivision shapefiles.
* S2 integration is performed with the assistance of scripts from KnowWhereGraph

County subdivisions (cousub) are easy to link to Data Commons by their 10-digit FIPS code (GEOID).

**Script**: *AdminRegionsLevel3-2ttl.py*
* Creates a .ttl file for all county subdivisions in a given state from data in a TIGER shapefile from the US Census Bureau.
* See the table below for additional detail.

| cousub attribute | Description | Lift to graph | Ontology property | Notes |
| --- | --- | --- | --- | --- |
| STATEFP | State FIPS code | Yes | kwg-ont:administrativePartOf | STATEFP + COUNTYFP |
| COUNTYFP | County FIPS code | Yes | kwg-ont:administrativePartOf | STATEFP + COUNTYFP |
| COUSUBFP | County subdivision FIPS code | No |  |  |
| COUSUBNS | County subdivision ANSI feature code | No |  |  |
| GEOID | County subidivision identifier | Yes | kwg-ont:hasFIPS |  |
| GEOIDFQ | Fully qualified GEOID | No |  |  |
| NAME | County subdivision name | No |  |  |
| NAMELSAD | Name and legal/statistical area description code | Yes | rdfs:label | + County + State |
| LSAD | Legal/statistical area description code | No |  |  |
| CLASSFP | FIPS class code | No |  |  |
| MTFCC | MAF/TIGER feature class code | No |  |  |
| FUNCSTAT | Functional status | No |  |  |
| ALAND | Land area | No |  |  |
| AWATER | Water area | No |  |  |
| INTPTLAT | Internal point latitude | No |  |  |
| INTPTLON | Internal point longitude | No |  |  |
| geometry | Polygon | Yes | geo:hasGeometry/geo:asWKT |  |

## Additional Administrative Region Information
For the state of Maine (ME) town and parcel data can be downloaded from the Maine State GeoLibrary Data Catalog
  1. [Maine Town and Townships Boundary Polygons Feature](https://maine.hub.arcgis.com/datasets/maine::maine-town-and-townships-boundary-polygons-feature-1/explore?showTable=true)
  2. [Maine Parcels Organized Towns Feature](https://maine.hub.arcgis.com/maps/maine::maine-parcels-organized-towns-feature/about) and [Maine Parcels Unorganized Territory](https://maine.hub.arcgis.com/datasets/868097d1a133446f8ffae242929a25dd/explore)

The US Census Bureau provides the latest [TIGER/Line® shapefiles](https://www.census.gov/cgi-bin/geo/shapefiles/index.php) for various regions beyond state, county, and county subdivision.
The following types of regions are available:
  1. American Indian Area Geography
  2. Blocks
  3. Block Groups
  4. Census Tracts
  5. Congressional Districts
  6. Consolidated Cities
  7. Core Based Statistical Areas
  8. Counties (and equivalent)
  9. County Subdivisions
  10. Estate
  11. International Boundary
  12. Places
  13. Public Use Microdata Areas
  14. School District
  15. School District Administrative Areas (SDAM)
  16. States (and equivalent)
  17. State Legislative District
  18. Subbario (SubMinor Civil Division)
  19. Urban Areas
  20. ZIP Code Tabulation Areas

### Contributors
* [David Kedrowski](https://github.com/dkedrowski)
* [Shirly Stephen](https://github.com/shirlysteph)
* [Torsten Hahmann](https://github.com/thahmann)

## Administrative Regions
For SAWGraph, admininstrative regions include
* States (AdministrativeRegion_1; from KnowWhereGraph)
* Counties (AdministrativeRegion_2; from KnowWhereGraph)
* County subdivisions (AdministrativeRegion_3; from US Census Bureau) - these are often townships
  * Actual towns and cities tend to be noncontiguous leaving a patchwork of gaps
  * This is as deep as the US Census Bureau goes with municipal subdivisions

The representation of states and counties are from [GADM](https://gadm.org/data.html). There is no data for more granular regions, such as towns (AdministrativeRegion_3).

County subdivisions are easy to link to Data Commons by their 10-digit FIPS code (GEOID).
Their shapefiles are available [here](https://www.census.gov/cgi-bin/geo/shapefiles/index.php).

Currently, the graph includes county subdivisions from Maine and Illinois.

* For the state of Maine (ME) town and parcel data can be downloaded from the Maine State GeoLibrary Data Catalog
  1. [Maine Town and Townships Boundary Polygons Feature](https://maine.hub.arcgis.com/datasets/maine::maine-town-and-townships-boundary-polygons-feature-1/explore?showTable=true)
  2. [Maine Parcels Organized Towns Feature](https://maine.hub.arcgis.com/maps/maine::maine-parcels-organized-towns-feature/about) and [Maine Parcels Unorganized Territory](https://maine.hub.arcgis.com/datasets/868097d1a133446f8ffae242929a25dd/explore)

For additional states, the US Census Bureau provides the latest TIGER/Line® shapefiles for various regions, including county subdivisions [here](https://www.census.gov/cgi-bin/geo/shapefiles/index.php).
The following types of regions are provided:
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

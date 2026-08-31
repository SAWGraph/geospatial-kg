# Spatial Integration

SAWGraph integrates all features with a geometric representation to two datasets: level 13 S2 cells (S2) and level 3 administrative regions (AR3) - county subdivisions such as townships in the US. The S2 cells provide a global grid that can be used to determine when features are near each other. The administrative regions allow users to select only those features within some given political boundary, such as states, counties, and county subdivisions. Integrating to just two (carefully chosen) datasets helps keep an already large knowledge to a manageable size.

## Folders

- `KWG Tools`: contains a tool from KnowWhereGraph to cross-integrate any two turtle files that include features with geometries, as long as each includes geometries of a consistent dimension
- `s2-coverings`: contains SAWGraph's modifications to the [s2-coverings tool from KnowWhereGraph](https://github.com/KnowWhereGraph/s2-coverings) which includes two tools, one to create S2 cells (not used as part of the integration process) and one to integrate an input turtle file with S2 cells
- `input`: as currently implemented, this is a place to put a single turtle file for integration with both S2 and AR3
- `output`: each execution of SAWGraph's tool creates two turtle files, one for S2 integration and one for AR3 integration, and they are written here
- `us_ar3`: contains turtle files of level 3 administrative regions on a state-by-state basis
- `us_s2`: contains turtle files of level 13 S2 cells on a state-by-state basis
- `support`: contains a .tsv file that is a crosswalk between states, state names, state abbreviations, county names, and FIPS codes

## Python Files

- `namespaces.py`: contains a dictionary of project namespaces so the resulting outfiles can use easier to read CURIEs instead of full IRIs
- `xintegrate.py`: SAWGraph's version of KWG's cross-integration script (used for integrating with level 3 administrative regions)
- `s2-coverings\src\integrate.py`: SAWGraph's version of KWG's S2 integration script
- `integrate_s2_ar3.py`: the primary script to coordinate the S2 and AR3 integration

## Implementation

All of the files and directories above should be copied to some working directory.
Additionally ...

### Examples

`python3 integrate_s2_ar3.py --states "CO NM TX" --path input --dim 2 --name hydrofabric_catchment_huc13`
- `--states`: HUC 13 covers portions of 3 states (always put multiple states in quotes separated by spaces)
- `--path`: the input .ttl file is in the `input` directory within the working directory
- `--dim`: the geometries are polygons (2 dimensional)
- `--name`: the output files (placed in the `output` directory within the working directory) will have `s2_` or `ar3_` prefixed and .ttl appended to them
- 
`python3 integrate_s2_ar3.py --states "CO NM TX" --path input --dim 1 --name us_nhd_flowline_huc13`
- `--states`: HUC 13 covers portions of 3 states (always put multiple states in quotes separated by spaces)
- `--path`: the input .ttl file is in the `input` directory within the working directory
- `--dim`: the geometries are lines (1 dimensional)
- `--name`: the output files (placed in the `output` directory within the working directory) will have `s2_` or `ar3_` prefixed and .ttl appended to them
- 
`python3 integrate_s2_ar3.py --states CO --path input --dim 0 --name co-dwr_wells_from-api`
- `--states`: these are Colorado water wells (quotes are not needed for a single state)
- `--path`: the input .ttl file is in the `input` directory within the working directory
- `--dim`: the geometries are points (0 dimensional)
- `--name`: the output files (placed in the `output` directory within the working directory) will have `s2_` or `ar3_` prefixed and .ttl appended to them

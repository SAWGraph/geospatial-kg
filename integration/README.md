# Spatial Integration
SAWGraph integrates all features with a geometric representation to two datasets: level 13 S2 cells (S2) and level 3 administrative regions (AR3), which are county subdivisions such as townships in the US. The S2 cells provide a global grid that can be used to determine when features are near each other. The administrative regions allow users to select only those features within some given political boundary, such as states, counties, and county subdivisions. Integrating to just two (carefully chosen) datasets helps keep an already large knowledge graph to a more manageable size.

## Workspace
Choose or create a folder/directory for your workspace. Within that workspace you will need the following folders and files:

**Python Files**
- `integrate_s2_ar3.py`: the primary script to coordinate the S2 and AR3 integration
- `namespaces.py`: contains a dictionary of project namespaces so the resulting outfiles can use easier to read CURIEs instead of full IRIs (this may require updates over time)
- `xintegrate.py`: SAWGraph's version of KWG's cross-integration script (used for integrating with level 3 administrative regions) (see `KWG Tools.zip` below)

**Folders**
- `input`: as currently implemented, this is a place to put a single turtle file for integration with both S2 and AR3
- `output`: each execution of SAWGraph's tool creates two turtle files, one for S2 integration and one for AR3 integration, and they are written here
- `s2-coverings`: contains SAWGraph's modifications to the [s2-coverings tool from KnowWhereGraph](https://github.com/SAWGraph/s2-coverings) which includes two tools, one to create S2 cells (not used as part of the integration process) and one to integrate an input turtle file with S2 cells. There are two branches, `integration-c101` created for a Rocky Linux server using Apptainer and `integration-win` created for Windows using Docker.
- `support`: contains a .tsv file that is a crosswalk between states, state names, state abbreviations, county names, and FIPS codes
- `us_ar3`: contains turtle files of level 3 administrative regions on a state-by-state basis (see `Other Files` below)
- `us_s2`: contains turtle files of level 13 S2 cells on a state-by-state basis (see `Other Files` below)

**Other Files in this Github Folder**
- `KWG Tools.zip`: contains the original tool from KnowWhereGraph to cross-integrate any two turtle files that include features with geometries, as long as each includes geometries of a consistent dimension

**Other Files at Zenodo**
- `us_ar3.zip`: the contents of this zip file should be placed within the `us_ar3` folder in the workspace, including the `current_ar3` subfolder
- `us_s2.zip`: the contents of this zip file should be placed within the `us_s2` folder in the workspace
- `s2-coverings-main.sif`: this file should be placed in the `s2-coverings/src` folder when used on a system using Apptainer instead of Docker

**Workspace Structure**

This is an abbreviated and annotated view of what a typical workspace structure will look like
```
working_directory
|   integrate_s2_ar3.py
|   namespaces.py
|   xintegrate.py
|
+---input              Place a copy of the current file requiring integration here
|
+---output             Output .ttl files will be written here
|
+---s2-coverings       files and subfolders not shown here
|
+---support                                              
|   fips2county.tsv
|
+---us_ar3             State-by-state .ttl files not shown here (from us_ar3.zip)
|   \---current_ar3    empty (used to temporarily store files during script execution)
|
\---us_s2              State-by-state .ttl files not shown here (from us_s2.zip)
```

## Use
From a command line within the working directory, the script is called with four parameters.
- `--states`: for a single state, just list its 2-character abbreviation (in caps); for multiple states, put them in double quotes separated by spaces
- `--path`: the location of the input file (just `input` for the directory structure shown above)
- `--dim`: the dimension of the input geometries (0 for points, 1 for lines, and 2 for polygons)
- `--name`: the output files will have `s2_` or `ar3_` prepended and .ttl appended to this

Examples of each dimension are provided with additional notes. Docker needs to be running before executing the script.

### Examples
`python3 integrate_s2_ar3.py --states "CO NM TX" --path input --dim 2 --name hydrofabric_catchment_huc13`
- `--states`: HUC 13 covers portions of 3 states (always put multiple states in quotes separated by spaces)
- `--dim`: the geometries are polygons (2 dimensional)

`python3 integrate_s2_ar3.py --states "CO NM TX" --path input --dim 1 --name us_nhd_flowline_huc13`
- `--dim`: the geometries are lines (1 dimensional)

`python3 integrate_s2_ar3.py --states CO --path input --dim 0 --name co-dwr_wells_from-api`
- `--states`: these are Colorado water wells (quotes are not needed for a single state)
- `--dim`: the geometries are points (0 dimensional)

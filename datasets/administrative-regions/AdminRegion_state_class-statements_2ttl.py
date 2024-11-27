"""Create a single .ttl file of just the rdf:type statements for all admin regions for a single state

Under ### State ###, define
    the state's two-letter abbreviation in lower case and
    the state's 2-digit FIPS code as a string

Under ### Input Files ###, define
    the input path / filename template for level 1 administrative regions,
    the input path / filename template for level 2 administrative regions, and
    the input path / filename template for level 3 administrative regions

Under ### Output File ###, define
    the path / filename for the output .ttl file for the given state's class statements

Under ### Prefixes ###, define a list of
    rdf prefixes needed for the AdminRegion class statements (levels 1-3)
"""
### State ###
state_abbr = 'il'
state_fips = '17'
state_iri = 'kwgr:administrativeRegion.USA.' + state_fips

### Input FIles ###
input1 = 'ttl_files/AdministrativeRegion_1/us_admin-regions_level-1.ttl'
input2 = 'ttl_files/AdministrativeRegion_2/' + state_abbr + '_' + state_fips + '_admin-regions_level-2.ttl'
input3 = 'ttl_files/AdministrativeRegion_3/' + state_abbr + '_' + state_fips + '_admin-regions_level-3.ttl'

### Output File ###
output = 'ttl_files/class_statements/' + state_abbr + '_' + state_fips + '_admin-region_class-statements.ttl'

### Prefixes ###
prefixes = ['@prefix dcgeoid: <https://datacommons.org/browser/geoId/> .',
            '@prefix kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/> .',
            '@prefix kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/> .',
            '@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .']

# Create the output .ttl file
with open(output, 'w') as outfile:
    # Add the prefixes to the output file
    for prefix in prefixes:
        outfile.write(prefix)
        outfile.write('\n')
    outfile.write('\n')
    with open(input1, 'r') as infile:
        for line in infile:
            # Finds the class statement for AdministrativeRegion_1
            if state_iri in line:
                outfile.write(line.replace(';', '.'))  # Making sure syntax is correct
    for input in [input2, input3]:
        with open(input, 'r') as infile:
            for line in infile:
                # Finds the class statements for AdministrativeRegion_2 and AdministrativeRegion_3
                if 'administrativeregion_' in line.lower():
                    outfile.write(line.replace(';', '.'))  # Making sure syntax is correct

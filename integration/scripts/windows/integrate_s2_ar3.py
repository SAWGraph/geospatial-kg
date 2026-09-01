import argparse
from pathlib import Path
import pandas as pd
from rdflib import Graph
import shutil
import os
import sys
import time
import datetime
from namespaces import _PREFIX


def initial_kg(_PREFIX):
    print('      Initializing an RDFLib Graph()')
    graph = Graph()
    for prefix in _PREFIX:
        graph.bind(prefix, _PREFIX[prefix])
    return graph


def consolidate_ttl_files(filespath, outfilename):
    print('\n   Consolidating output files to a single turtle file')
    graph = initial_kg(_PREFIX)
    for filename in os.listdir(filespath):
        if filename.endswith('.ttl'):
            graph.parse(filespath / filename)
    print('      Serializing the Graph() as a turtle file')
    graph.serialize(destination=outfilename)
    shutil.rmtree(filespath)


def integrate_s2(states, source, wd, input_path, name):
    print('\nPerforming S2 integration')
    ### Copy appropriate state files to the working directory ###
    print('   Copying state S2 files to working directory')
    for state in states:
        fips = fips_df[fips_df['StateAbbr'] == state.upper()]['StateFIPS'].iloc[0]
        s2name = f'{state.lower()}_{fips:02d}_s2-l13.ttl'
        shutil.copy2(source / s2name, wd)

    ### Execute s2-coverings/src/integrate.py script
    print('   Integrating\n')
    try:
        os.system(
            f'docker run -v ./:/s2 ghcr.io/knowwheregraph/s2-coverings:main python3 s2-coverings/src/integrate.py --path {input_path}')
    except Exception as e:
        print(f'Exception: {e}')

    ### Cleanup: delete state files from the working directory ###
    ###          rename S2 integration output file
    print('\n   Cleaning up working directory\n   Renaming S2 integration output file')
    for state in states:
        fips = fips_df[fips_df['StateAbbr'] == state.upper()]['StateFIPS'].iloc[0]
        s2name = f'{state.lower()}_{fips:02d}_s2-l13.ttl'
        os.unlink(s2_wd / s2name)
    try:
        out_path = Path() / 'output'
        s2_out_file = list(out_path.glob('*_compressed'))
        os.rename(s2_out_file[0], f'./output/s2_{name}.ttl')
    except FileNotFoundError:
        print('S2 integration output file ("input compressed") not found')
    except PermissionError:
        print('Permission to rename S2 integration output file denied')
    except Exception as e:
        print(f'Renaming the S2 integration output file failed: {e}')


def integrate_ar3(states, source, wd, input_path, dim, outfile):
    print('\nPerforming AR3 integration')
    ### Copy appropriate state files to the working directory ###
    print('   Copying state AR3 files to working directory')
    for state in states:
        fips = fips_df[fips_df['StateAbbr'] == state.upper()]['StateFIPS'].iloc[0]
        ar3name = f'{state.lower()}_{fips:02d}_admin-regions_level-3.ttl'
        shutil.copy2(source / ar3name, wd)

    ### #Execute xintegrate.py script
    print('   Integrating\n')
    try:
        os.system(f'py xintegrate.py {input_path} {dim} {wd} 2 {outfile}')
    except Exception as e:
        print(f'Exception: {e}')

    ### Cleanup: delete state files from the working directory ###
    print('   Cleaning up working directory\n')
    for state in states:
        fips = fips_df[fips_df['StateAbbr'] == state.upper()]['StateFIPS'].iloc[0]
        ar3name = f'{state.lower()}_{fips:02d}_admin-regions_level-3.ttl'
        os.unlink(ar3_wd / ar3name)


if __name__ == '__main__':
    start_time = time.time()

    ### Parse command line arguments ###
    parser = argparse.ArgumentParser(
        prog='integrate_s2',
        description='essentially a wrapper/interface for the KWG/Integration integrate.py script (for integrating geometries with S2 cells) and KWG integrate.py script (for doing cross integration, here fixed to county subdivisions, or administrative regions level 3)'
    )
    parser.add_argument('-s', '--states')
    parser.add_argument('-p1', '--path')
    parser.add_argument('-d1', '--dim')
    parser.add_argument('-n', '--name')
    args = parser.parse_args()
    try:
        state_list = args.states.split()
    except Exception as e:
        print('No --states argument present or not formatted as a space delimited string.')
        sys.exit()

    ### Set up folders ###
    cwd = Path()  # .resolve()
    fips2county = cwd / 'support/fips2county.tsv'
    s2_source = cwd / 'us_s2'
    s2_wd = cwd / 's2-coverings/output/level_13'
    s2_out = cwd / f'output/s2_{args.name}.ttl'
    ar3_source = cwd / 'us_ar3'
    ar3_wd = cwd / 'us_ar3/current_ar3'
    ar3_out = cwd / f'output/ar3_{args.name}.ttl'

    ### Create df to convert state abbreviations to 2-digit FIPS codes ###
    fips_df = pd.read_csv(fips2county, sep='\t')

    integrate_s2(state_list, s2_source, s2_wd, args.path, args.name)
    integrate_ar3(state_list, ar3_source, ar3_wd, args.path, args.dim, ar3_out)

    print(f'Runtime: {str(datetime.timedelta(seconds=time.time() - start_time))} HMS\n')

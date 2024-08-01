#!/usr/bin/env python3
# ******************************************************************************
# ms_sword_edit.py
# ******************************************************************************

# Purpose:
# Given a SWORD shapefiles, this script ensures that SWORD
# geometries use the same longitude convention as MERIT-Basins-Basins near the
# international date line. This script also creates an empty SWORD shapefile
# for Pfaf 54, which contains no SWORD reaches.

# Author:
# Jeffrey Wade, 2024


# ******************************************************************************
# Import Python modules
# ******************************************************************************
import sys
import fiona
from fiona.model import to_dict


# ******************************************************************************
# Declaration of variables (given as command line arguments)
# ******************************************************************************
# 1 - sword_shp
# 2 - sword_out


# ******************************************************************************
# Get command line arguments
# ******************************************************************************
IS_arg = len(sys.argv)
if IS_arg != 3:
    print('ERROR - 2 arguments must be used')
    raise SystemExit(22)

sword_shp = sys.argv[1]
sword_out = sys.argv[2]


# ******************************************************************************
# Check if folders exist
# ******************************************************************************
# Empty sword region will fail this test, catch error
if not (sword_shp.split('hb')[1][0:2] == '54'):

    try:
        with open(sword_shp) as file:
            pass
    except IOError:
        print('ERROR - Unable to open '+sword_shp)
        raise SystemExit(22)


# ******************************************************************************
# Edit SWORD geometries for relevant regions
# ******************************************************************************
print('- Editing geometries')

# ------------------------------------------------------------------------------
# Alter SWORD geometries of pfaf 35 to match MERIT-Basins handling of
# -180 meridian
# ------------------------------------------------------------------------------
if sword_shp.split('hb')[1][0:2] == '35':

    with fiona.open(sword_shp, 'r') as source:

        meta = source.meta

        with fiona.open(sword_out, 'w', **meta) as output:

            for rch in source:

                # Store geometry coordinates dictionary
                rch_crd = rch['geometry']['coordinates']

                # Loop through coordinates, checking for values east of
                # meridian
                for i in range(len(rch_crd)):

                    if rch_crd[i][0] < 0:

                        # Calculate new lon in MERIT-Basins proj
                        # (allowing lon>180)
                        new_x_crd = 180 + -1*(-180 - rch_crd[i][0])

                        # Update coordinate tuple in rch_crd
                        rch_crd[i] = (new_x_crd, rch_crd[i][1])

                # Replace coordinate geometry in reach and write to file
                new_rch = to_dict(rch)

                new_rch['geometry']['coordinates'] = rch_crd

                output.write(new_rch)

# ------------------------------------------------------------------------------
# Write empty sword shapefile for missing pfaf 54 file (no sword reaches)
# ------------------------------------------------------------------------------
elif sword_shp.split('hb')[1][0:2] == '54':

    # Alter filepath to load another file
    sword_new_shp = sword_shp.split('hb')[0] + 'hb53' + sword_shp.split('54')[1]

    # Write an empty polygon shapefile, using another region as source
    with fiona.open(sword_new_shp, 'r') as source:

        meta = source.meta

        with fiona.open(sword_out, "w", **meta):
            pass

# ------------------------------------------------------------------------------
# Copy unchanged SWORD files into new fixed folder
# ------------------------------------------------------------------------------
else:

    # Copy unchanged file to output data
    with fiona.open(sword_shp, 'r') as source:

        meta = source.meta

        with fiona.open(sword_out, 'w', **meta) as output:
            for rch in source:
                output.write(rch)

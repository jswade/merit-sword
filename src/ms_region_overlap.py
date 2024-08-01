# !/usr/bin/env python3
# *******************************************************************************
# ms_region_overlap.py
# ******************************************************************************

# Purpose:
# Given an folder containing SWORD shapefiles and MERIT-Basins dissolved
# his script identifies overlaps between hydrologic regions as defined by SWORD
# and MERIT-Basins.

# Author:
# Jeffrey Wade, 2024

# ******************************************************************************
# Import Python modules
# ******************************************************************************
import sys
import os
import numpy as np
import pandas as pd
import fiona
import shapely.geometry
import shapely.ops
import shapely.prepared
import glob


# ******************************************************************************
# Declaration of variables (given as command line arguments)
# ******************************************************************************
# 1 - sword_in
# 2 - mb_in
# 3 - sw_to_mb_out
# 4 - mb_to_sw_out


# ******************************************************************************
# Get command line arguments
# ******************************************************************************
IS_arg = len(sys.argv)
if IS_arg != 5:
    print('ERROR - 4 arguments must be used')
    raise SystemExit(22)

sword_in = sys.argv[1]
mb_in = sys.argv[2]
sw_to_mb_out = sys.argv[3]
mb_to_sw_out = sys.argv[4]


# ******************************************************************************
# Check if folders exist
# ******************************************************************************
try:
    if os.path.isdir(sword_in):
        pass
except IOError:
    print('ERROR - '+sword_in+' invalid folder path')
    raise SystemExit(22)

try:
    if os.path.isdir(mb_in):
        pass
except IOError:
    print('ERROR - '+mb_in+' invalid folder path')
    raise SystemExit(22)


# ******************************************************************************
# Check if region overlap files have already been generated
# ******************************************************************************
try:
    with open(sw_to_mb_out) as file:
        print('Overlap files already generated')
        sys.exit()
except IOError:
    pass

try:
    with open(mb_to_sw_out) as file:
        print('Overlap files already generated')
        sys.exit()
except IOError:
    pass


# ******************************************************************************
# Read shapefiles
# ******************************************************************************
print('- Editing geometries')

# ------------------------------------------------------------------------------
# MERIT-Basins Dissolved Catchments
# ------------------------------------------------------------------------------
# Read MERIT-Basins dissolved catchment files
dis_mb_files = list(glob.iglob(mb_in+'*.shp'))

# Sort reach files by value
dis_mb_files.sort()

# Convert to shapefile
dis_mb_all = [fiona.open(j, 'r', crs="EPSG:4326") for j in dis_mb_files]

# Retrieve pfaf numbers from file
pfaf_list = pd.Series([x.partition("pfaf_")[-1][0:2]
                       for x in dis_mb_files]).sort_values()

# Sort pfaf_list
pfaf_srt = pfaf_list.sort_values(ignore_index=True)
pfaf_srt = pfaf_srt.reset_index(drop=True)

# ------------------------------------------------------------------------------
# SWORD
# ------------------------------------------------------------------------------

# Read SWORD files
sword_files = list(glob.iglob(sword_in+'*.shp'))

# Retrieve pfaf numbers from file
pfaf_sw_list = pd.Series([x.partition("reaches_hb")[-1][0:2]
                          for x in sword_files]).sort_values()

# Sort files by pfaf to align with MERIT-Basins
sword_files = pd.Series(sword_files)[pfaf_sw_list.index.values].tolist()

# Convert to shapefile
sword_lay_all = [fiona.open(j, 'r', crs="EPSG:4326") for j in sword_files]


# ******************************************************************************
# Identify mapping of SWORD regions to overlapping MB regions
# ******************************************************************************
print('- Identifying overlap of regions')

# Prepare geometries of each MERIT-Basins catchment boundary
dis_pre_all = []
dis_shy_all = []

for j in range(len(dis_mb_all)):

    # Create shapely geometric object for dissolved MB catchments
    dis_shy = shapely.geometry.shape(dis_mb_all[j][0]['geometry'])

    # Create prepared geometric object to allow for faster processing
    dis_pre = shapely.prepared.prep(dis_shy)

    dis_pre_all.append(dis_pre)
    dis_shy_all.append(dis_shy)

# Initalize list to store MB regions corresponding to each sword region
sw_to_mb_id = []

# Loop through pfaf regions
for j in range(len(pfaf_srt)):

    # --------------------------------------------------------------------------
    # Load pfaf specific files
    # --------------------------------------------------------------------------

    # Retrieve SWORD reaches for each pfaf
    sword_lay = sword_lay_all[j]

    # Retrieve prepared MERIT-Basins region boundary for each pfaf
    dis_pre = dis_pre_all[j]

    # Retrieve all MERIT-Basins regions except for current loop iteration
    dis_pre_else = dis_pre_all[:j] + dis_pre_all[j+1:]
    pfaf_else = pfaf_srt.drop(j).tolist()

    # --------------------------------------------------------------------------
    # Identify other MB regions that contain SWORD reaches for a given region
    # --------------------------------------------------------------------------

    # Initialize list to store corresponding MERIT-Basins region ids
    id_list = [pfaf_srt[j]]

    # Loop through SWORD reaches
    for sword_fea in sword_lay:

        # Create geometry object for SWORD reach
        sword_shy = shapely.geometry.shape(sword_fea['geometry'])

        # If reach is outside correct MERIT-Basins region boundary
        if not dis_pre.contains(sword_shy):

            # Check if reach is contained by another MERIT-Basins region
            for i in range(len(dis_pre_else)):

                # Retrieve feature
                cat_fea = dis_pre_else[i]

                # If reach is within another MB catchment, flag region
                if cat_fea.intersects(sword_shy):

                    # Append region to list
                    id_list.append(pfaf_else[i])

    # Append unique regions to mb_id list
    sw_to_mb_id.append(sorted(list(set(id_list))))


# ******************************************************************************
# Generate CSV files for output
# ******************************************************************************
print('- Writing overlaps to file')
# ------------------------------------------------------------------------------
# SWORD region to overlapping MB regions
# ------------------------------------------------------------------------------
# Find max overlapping regions for a single region
max_mb = max(len(x) for x in sw_to_mb_id)

# Pad lists to the same length
sw_to_mb_pad = [x + [np.nan] * (max_mb - len(x)) for x in sw_to_mb_id]

# Convert to df
sw_to_mb_reg = pd.DataFrame(sw_to_mb_pad)

# Set index to pfaf_srt
sw_to_mb_reg.index = pfaf_srt

# Rename columns
sw_to_mb_reg.index.name = 'sword'
sw_to_mb_reg.columns = ['mb'+str(x) for x in range(max_mb)]

# Write to file
sw_to_mb_reg.to_csv(sw_to_mb_out)

# ------------------------------------------------------------------------------
# MB region to overlapping SWORD regions
# ------------------------------------------------------------------------------
# Convert mb_ind to dictionary
sw_to_mb_dict = {}

for j in range(len(sw_to_mb_id)):
    sw_to_mb_dict[pfaf_srt[j]] = sw_to_mb_id[j]

# Reverse dictionary to map MB regions to overlapping SWORD regions
mb_to_sw_dict = {}

for key, val in sw_to_mb_dict.items():
    for reg in val:
        if reg not in mb_to_sw_dict:
            mb_to_sw_dict[reg] = []
        mb_to_sw_dict[reg].append(key)

# Sort dictionary
mb_to_sw_dict = {key: mb_to_sw_dict[key] for key in sorted(mb_to_sw_dict)}

# Find max overlapping regions for a single region
max_sw = max(len(x) for x in mb_to_sw_dict.values())

# Pad lists to the same length
mb_to_sw_pad = {x: y + [np.nan] * (max_sw - len(y)) for x, y in
                mb_to_sw_dict.items()}

# Convert to df
mb_to_sw_reg = pd.DataFrame.from_dict(mb_to_sw_pad, orient='index')

# Rename columns
mb_to_sw_reg.index.name = 'mb'
mb_to_sw_reg.columns = ['sword'+str(x) for x in range(max_sw)]

# Write to file
mb_to_sw_reg.to_csv(mb_to_sw_out)

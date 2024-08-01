#!/usr/bin/env python3
# ******************************************************************************
# ms_app_sword_to_mb.py
# ******************************************************************************

# Purpose:
# Given translations between MERIT-Basins and SWORD, a SWORD river shapefile,
# and a river shapefile from MERIT-Basins, this script confirm maps SWORD
# width estimates onto MB reaches

# Author:
# Jeffrey Wade, 2024


# ******************************************************************************
# Import Python modules
# ******************************************************************************
import sys
import re
import glob
import pandas as pd
import xarray as xr
import fiona
import numpy as np


# ******************************************************************************
# Declaration of variables (given as command line arguments)
# ******************************************************************************
# 1 - ms_trans_nc
# 2 - riv_mb_shp
# 3 - sword_shp
# 4 - mb_out


# ******************************************************************************
# Get command line arguments
# ******************************************************************************
IS_arg = len(sys.argv)
if IS_arg != 5:
    print('ERROR - 4 arguments must be used')
    raise SystemExit(22)

ms_trans_nc = sys.argv[1]
riv_mb_shp = sys.argv[2]
sword_shp = sys.argv[3]
mb_out = sys.argv[4]


# ******************************************************************************
# Check if files exist
# ******************************************************************************
try:
    with open(ms_trans_nc) as file:
        pass
except IOError:
    print('ERROR - Unable to open '+ms_trans_nc)
    raise SystemExit(22)

try:
    with open(riv_mb_shp) as file:
        pass
except IOError:
    print('ERROR - Unable to open '+riv_mb_shp)
    raise SystemExit(22)

try:
    with open(sword_shp) as file:
        pass
except IOError:
    print('ERROR - Unable to open '+sword_shp)
    raise SystemExit(22)

# Confirm files refer to same region
ms_trans_reg = ms_trans_nc.split('pfaf_')[1][0:2]
riv_mb_reg = riv_mb_shp.split('pfaf_')[1][0:2]
sword_reg = sword_shp.split('hb')[1][0:2]
mb_out_reg = mb_out.split('pfaf_')[1][0:2]

if not (ms_trans_reg == riv_mb_reg == sword_reg == mb_out_reg):
    print('ERROR - Input files correspond to different regions')
    raise SystemExit(22)


# ******************************************************************************
# Read shapefiles
# ******************************************************************************
print('- Reading files')
# ------------------------------------------------------------------------------
# MERIT-Basins Reaches
# ------------------------------------------------------------------------------
# Read MERIT-Basins River files
riv_mb_files = list(glob.iglob(re.sub(r'(?<=/riv/).*?(?=\.shp)', '*',
                    riv_mb_shp)))

# Sort reach files by value
riv_mb_files.sort()

# Convert to shapefile
riv_mb_all = [fiona.open(j, 'r', crs="EPSG:4326") for j in riv_mb_files]

# Retrieve pfaf numbers from file
mb_pfaf_list = pd.Series([x.partition("pfaf_")[-1][0:2]
                          for x in riv_mb_files]).sort_values()

# Sort pfaf_list
pfaf_srt = mb_pfaf_list.sort_values(ignore_index=True)
pfaf_srt = pfaf_srt.reset_index(drop=True)

# ------------------------------------------------------------------------------
# MB-to-SWORD Translation
# ------------------------------------------------------------------------------
# Read MB-to-SWORD files
ms_files = list(glob.iglob(re.sub(r'(?<=/mb_to_sword/).*?(?=\.nc)', '*',
                ms_trans_nc)))

# Sort reach files by value
ms_files.sort()

# Convert to shapefile
ms_all = [xr.open_dataset(j).to_dataframe() for j in ms_files]

# ------------------------------------------------------------------------------
# SWORD
# ------------------------------------------------------------------------------
# Read SWORD files
sword_files = list(glob.iglob(re.sub(r'(?<=/sword_edit/).*?(?=\.shp)', '*',
                                     sword_shp)))

# Retrieve pfaf numbers from file
sw_pfaf_list = pd.Series([x.partition("reaches_hb")[-1][0:2]
                          for x in sword_files]).sort_values()

# Sort files by pfaf to align with MERIT-Basins
sword_files = pd.Series(sword_files)[sw_pfaf_list.index.values].tolist()

# Convert to shapefile
sword_all = [fiona.open(j, 'r', crs="EPSG:4326") for j in sword_files]


# ------------------------------------------------------------------------------
# Get indices of target region shapefiles
# ------------------------------------------------------------------------------
ms_trans_ind = ms_files.index(ms_trans_nc)
riv_mb_ind = riv_mb_files.index(riv_mb_shp)
sword_ind = sword_files.index(sword_shp)


# ******************************************************************************
# Store SWORD width value in dictionary
# ******************************************************************************
print('- Retrieving SWORD river widths')
width_dicts = []

# Loop through SWORD layers
for sword_lay in sword_all:

    # Initialize dictionary
    width_dict = {}

    for sword_fea in sword_lay:

        # Relate reach_id to width
        width_dict[sword_fea['properties']['reach_id']] = \
                       sword_fea['properties']['width']

    # Append dictionary to width_dicts
    width_dicts.append(width_dict)


# ******************************************************************************
# Transfer SWORD widths to MERIT-Basins
# ******************************************************************************
print('- Transferring SWORD widths onto MB reaches')
# Retrieve MB-to-SWORD translation for target pfaf
ms_df = ms_all[ms_trans_ind]

# Retrieve MB layer
riv_mb_lay = riv_mb_all[riv_mb_ind]

# For given MB region, identify related SWORD pfaf regions
sm_pfaf = (ms_df.iloc[:, :40].map(lambda x: str(x)[:2])
           .values
           .flatten()
           .tolist())
sm_pfaf_uniq = list(np.unique([v for v in sm_pfaf if v != '0']))
sm_cat_ind = pfaf_srt.index[pfaf_srt.isin(sm_pfaf_uniq)].tolist()

# Retrieve and combine SWORD width dictionaries for relevant regions
sword_dict_all = [width_dicts[x] for x in sm_cat_ind]

sword_dict = {}
for d in sword_dict_all:
    sword_dict.update(d)

    # Catch empty regions, writing empty file
    if len(sm_cat_ind) == 0:

        with fiona.open(riv_mb_files[riv_mb_ind], 'r') as src:

            # Copy schema
            new_schema = src.schema.copy()

            # Add new columns
            new_schema['properties']['sword_wid'] = 'float'

            # Write new shapefile
            with fiona.open(mb_out, 'w', driver=src.driver, crs=src.crs,
                            schema=new_schema) as out:

                # Write features
                for riv_fea in src:

                    # Copy feature geometry and properties
                    new_geom = riv_fea['geometry']
                    new_id = riv_fea['id']
                    new_prop = dict(riv_fea['properties'])

                    # Write Null
                    new_prop['sword_wid'] = None

                    # Write new feature
                    out.write(fiona.Feature(geometry=new_geom, id=new_id,
                                            properties=new_prop))

        continue

# ------------------------------------------------------------------------------
# Assign SWORD width values to each MB reach (weighted average)
# ------------------------------------------------------------------------------
width_avg = []

# Loop through MB reaches
for riv_fea in riv_mb_lay:

    # Retrieve COMID
    comid = riv_fea['properties']['COMID']

    # Retrieve translated SWORD reaches and partial length values
    reach_ids = ms_df.loc[comid].iloc[0:40].astype('int')
    part_len = ms_df.loc[comid].iloc[40:]

    # Remove zero values
    reach_ids = reach_ids[reach_ids > 0]
    part_len = part_len[:len(reach_ids)]

    # If COMID has no corresponding SWORd reaches, return NaN value
    if len(reach_ids) == 0:
        width_weight = np.nan

    else:

        # Retrieve width values for translated reaches
        width_i = [sword_dict[reach_id] for reach_id in reach_ids]

        # Calculate weighted average of width values by partial length
        width_weight = np.sum(width_i * (part_len/np.sum(part_len)))

    width_avg.append(width_weight)

# Give width_avg index of MB reaches
width_avg = pd.Series(width_avg)
width_avg.index = ms_df.index

# ------------------------------------------------------------------------------
# Write MB layer to shapefile with new column for translated values
# ------------------------------------------------------------------------------
print('- Writing shapefiles')
with fiona.open(riv_mb_files[riv_mb_ind], 'r') as src:

    # Copy schema
    new_schema = src.schema.copy()

    # Add new columns
    new_schema['properties']['sword_wid'] = 'float'

    # Write new shapefile
    with fiona.open(mb_out, 'w', driver=src.driver, crs=src.crs,
                    schema=new_schema) as out:

        # Write features
        for riv_fea in src:

            # Copy feature geometry and properties
            new_geom = riv_fea['geometry']
            new_id = riv_fea['id']
            new_prop = dict(riv_fea['properties'])

            # Store translated width values if they exist
            if new_prop['COMID'] in width_avg.index:
                width_val = round(width_avg.loc[new_prop['COMID']], 2)
            else:
                width_val = np.nan

            # Check if values are NaN
            if np.isnan(width_val):
                # Write Null
                new_prop['sword_wid'] = None
            else:
                # Write value
                new_prop['sword_wid'] = width_val

            # Write new feature
            out.write(fiona.Feature(geometry=new_geom, id=new_id,
                                    properties=new_prop))

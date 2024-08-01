#!/usr/bin/env python3
# ******************************************************************************
# ms_app_meandrs_to_sword.py
# ******************************************************************************

# Purpose:
# Given translations between Merit-Basins and SWORD, a SWORD river shapefile,
# and a river shapefile from the MeanDRS dataset, this script maps discharge
# simulations from MeanDRS onto SWORD reaches

# Author:
# Jeffrey Wade, 2024

# ******************************************************************************
# Import Python modules
# ******************************************************************************
import sys
import re
import glob
import pandas as pd
import fiona
import xarray as xr
import numpy as np

# ******************************************************************************
# Declaration of variables (given as command line arguments)
# ******************************************************************************
# 1 - ms_trans_nc
# 2 - sm_trans_nc
# 3 - riv_meandrs_shp
# 4 - sword_shp
# 5 - sword_out

# ******************************************************************************
# Get command line arguments
# ******************************************************************************
IS_arg = len(sys.argv)
if IS_arg != 6:
    print('ERROR - 5 arguments must be used')
    raise SystemExit(22)

ms_trans_nc = sys.argv[1]
sm_trans_nc = sys.argv[2]
riv_meandrs_shp = sys.argv[3]
sword_shp = sys.argv[4]
sword_out = sys.argv[5]


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
    with open(sm_trans_nc) as file:
        pass
except IOError:
    print('ERROR - Unable to open '+sm_trans_nc)
    raise SystemExit(22)

try:
    with open(riv_meandrs_shp) as file:
        pass
except IOError:
    print('ERROR - Unable to open '+riv_meandrs_shp)
    raise SystemExit(22)

try:
    with open(sword_shp) as file:
        pass
except IOError:
    print('ERROR - Unable to open '+sword_shp)
    raise SystemExit(22)

# Confirm files refer to same region
ms_trans_reg = ms_trans_nc.split('pfaf_')[1][0:2]
sm_trans_reg = sm_trans_nc.split('pfaf_')[1][0:2]
riv_meandrs_reg = riv_meandrs_shp.split('pfaf_')[1][0:2]
sword_reg = sword_shp.split('hb')[1][0:2]
sword_out_reg = sword_out.split('hb')[1][0:2]

if not (ms_trans_reg == sm_trans_reg == riv_meandrs_reg == sword_reg ==
        sword_out_reg):
    print('ERROR - Input files correspond to different regions')
    raise SystemExit(22)


# ******************************************************************************
# Read shapefiles
# ******************************************************************************
print('- Reading files')

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
# SWORD-to-MB Translation
# ------------------------------------------------------------------------------
# Read SWORD-to-MB files
sm_files = list(glob.iglob(re.sub(r'(?<=/sword_to_mb/).*?(?=\.nc)', '*',
                sm_trans_nc)))

# Sort reach files by value
sm_files.sort()

# Convert to shapefile
sm_all = [xr.open_dataset(j).to_dataframe() for j in sm_files]

# ------------------------------------------------------------------------------
# MeanDRS Rivers
# ------------------------------------------------------------------------------

# Read MeanDRS (MB) files
meandrs_files = list(glob.iglob(re.sub(r'(?<=/riv_COR/).*?(?=\.shp)', '*',
                     riv_meandrs_shp)))

# Sort reach files by value
meandrs_files.sort()

# Convert to shapefile
meandrs_all = [fiona.open(j, 'r', crs="EPSG:4326") for j in meandrs_files]

# Retrieve pfaf numbers from file
mb_pfaf_list = pd.Series([x.partition("pfaf_")[-1][0:2]
                          for x in meandrs_files]).sort_values()

# Sort pfaf_list
pfaf_srt = mb_pfaf_list.sort_values(ignore_index=True)
pfaf_srt = pfaf_srt.reset_index(drop=True)

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
sm_trans_ind = sm_files.index(sm_trans_nc)
riv_meandrs_ind = meandrs_files.index(riv_meandrs_shp)
sword_ind = sword_files.index(sword_shp)

# Retrieve SWORD-to-MB translations for each pfaf
sm_df = sm_all[sm_trans_ind]

# For given SWORD region, identify related MB pfaf regions
ms_pfaf = (sm_df.iloc[:, :40].map(lambda x: str(x)[:2])
           .values.
           flatten().
           tolist())
ms_pfaf_uniq = list(np.unique([v for v in ms_pfaf if v != '0']))
ms_cat_ind = pfaf_srt.index[pfaf_srt.isin(ms_pfaf_uniq)].tolist()


# ******************************************************************************
# Store MeanDRS MeanQ value in dictionary
# ******************************************************************************
print('- Retrieving MeanDRS discharge simulations')
meanQ_dicts = []
meandrs_sub = [meandrs_all[x] for x in ms_cat_ind]

# Loop through MeanDRS layers related to target region
for meandrs_lay in meandrs_sub:

    # Initialize dictionary
    meanQ_dict = {}

    for riv_fea in meandrs_lay:

        # Relate COMID to MeanQ
        meanQ_dict[riv_fea['properties']['COMID']] = \
            riv_fea['properties']['meanQ']

    # Append dictionary to meanQ_dicts
    meanQ_dicts.append(meanQ_dict)

# ******************************************************************************
# Translate MeanDRS values to SWORD
# ******************************************************************************
print('- Translating MeanDRS discharge onto SWORD reaches')
# --------------------------------------------------------------------------
# Load pfaf specific files
# --------------------------------------------------------------------------
# Retrieve SWORD-to-MB translation for target region
sm_df = sm_all[sm_trans_ind]

# Retrieve SWORD layer
sword_lay = sword_all[sword_ind]

meandrs_dict = {}
for d in meanQ_dicts:
    meandrs_dict.update(d)

# ------------------------------------------------------------------------------
# Assign MeanDRS meanQ values to each SWORD reach (weighted average)
# ------------------------------------------------------------------------------
meanQ_avg = []

# Loop through SWORD reaches
for reach_id in sm_df.index:

    # Retrieve translated MB reaches and partial length values
    comids = sm_df.loc[reach_id].iloc[0:40].astype('int')
    part_len = sm_df.loc[reach_id].iloc[40:]

    # Remove zero values
    comids = comids[comids > 0]
    part_len = part_len[:len(comids)]

    # If no translated reaches, return NaN value
    if len(comids) == 0:

        meanQ_weight = np.nan

    else:

        # Retrieve meanQ values for translated reaches
        meanQ_i = [meandrs_dict[comid] for comid in comids]

        # Calculate weighted average of meanQ values by partial length
        meanQ_weight = np.sum(meanQ_i * (part_len/np.sum(part_len)))

    meanQ_avg.append(meanQ_weight)

# Give meanQ_avg index of sword reaches
meanQ_avg = pd.Series(meanQ_avg)
meanQ_avg.index = sm_df.index

# ------------------------------------------------------------------------------
# Write SWORD layer to shapefile with new columns for translated values
# ------------------------------------------------------------------------------
print('- Writing shapefiles')
with fiona.open(sword_files[sword_ind], 'r') as src:

    # Copy schema
    new_schema = src.schema.copy()

    # Add new columns
    new_schema['properties']['meanDRS_Q'] = 'float'

    # Write new shapefile
    with fiona.open(sword_out, 'w', driver=src.driver, crs=src.crs,
                    schema=new_schema) as out:

        # Write features
        for sword_fea in src:

            # Copy feature geometry and properties
            new_geom = sword_fea['geometry']
            new_id = sword_fea['id']
            new_prop = dict(sword_fea['properties'])

            # Store meanQ values
            meanQ_val = round(meanQ_avg.loc[new_prop['reach_id']], 2)

            # Check if values are NaN
            if np.isnan(meanQ_val):
                # Write Null
                new_prop['meanDRS_Q'] = None
            else:
                # Write value
                new_prop['meanDRS_Q'] = meanQ_val

            # Write new feature
            out.write(fiona.Feature(geometry=new_geom, id=new_id,
                                    properties=new_prop))

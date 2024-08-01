#!/usr/bin/env python3
# ******************************************************************************
# ms_diagnostic.py
# ******************************************************************************

# Purpose:
# Given translations between MERIT-Basins and SWORD, a MERIT-SWORD river
# shapefile, a SWORD river shapefile, a mb river shapefile, this script confirms
# that the translations between datasets can be converted between without any
# loss of data

# Author:
# Jeffrey Wade, 2024


# ******************************************************************************
# Import Python modules
# ******************************************************************************
import glob
import re
import sys
import pandas as pd
import fiona
import xarray as xr
import numpy as np


# ******************************************************************************
# Declaration of variables (given as command line arguments)
# ******************************************************************************
# 1 - ms_trans_nc
# 2 - sm_trans_nc
# 3 - riv_ms_shp
# 4 - riv_mb_shp
# 5 - sword_shp
# 6 - ms_transpose_out
# 7 - sm_transpose_out


# ******************************************************************************
# Get command line arguments
# ******************************************************************************
IS_arg = len(sys.argv)
if IS_arg != 8:
    print('ERROR - 7 arguments must be used')
    raise SystemExit(22)

ms_trans_nc = sys.argv[1]
sm_trans_nc = sys.argv[2]
riv_ms_shp = sys.argv[3]
riv_mb_shp = sys.argv[4]
sword_shp = sys.argv[5]
ms_transpose_out = sys.argv[6]
sm_transpose_out = sys.argv[7]


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
    with open(riv_ms_shp) as file:
        pass
except IOError:
    print('ERROR - Unable to open '+riv_ms_shp)
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
sm_trans_reg = sm_trans_nc.split('pfaf_')[1][0:2]
riv_ms_reg = riv_ms_shp.split('pfaf_')[1][0:2]
riv_mb_reg = riv_mb_shp.split('pfaf_')[1][0:2]
sword_reg = sword_shp.split('hb')[1][0:2]
ms_transpose_reg = ms_transpose_out.split('pfaf_')[1][0:2]
sm_transpose_reg = sm_transpose_out.split('pfaf_')[1][0:2]

if not (ms_trans_reg == sm_trans_reg == riv_ms_reg == riv_mb_reg ==
        sword_reg == ms_transpose_reg == sm_transpose_reg):
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
# MERIT-SWORD Rivers
# ------------------------------------------------------------------------------
# Read MERIT-SWORD files
riv_ms_files = list(glob.iglob(re.sub(r'(?<=/ms_riv_network/).*?(?=\.shp)', '*',
                    riv_ms_shp)))

# Sort reach files by value
riv_ms_files.sort()

# Convert to shapefile
riv_ms_all = [fiona.open(j, 'r', crs="EPSG:4326") for j in riv_ms_files]

# ------------------------------------------------------------------------------
# MERIT-Basins Rivers
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
riv_ms_ind = riv_ms_files.index(riv_ms_shp)
riv_mb_ind = riv_mb_files.index(riv_mb_shp)
sword_ind = sword_files.index(sword_shp)


# ******************************************************************************
# Transpose MB table to SWORD table for target region
# ******************************************************************************
print('- Transposing MB-to-SWORD translation')
# Retrieve MB-SWORD, SWORD-MB, and SWORD shapefile for target region
sm_df_check = sm_all[sm_trans_ind]
sword_lay = sword_all[sword_ind]

# For given SWORD region, identify related MB pfaf regions
ms_pfaf = (sm_df_check.iloc[:, :40].map(lambda x: str(x)[:2])
           .values
           .flatten()
           .tolist())
ms_pfaf_uniq = list(np.unique([v for v in ms_pfaf if v != '0']))
ms_cat_ind = pfaf_srt.index[pfaf_srt.isin(ms_pfaf_uniq)].tolist()

# Retrieve relevant MB-to-SWORD translations
ms_dfs = [ms_all[x][ms_all[x].iloc[:, 0] != 0] for x in ms_cat_ind]


# Catch regions with no translated reaches
if len(ms_dfs) == 0:

    # Write empty netcdf to file
    sm_df = pd.DataFrame()
    sm_ds = xr.Dataset.from_dataframe(sm_df)
    sm_ds = sm_ds.rename({'index': 'sword'})

    # Set compression
    sm_encoding = {var: {'zlib': True} for var in sm_ds.data_vars}

    sm_ds.to_netcdf(sm_transpose_out, format='NETCDF4', engine='netcdf4',
                    encoding=sm_encoding)

else:

    # Combine all non-zero dfs
    ms_df = pd.concat(ms_dfs)

    # Get unique SWORD values in MB-to-SWORD translations, dropping 0
    sw_uniq = list(set(ms_df.iloc[:, :40].values.flatten().tolist()))
    sw_uniq = [x for x in sw_uniq if x != 0]

    # Rename columns of ms_df to integers to simplify part_len retrieval
    ms_df.columns = range(80)

    # Read SWORD reach ids from shapefile
    sword_id = []

    for sword_fea in sword_lay:
        sword_id.append(sword_fea['properties']['reach_id'])
    sword_id = sorted(sword_id)

    # Create SWORD table from SWORD IDs
    sm_df = pd.DataFrame(0., index=sword_id, columns=range(80))

    # Find all occurences of SWORD reaches in MB table
    # Store corresponding MB IDs and part_lens
    for sw_id in sw_uniq:

        # Ignore reaches from other regions
        if sw_id not in sm_df.index:
            continue

        # Retrieve locations of SWORD ID occurences in MB table
        locs = (ms_df == sw_id).stack()
        sw_locs = locs[locs].index.tolist()

        # If no translation for SWORD reach, continue
        if len(sw_locs) == 0:
            continue

        # Get MB IDs of each SWORD ID occurence
        m_id = [x[0] for x in sw_locs]

        # Get corresponding part_len values for each SWORD ID occurence
        # part_len columns are 40 indices after correspond ID column
        m_part_len = [ms_df.loc[idx, col+40] for idx, col in sw_locs]

        # Sort m_id and m_part_len by intersecting length values
        # Break ties in reach length by reach id
        m_srt = pd.DataFrame({'id': m_id, 'part_len': m_part_len}).sort_values(
                             by=['part_len', 'id'],
                             ascending=[False, False]).reset_index(drop=True)

        # Insert values into sm_df
        sm_df.loc[sw_id, 0: len(m_srt)-1] = m_srt.iloc[:, 0]
        sm_df.loc[sw_id, 40: 40+len(m_srt)-1] = m_srt.iloc[:, 1].values

    # Convert MB ID columns to integer
    for i in range(40):
        sm_df[i] = sm_df[i].astype(int)

    # Rename sm_df columns
    m_id_col = ['mb_' + str(x) for x in range(1, 41)]
    part_len_col = ['part_len_' + str(x) for x in range(1, 41)]
    sm_df.columns = m_id_col + part_len_col

    # Check if transposed table equals original SWORD table
    if not (sm_df.equals(sm_df_check)):
        print('ERROR - Transposed table is not equal to original translation')
        raise SystemExit(22)

    # Convert dataframe back to NetCDF
    sm_ds = xr.Dataset.from_dataframe(sm_df)
    sm_ds = sm_ds.rename({'index': 'sword'})

    # Set compression
    sm_encoding = {var: {'zlib': True} for var in sm_ds.data_vars}

    # Set attributes
    sm_ds.attrs = {'description': 'SWORD to MERIT-Basins Translation: Pfaf ' +
                   pfaf_srt[0]}

    # Set variable attributes
    sm_ds['sword'].attrs = {'units': 'unitless',
                            'long_name': 'SWORD reach_id'}

    # If dataset has values:
    if len(sm_ds) > 0:
        for t in range(40):

            # Set attributes for mb_1 to mb_40 variables
            sm_ds[m_id_col[t]].attrs = {'units': 'unitless',
                                                 'long_name': 'MB COMID (' +
                                                 str(t + 1) +
                                                 ') corresponding to'
                                                 ' SWORD reach'}

            # Set attributes for part_len_1 to part_len_40 variables
            sm_ds[part_len_col[t]].attrs = {'units': 'meters',
                                            'long_name':
                                            'Partial length of SWORD reach '
                                            'within corresponding MB catchment'
                                            ' ('+str(t+1)+')'}

    # Write transposed SWORD table to file
    sm_ds.to_netcdf(sm_transpose_out, format='NETCDF4', engine='netcdf4',
                    encoding=sm_encoding)


# ******************************************************************************
# Transpose SWORD table to MB table for each region (Only MERIT-SWORD reaches)
# ******************************************************************************
print('- Transposing SWORD to MB translation')

# Retrieve MB-to-SWORD translation and MB shapefile of target region
ms_df_check = ms_all[ms_trans_ind]
riv_mb_lay = riv_mb_all[riv_mb_ind]

# For given MB region, identify related SWORD pfaf regions
sm_pfaf = (ms_df_check.iloc[:, :40].map(lambda x: str(x)[:2])
           .values
           .flatten()
           .tolist())
sm_pfaf_uniq = list(np.unique([v for v in sm_pfaf if v != '0']))
sm_cat_ind = pfaf_srt.index[pfaf_srt.isin(sm_pfaf_uniq)].tolist()

# Retrieve relevant SWORD-to-MB translations
sm_dfs = [sm_all[x][sm_all[x].iloc[:, 0] != 0] for x in sm_cat_ind]

# Catch regions with no translated reaches
if len(sm_dfs) == 0:
    # Write empty dataframe to file
    ms_df = pd.DataFrame()
    ms_ds = xr.Dataset.from_dataframe(ms_df)
    ms_ds = ms_ds.rename({'index': 'mb'})

    # Set compression
    ms_encoding = {var: {'zlib': True} for var in ms_ds.data_vars}

    ms_ds.to_netcdf(ms_transpose_out, format='NETCDF4', engine='netcdf4',
                    encoding=ms_encoding)
else:

    # Combine all non-zero dfs
    sm_df = pd.concat(sm_dfs)

    # Get unique MB values in SWORD-to-MB translations, dropping 0
    mb_uniq = list(set(sm_df.iloc[:, :40].values.flatten().tolist()))
    mb_uniq = [x for x in mb_uniq if x != 0]

    # Rename columns of sm_df to integers to simplify part_len retrieval
    sm_df.columns = range(80)

    # Read MB COMIDS from shapefile
    # Can't retrieve from MMB-SWORD table, since some MB reaches have no
    # SWORD counterpart
    mb_id = []

    for mb_fea in riv_mb_lay:
        mb_id.append(mb_fea['properties']['COMID'])
    mb_id = sorted(mb_id)

    # Create MB table from MB IDs
    ms_df = pd.DataFrame(0., index=mb_id, columns=range(80))

    # Find all occurences of MB reach in SWORD table
    # Store corresponding SWORD IDs and part_lens
    # for i in range(len(ms_df)):
    for m_id in mb_uniq:

        # Ignore reaches from other regions
        if m_id not in ms_df.index:
            continue

        # Retrieve locations of MB ID occurences in SWORD table
        locs = (sm_df == m_id).stack()
        m_locs = locs[locs].index.tolist()

        # If no translation for MB reach, continue
        if len(m_locs) == 0:
            continue

        # Get SWORD IDs of each MB ID occurence
        sw_id = [x[0] for x in m_locs]

        # Get corresponding part_len values for each MB ID occurence
        # part_len columns are 40 indices after correspond ID column
        sw_part_len = [sm_df.loc[idx, col+40] for idx, col in m_locs]

        # Sort sw_id and sw_part_len by intersecting length values
        # Break ties in reach length by reach id
        sw_srt = pd.DataFrame({'id': sw_id,
                               'part_len': sw_part_len}).sort_values(
                              by=['part_len', 'id'],
                              ascending=[False, False]).reset_index(drop=True)

        # Insert values into ms_df
        ms_df.loc[m_id, 0:len(sw_srt)-1] = sw_srt.iloc[:, 0]
        ms_df.loc[m_id, 40:40+len(sw_srt)-1] = sw_srt.iloc[:, 1].values

    # Convert SWORD ID columns to integer
    for i in range(40):
        ms_df[i] = ms_df[i].astype(int)

    # Rename ms_df columns
    sw_id_col = ['sword_' + str(x) for x in range(1, 41)]
    part_len_col = ['part_len_' + str(x) for x in range(1, 41)]
    ms_df.columns = sw_id_col + part_len_col

    # Check if transposed table equals original mb table
    if not (ms_df.equals(ms_df_check)):
        print('ERROR - Transposed table is not equal to original translation')
        raise SystemExit(22)

    # Convert dataframe back to NetCDF
    ms_ds = xr.Dataset.from_dataframe(ms_df)
    ms_ds = ms_ds.rename({'index': 'mb'})

    # Set compression
    ms_encoding = {var: {'zlib': True} for var in ms_ds.data_vars}

    # Set attributes
    ms_ds.attrs = {'description': 'MERIT-Basins to SWORD Translation: Pfaf ' +
                   pfaf_srt[0]}

    # Set variable attributes
    ms_ds['mb'].attrs = {'units': 'unitless',
                         'long_name': 'MERIT-Basins reach COMID'}

    # If dataset has values:
    if len(ms_ds) > 0:
        for t in range(40):

            # Set attributes for sword_1 to sword_40 variables
            ms_ds[sw_id_col].attrs = {'units': 'unitless',
                                               'long_name':
                                               'SWORD reach_id (' +
                                               str(t + 1) + ') corresponding to'
                                               ' MB reach'}

            # Set attributes for part_len_1 to part_len_40 variables
            ms_ds[part_len_col[t]].attrs = {'units': 'meters',
                                            'long_name':
                                            'Partial length of SWORD reach (' +
                                            str(t+1)+') '
                                            'within corresponding MB catchment'}

    # Write transposed SWORD table to file
    ms_ds.to_netcdf(ms_transpose_out, format='NETCDF4', engine='netcdf4',
                    encoding=ms_encoding)

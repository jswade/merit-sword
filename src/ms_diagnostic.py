#!/usr/bin/env python3
# ******************************************************************************
# ms_diagnostic.py
# ******************************************************************************

# Purpose:
# Given translations between MB and SWORD, a MERIT-SWORD river shapefile, a
# SWORD river shapefile, a catchment shapefile for MERIT-SWORD reaches, and a
# dissolved catchment shapefile from MERIT-Basins, generate quality flags
# for translations between MB and SWORD reaches

# Author:
# Jeffrey Wade, 2024


# ******************************************************************************
# Import Python modules
# ******************************************************************************
import sys
import glob
import re
import pandas as pd
import fiona
import shapely.geometry
import shapely.ops
import shapely.prepared
from collections import Counter
import xarray as xr
import rtree
import numpy as np

# ******************************************************************************
# Declaration of variables (given as command line arguments)
# ******************************************************************************
# 1 - ms_trans_nc
# 2 - sm_trans_nc
# 3 - riv_ms_shp
# 4 - cat_mb_shp
# 5 - cat_sw_shp
# 6 - cat_dis_mb_shp
# 7 - sword_shp
# 8 - sw_to_mb_reg_in
# 9 - mb_to_reg_reg_in
# 10 - ms_diag_out
# 11 - sm_diag_out

# ******************************************************************************
# Get command line arguments
# ******************************************************************************
IS_arg = len(sys.argv)
if IS_arg != 12:
    print('ERROR - 11 arguments must be used')
    raise SystemExit(22)

ms_trans_nc = sys.argv[1]
sm_trans_nc = sys.argv[2]
riv_ms_shp = sys.argv[3]
cat_mb_shp = sys.argv[4]
cat_sw_shp = sys.argv[5]
cat_dis_mb_shp = sys.argv[6]
sword_shp = sys.argv[7]
sw_to_mb_reg_csv = sys.argv[8]
mb_to_sw_reg_csv = sys.argv[9]
ms_diag_out = sys.argv[10]
sm_diag_out = sys.argv[11]


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
    with open(cat_mb_shp) as file:
        pass
except IOError:
    print('ERROR - Unable to open '+cat_mb_shp)
    raise SystemExit(22)

try:
    with open(cat_sw_shp) as file:
        pass
except IOError:
    print('ERROR - Unable to open '+cat_sw_shp)
    raise SystemExit(22)

try:
    with open(cat_dis_mb_shp) as file:
        pass
except IOError:
    print('ERROR - Unable to open '+cat_dis_mb_shp)
    raise SystemExit(22)

try:
    with open(sword_shp) as file:
        pass
except IOError:
    print('ERROR - Unable to open '+sword_shp)
    raise SystemExit(22)

try:
    with open(sw_to_mb_reg_csv) as file:
        pass
except IOError:
    print('ERROR - Unable to open '+sw_to_mb_reg_csv)
    raise SystemExit(22)

try:
    with open(mb_to_sw_reg_csv) as file:
        pass
except IOError:
    print('ERROR - Unable to open '+mb_to_sw_reg_csv)
    raise SystemExit(22)

# Confirm files refer to same region
ms_trans_reg = ms_trans_nc.split('pfaf_')[1][0:2]
sm_trans_reg = sm_trans_nc.split('pfaf_')[1][0:2]
riv_ms_reg = riv_ms_shp.split('pfaf_')[1][0:2]
cat_mb_reg = cat_mb_shp.split('pfaf_')[1][0:2]
cat_sw_reg = cat_sw_shp.split('pfaf_')[1][0:2]
cat_dis_mb_reg = cat_dis_mb_shp.split('pfaf_')[1][0:2]
sword_reg = sword_shp.split('hb')[1][0:2]
ms_diag_reg = ms_diag_out.split('pfaf_')[1][0:2]
sm_diag_reg = sm_diag_out.split('pfaf_')[1][0:2]

if not (ms_trans_reg == sm_trans_reg == riv_ms_reg == cat_mb_reg ==
        cat_sw_reg == cat_dis_mb_reg == sword_reg == ms_diag_reg ==
        sm_diag_reg):
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
# Read MB Translate Catchments
# ------------------------------------------------------------------------------

# Read MB translation catchment files
cat_mb_trans = fiona.open(cat_mb_shp, 'r', crs="EPSG:4326")

# ------------------------------------------------------------------------------
# Read SWORD Translate Catchments
# ------------------------------------------------------------------------------

# Read SWORD translation catchment files
cat_sw_trans = fiona.open(cat_sw_shp, 'r', crs="EPSG:4326")

# ------------------------------------------------------------------------------
# MERIT-Basins Dissolved Catchments
# ------------------------------------------------------------------------------
# Read MERIT-Basins Dissolved Catchment files
cat_dis_mb_files = list(glob.iglob(re.sub(r'(?<=/cat_disso/).*?(?=\.shp)', '*',
                        cat_dis_mb_shp)))

# Sort files by value
cat_dis_mb_files.sort()

# Convert to shapefile
cat_dis_mb_all = [fiona.open(j, 'r', crs="EPSG:4326") for j in
                  cat_dis_mb_files]

# Retrieve pfaf numbers from file
mb_pfaf_list = pd.Series([x.partition("pfaf_")[-1][0:2] for x in
                          cat_dis_mb_files]).sort_values()

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
cat_dis_mb_ind = cat_dis_mb_files.index(cat_dis_mb_shp)
sword_ind = sword_files.index(sword_shp)


# ******************************************************************************
# Generate connectivity dataframe for MB reach topology
# ******************************************************************************
print('- Reading river topology')

# Retrieve MERIT-SWORD reaches and translation for target pfaf
riv_ms = riv_ms_all[riv_ms_ind]
ms_df = ms_all[ms_trans_ind]

# Catch regions with no translated reaches
if len(ms_df) == 0:
    con_lay = pd.DataFrame()
else:
    # Inititalize df
    con_df = pd.DataFrame(0, index=ms_df.index, columns=range(5))

    # Loop through MERIT-Basins reaches
    for riv_fea in riv_ms:

        # Retrieve COMID
        comid = riv_fea['properties']['COMID']

        # Retrieve topological connections
        con_df.loc[comid, 0] = riv_fea['properties']['NextDownID']
        con_df.loc[comid, 1] = riv_fea['properties']['up1']
        con_df.loc[comid, 2] = riv_fea['properties']['up2']
        con_df.loc[comid, 3] = riv_fea['properties']['up3']
        con_df.loc[comid, 4] = riv_fea['properties']['up4']


# ******************************************************************************
# Run diagnostics: SWORD-to-MB Translation
# ******************************************************************************
print('- Running SWORD-to-MB diagnostics')
# ------------------------------------------------------------------------------
# Load pfaf specific files
# ------------------------------------------------------------------------------
# Retrieve SWORD-to-MB translation for target pfaf
sm_df = sm_all[ms_trans_ind]

# Retrieve SWORD layer
sword_lay = sword_all[sword_ind]

# Relate SWORD shapefile index to SWORD reach_id
s_lookup = {}
for sword_fea in sword_lay:
    s_lookup[sword_fea['properties']['reach_id']] = int(sword_fea['id'])

# Retrieve reach_id values from translations
reach_id = sm_df.index.values

# For given SWORD region, identify related MB pfaf regions
ms_pfaf = (sm_df.iloc[:, :40].map(lambda x: str(x)[:2])
           .values
           .flatten()
           .tolist())
ms_pfaf_uniq = list(np.unique([v for v in ms_pfaf if v != '0']))
ms_cat_ind = pfaf_srt.index[pfaf_srt.isin(ms_pfaf_uniq)].tolist()

# Retrieve dissolved MERIT-Basins catchments for relevant regions
cat_dis_mb_lays = [cat_dis_mb_all[x] for x in ms_cat_ind]

# ------------------------------------------------------------------------------
# Create spatial index for the bounds of each MB cat of the SWORD trans.
# ------------------------------------------------------------------------------
# Relate catchment id to bounds of feature geometry
cat_sw_index = rtree.index.Index()
for cat_fea in cat_sw_trans:
    cat_fid = int(cat_fea['id'])
    cat_shy = shapely.geometry.shape(cat_fea['geometry'])
    cat_sw_index.insert(cat_fid, cat_shy.bounds)

# ------------------------------------------------------------------------------
# Create spatial index for the bounds of each SWORD reach
# ------------------------------------------------------------------------------
# Relate sword id to bounds of feature geometry
sword_index = rtree.index.Index()
for sword_fea in sword_lay:
    sword_fid = int(sword_fea['id'])
    sword_shy = shapely.geometry.shape(sword_fea['geometry'])
    sword_index.insert(sword_fid, sword_shy.bounds)

# ------------------------------------------------------------------------------
# Create spatial index for the bounds of each dissolved MB region
# ------------------------------------------------------------------------------
# Relate pfaf id to bounds of feature geometry
dis_cat_index = rtree.index.Index()
for i in range(len(cat_dis_mb_lays)):
    cat_lay = cat_dis_mb_lays[i]
    for cat_fea in cat_lay:
        cat_fid = i
        cat_shy = shapely.geometry.shape(cat_fea['geometry'])
        dis_cat_index.insert(cat_fid, cat_shy.bounds)

# ------------------------------------------------------------------------------
# Create lookup table for index of MERIT-SWORD catchments
# ------------------------------------------------------------------------------
# Relate COMID to index position
cat_sw_trans_hash = {}
for cat_fea in cat_sw_trans:
    cat_sw_trans_hash[cat_fea['properties']['COMID']] = int(cat_fea['id'])

# ------------------------------------------------------------------------------
# Create lookup table for index of SWORD reaches
# ------------------------------------------------------------------------------
# Relate reach_id to index position
sword_hash = {}
for sword_fea in sword_lay:
    sword_hash[sword_fea['properties']['reach_id']] = int(sword_fea['id'])

# ------------------------------------------------------------------------------
# Create dictionary to store flags
# ------------------------------------------------------------------------------
sm_flag = {}

for val in reach_id:

    # Initalize flag values for each SWORD translation
    sm_flag[val] = '0'
    

# ******************************************************************************
# Run MB reach topology diagnostic
# ******************************************************************************
print('- Running topology diagnostic')
# MB reaches referenced to each SWORD reach should be topologically
# connected

# ------------------------------------------------------------------------------
# Confirm topology of MB translations
# ------------------------------------------------------------------------------
for sword_id in reach_id:

    # Retrieve referenced MB reaches from SWORD reach, removing zeroes
    mb_ref = sm_df.loc[sword_id].iloc[0:40].astype('int')
    mb_ref = mb_ref[mb_ref > 0].to_list()

    # If there are 0 or 1 referenced MB reaches, diagnostic not possible
    if len(mb_ref) > 1:

        # Loop through MB reaches
        for mb_id in mb_ref:

            # Retrieve connected MB reaches, drop zeros
            con_rch = con_df.loc[mb_id, :]
            con_rch = con_rch[con_rch != 0]

            # If MB reach is not connected to other referenced reaches
            if not con_rch.isin(mb_ref).any():

                # Check for shared downstream neighbors with other reaches
                # Retrieve downstream ids from mb_ref reaches
                mb_ref_dn = [con_df.loc[x][0] for
                             x in mb_ref]

                # Identify duplicate downstream id values
                dn_cnt = Counter(mb_ref_dn)
                dup_dn = [x for x, val in dn_cnt.items() if val > 1]

                # If MB doesn't share downstream neighbor with another
                # selected reach, flag SWORD reach with 1
                if not con_df.loc[mb_id][0] in dup_dn:
                    sm_flag[sword_id] = '1'

                    # Proceed to next sword reach
                    break


# ******************************************************************************
# Run absent translation diagnostic
# ******************************************************************************
print('- Running absent translation diagnostic')
# Flag reaches with 2 that do not have a corresponding translation
sword_notrans = []
for sword_id in reach_id:
    # Check for absent MB translation and flag reach
    if sm_df.loc[sword_id].iloc[0].astype('int') == 0:
        sm_flag[sword_id] = '2'
        sword_notrans.append(sword_id)


# **************************************************************************
# Run SWORD absent reach flow accumulation diagnostic
# **************************************************************************
# Flag MERIT-SWORD reaches with no corresponding translated reach due to
# flow accumulation validation

# --------------------------------------------------------------------------
# Find catchments with no translations that intersect with SWORD
# --------------------------------------------------------------------------
# Loop through SWORD reaches with no translation
for sword_id in sword_notrans:

    # Retrieve SWORD geometry
    sword_shy = shapely.geometry.shape(sword_lay[sword_hash[sword_id]]
                                       ['geometry'])

    # Create prepared geometric object to allow for faster processing
    sword_pre = shapely.prepared.prep(sword_shy)

    # Filter MERIT-SWORD catchment bounding boxes with SWORD reaches
    cat_int_fid = [int(x) for x in
                   list(cat_sw_index.intersection(sword_shy.bounds))]

    # Intersect of filtered MERIT-SWORD translation catchments
    for i in range(len(cat_int_fid)):

        # Retrieve MERIT-SWORD geometry corresponding to intersect fid
        cat_fea = cat_sw_trans[cat_int_fid[i]]

        cat_shy = shapely.geometry.shape(cat_fea['geometry'])

        # ------------------------------------------------------------------
        # If any SWORD reaches intersects with catchment, flag reach
        # ------------------------------------------------------------------
        if sword_pre.intersects(cat_shy):

            # Flag reach with '21'
            sm_flag[sword_id] = '21'

            break


# **************************************************************************
# Run SWORD ocean diagnostic
# **************************************************************************
# Flag SWORD reaches that don't have a MB counterpart and are located
# outside of the MB coastline

# Create shapely geometric object for dissolved MB catchments
dis_shys = [shapely.geometry.shape(x[0]['geometry']) for x in cat_dis_mb_lays]

for sword_id in reach_id:

    # If no MERIT reaches assigned to SWORD reach:
    if sm_df.loc[sword_id].iloc[0].astype('int') == 0:

        # Retrieve shapefile
        sword_fea = sword_lay[s_lookup[sword_id]]

        sword_shy = shapely.geometry.shape(sword_fea['geometry'])

        # Filter dissolved MB region bounding boxes with SWORD reaches
        sword_int_fid = [int(x) for x in
                         list(dis_cat_index.intersection(sword_shy.bounds))]

        # If reach is outside MB region boundary
        # (assumed to be ocean), flag reach with '22'
        for i in sword_int_fid:
            if not dis_shys[i].contains(sword_shy):
                sm_flag[sword_id] = '22'


# ******************************************************************************
# Write flags to shapefiles: SWORD
# ******************************************************************************
# Convert flag to dataframe
sm_flag_df = pd.DataFrame.from_dict(sm_flag, orient='index',
                                    columns=['flag'])

# Convert to xarray Dataset
sm_flag_ds = xr.Dataset.from_dataframe(sm_flag_df)
sm_flag_ds = sm_flag_ds.rename({'index': 'sword'})

# Convert values to string in dataset
sm_flag_ds['flag'] = sm_flag_ds['flag'].astype(int)

# Set compression
sm_encoding = {'flag': {'zlib': True}}

# Set attributes
sm_flag_ds.attrs = {'description': 'SWORD to MERIT-Basins'
                    ' Translation Diagnostic: '
                    'Pfaf '+pfaf_srt[0]}

# Set variable attributes
sm_flag_ds['sword'].attrs = {'units': 'unitless',
                             'long_name': 'SWORD reach_id'}

sm_flag_ds['flag'].attrs = {'units': 'unitless',
                            'long_name': 'Diagnostic Integer Flag'}

# Write to NetCDF
sm_flag_ds.to_netcdf(sm_diag_out, format='NETCDF4', engine='netcdf4',
                     encoding=sm_encoding)


# ******************************************************************************
# Run diagnostics: MB-to-SWORD Translation
# ******************************************************************************
print('- Running MB-to-SWORD diagnostics')
# ------------------------------------------------------------------------------
# Load pfaf specific files
# ------------------------------------------------------------------------------
# Retrieve MB-to-SWORD  translation for target pfaf
ms_df = ms_all[ms_trans_ind]

# Retrieve COMID values from translations
comid = ms_df.index.values

# For given MB region, identify related SWORD pfaf regions
sm_pfaf = (ms_df.iloc[:, :40].map(lambda x: str(x)[:2])
           .values
           .flatten()
           .tolist())
sm_pfaf_uniq = list(np.unique([v for v in sm_pfaf if v != '0']))
sm_cat_ind = pfaf_srt.index[pfaf_srt.isin(sm_pfaf_uniq)].tolist()

# Retrieve SWORD layer
sword_lays = [sword_all[x] for x in sm_cat_ind]

# ------------------------------------------------------------------------------
# Create spatial index for the bounds of each translated MB catchment
# ------------------------------------------------------------------------------
# Relate catchment id to bounds of feature geometry
cat_index = rtree.index.Index()
for cat_fea in cat_mb_trans:
    cat_fid = int(cat_fea['id'])
    cat_shy = shapely.geometry.shape(cat_fea['geometry'])
    cat_index.insert(cat_fid, cat_shy.bounds)

# ------------------------------------------------------------------------------
# Create spatial index for the bounds of each SWORD reach
# ------------------------------------------------------------------------------
# Relate sword id to bounds of feature geometry
sword_index = rtree.index.Index()
# Create counter to store the index of the corresponding SWORD region
# Counter is shifted by 1, as leading zeros deleted as integer
ct = 1
for sword_lay in sword_lays:
    for sword_fea in sword_lay:
        # Index of sword layer stored as first digit
        sword_fid = int(str(ct) + str(sword_fea['id']))
        sword_shy = shapely.geometry.shape(sword_fea['geometry'])
        sword_index.insert(sword_fid, sword_shy.bounds)
    ct = ct + 1

# ------------------------------------------------------------------------------
# Create lookup table for index of translation catchments
# --------------------------------------------------------------------------v
# Relate COMID to index position
cat_mb_trans_hash = {}
for cat_fea in cat_mb_trans:
    cat_mb_trans_hash[cat_fea['properties']['COMID']] = int(cat_fea['id'])

# Store COMIDs of values in translation
mb_trans_comid = list(cat_mb_trans_hash.keys())

# ------------------------------------------------------------------------------
# Create dictionary to store flags
# ------------------------------------------------------------------------------
ms_flag = {}

for val in comid:

    # Initalize flag values for each MB translation
    ms_flag[val] = '0'


# ******************************************************************************
# Run SWORD reach topology diagnostic
# ******************************************************************************
print('- Running topology diagnostic')
# SWORD reaches referenced to each MB reach should be topologically
# connected

# ------------------------------------------------------------------------------
# Create lookup tables for SWORD connectivity
# ------------------------------------------------------------------------------
s_con_dn = {}
s_con_up = {}

# Link SWORD reach_ids to their reach connections
for sword_lay in sword_lays:
    for sword_fea in sword_lay:

        # Retrieve upstream and downstream reaches
        id_up = sword_fea['properties']['rch_id_up']
        id_dn = sword_fea['properties']['rch_id_dn']

        # Catch empty id_up or id_dn
        if id_up is not None:
            up_list = sword_fea['properties']['rch_id_up'].split(" ")
        if id_dn is not None:
            dn_list = sword_fea['properties']['rch_id_dn'].split(" ")

        # Add ids as integers to dictionary
        s_con_up[int(sword_fea['properties']['reach_id'])] = [int(x) for x
                                                              in up_list]

        s_con_dn[int(sword_fea['properties']['reach_id'])] = [int(x) for x
                                                              in dn_list]

# ------------------------------------------------------------------------------
# Confirm topology of SWORD translations
# ------------------------------------------------------------------------------
for mb_id in comid:

    # Retrieve referenced SWORD reaches from MB reach, removing zeroes
    sword_ref = ms_df.loc[mb_id].iloc[0:40].astype('int')
    sword_ref = sword_ref[sword_ref > 0].to_list()

    # If there are 0 or 1 referenced SWORD reaches, diagnostic not possible
    if len(sword_ref) > 1:

        # Loop through SWORD reaches
        for sword_id in sword_ref:

            # Retrieve connected SWORD reaches, drop zeros
            con_rch = pd.Series(s_con_dn[sword_id] + s_con_up[sword_id])
            con_rch = con_rch[con_rch != 0]

            # If SWORD reach is not connected to other referenced reaches
            if not con_rch.isin(sword_ref).any():

                # Check for shared downstream neighbors with other reaches
                # Retrieve downstream ids from sword_ref reaches
                sword_ref_dn = []
                for x in sword_ref:
                    sword_ref_dn.extend(s_con_dn[x])

                # Identify duplicate downstream id values
                dn_cnt = Counter(sword_ref_dn)
                dup_dn = [x for x, val in dn_cnt.items() if val > 1]

                # Check for shared upstream neighbors with other reaches
                # Retrieve upstream ids from sword_ref reaches
                sword_ref_up = []
                for x in sword_ref:
                    sword_ref_up.extend(s_con_up[x])

                # Identify duplicate upstream id values
                up_cnt = Counter(sword_ref_up)
                dup_up = [x for x, val in up_cnt.items() if val > 1]

                # If MB doesn't share downstream  or upstream neighbor
                # with another selected reach, flag SWORD reach with 1
                if not any(val in s_con_dn[sword_id] for val in dup_dn) and\
                   not any(val in s_con_up[sword_id] for val in dup_up):
                    ms_flag[mb_id] = '1'

                    # Proceed to next sword reach
                    break


# ******************************************************************************
# Run absent translation diagnostic
# ******************************************************************************
print('- Running absent translation diagnostic')
# Flag reaches with 2 that do not have a corresponding translation
ms_notrans = []
for mb_id in comid:
    # Check for absent SWORD translation and flag reach
    if ms_df.loc[mb_id].iloc[0].astype('int') == 0:
        ms_flag[mb_id] = '2'
        ms_notrans.append(mb_id)


# ******************************************************************************
# Run MB absent reach flow accumulation diagnostic
# ******************************************************************************
# Flag MERIT-SWORD reaches with no corresponding translated reach due to
# flow accumulation validation

# ------------------------------------------------------------------------------
# Find catchments with no translations that intersect with SWORD
# ------------------------------------------------------------------------------
# Loop through MB reaches with no translation
for mb_id in mb_trans_comid:

    # Check if MB reach is in ms_notrans
    if mb_id not in ms_notrans:
        continue

    # Retrieve translation cat geometry
    cat_shy = shapely.geometry.shape(cat_mb_trans[cat_mb_trans_hash
                                                  [mb_id]]['geometry'])

    # Create prepared geometric object to allow for faster processing
    cat_pre = shapely.prepared.prep(cat_shy)

    # Filter SWORD reach bounding boxes with MB Catchments
    sword_int_fid = [int(x) for x in
                     list(sword_index.intersection(cat_shy.bounds))]

    # --------------------------------------------------------------------------
    # Intersect index filtered SWORD reaches with translation catchments
    # --------------------------------------------------------------------------

    # Intersect of filtered SWORD reaches
    for i in range(len(sword_int_fid)):

        # Load relevant sword layer
        # sword layer integer shifted by 1 to prevent leading zero from
        # being deleted
        sword_lay = sword_lays[int(str(sword_int_fid[i])[0])-1]

        # Retrieve SWORD geometry corresponding to intersect fid
        sword_fea = sword_lay[int(str(sword_int_fid[i])[1:])]

        sword_shy = shapely.geometry.shape(sword_fea['geometry'])

        # ----------------------------------------------------------------------
        # If any SWORD reaches intersects with catchment, flag reach
        # ----------------------------------------------------------------------
        if cat_pre.intersects(sword_shy):

            # Flag reach with '21'
            ms_flag[mb_id] = '21'

            break


# ******************************************************************************
# Write flags to NetCDF: MB
# ******************************************************************************
print('- Writing diagnostics to file')
# Convert flag to dataframe
ms_flag_df = pd.DataFrame.from_dict(ms_flag, orient='index', columns=['flag'])

# Convert to xarray Dataset
ms_flag_ds = xr.Dataset.from_dataframe(ms_flag_df)
ms_flag_ds = ms_flag_ds.rename({'index': 'mb'})

# Convert values to string in dataset
ms_flag_ds['flag'] = ms_flag_ds['flag'].astype(int)

# Set compression
ms_encoding = {'flag': {'zlib': True}}

# Set attributes
ms_flag_ds.attrs = {'description': 'MERIT-Basins to SWORD '
                    'Translation Diagnostic: '
                    'Pfaf '+pfaf_srt[0]}

# Set variable attributes
ms_flag_ds['mb'].attrs = {'units': 'unitless',
                          'long_name': 'MERIT-Basins reach COMID'}

ms_flag_ds['flag'].attrs = {'units': 'unitless',
                            'long_name': 'Diagnostic Integer Flag'}

# Write to NetCDF
ms_flag_ds.to_netcdf(ms_diag_out, format='NETCDF4', engine='netcdf4',
                     encoding=ms_encoding)

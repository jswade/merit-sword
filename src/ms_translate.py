#!/usr/bin/env python3
# ******************************************************************************
# ms_translate.py
# ******************************************************************************

# Purpose:
# Given a MERIT-SWORD river shapefile, a catchment and river shapefile from
# MERIT-Basins,a SWORD river shapefile, and files that identify overlaps
# between hydrologic regions, this script establishing one-to-many links
# (i.e. translations) between reaches in the two datasets and outputs them as
# NetCDF files.

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
import shapely.geometry
import shapely.ops
import shapely.prepared
import rtree
import xarray as xr
import numpy as np


# ******************************************************************************
# Declaration of variables (given as command line arguments)
# ******************************************************************************
# 1 - riv_ms_shp
# 2 - riv_mb_shp
# 3 - cat_mb_shp
# 3 - sword_shp
# 5 - sw_to_mb_reg_in
# 6 - mb_to_reg_reg_in
# 7 - cat_mb_out
# 8 - cat_sw_out
# 9 - mb_to_sword_out
# 10 - sword_to_mb_out


# ******************************************************************************
# Get command line arguments
# ******************************************************************************
IS_arg = len(sys.argv)
if IS_arg != 11:
    print('ERROR - 10 arguments must be used')
    raise SystemExit(22)

riv_ms_shp = sys.argv[1]
riv_mb_shp = sys.argv[2]
cat_mb_shp = sys.argv[3]
sword_shp = sys.argv[4]
sw_to_mb_reg_csv = sys.argv[5]
mb_to_sw_reg_csv = sys.argv[6]
cat_mb_out = sys.argv[7]
cat_sw_out = sys.argv[8]
mb_to_sword_out = sys.argv[9]
sword_to_mb_out = sys.argv[10]


# ******************************************************************************
# Check if files exist
# ******************************************************************************
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
    with open(cat_mb_shp) as file:
        pass
except IOError:
    print('ERROR - Unable to open '+cat_mb_shp)
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
riv_ms_reg = riv_ms_shp.split('pfaf_')[1][0:2]
riv_mb_reg = riv_mb_shp.split('pfaf_')[1][0:2]
cat_mb_reg = cat_mb_shp.split('pfaf_')[1][0:2]
sword_reg = sword_shp.split('hb')[1][0:2]
cat_mb_out_reg = cat_mb_out.split('pfaf_')[1][0:2]
cat_sw_out_reg = cat_sw_out.split('pfaf_')[1][0:2]
mb_out_reg = mb_to_sword_out.split('pfaf_')[1][0:2]
sword_out_reg = sword_to_mb_out.split('pfaf_')[1][0:2]

if not (riv_ms_reg == cat_mb_reg == sword_reg == cat_mb_out_reg ==
        cat_sw_out_reg == mb_out_reg == sword_out_reg == riv_mb_reg):
    print('ERROR - Input files correspond to different regions')
    raise SystemExit(22)


# ******************************************************************************
# Read shapefiles
# ******************************************************************************
print('- Reading shapefiles')
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
# MERIT-Basins Catchments
# ------------------------------------------------------------------------------
# Read MERIT-Basins Catchment files
cat_mb_files = list(glob.iglob(re.sub(r'(?<=/cat/).*?(?=\.shp)', '*',
                    cat_mb_shp)))

# Sort files by value
cat_mb_files.sort()

# Convert to shapefile
cat_mb_all = [fiona.open(j, 'r', crs="EPSG:4326") for j in cat_mb_files]

# Retrieve pfaf numbers from file
mb_pfaf_list = pd.Series([x.partition("pfaf_")[-1][0:2]
                          for x in cat_mb_files]).sort_values()

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
# Region Overlap Files
# ------------------------------------------------------------------------------
sw_to_mb_reg = pd.read_csv(sw_to_mb_reg_csv, index_col=0)
mb_to_sw_reg = pd.read_csv(mb_to_sw_reg_csv, index_col=0)

# ------------------------------------------------------------------------------
# Get indices of target region shapefiles
# ------------------------------------------------------------------------------
riv_ms_ind = riv_ms_files.index(riv_ms_shp)
riv_mb_ind = riv_mb_files.index(riv_mb_shp)
cat_mb_ind = cat_mb_files.index(cat_mb_shp)
sword_ind = sword_files.index(sword_shp)


# ******************************************************************************
# Create lookup dictionary for flow accumulation
# ******************************************************************************
# Retrieve MB pfaf regions to load for given SWORD region
mb_reg = sw_to_mb_reg.loc[int(sword_reg)].dropna().astype(int).values.tolist()

# Find MB file indices corresponding to those pfaf regions
mb_reg_ind = [mb_pfaf_list.index[mb_pfaf_list == str(x)].values[0] for x in
              mb_reg]

# Retrieve SWORD pfaf regions to load for given MB region
sw_reg = mb_to_sw_reg.loc[int(cat_mb_reg)].dropna().astype(int).values.\
                                                                        tolist()

# Find SWORD file indices corresponding to those pfaf regions
sw_reg_ind = [pfaf_srt.index[pfaf_srt == str(x)].values[0] for x in sw_reg]

# Initialize pfaf-specific dictionaries
mfa = {}
sfa = {}

# ------------------------------------------------------------------------------
# MB Flow Accumulation
# ------------------------------------------------------------------------------
for riv_lay in [riv_ms_all[x] for x in
                np.unique(np.concatenate((mb_reg_ind, sw_reg_ind)))]:
    for riv_fea in riv_lay:
        # Store flow accumulation for each MS reach (km2)
        mfa[riv_fea['properties']['COMID']] = riv_fea['properties']['uparea']

# ------------------------------------------------------------------------------
# SWORD Flow Accumulation
# ------------------------------------------------------------------------------
for riv_lay in [sword_all[x] for x in
                np.unique(np.concatenate((mb_reg_ind, sw_reg_ind)))]:
    for riv_fea in riv_lay:
        # Store flow accumulation for each SWORD reach (km2)
        sfa[riv_fea['properties']['reach_id']] = riv_fea['properties']['facc']


# ******************************************************************************
# Translate from SWORD reaches to MB reaches for target region (SWORD-to-MB)
# ******************************************************************************
print('- Translating from SWORD to MB')

# Retrieve MB, SWORD, MERIT-SWORD for target region
riv_ms_lay = riv_ms_all[riv_ms_ind]
sword_lay = sword_all[sword_ind]

# ------------------------------------------------------------------------------
# Identify MB catchments corresponding to MERIT-SWORD reaches
# ------------------------------------------------------------------------------
# Load relevant MB catchments
cat_mb_lays = [cat_mb_all[x] for x in mb_reg_ind]

# Retrieve list of MERIT-SWORD reach COMIDs
ms_list = []
for riv_fea in riv_ms_lay:
    ms_list.append(riv_fea['properties']['COMID'])

# Retrieve schema and crs
cat_mb_schema = cat_mb_all[0].schema.copy()
cat_mb_crs = cat_mb_all[0].crs

# Write catchments corresponding to MERIT-SWORD reaches to file
with fiona.open(cat_sw_out, 'w', schema=cat_mb_schema,
                driver='ESRI Shapefile',
                crs=cat_mb_crs) as output:
    for cat_mb_lay in cat_mb_lays:
        for cat_fea in cat_mb_lay:
            if cat_fea['properties']['COMID'] in ms_list:
                output.write(cat_fea)

# ------------------------------------------------------------------------------
# Read selected translation catchments
# ------------------------------------------------------------------------------
# Read MERIT-SWORD catchment file
cat_sw_lay = fiona.open(cat_sw_out, 'r', crs="EPSG:4326")

# ------------------------------------------------------------------------------
# Create spatial index for the bounds of each MERIT-SWORD catchment
# ------------------------------------------------------------------------------
# Relate catchment id to bounds of feature geometry
cat_index = rtree.index.Index()
for cat_fea in cat_sw_lay:
    cat_fid = int(cat_fea['id'])
    cat_shy = shapely.geometry.shape(cat_fea['geometry'])
    cat_index.insert(cat_fid, cat_shy.bounds)

# ------------------------------------------------------------------------------
# Identify MB reaches corresponding to each SWORD reach (SWORD-to-MB)
# ------------------------------------------------------------------------------

# Create dictionaries to store SWORD to MB translation and lengths
sw_cat = {}
sw_len = {}

for sword_fea in sword_lay:

    # Create shapely geometric object for each sword reach
    sword_shy = shapely.geometry.shape(sword_fea['geometry'])

    # Create prepared geometric object to allow for faster processing
    sword_pre = shapely.prepared.prep(sword_shy)

    # Filter MERIT catchments bounding boxes with SWORD reach
    cat_int_fid = [int(x) for x in
                   list(cat_index.intersection(sword_shy.bounds))]

    # --------------------------------------------------------------------------
    # Intersect index filtered MERIT-SWORD catchments with SWORD reach
    # --------------------------------------------------------------------------

    comid_dict = {}

    for i in range(len(cat_int_fid)):

        # Retrieve translation cat geometry corresponding to intersect fid
        cat_fea = cat_sw_lay[cat_int_fid[i]]

        cat_shy = shapely.geometry.shape(cat_fea['geometry'])

        # ----------------------------------------------------------------------
        # If catchment intersects with reach, extract COMID
        # ----------------------------------------------------------------------

        if sword_pre.intersects(cat_shy):

            # Check for valid catchment geometry (self-ring intersects)

            if not cat_shy.is_valid:

                # Zero distance buffer for invalid geometries
                cat_shy = cat_shy.buffer(0)

            # Catch errors where SWORD reaches have 0 length
            if sword_shy.length > 0:
                # Store length of SWORD reach contained by intersect cat
                # Multiply by sword length in km so we don't need to...
                # reproject shapefiles
                # Round length to 2 decimal places
                comid_dict[cat_fea['properties']['COMID']] = \
                    round(sword_fea['properties']['reach_len'] *
                          (sword_shy.intersection(cat_shy).length /
                           sword_shy.length), 2)
            else:
                comid_dict[cat_fea['properties']['COMID']] = 0

    # Order MB comids by length of SWORD reach contained within cat
    # Sort by comid if tie in intersecting length
    sw_cat_ord = sorted(comid_dict, key=lambda x: (-comid_dict[x], -x))

    sw_len_ord = [comid_dict[x] for x in sw_cat_ord]

    # --------------------------------------------------------------------------
    # Compare flow accumulation values between translated reaches
    # --------------------------------------------------------------------------

    if len(sw_cat_ord) > 0:

        # Retrieve flow accumulation value for SWORD reach
        sword_fa = sfa[sword_fea['properties']['reach_id']]

        # Retrieve flow accumulations for MERIT-SWORD reaches
        mb_fa = [mfa[x] for x in sw_cat_ord]

        # Find indices of translations where flow accumulation values are
        # within of 1 order of magnitude of each other
        fa_valid = [ind for ind in range(len(sw_cat_ord)) if
                    (sword_fa / mb_fa[ind] < 10) &
                    (sword_fa / mb_fa[ind] > 0.1)]

        # Only keep translated reaches with valid flow accumulations
        sw_cat_ord = [sw_cat_ord[ind] for ind in fa_valid]
        sw_len_ord = [sw_len_ord[ind] for ind in fa_valid]

    # --------------------------------------------------------------------------
    # Format for outputs
    # --------------------------------------------------------------------------

    # Pad lists to reach desired length and insert to dictionary
    sw_cat[sword_fea['properties']['reach_id']] = sw_cat_ord + [0] * \
        (40 - len(sw_cat_ord))

    sw_len[sword_fea['properties']['reach_id']] = sw_len_ord + [0] * \
        (40 - len(sw_len_ord))


# ******************************************************************************
# Translate from MB reaches to SWORD reaches for target region (MB-to-SWORD)
# ******************************************************************************
print('- Translating from MB to SWORD')

# Retrieve MB, SWORD, MERIT-SWORD for each pfaf
riv_ms_lays = [riv_ms_all[x] for x in sw_reg_ind]
riv_mb_lay = riv_mb_all[riv_mb_ind]
sword_lays = [sword_all[x] for x in sw_reg_ind]

# ------------------------------------------------------------------------------
# Identify MB catchments corresponding to MERIT-SWORD reaches
# ------------------------------------------------------------------------------
# Load MB catchment of target region
cat_mb_lay = cat_mb_all[cat_mb_ind]

# Retrieve list of MERIT-SWORD reach COMIDs
ms_list = []
for riv_ms_lay in riv_ms_lays:
    for riv_fea in riv_ms_lay:
        if str(riv_fea['properties']['COMID'])[0:2] == pfaf_srt[riv_mb_ind]:
            ms_list.append(riv_fea['properties']['COMID'])

# Retrieve schema and crs
cat_mb_schema = cat_mb_all[0].schema.copy()
cat_mb_crs = cat_mb_all[0].crs

# Write catchments corresponding to MERIT-SWORD reaches to file
with fiona.open(cat_mb_out, 'w', schema=cat_mb_schema,
                driver='ESRI Shapefile',
                crs=cat_mb_crs) as output:
    for cat_fea in cat_mb_lay:
        if cat_fea['properties']['COMID'] in ms_list:
            output.write(cat_fea)

# ------------------------------------------------------------------------------
# Read selected translation catchments
# ------------------------------------------------------------------------------
# Read MERIT-SWORD catchment file
cat_mb_lay = fiona.open(cat_mb_out, 'r', crs="EPSG:4326")

# ------------------------------------------------------------------------------
# Create spatial index for the bounds of each SWORD reach in relevant regions
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
# Identify SWORD reaches corresponding to each MB reach (MB-to-SWORD)
# ------------------------------------------------------------------------------
# Create hash of cat_ms_lay COMIDS
cat_mb_hash = {}

for cat_fea in cat_mb_lay:
    cat_mb_hash[cat_fea['properties']['COMID']] = int(cat_fea['id'])

# Create dictionary to store MB to SWORD translation and lengths
m_cat = {}
m_len = {}

for riv_fea in riv_mb_lay:

    # If MB reach not in MERIT-SWORD network, it has no translation
    if not (riv_fea['properties']['COMID'] in ms_list):

        # Pad lists to reach desired length and insert to dictionary
        m_cat[riv_fea['properties']['COMID']] = [0] * 40

        m_len[riv_fea['properties']['COMID']] = [0] * 40

        # Continue to next reach
        continue

    # If MB reach is in MERIT-SWORD network, translate to SWORD
    # Load translation  catchment corresponding to MB reach
    cat_fea = cat_mb_lay[cat_mb_hash[riv_fea['properties']['COMID']]]

    # Create shapely geometric object for each sword reach
    cat_shy = shapely.geometry.shape(cat_fea['geometry'])

    # Create prepared geometric object to allow for faster processing
    cat_pre = shapely.prepared.prep(cat_shy)

    # Filter MERIT catchments bounding boxes with SWORD buffer
    sword_int_fid = [int(x) for x in
                     list(sword_index.intersection(cat_shy.bounds))]

    # --------------------------------------------------------------------------
    # Intersect index filtered SWORD reaches with MERIT-SWORD catchments
    # --------------------------------------------------------------------------

    sword_dict = {}

    for i in range(len(sword_int_fid)):

        # Load relevant sword layer
        # sword layer integer shifted by 1 to prevent leading zero from
        # being deleted
        sword_lay = sword_lays[int(str(sword_int_fid[i])[0])-1]

        # Retrieve SWORD geometry corresponding to intersect fid
        sword_fea = sword_lay[int(str(sword_int_fid[i])[1:])]

        sword_shy = shapely.geometry.shape(sword_fea['geometry'])

        # ----------------------------------------------------------------------
        # If catchment intersects with reach, extract COMID
        # ----------------------------------------------------------------------

        if cat_pre.intersects(sword_shy):

            # Check for valid catchment geometry (self-ring intersects)
            if not cat_shy.is_valid:

                # Zero distance buffer for invalid geometries
                cat_shy = cat_shy.buffer(0)

            # Catch errors where SWORD reaches have 0 length
            if sword_shy.length > 0:
                # Store parttion of SWORD reach contained by intersect cat
                sword_dict[sword_fea['properties']['reach_id']] = \
                    round(sword_fea['properties']['reach_len'] *
                          (sword_shy.intersection(cat_shy).length /
                           sword_shy.length), 2)

            else:
                sword_dict[sword_fea['properties']['reach_id']] = 0

    # Order SWORD reach_ids by parttion of SWORD reach contained within cat
    # Sort by comid if tie in intersecting length
    m_cat_ord = sorted(sword_dict, key=lambda x: (-sword_dict[x], -x))

    m_len_ord = [sword_dict[x] for x in m_cat_ord]

    # --------------------------------------------------------------------------
    # Compare flow accumulation values between translated reaches
    # --------------------------------------------------------------------------

    if len(m_cat_ord) > 0:

        # Retrieve flow accumulation value for MB reach
        mb_fa = mfa[cat_fea['properties']['COMID']]

        # Retrieve flow accumulations for SWORD reaches
        sword_fa = [sfa[x] for x in m_cat_ord]

        # Find indices of translations where flow accumulation values are
        # within of 1 order of magnitude of each other
        fa_valid = [ind for ind in range(len(m_cat_ord)) if
                    (mb_fa / sword_fa[ind] < 10) &
                    (mb_fa / sword_fa[ind] > 0.1)]

        # Only keep translated reaches with valid flow accumulations
        m_cat_ord = [m_cat_ord[ind] for ind in fa_valid]
        m_len_ord = [m_len_ord[ind] for ind in fa_valid]

    # Pad lists to reach desired length and insert to dictionary
    m_cat[cat_fea['properties']['COMID']] = m_cat_ord + [0] * \
        (40 - len(m_cat_ord))

    m_len[cat_fea['properties']['COMID']] = m_len_ord + [0] * \
        (40 - len(m_len_ord))


# ******************************************************************************
# Write translated reaches to NetCDF
# ******************************************************************************
print('- Writing translations to file')
# ------------------------------------------------------------------------------
# SWORD-to-MB translation
# ------------------------------------------------------------------------------
# If no translated reaches, write empty file
if len(sw_cat) == 0:

    sw_df = pd.DataFrame()

else:

    # Convert dictionaries to dataframes
    sw_cat_df = pd.DataFrame(sw_cat).T.sort_index()
    sw_len_df = pd.DataFrame(sw_len).T.sort_index()

    # Rename columns
    sw_cat_df.columns = ['mb_' + str(x) for x in range(1, 41)]
    sw_len_df.columns = ['part_len_' + str(x) for x in range(1, 41)]

    # Combine dataframes for output
    sw_df = sw_cat_df.join(sw_len_df, how='inner')

# Convert dataframe to xarray dataset
sw_ds = xr.Dataset.from_dataframe(sw_df)
sw_ds = sw_ds.rename({'index': 'sword'})

# Set compression
sw_encoding = {var: {'zlib': True} for var in sw_ds.data_vars}

# Set attributes
sw_ds.attrs = {'description': 'SWORD to MERIT-Basins Translation: Pfaf ' +
               pfaf_srt[0]}

# Set variable attributes
sw_ds['sword'].attrs = {'units': 'unitless',
                        'long_name': 'SWORD reach_id'}

# If dataset has values:
if len(sw_ds) > 0:
    for t in range(40):

        # Set attributes for mb_1 to mb_40 variables
        sw_ds[sw_cat_df.columns[t]].attrs = {'units': 'unitless',
                                             'long_name': 'MB COMID (' +
                                             str(t + 1) + ') corresponding to'
                                             ' SWORD reach'}

        # Set attributes for part_len_1 to part_len_40 variables
        sw_ds[sw_len_df.columns[t]].attrs = {'units': 'meters',
                                             'long_name':
                                             'Partial length of SWORD reach '
                                             'within corresponding MB catchment'
                                             ' ('+str(t+1)+')'}

# Write to NetCDF
sw_ds.to_netcdf(sword_to_mb_out, format='NETCDF4', engine='netcdf4',
                encoding=sw_encoding)

# ------------------------------------------------------------------------------
# MB-to-SWORD translation
# ------------------------------------------------------------------------------
# If no translated reaches, write empty file
if len(m_cat) == 0:

    m_df = pd.DataFrame()

else:

    # Convert dictionaries to dataframes
    m_cat_df = pd.DataFrame(m_cat).T.sort_index()
    m_len_df = pd.DataFrame(m_len).T.sort_index()

    # Rename columns
    m_cat_df.columns = ['sword_' + str(x) for x in range(1, 41)]
    m_len_df.columns = ['part_len_' + str(x) for x in range(1, 41)]

    # Combine dataframes for output
    m_df = m_cat_df.join(m_len_df, how='inner')

# Convert dataframe to xarray dataset
m_ds = xr.Dataset.from_dataframe(m_df)
m_ds = m_ds.rename({'index': 'mb'})

# Set compression
m_encoding = {var: {'zlib': True} for var in m_ds.data_vars}

# Set attributes
m_ds.attrs = {'description': 'MERIT-Basins to SWORD Translation: Pfaf ' +
              pfaf_srt[0]}

# Set variable attributes
m_ds['mb'].attrs = {'units': 'unitless',
                    'long_name': 'MERIT-Basins reach COMID'}

# If dataset has values:
if len(m_ds) > 0:
    for t in range(40):

        # Set attributes for sword_1 to sword_40 variables
        m_ds[m_cat_df.columns[t]].attrs = {'units': 'unitless',
                                           'long_name':
                                           'SWORD reach_id (' +
                                           str(t + 1) + ') corresponding to'
                                           ' MB reach'}

        # Set attributes for part_len_1 to part_len_40 variables
        m_ds[m_len_df.columns[t]].attrs = {'units': 'meters',
                                           'long_name':
                                           'Partial length of SWORD reach (' +
                                           str(t+1)+') '
                                           'within corresponding MB catchment'}

# Write to NetCDF
m_ds.to_netcdf(mb_to_sword_out, format='NETCDF4', engine='netcdf4',
               encoding=m_encoding)

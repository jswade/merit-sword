#!/usr/bin/env python3
# ******************************************************************************
# ms_riv_trace.py
# ******************************************************************************

# Purpose:
# Given a river shapefile from MERIT-Basins, a catchment shapefile from
# MERIT-Basins, a river shapefile from SWORD, and csv files identifying
# overlaps between regions in the datasets, this script generates a shapefile of
# MERIT-Basins reaches that correspond to reaches in SWORD.

# Author:
# Jeffrey Wade, 2024

# ******************************************************************************
# Import Python modules
# ******************************************************************************
import sys
import re
import pandas as pd
import fiona
import shapely.geometry
import shapely.ops
import shapely.prepared
import glob
import rtree


# ******************************************************************************
# Declaration of variables (given as command line arguments)
# ******************************************************************************
# 1 - riv_mb_shp
# 2 - cat_mb_shp
# 3 - sword_shp
# 4 - sw_to_mb_reg_in
# 5 - mb_to_reg_reg_in
# 6 - riv_ms_out

# ******************************************************************************
# Get command line arguments
# ******************************************************************************
IS_arg = len(sys.argv)
if IS_arg != 7:
    print('ERROR - 6 arguments must be used')
    raise SystemExit(22)

riv_mb_shp = sys.argv[1]
cat_mb_shp = sys.argv[2]
sword_shp = sys.argv[3]
sw_to_mb_reg_csv = sys.argv[4]
mb_to_sw_reg_csv = sys.argv[5]
riv_ms_out = sys.argv[6]


# ******************************************************************************
# Check if files exist
# ******************************************************************************
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
riv_mb_reg = riv_mb_shp.split('pfaf_')[1][0:2]
cat_mb_reg = cat_mb_shp.split('pfaf_')[1][0:2]
sword_reg = sword_shp.split('hb')[1][0:2]
riv_ms_out_reg = riv_ms_out.split('pfaf_')[1][0:2]

if not (riv_mb_reg == cat_mb_reg == riv_ms_out_reg == sword_reg):
    print('ERROR - Input files correspond to different regions')
    raise SystemExit(22)


# ******************************************************************************
# Read files
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
mb_pfaf_list = pd.Series([x.partition("pfaf_")[-1][0:2] for x in
                          cat_mb_files]).sort_values()

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
sw_pfaf_list = pd.Series([x.partition("reaches_hb")[-1][0:2] for x in
                          sword_files]).sort_values()

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
# Get region indices of target region shapefiles
# ------------------------------------------------------------------------------
riv_mb_ind = riv_mb_files.index(riv_mb_shp)
cat_mb_ind = cat_mb_files.index(cat_mb_shp)
sword_ind = sword_files.index(sword_shp)


# ******************************************************************************
# Create spatial index for bounds of each MERIT-Basins catchment
# ******************************************************************************
print('- Preparing spatial indices')

# Retrieve MB pfaf regions to load for given SWORD region
mb_reg = (sw_to_mb_reg.loc[int(riv_mb_reg)]
          .dropna().astype(int).values.tolist())

# Find MB file indices corresponding to those pfaf regions
mb_reg_ind = [mb_pfaf_list.index[mb_pfaf_list == str(x)].values[0] for x in
              mb_reg]

# Initialize liss to store index for each pfaf region
cat_index = []

# Loop through overlapping pfaf regions
for j in mb_reg_ind:

    # Initialize index
    cat_index_j = rtree.index.Index()

    # Relate catchment id to bounds of feature geometry
    for cat_fea in cat_mb_all[j]:
        cat_fid = int(cat_fea['id'])
        cat_shy = shapely.geometry.shape(cat_fea['geometry'])
        cat_index_j.insert(cat_fid, cat_shy.bounds)

    # Append to list
    cat_index.append(cat_index_j)


# ******************************************************************************
# Link MERIT-Basins and SWORD reaches for region of interest
# ******************************************************************************
print('- Generating MERIT-SWORD network')

# Retrieve SWORD layer for current region
sword_lay = sword_all[sword_ind]

# Retrieve MB layers for all overlapping regions
riv_mb_lays = [riv_mb_all[i] for i in mb_reg_ind]
cat_mb_lays = [cat_mb_all[i] for i in mb_reg_ind]

# ------------------------------------------------------------------------------
# Identify MERIT-Basins catchments intersected by SWORD reaches
# ------------------------------------------------------------------------------
print('- Identifying intersecting reaches')

riv_out = []

# Loop through relevant MERIT-Basins regions
for i in range(len(riv_mb_lays)):

    for sword_fea in sword_lay:

        # Create shapely geometric object for each sword reach
        sword_shy = shapely.geometry.shape(sword_fea['geometry'])

        # Create prepared geometric object to allow for faster processing
        sword_pre = shapely.prepared.prep(sword_shy)

        # Filter MB catchment bounding boxes with SWORD reach
        riv_int_fid = [int(x) for x in
                       list(cat_index[i].intersection(sword_shy.bounds))]

        # ----------------------------------------------------------------------
        # Intersect index filtered MB catchments with SWORD reaches
        # ----------------------------------------------------------------------

        comid_dict = {}

        for t in range(len(riv_int_fid)):

            # Retrieve MB cat geometry corresponding to intersect fid
            cat_fea = cat_mb_lays[i][riv_int_fid[t]]

            cat_shy = shapely.geometry.shape(cat_fea['geometry'])

            # ------------------------------------------------------------------
            # If catchment intersects with reach, extract properties
            # ------------------------------------------------------------------

            if sword_pre.intersects(cat_shy):

                # Check for valid catchment geometry (self-ring intersects)
                if not cat_shy.is_valid:

                    # Zero distance buffer for invalid geometries
                    cat_shy = cat_shy.buffer(0)

                # Catch errors where SWORD reaches have 0 length
                if sword_shy.length > 0:
                    # Store frac of SWORD reach contained by intersect cat
                    # Key is fractional intersection value
                    comid_dict[sword_shy.intersection(cat_shy).length /
                               sword_shy.length] = \
                               cat_fea['properties']['COMID']
                else:
                    comid_dict[0] = cat_fea['properties']['COMID']

        # Order MB comids by fraction of SWORD reach contained within cat
        cat_ord = [comid_dict[x] for x in
                   sorted(comid_dict.keys(), reverse=True)]

        if len(cat_ord) > 0:
            # Add cat with highest proportion of intersection to list
            riv_out.append(cat_ord[0])

# ------------------------------------------------------------------------------
# Trace selected MERIT-Basins reaches down-network using ID links
# ------------------------------------------------------------------------------
print('- Performing topological tracing')

# Remove duplicate values
mb_sel = list(set(riv_out))

# Initialize list to store selected MERIT-Basins reaches
riv_trace = []

# Add all merit_sel reaches to list
riv_trace.extend(mb_sel)

# Create dictionary of MB reaches and their next downstream ID
nd_dict = {}

for riv_lay in riv_mb_lays:

    for riv_fea in riv_lay:

        # Retrieve COMID and NextDownID
        mb_id = riv_fea['properties']['COMID']
        mb_nextdown = riv_fea['properties']['NextDownID']

        # Store in dictionary
        nd_dict[mb_id] = mb_nextdown

# Loop through mb_sel reaches
for rch in mb_sel:

    # Retrieve ID of first downstream reach
    nextid = nd_dict[rch]

    # Add first nextid to riv_trace list
    riv_trace.append(nextid)

    # While nextid doesn't equal 0 (end of network):
    # Continue finding next downstream reach
    while nextid != 0:

        # Retrieve nextid of next downstream reach
        nextid = nd_dict[nextid]

        # Add first nextid to riv_trace list
        riv_trace.append(nextid)

# Remove duplicates from riv_trace list
riv_trace = list(set(riv_trace))

# Remove zeroes from output list
riv_trace = [i for i in riv_trace if i != 0]

# ------------------------------------------------------------------------------
# Remove MERIT-Basins reaches outside of buffer of SWORD reaches
# ------------------------------------------------------------------------------
print('- Removing reaches outside buffer')

# Retrieve SWORD geometries
sword_geom = [shapely.geometry.shape(sword_lay[j]['geometry']) for j
              in range(len(sword_lay))]

# Merge sword into single feature to speed up distance calculation
sword_merge = shapely.ops.unary_union(sword_geom)

# Set sword buffer removal distance in degrees (10km)
rem_buf = .09

# Retrieve MB features
riv_feas = [riv_fea for lay in riv_mb_lays for riv_fea in lay if
            riv_fea['properties']['COMID'] in riv_trace]

# Initialize list to store reaches filtered by buffer distance
riv_fil = []

# Loop through relevant reaches
for riv_fea in riv_feas:

    # Create shapely geometric object for each sword reach
    riv_shy = shapely.geometry.shape(riv_fea['geometry'])

    # Distance between sword reach and merit reach
    sword_dis = sword_merge.distance(riv_shy)

    # --------------------------------------------------------------------------
    # Current reach is within buffer distances of sword network
    # --------------------------------------------------------------------------
    if sword_dis < rem_buf:
        # Add id to list
        riv_fil.append(riv_fea['properties']['COMID'])


# ******************************************************************************
# Write traced/buffer-removed MERIT-SWORD network to file
# ******************************************************************************
print('- Writing shapefiles')

# Retrieve schema and crs
mb_schema = riv_mb_all[riv_mb_ind].schema.copy()
mb_crs = riv_mb_all[riv_mb_ind].crs

with fiona.open(riv_ms_out, 'w', schema=mb_schema,
                driver='ESRI Shapefile',
                crs=mb_crs) as output:
    # Loop through relevant pfaf regions
    for riv_lay in riv_mb_lays:
        for riv_fea in riv_lay:
            if riv_fea['properties']['COMID'] in riv_fil:
                output.write(riv_fea)

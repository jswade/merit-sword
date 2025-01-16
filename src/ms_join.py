#!/usr/bin/env python3
# ******************************************************************************
# ms_join.py
# ******************************************************************************

# Purpose:
# Given translations between MB and SWORD, diagnostic qualtity flags,
# a MERIT-SWORD river shapefile, a
# SWORD river shapefile, join translations and diagnostic flags to shapefiles

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
# 3 - ms_diag_nc
# 4 - sm_diag_nc
# 5 - riv_mb_shp
# 6 - sword_shp
# 7 - sw_shp_out
# 8 - mb_shp_out

# ******************************************************************************
# Get command line arguments
# ******************************************************************************
IS_arg = len(sys.argv)
if IS_arg != 9:
    print('ERROR - 8 arguments must be used')
    raise SystemExit(22)

ms_trans_nc = sys.argv[1]
sm_trans_nc = sys.argv[2]
ms_diag_nc = sys.argv[3]
sm_diag_nc = sys.argv[4]
riv_mb_shp = sys.argv[5]
sword_shp = sys.argv[6]
sw_shp_out = sys.argv[7]
mb_shp_out = sys.argv[8]


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
    with open(ms_diag_nc) as file:
        pass
except IOError:
    print('ERROR - Unable to open '+ms_diag_nc)
    raise SystemExit(22)

try:
    with open(sm_diag_nc) as file:
        pass
except IOError:
    print('ERROR - Unable to open '+sm_diag_nc)
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
ms_diag_reg = ms_diag_nc.split('pfaf_')[1][0:2]
sm_diag_reg = sm_diag_nc.split('pfaf_')[1][0:2]
riv_mb_reg = riv_mb_shp.split('pfaf_')[1][0:2]
sword_reg = sword_shp.split('hb')[1][0:2]

if not (ms_trans_reg == sm_trans_reg == riv_mb_reg == sword_reg ==
        ms_diag_reg == sm_diag_reg):
    print('ERROR - Input files correspond to different regions')
    raise SystemExit(22)


# ******************************************************************************
# Read files
# ******************************************************************************
print('- Reading files')
# ------------------------------------------------------------------------------
# MB-to-SWORD Translation
# ------------------------------------------------------------------------------
# Read MB-to-SWORD translation
ms_df = xr.open_dataset(ms_trans_nc).to_dataframe()

# ------------------------------------------------------------------------------
# SWORD-to-MB Translation
# ------------------------------------------------------------------------------
# Read SWORD-to-MB translation
sm_df = xr.open_dataset(sm_trans_nc).to_dataframe()

# ------------------------------------------------------------------------------
# MB-to-SWORD Translation Diagnostic
# ------------------------------------------------------------------------------
# Read MB-to-SWORD translation diagnostic
ms_diag = xr.open_dataset(ms_diag_nc).to_dataframe()

# ------------------------------------------------------------------------------
# SWORD-to-MB Translation Diagnostic
# ------------------------------------------------------------------------------
# Read SWORD-to-MB translation diagnostic
sm_diag = xr.open_dataset(sm_diag_nc).to_dataframe()

# ------------------------------------------------------------------------------
# MB Rivers
# ------------------------------------------------------------------------------
# Read MB shapefile
with fiona.open(riv_mb_shp, "r", crs="EPSG:4326") as src:
    mb_schema = src.schema
    mb_crs = src.crs
    mb_records = list(src)

# ------------------------------------------------------------------------------
# SWORD
# ------------------------------------------------------------------------------
# Read SWORD shapefile
with fiona.open(sword_shp, "r", crs="EPSG:4326") as src:
    sw_schema = src.schema
    sw_crs = src.crs
    sw_records = list(src)


# ******************************************************************************
# Join translation and diagnostic to MB shapefile
# ******************************************************************************
print('- Joining MB Tables')
# ------------------------------------------------------------------------------
# Reformat files for joining
# ------------------------------------------------------------------------------
# Rename index
ms_df.index.names = ['COMID']
ms_diag.index.names = ['COMID']
ms_diag = ms_diag.rename(columns={"flag": "diag_flag"})

# Convert translations to dictionary
ms_dict = ms_df.to_dict(orient="index")
ms_diag_dict = ms_diag.to_dict(orient="index")

# ------------------------------------------------------------------------------
# Update MB Shapefile with translations and diagnostics
# ------------------------------------------------------------------------------
# Update the MB schema to join column in ms_diag
mb_schema["properties"]["diag_flag"] = "int"

# Update the MB schema to join columns in ms_df
for i in range(len(ms_df.columns)):
    if i < 40:
        mb_schema["properties"][ms_df.columns[i]] = "int"
    else:
        mb_schema["properties"][ms_df.columns[i]] = "float"

# Join records from ms_df and ms_diag to MB shapefile
mb_up_records = []
for record in mb_records:
    comid = record["properties"]["COMID"]
    record["properties"].update(ms_diag_dict[comid])
    record["properties"].update(ms_dict[comid])
    mb_up_records.append(record)

# ------------------------------------------------------------------------------
# Write updated shapefile to file
# ------------------------------------------------------------------------------
with fiona.open(mb_shp_out, "w", driver="ESRI Shapefile",
                schema=mb_schema, crs=mb_crs) as dst:
    for record in mb_up_records:
        dst.write(record)


# ******************************************************************************
# Join translation and diagnostic to SWORD shapefile
# ******************************************************************************
print('- Joining SWORD Tables')
# ------------------------------------------------------------------------------
# Reformat files for joining
# ------------------------------------------------------------------------------
# Rename index
sm_df.index.names = ['reach_id']
sm_diag.index.names = ['reach_id']
sm_diag = sm_diag.rename(columns={"flag": "diag_flag"})

# Convert translations to dictionary
sm_dict = sm_df.to_dict(orient="index")
sm_diag_dict = sm_diag.to_dict(orient="index")

# ------------------------------------------------------------------------------
# Update SWORD Shapefile with translations and diagnostics
# ------------------------------------------------------------------------------
# Update the SWORD schema to join column in ms_diag
sw_schema["properties"]["diag_flag"] = "int"

# Update the MB schema to join columns in ms_df
for i in range(len(sm_df.columns)):
    if i < 40:
        sw_schema["properties"][sm_df.columns[i]] = "int"
    else:
        sw_schema["properties"][sm_df.columns[i]] = "float"

# Join records from sm_df and sm_diag to SWORD shapefile
sw_up_records = []
for record in sw_records:
    reach_id = record["properties"]["reach_id"]
    record["properties"].update(sm_diag_dict[reach_id])
    record["properties"].update(sm_dict[reach_id])
    sw_up_records.append(record)

# ------------------------------------------------------------------------------
# Write updated shapefile to file
# ------------------------------------------------------------------------------
with fiona.open(sw_shp_out, "w", driver="ESRI Shapefile",
                schema=sw_schema, crs=sw_crs) as dst:
    for record in sw_up_records:
        dst.write(record)

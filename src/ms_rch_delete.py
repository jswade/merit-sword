#!/usr/bin/env python3
# ******************************************************************************
# ms_rch_delete.py
# ******************************************************************************

# Purpose:
# Given a river shapefile of MERIT-SWORD reaches and a CSV containing reaches
# identified from manual removal, this script removes selected reaches to
# generate the final MERIT-SWORD river network.

# Author:
# Jeffrey Wade, 2024

# ******************************************************************************
# Import Python modules
# ******************************************************************************
import sys
import pandas as pd
import fiona


# ******************************************************************************
# Declaration of variables (given as command line arguments)
# ******************************************************************************
# 1 - riv_ms_shp
# 2 - del_csv
# 3 - riv_ms_out


# ******************************************************************************
# Get command line arguments
# ******************************************************************************
IS_arg = len(sys.argv)
if IS_arg != 4:
    print('ERROR - 3 arguments must be used')
    raise SystemExit(22)

riv_ms_shp = sys.argv[1]
del_csv = sys.argv[2]
riv_ms_out = sys.argv[3]


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
    with open(del_csv) as file:
        pass
except IOError:
    print('ERROR - Unable to open '+del_csv)
    raise SystemExit(22)

# Confirm files refer to same region
riv_ms_reg = riv_ms_shp.split('pfaf_')[1][0:2]
riv_ms_out_reg = riv_ms_out.split('pfaf_')[1][0:2]

if not (riv_ms_reg == riv_ms_out_reg):
    print('ERROR - Input files correspond to different regions')
    raise SystemExit(22)


# ******************************************************************************
# Read files
# ******************************************************************************
print('- Reading files')
# Read MERIT-SWORD file
riv_ms = fiona.open(riv_ms_shp, 'r', crs="EPSG:4326")

# Read csv
del_df = pd.read_csv(del_csv)


# ******************************************************************************
# Remove reaches from traced MERIT-SWORD network
# ******************************************************************************
print('- Removing reaches')
# Retrieve schema and crs
ms_schema = riv_ms.schema.copy()
ms_crs = riv_ms.crs

# Retrieve reaches to be deleted from given region
del_rch = del_df.COMID.to_list()

# Write filtered reaches to file
with fiona.open(riv_ms_out, 'w', schema=ms_schema,
                driver='ESRI Shapefile',
                crs=ms_crs) as output:
    for riv_fea in riv_ms:
        if riv_fea['properties']['COMID'] not in del_rch:
            output.write(riv_fea)

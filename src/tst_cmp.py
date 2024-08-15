#!/usr/bin/env python3
# ******************************************************************************
# tst_cmp.py
# ******************************************************************************

# Purpose:
# Given an original MERIT-SWORD file and a file generating during testing,
# ensure that files are identical.

# Author:
# Jeffrey Wade, 2024


# ******************************************************************************
# Import Python modules
# ******************************************************************************
import sys
import filecmp


# ******************************************************************************
# Declaration of variables (given as command line arguments)
# ******************************************************************************
# 1 - file_org
# 2 - file_tst


# ******************************************************************************
# Get command line arguments
# ******************************************************************************
IS_arg = len(sys.argv)
if IS_arg != 3:
    print('ERROR - 2 arguments must be used')
    raise SystemExit(22)

file_org = sys.argv[1]
file_tst = sys.argv[2]


# ******************************************************************************
# Check if files exist
# ******************************************************************************
try:
    with open(file_org) as file:
        pass
except IOError:
    print('ERROR - Unable to open ' + file_org)
    raise SystemExit(22)

try:
    with open(file_tst) as file:
        pass
except IOError:
    print('ERROR - Unable to open ' + file_tst)
    raise SystemExit(22)


# ******************************************************************************
# Compare original and test files
# ******************************************************************************

# Clear cache
filecmp.clear_cache()

# If files are not identical, raise error
if not (filecmp.cmp(file_org, file_tst, shallow=False)):
    print('ERROR - Comparison failed.')
    raise SystemExit(99)
else:
    print('Comparison successful!')

##!/bin/bash
##*****************************************************************************
##tst_pub_repr_Wade_etal_202x.sh
##*****************************************************************************
##Purpose:
##This script reproduces all pre- and post-processing steps used in the
##writing of:
##Wade, J., David, C., Altenau, E., Collins, E.,  Oubanas, H., Coss, S.,
##Cerbelaud, A., Tom, M., Durand, M., Pavelsky, T. (In Review). Bidirectional
##Translations Between Observational and Topography-based Hydrographic
##Datasets: MERIT-Basins and the SWOT River Database (SWORD).
##DOI: xx.xxxx/xxxxxxxxxxxx
##The files used are available from:
##Wade, J., David, C., Altenau, E., Collins, E.,  Oubanas, H., Coss, S.,
##Cerbelaud, A., Tom, M., Durand, M., Pavelsky, T. (2024). MERIT-SWORD:
##Bidirectional Translations Between MERIT-Basins and the SWORD River
##Database (SWORD).
##Zenodo
##DOI: 10.5281/zenodo.13183883
##The following are the possible arguments:
## - No argument: all unit tests are run
## - One unique unit test number: this test is run
## - Two unit test numbers: all tests between those (included) are run
##The script returns the following exit codes
## - 0  if all experiments are successful
## - 22 if some arguments are faulty
## - 99 if a comparison failed
##Author:
##Jeffrey Wade, Cedric H. David, 2024
#
#*****************************************************************************
#Publication message
#*****************************************************************************
echo "********************"
echo "Reproducing files for: https://doi.org/10.5281/zenodo.13183883"
echo "********************"


#*****************************************************************************
#Set Pfaf and SWORD regions
#*****************************************************************************
pfaf='11'
reg='af'


#*****************************************************************************
#Select which unit tests to perform based on inputs to this shell script
#*****************************************************************************
#Perform all unit tests if no options are given
tot=9
if [ "$#" = "0" ]; then
     fst=1
     lst=$tot
     echo "Performing all unit tests: $1-$2"
     echo "********************"
fi

#Perform one single unit test if one option is given
if [ "$#" = "1" ]; then
     fst=$1
     lst=$1
     echo "Performing one unit test: $1"
     echo "********************"
fi

#Perform all unit tests between first and second option given (both included)
if [ "$#" = "2" ]; then
     fst=$1
     lst=$2
     echo "Performing unit tests: $1-$2"
     echo "********************"
fi

#Exit if more than two options are given
if [ "$#" -gt "2" ]; then
     echo "A maximum of two options can be used" 1>&2
     exit 22
fi


#*****************************************************************************
#Initialize count for unit tests
#*****************************************************************************
unt=0


#*****************************************************************************
#Edit SWORD network to match longitude conventions of MERIT-Basins
#*****************************************************************************
unt=$((unt+1))
if (("$unt" >= "$fst")) && (("$unt" <= "$lst")) ; then
echo "Running unit test $unt/$tot"

run_file=tmp_run_$unt.txt
cmp_file=tmp_cmp_$unt.txt

mkdir -p "../output_test/sword_edit"

echo "- Editing SWORD network"
../src/ms_sword_edit.py                                                        \
    ../input/SWORD/${reg}_sword_reaches_hb${pfaf}_v16.shp                      \
    ../output_test/sword_edit/${reg}_sword_reaches_hb${pfaf}_v16.shp           \
    > $run_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed run: $run_file" >&2 ; exit $x ; fi

echo "- Comparing SWORD file (.shp)"
../src/tst_cmp.py                                                              \
    ../input/SWORD/${reg}_sword_reaches_hb${pfaf}_v16.shp                      \
    ../output_test/sword_edit/${reg}_sword_reaches_hb${pfaf}_v16.shp           \
    > $cmp_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed comparison: $cmp_file" >&2 ; exit $x ; fi
#    
rm -f $run_file
rm -f $cmp_file
echo "Success"
echo "********************"
fi


#*****************************************************************************
#Identify overlap between SWORD and MERIT-Basins Regions
#*****************************************************************************
unt=$((unt+1))
if (("$unt" >= "$fst")) && (("$unt" <= "$lst")) ; then
echo "Running unit test $unt/$tot"

run_file=tmp_run_$unt.txt
cmp_file=tmp_cmp_$unt.txt

mkdir -p "../output_test/ms_region_overlap"

echo "- Identifying overlap between hydrographic regions"
python ../src/ms_region_overlap.py                                             \
    ../output/sword_edit/                                                      \
    ../input/MeanDRS/cat_disso/                                                \
    ../output_test/ms_region_overlap/sword_to_mb_reg_overlap.csv               \
    ../output_test/ms_region_overlap/mb_to_sword_reg_overlap.csv               \
    > $run_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed run: $run_file" >&2 ; exit $x ; fi

echo "- Comparing overlap file 1 (.csv)"
../src/tst_cmp.py                                                              \
    ../output/ms_region_overlap/sword_to_mb_reg_overlap.csv                    \
    ../output_test/ms_region_overlap/sword_to_mb_reg_overlap.csv               \
    > $cmp_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed comparison: $cmp_file" >&2 ; exit $x ; fi

echo "- Comparing overlap file 2 (.csv)"
../src/tst_cmp.py                                                              \
    ../output/ms_region_overlap/mb_to_sword_reg_overlap.csv                    \
    ../output_test/ms_region_overlap/mb_to_sword_reg_overlap.csv               \
    > $cmp_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed comparison: $cmp_file" >&2 ; exit $x ; fi

rm -f $run_file
rm -f $cmp_file
echo "Success"
echo "********************"
fi


#*****************************************************************************
#Generate MERIT-SWORD river network
#*****************************************************************************
unt=$((unt+1))
if (("$unt" >= "$fst")) && (("$unt" <= "$lst")) ; then
echo "Running unit test $unt/$tot"

run_file=tmp_run_$unt.txt
cmp_file=tmp_cmp_$unt.txt

mkdir -p "../output_test/ms_riv_trace"

echo "- Generating MERIT-SWORD river network"
../src/ms_riv_trace.py                                                         \
    ../input/MB/riv/riv_pfaf_${pfaf}_MERIT_Hydro_v07_Basins_v01.shp            \
    ../input/MB/cat/cat_pfaf_${pfaf}_MERIT_Hydro_v07_Basins_v01.shp            \
    ../output/sword_edit/${reg}_sword_reaches_hb${pfaf}_v16.shp                \
    ../output/ms_region_overlap/sword_to_mb_reg_overlap.csv                    \
    ../output/ms_region_overlap/mb_to_sword_reg_overlap.csv                    \
    ../output_test/ms_riv_trace/meritsword_pfaf_${pfaf}_trace.shp              \
    > $run_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed run: $run_file" >&2 ; exit $x ; fi

echo "- Comparing MERIT-SWORD traced file (.shp)"
../src/tst_cmp.py                                                              \
    ../output/ms_riv_trace/meritsword_pfaf_${pfaf}_trace.shp                   \
    ../output_test/ms_riv_trace/meritsword_pfaf_${pfaf}_trace.shp              \
    > $cmp_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed comparison: $cmp_file" >&2 ; exit $x ; fi

rm -f $run_file
rm -f $cmp_file
echo "Success"
echo "********************"
fi


#*****************************************************************************
#Remove manually deleted reaches from MERIT-SWORD river network
#*****************************************************************************
unt=$((unt+1))
if (("$unt" >= "$fst")) && (("$unt" <= "$lst")) ; then
echo "Running unit test $unt/$tot"

run_file=tmp_run_$unt.txt
cmp_file=tmp_cmp_$unt.txt

mkdir -p "../output_test/ms_riv_network"

echo "- Removing reaches from MERIT-SWORD river network"
../src/ms_rch_delete.py                                                        \
    ../output/ms_riv_trace/meritsword_pfaf_${pfaf}_trace.shp                   \
    ../output/ms_riv_edit/meritsword_edits.csv                                 \
    ../output_test/ms_riv_network/meritsword_pfaf_${pfaf}_network.shp          \
    > $run_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed run: $run_file" >&2 ; exit $x ; fi

echo "- Comparing MERIT-SWORD network file (.shp)"
../src/tst_cmp.py                                                              \
    ../output/ms_riv_network/meritsword_pfaf_${pfaf}_network.shp               \
    ../output_test/ms_riv_network/meritsword_pfaf_${pfaf}_network.shp          \
    > $cmp_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed comparison: $cmp_file" >&2 ; exit $x ; fi

rm -f $run_file
rm -f $cmp_file
echo "Success"
echo "********************"
fi


#*****************************************************************************
#Establish translations between MERIT-Basins and SWORD reaches
#*****************************************************************************
unt=$((unt+1))
if (("$unt" >= "$fst")) && (("$unt" <= "$lst")) ; then
echo "Running unit test $unt/$tot"

run_file=tmp_run_$unt.txt
cmp_file=tmp_cmp_$unt.txt

mkdir -p "../output_test/ms_translate_cat/sword_to_mb"
mkdir -p "../output_test/ms_translate_cat/mb_to_sword"
mkdir -p "../output_test/ms_translate/mb_to_sword"
mkdir -p "../output_test/ms_translate/sword_to_mb"

echo "- Translating between MERIT-Basins and SWORD reaches"
../src/ms_translate.py                                                         \
    ../output/ms_riv_network/meritsword_pfaf_${pfaf}_network.shp               \
    ../input/MB/riv/riv_pfaf_${pfaf}_MERIT_Hydro_v07_Basins_v01.shp            \
    ../input/MB/cat/cat_pfaf_${pfaf}_MERIT_Hydro_v07_Basins_v01.shp            \
    ../output/sword_edit/${reg}_sword_reaches_hb${pfaf}_v16.shp                \
    ../output/ms_region_overlap/sword_to_mb_reg_overlap.csv                    \
    ../output/ms_region_overlap/mb_to_sword_reg_overlap.csv                    \
    ../output_test/ms_translate_cat/mb_to_sword/mb_to_sword_pfaf_${pfaf}_translate_cat.shp\
    ../output_test/ms_translate_cat/sword_to_mb/sword_to_mb_pfaf_${pfaf}_translate_cat.shp\
    ../output_test/ms_translate/mb_to_sword/mb_to_sword_pfaf_${pfaf}_translate.nc\
    ../output_test/ms_translate/sword_to_mb/sword_to_mb_pfaf_${pfaf}_translate.nc\
    > $run_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed run: $run_file" >&2 ; exit $x ; fi

echo "- Comparing translation catchment file 1 (.shp)"
../src/tst_cmp.py                                                              \
    ../output/ms_translate_cat/mb_to_sword/mb_to_sword_pfaf_${pfaf}_translate_cat.shp\
    ../output_test/ms_translate_cat/mb_to_sword/mb_to_sword_pfaf_${pfaf}_translate_cat.shp\
    > $cmp_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed comparison: $cmp_file" >&2 ; exit $x ; fi

echo "- Comparing translation catchment file 2 (.shp)"
../src/tst_cmp.py                                                              \
    ../output/ms_translate_cat/sword_to_mb/sword_to_mb_pfaf_${pfaf}_translate_cat.shp\
    ../output_test/ms_translate_cat/sword_to_mb/sword_to_mb_pfaf_${pfaf}_translate_cat.shp\
    > $cmp_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed comparison: $cmp_file" >&2 ; exit $x ; fi

echo "- Comparing translation file 1 (.nc)"
../src/tst_cmp.py                                                              \
    ../output/ms_translate/mb_to_sword/mb_to_sword_pfaf_${pfaf}_translate.nc   \
    ../output_test/ms_translate/mb_to_sword/mb_to_sword_pfaf_${pfaf}_translate.nc\
    > $cmp_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed comparison: $cmp_file" >&2 ; exit $x ; fi

echo "- Comparing translation file 2 (.nc)"
../src/tst_cmp.py                                                              \
    ../output/ms_translate/sword_to_mb/sword_to_mb_pfaf_${pfaf}_translate.nc   \
    ../output_test/ms_translate/sword_to_mb/sword_to_mb_pfaf_${pfaf}_translate.nc\
    > $cmp_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed comparison: $cmp_file" >&2 ; exit $x ; fi

rm -f $run_file
rm -f $cmp_file
echo "Success"
echo "********************"
fi


#*****************************************************************************
#Evaluate quality of translations with diagnostic tests
#*****************************************************************************
unt=$((unt+1))
if (("$unt" >= "$fst")) && (("$unt" <= "$lst")) ; then
echo "Running unit test $unt/$tot"

run_file=tmp_run_$unt.txt
cmp_file=tmp_cmp_$unt.txt

mkdir -p "../output_test/ms_diagnostic/mb_to_sword"
mkdir -p "../output_test/ms_diagnostic/sword_to_mb"

echo "- Evaluating quality of translations with diagnostics"
../src/ms_diagnostic.py                                                        \
    ../output/ms_translate/mb_to_sword/mb_to_sword_pfaf_${pfaf}_translate.nc   \
    ../output/ms_translate/sword_to_mb/sword_to_mb_pfaf_${pfaf}_translate.nc   \
    ../output/ms_riv_network/meritsword_pfaf_${pfaf}_network.shp               \
    ../output/ms_translate_cat/mb_to_sword/mb_to_sword_pfaf_${pfaf}_translate_cat.shp\
    ../output/ms_translate_cat/sword_to_mb/sword_to_mb_pfaf_${pfaf}_translate_cat.shp\
    ../input/MeanDRS/cat_disso/cat_pfaf_${pfaf}_MERIT_Hydro_v07_Basins_v01_disso.shp\
    ../output/sword_edit/${reg}_sword_reaches_hb${pfaf}_v16.shp                \
    ../output/ms_region_overlap/sword_to_mb_reg_overlap.csv                    \
    ../output/ms_region_overlap/mb_to_sword_reg_overlap.csv                    \
    ../output_test/ms_diagnostic/mb_to_sword/mb_to_sword_pfaf_${pfaf}_diagnostic.nc\
    ../output_test/ms_diagnostic/sword_to_mb/sword_to_mb_pfaf_${pfaf}_diagnostic.nc\
    > $run_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed run: $run_file" >&2 ; exit $x ; fi

echo "- Comparing diagnostic file 1 (.nc)"
../src/tst_cmp.py                                                              \
    ../output/ms_diagnostic/mb_to_sword/mb_to_sword_pfaf_${pfaf}_diagnostic.nc \
    ../output_test/ms_diagnostic/mb_to_sword/mb_to_sword_pfaf_${pfaf}_diagnostic.nc\
    > $cmp_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed comparison: $cmp_file" >&2 ; exit $x ; fi

echo "- Comparing diagnostic file 2 (.nc)"
../src/tst_cmp.py                                                              \
    ../output/ms_diagnostic/sword_to_mb/sword_to_mb_pfaf_${pfaf}_diagnostic.nc \
    ../output_test/ms_diagnostic/sword_to_mb/sword_to_mb_pfaf_${pfaf}_diagnostic.nc\
    > $cmp_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed comparison: $cmp_file" >&2 ; exit $x ; fi

rm -f $run_file
rm -f $cmp_file
echo "Success"
echo "********************"
fi


#*****************************************************************************
#Transpose between translations to confirm no loss of data
#*****************************************************************************
unt=$((unt+1))
if (("$unt" >= "$fst")) && (("$unt" <= "$lst")) ; then
echo "Running unit test $unt/$tot"

run_file=tmp_run_$unt.txt
cmp_file=tmp_cmp_$unt.txt

mkdir -p "../output_test/ms_transpose/mb_transposed"
mkdir -p "../output_test/ms_transpose/sword_transposed"

echo "- Transposing between translation tables"
../src/ms_transpose.py                                                         \
    ../output/ms_translate/mb_to_sword/mb_to_sword_pfaf_${pfaf}_translate.nc   \
    ../output/ms_translate/sword_to_mb/sword_to_mb_pfaf_${pfaf}_translate.nc   \
    ../output/ms_riv_network/meritsword_pfaf_${pfaf}_network.shp               \
    ../input/MB/riv/riv_pfaf_${pfaf}_MERIT_Hydro_v07_Basins_v01.shp            \
    ../output/sword_edit/${reg}_sword_reaches_hb${pfaf}_v16.shp                \
    ../output_test/ms_transpose/mb_transposed/mb_to_sword_pfaf_${pfaf}_transpose.nc\
    ../output_test/ms_transpose/sword_transposed/sword_to_mb_pfaf_${pfaf}_transpose.nc\
    > $run_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed run: $run_file" >&2 ; exit $x ; fi

echo "- Comparing transposed file 1 (.nc)"
../src/tst_cmp.py                                                              \
    ../output/ms_transpose/mb_transposed/mb_to_sword_pfaf_${pfaf}_transpose.nc \
    ../output_test/ms_transpose/mb_transposed/mb_to_sword_pfaf_${pfaf}_transpose.nc\
    > $cmp_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed comparison: $cmp_file" >&2 ; exit $x ; fi

echo "- Comparing transposed file 2 (.nc)"
../src/tst_cmp.py                                                              \
    ../output/ms_transpose/sword_transposed/sword_to_mb_pfaf_${pfaf}_transpose.nc\
    ../output_test/ms_transpose/sword_transposed/sword_to_mb_pfaf_${pfaf}_transpose.nc\
    > $cmp_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed comparison: $cmp_file" >&2 ; exit $x ; fi

rm -f $run_file
rm -f $cmp_file
echo "Success"
echo "********************"
fi


#*****************************************************************************
#Map discharge simulations from MeanDRS onto SWORD reaches
#*****************************************************************************
unt=$((unt+1))
if (("$unt" >= "$fst")) && (("$unt" <= "$lst")) ; then
echo "Running unit test $unt/$tot"

run_file=tmp_run_$unt.txt
cmp_file=tmp_cmp_$unt.txt

mkdir -p "../output_test/app_meandrs_to_sword"

echo "- Mapping MeanDRS discharge simulations onto SWORD reaches"
../src/ms_app_meandrs_to_sword.py                                              \
    ../output/ms_translate/mb_to_sword/mb_to_sword_pfaf_${pfaf}_translate.nc   \
    ../output/ms_translate/sword_to_mb/sword_to_mb_pfaf_${pfaf}_translate.nc   \
    ../input/MeanDRS/riv_COR/riv_pfaf_${pfaf}_MERIT_Hydro_v07_Basins_v01_GLDAS_COR.shp\
    ../output/sword_edit/${reg}_sword_reaches_hb${pfaf}_v16.shp                \
    ../output_test/app_meandrs_to_sword/${reg}_sword_reaches_hb${pfaf}_v16_meandrs.shp\
    > $run_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed run: $run_file" >&2 ; exit $x ; fi

echo "- Comparing MeanDRS discharge mapping file (.shp)"
../src/tst_cmp.py                                                              \
    ../output/app_meandrs_to_sword/${reg}_sword_reaches_hb${pfaf}_v16_meandrs.shp\
    ../output_test/app_meandrs_to_sword/${reg}_sword_reaches_hb${pfaf}_v16_meandrs.shp\
    > $cmp_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed comparison: $cmp_file" >&2 ; exit $x ; fi

rm -f $run_file
rm -f $cmp_file
echo "Success"
echo "********************"
fi


#*****************************************************************************
#Map river widths from SWORD onto MERIT-Basins reaches
#*****************************************************************************
unt=$((unt+1))
if (("$unt" >= "$fst")) && (("$unt" <= "$lst")) ; then
echo "Running unit test $unt/$tot"

run_file=tmp_run_$unt.txt
cmp_file=tmp_cmp_$unt.txt

mkdir -p "../output_test/app_sword_to_mb"

echo "- Mapping SWORD river widths onto MERIT-Basins reaches"
../src/ms_app_sword_to_mb.py                                                   \
    ../output/ms_translate/mb_to_sword/mb_to_sword_pfaf_${pfaf}_translate.nc   \
    ../input/MB/riv/riv_pfaf_${pfaf}_MERIT_Hydro_v07_Basins_v01.shp            \
    ../output/sword_edit/${reg}_sword_reaches_hb${pfaf}_v16.shp                \
    ../output_test/app_sword_to_mb/riv_pfaf_${pfaf}_MERIT_Hydro_v07_Basins_v01_sword.shp\
    > $run_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed run: $run_file" >&2 ; exit $x ; fi

echo "- Comparing SWORD width mapping file (.shp)"
../src/tst_cmp.py                                                              \
    ../output/app_sword_to_mb/riv_pfaf_${pfaf}_MERIT_Hydro_v07_Basins_v01_sword.shp\
    ../output_test/app_sword_to_mb/riv_pfaf_${pfaf}_MERIT_Hydro_v07_Basins_v01_sword.shp\
    > $cmp_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed comparison: $cmp_file" >&2 ; exit $x ; fi

rm -f $run_file
rm -f $cmp_file
echo "Success"
echo "********************"
fi


#*****************************************************************************
#Clean up
#*****************************************************************************
rm -rf ../output_test/

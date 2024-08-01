#!/bin/bash
#*****************************************************************************
#tst_pub_repr_all_Wade_etal_202x.sh
#*****************************************************************************

#Purpose:
#This script reproduces all pre- and post-processing steps for all regions
#used in the writing of:
#Wade, J., David, C., Altenau, E., Collins, E., Coss, S., Cerbelaud, A.,
#Tom, M., Durand, M., Pavelsky, T. (In Review). Bidirectional Translations
#Between Observational and Topography-based Hydrographic Datasets:
#MERIT-Basins and the SWOT River Database (SWORD).
#DOI: xx.xxxx/xxxxxxxxxxxx
#The files used are available from:
#Wade, J., David, C., Altenau, E., Collins, E., Coss, S., Cerbelaud, A.,
#Tom, M., Durand, M., Pavelsky, T. (2024). MERIT-SWORD: Bidirectional
#Translations Between MERIT-Basins and the SWORD River Database (SWORD).
#Zenodo
#DOI: 10.5281/zenodo.13156892
#The following are the possible arguments:
# - No argument: all unit tests are run
# - One unique unit test number: this test is run
# - Two unit test numbers: all tests between those (included) are run
#The script returns the following exit codes
# - 0  if all experiments are successful
# - 22 if some arguments are faulty
#Author:
#Jeffrey Wade, Cedric H. David, 2024

#*****************************************************************************
#Publication message
#*****************************************************************************
echo "********************"
echo "Reproducing files for: https://doi.org/10.5281/zenodo.13156892"
echo "********************"


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
#Define file and region names
#*****************************************************************************
reg=(
     "af"
     "af"
     "af"
     "af"
     "af"
     "af"
     "af"
     "af"
     "eu"
     "eu"
     "eu"
     "eu"
     "eu"
     "eu"
     "eu"
     "eu"
     "eu"
     "as"
     "as"
     "as"
     "as"
     "as"
     "as"
     "as"
     "as"
     "as"
     "as"
     "as"
     "as"
     "as"
     "as"
     "as"
     "oc"
     "oc"
     "oc"
     "oc"
     "oc"
     "oc"
     "oc"
     "sa"
     "sa"
     "sa"
     "sa"
     "sa"
     "sa"
     "sa"
     "na"
     "na"
     "na"
     "na"
     "na"
     "na"
     "na"
     "na"
     "na"
     "na"
     "na"
     "na"
     "na"
     "na"
     "na"
     )
       
pfaf=(
      11
      12
      13
      14
      15
      16
      17
      18
      21
      22
      23
      24
      25
      26
      27
      28
      29
      31
      32
      33
      34
      35
      36
      41
      42
      43
      44
      45
      46
      47
      48
      49
      51
      52
      53
      54
      55
      56
      57
      61
      62
      63
      64
      65
      66
      67
      71
      72
      73
      74
      75
      76
      77
      78
      81
      82
      83
      84
      85
      86
      91
      )


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

mkdir -p "../output_test/sword_edit"

echo "- Editing SWORD network"
for ((i = 1; i < ${#pfaf[@]}; i++)); do

    echo $i

    ../src/ms_sword_edit.py                                                    \
        ../input/SWORD/${reg[i]}_sword_reaches_hb${pfaf[i]}_v16.shp            \
        ../output_test/sword_edit/${reg[i]}_sword_reaches_hb${pfaf[i]}_v1\6.shp\
        > $run_file
    x=$? && if [ $x -gt 0 ] ; then echo "Failed run: $run_file" >&2 ; exit $x ; fi

done

rm -f $run_file
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

mkdir -p "../output_test/ms_region_overlap"

echo "- Identifying overlap between hydrographic regions"
python ../src/ms_region_overlap.py                                             \
    ../output_test/sword_edit/                                                 \
    ../input/MeanDRS/cat_disso/                                                \
    ../output_test/ms_region_overlap/sword_to_mb_reg_overlap.csv               \
    ../output_test/ms_region_overlap/mb_to_sword_reg_overlap.csv               \
    > $run_file
x=$? && if [ $x -gt 0 ] ; then echo "Failed run: $run_file" >&2 ; exit $x ; fi

rm -f $run_file
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

mkdir -p "../output_test/ms_riv_trace"

echo "- Generating MERIT-SWORD river network"

for ((i = 1; i < ${#pfaf[@]}; i++)); do

    echo $i

    ../src/ms_riv_trace.py                                                     \
        ../input/MB/riv/riv_pfaf_${pfaf[i]}_MERIT_Hydro_v07_Basins_v01.shp     \
        ../input/MB/cat/cat_pfaf_${pfaf[i]}_MERIT_Hydro_v07_Basins_v01.shp     \
        ../output_test/sword_edit/${reg[i]}_sword_reaches_hb${pfaf[i]}_v16.shp \
        ../output_test/ms_region_overlap/sword_to_mb_reg_overlap.csv           \
        ../output_test/ms_region_overlap/mb_to_sword_reg_overlap.csv           \
        ../output_test/ms_riv_trace/meritsword_pfaf_${pfaf[i]}_trace.shp       \
        > $run_file
    x=$? && if [ $x -gt 0 ] ; then echo "Failed run: $run_file" >&2 ; exit $x ; fi

done

rm -f $run_file
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

mkdir -p "../output_test/ms_riv_network"

echo "- Removing reaches from MERIT-SWORD river network"
for ((i = 1; i < ${#pfaf[@]}; i++)); do

    echo $i
    
    ../src/ms_rch_delete.py                                                    \
        ../output_test/ms_riv_trace/meritsword_pfaf_${pfaf[i]}_trace.shp       \
        ../input/MERITSWORD/riv_edit/meritsword_edits.csv                      \
        ../output_test/ms_iv_network/meritsword_pfaf_${pfaf[i]}_network.shp    \
        > $run_file
    x=$? && if [ $x -gt 0 ] ; then echo "Failed run: $run_file" >&2 ; exit $x ; fi
    
done

rm -f $run_file
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

mkdir -p "../output_test/ms_translate/cat/sword_to_mb"
mkdir -p "../output_test/ms_translate/cat/mb_to_sword"
mkdir -p "../output_test/ms_translate/mb_to_sword"
mkdir -p "../output_test/ms_translate/sword_to_mb"

echo "- Translating between MERIT-Basins and SWORD reaches"
for ((i = 1; i < ${#pfaf[@]}; i++)); do

    echo $i
    
    ../src/ms_translate.py                                                     \
        ../output_test/ms_riv_network/meritsword_pfaf_${pfaf[i]}_network.shp   \
        ../input/MB/riv/riv_pfaf_${pfaf[i]}_MERIT_Hydro_v07_Basins_v01.shp     \
        ../input/MB/cat/cat_pfaf_${pfaf[i]}_MERIT_Hydro_v07_Basins_v01.shp     \
        ../output_test/sword_edit/${reg[i]}_sword_reaches_hb${pfaf[i]}_v16.shp \
        ../output_test/ms_region_overlap/sword_to_mb_reg_overlap.csv           \
        ../output_test/ms_region_overlap/mb_to_sword_reg_overlap.csv           \
        ../output_test/ms_translate/cat/mb_to_sword/mb_to_sword_pfaf_${pfaf[i]}_translate_cat.shp\
        ../output_test/ms_translate/cat/sword_to_mb/sword_to_mb_pfaf_${pfaf[i]}_translate_cat.shp\
        ../output_test/ms_translate/mb_to_sword/mb_to_sword_pfaf_${pfaf[i]}_translate.nc\
        ../output_test/ms_translate/sword_to_mb/sword_to_mb_pfaf_${pfaf[i]}_translate.nc\
        > $run_file
    x=$? && if [ $x -gt 0 ] ; then echo "Failed run: $run_file" >&2 ; exit $x ; fi

done

rm -f $run_file
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

mkdir -p "../output_test/ms_diagnostic/mb_to_sword"
mkdir -p "../output_test/ms_diagnostic/sword_to_mb"

echo "- Evaluating quality of translations with diagnostics"
for ((i = 1; i < ${#pfaf[@]}; i++)); do

    echo $i
    
    ../src/ms_diagnostic.py                                                    \
        ../output_test/ms_translate/mb_to_sword/mb_to_sword_pfaf_${pfaf[i]}_translate.nc\
        ../output_test/ms_translate/sword_to_mb/sword_to_mb_pfaf_${pfaf[i]}_translate.nc\
        ../output_test/ms_riv/riv_network/meritsword_pfaf_${pfaf[i]}_network.shp\
        ../output_test/ms_translate_cat/mb_to_sword/mb_to_sword_pfaf_${pfaf[i]}_translate_cat.shp\
        ../output_test/ms_translate_cat/sword_to_mb/sword_to_mb_pfaf_${pfaf[i]}_translate_cat.shp\
        ../input/MeanDRS/cat_disso/cat_pfaf_${pfaf[i]}_MERIT_Hydro_v07_Basins_v01_disso.shp\
        ../output_test/sword_edit/${reg[i]}_sword_reaches_hb${pfaf[i]}_v16.shp \
        ../output_test/ms_region_overlap/sword_to_mb_reg_overlap.csv           \
        ../output_test/ms_region_overlap/mb_to_sword_reg_overlap.csv           \
        ../output_test/ms_diagnostic/mb_to_sword/mb_to_sword_pfaf_${pfaf[i]}_diagnostic.nc\
        ../output_test/ms_diagnostic/sword_to_mb/sword_to_mb_pfaf_${pfaf[i]}_diagnostic.nc\
        > $run_file
    x=$? && if [ $x -gt 0 ] ; then echo "Failed run: $run_file" >&2 ; exit $x ; fi

done

rm -f $run_file
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

mkdir -p "../output_test/ms_transpose/mb_transposed"
mkdir -p "../output_test/ms_transpose/sword_transposed"

echo "- Transposing between translation tables"
for ((i = 1; i < ${#pfaf[@]}; i++)); do

    echo $i
    
    ../src/ms_transpose.py                                                     \
        ../output_test/ms_translate/mb_to_sword/mb_to_sword_pfaf_${pfaf[i]}_translate.nc\
        ../output_test/ms_translate/sword_to_mb/sword_to_mb_pfaf_${pfaf[i]}_translate.nc\
        ../output_test/ms_riv_network/meritsword_pfaf_${pfaf[i]}_network.shp   \
        ../input/MB/riv/riv_pfaf_${pfaf[i]}_MERIT_Hydro_v07_Basins_v01.shp     \
        ../output_test/sword_edit/${reg[i]}_sword_reaches_hb${pfaf[i]}_v16.shp \
        ../output_test/ms_transpose/mb_transposed/mb_to_sword_pfaf_${pfaf[i]}_transpose.nc\
        ../output_test/ms_transpose/sword_transposed/sword_to_mb_pfaf_${pfaf[i]}_transpose.nc\
        > $run_file
    x=$? && if [ $x -gt 0 ] ; then echo "Failed run: $run_file" >&2 ; exit $x ; fi
    
done

rm -f $run_file
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

mkdir -p "../output_test/app_meandrs_to_sword"

echo "- Mapping MeanDRS discharge simulations onto SWORD reaches"
for ((i = 1; i < ${#pfaf[@]}; i++)); do

    echo $i
    
    ../src/ms_app_meandrs_to_sword.py                                          \
        ../output_test/ms_translate/mb_to_sword/mb_to_sword_pfaf_${pfaf[i]}_translate.nc\
        ../output_test/ms_translate/sword_to_mb/sword_to_mb_pfaf_${pfaf[i]}_translate.nc\
        ../input/MeanDRS/riv_COR/riv_pfaf_${pfaf[i]}_MERIT_Hydro_v07_Basins_v01_GLDAS_COR.shp\
        ../output_test/sword_edit/${reg[i]}_sword_reaches_hb${pfaf[i]}_v16.shp \
        ../output_test/app_meandrs_to_sword/${reg[i]}_sword_reaches_hb${pfaf[i]}_v16_meandrs.shp\
        > $run_file
    x=$? && if [ $x -gt 0 ] ; then echo "Failed run: $run_file" >&2 ; exit $x ; fi
    
done

rm -f $run_file
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

mkdir -p "../output_test/app_sword_to_mb"

echo "- Mapping SWORD river widths onto MERIT-Basins reaches"
for ((i = 1; i < ${#pfaf[@]}; i++)); do

    echo $i
        
    ../src/ms_app_sword_to_mb.py                                              \
        ../output_test/ms_translate/mb_to_sword/mb_to_sword_pfaf_${pfaf[i]}_translate.nc\
        ../input/MB/riv/riv_pfaf_${pfaf[i]}_MERIT_Hydro_v07_Basins_v01.shp     \
        ../output_test/sword_edit/${reg[i]}_sword_reaches_hb${pfaf[i]}_v16.shp \
        ../output_test/app_sword_to_mb/riv_pfaf_${pfaf[i]}_MERIT_Hydro_v07_Basins_v01_sword.shp\
        > $run_file
    x=$? && if [ $x -gt 0 ] ; then echo "Failed run: $run_file" >&2 ; exit $x ; fi

rm -f $run_file
echo "Success"
echo "********************"
fi

#*****************************************************************************
#Done
#*****************************************************************************

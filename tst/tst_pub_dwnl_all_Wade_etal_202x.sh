#!/bin/bash
#*****************************************************************************
#tst_dwnl_all_Wade_etal_202x.sh
#*****************************************************************************

#Purpose:
#This script downloads all the files corresponding to:
#Wade, J., David, C., Altenau, E., Collins, E.,  Oubanas, H., Coss, S.,
#Cerbelaud, A., Tom, M., Durand, M., Pavelsky, T. (In Review). Bidirectional
#Translations Between Observational and Topography-based Hydrographic
#Datasets: MERIT-Basins and the SWOT River Database (SWORD).
#DOI: xx.xxxx/xxxxxxxxxxxx
#The files used are available from:
#Wade, J., David, C., Altenau, E., Collins, E.,  Oubanas, H., Coss, S.,
#Cerbelaud, A., Tom, M., Durand, M., Pavelsky, T. (2024). MERIT-SWORD:
#Bidirectional Translations Between MERIT-Basins and the SWORD River
#Database (SWORD).
#Zenodo
#DOI: 10.5281/zenodo.13183883
#The script returns the following exit codes
# - 0  if all downloads are successful 
# - 22 if there was a conversion problem
# - 44 if one download is not successful
#Author:
#Jeffrey Wade, Cedric H. David, 2024.

#*****************************************************************************
#Publication message
#*****************************************************************************
echo "********************"
echo "Downloading files from:   https://doi.org/xx.xxxx/xxxxxxxxxxxx"
echo "which correspond to   :   https://doi.org/xx.xxxx/xxxxxxxxxxxx"
echo "These files are under a CC BY-NC-SA 4.0 license."
echo "Please cite these two DOIs if using these files for your publications."
echo "********************"


#*****************************************************************************
#Download MERIT-SWORD Zenodo Repository to /output/
#*****************************************************************************
echo "- Downloading MERIT-SWORD repository"
#-----------------------------------------------------------------------------
#Download parameters
#-----------------------------------------------------------------------------
URL="https://zenodo.org/records/13183883/files"
folder="../output"
list=("app_meandrs_to_sword.zip"                                               \
      "app_sword_to_mb.zip"                                                    \
      "ms_diagnostic.zip"                                                      \
      "ms_region_overlap.zip"                                                  \
      "ms_riv_edit.zip"                                                        \
      "ms_riv_network.zip"                                                     \
      "ms_riv_trace.zip"                                                       \
      "ms_translate.zip"                                                       \
      "ms_translate_cat.zip"                                                   \
      "ms_transpose.zip"                                                       \
      "sword_edit.zip"                                                         \
      )

#-----------------------------------------------------------------------------
#Download process
#-----------------------------------------------------------------------------
mkdir -p $folder
for file in "${list[@]}"
do
    wget -nv -nc $URL/$file -P $folder
    if [ $? -gt 0 ] ; then echo "Problem downloading $file" >&2 ; exit 44 ; fi
done

#-----------------------------------------------------------------------------
#Extract files
#-----------------------------------------------------------------------------
for file in "${list[@]}"
do
    unzip -nq "${folder}/${file}" -d "${folder}/"
    if [ $? -gt 0 ] ; then echo "Problem converting" >&2 ; exit 22 ; fi
done

#-----------------------------------------------------------------------------
#Delete zip file
#-----------------------------------------------------------------------------
for file in "${list[@]}"
do
    rm "${folder}/${file}"
    if [ $? -gt 0 ] ; then echo "Problem converting" >&2 ; exit 22 ; fi
done

echo "Success"
echo "********************"

#*****************************************************************************
#Done
#*****************************************************************************


#*****************************************************************************
#Download SWORD files
#*****************************************************************************
echo "- Downloading SWORD files"
#-----------------------------------------------------------------------------
#Download parameters
#-----------------------------------------------------------------------------
URL="https://zenodo.org/records/10013982/files"
folder="../input/SWORD"
list=("SWORD_v16_shp.zip")

echo "${folder}/${list%.zip}/shp"/*reaches*

#-----------------------------------------------------------------------------
#Download process
#-----------------------------------------------------------------------------
mkdir -p $folder
for file in "${list[@]}"
do
    wget -nv -nc $URL/$file -P $folder/
    if [ $? -gt 0 ] ; then echo "Problem downloading $file" >&2 ; exit 44 ; fi
done

#-----------------------------------------------------------------------------
#Extract files
#-----------------------------------------------------------------------------
unzip -nq "${folder}/${list}" -d "${folder}/${list%.zip}"
if [ $? -gt 0 ] ; then echo "Problem converting" >&2 ; exit 22 ; fi

#-----------------------------------------------------------------------------
#Delete zip file
#-----------------------------------------------------------------------------
rm "${folder}/${list}"
if [ $? -gt 0 ] ; then echo "Problem converting" >&2 ; exit 22 ; fi

#-----------------------------------------------------------------------------
#Relocate reach files from subdirectories
#-----------------------------------------------------------------------------
find "${folder}/${list%.zip}" -type f -name "*reaches*" -exec mv {} "${folder}" \;
if [ $? -gt 0 ] ; then echo "Problem converting" >&2 ; exit 22 ; fi

rm -rf "${folder}/${list%.zip}"
if [ $? -gt 0 ] ; then echo "Problem converting" >&2 ; exit 22 ; fi

echo "Success"
echo "********************"

#*****************************************************************************
#Done
#*****************************************************************************


#*****************************************************************************
#Download MERIT-Basins files
#*****************************************************************************
echo "- Downloading MERIT-Basins files"
#-----------------------------------------------------------------------------
#Download parameters from Google Drive
#-----------------------------------------------------------------------------
# Embedded Folder View shows all 61 files, rather than the 50 limited by G.D.
URL="https://drive.google.com/embeddedfolderview?id=1nXMgbDjLLtB9XPwfVCLcF_0"\
"vlYS2M3wy"
folder="../input/MB"

mkdir -p $folder

#Retrieve HTML from Google Drive file view
wget -q -O "${folder}/temphtml" "$URL"
if [ $? -gt 0 ] ; then echo "Problem downloading MERIT-Basins" >&2 ; exit 44 ; fi

#Scrape download id and name for each file from HTML
idlist=($(grep -o '<div class="flip-entry" id="entry-[0-9a-zA-Z_-]*"'         \
    "${folder}/temphtml" | sed 's/^.*id="entry-\([0-9a-zA-Z_-]*\)".*$/\1/'))
if [ $? -gt 0 ] ; then echo "Problem downloading MERIT-Basins" >&2 ; exit 44 ; fi

filelist=($(grep -o '"flip-entry-title">[^<]*<' "${folder}/temphtml" |        \
    sed 's/"flip-entry-title">//; s/<$//'))
if [ $? -gt 0 ] ; then echo "Problem downloading MERIT-Basins" >&2 ; exit 44 ; fi

#Check if lists have same length
if [ ${#filelist[@]} -ne ${#idlist[@]} ]; then echo "Problem downloading MERIT-Basins" \
    >&2 ; exit 44 ; fi

rm "${folder}/temphtml"
if [ $? -gt 0 ] ; then echo "Problem converting" >&2 ; exit 22 ; fi

#-----------------------------------------------------------------------------
#Download process, bypassing Google Drive download warning using cookies
#-----------------------------------------------------------------------------

#Loop through files and ids
for i in ${!filelist[@]};
do
    file="${filelist[i]}"
    id="${idlist[i]}"

    #Save uuid value from server for authentication
    wget "https://docs.google.com/uc?export=download&id=1z-l1ICC7X4iKy0vd7FkT5X4u8Ie2l3sy" -O- | sed -rn 's/.*name="uuid" value=\"([0-9A-Za-z_\-]+).*/\1/p' > "${folder}/google_uuid.txt"
    if [ $? -gt 0 ] ; then echo "Problem downloading $file" >&2 ; exit 44 ; fi

    #Download file from server using uuid value
    wget -O "${folder}/$file" "https://drive.usercontent.google.com/download?export=download&id=${id}&confirm=t&uuid=$(<"${folder}/google_uuid.txt")"

    rm "${folder}/google_uuid.txt"
    if [ $? -gt 0 ] ; then echo "Problem converting" >&2 ; exit 22 ; fi
    
done

#-----------------------------------------------------------------------------
#Extract files
#-----------------------------------------------------------------------------
for file in "${filelist[@]}"
do
    unzip -nq "${folder}/$file" -d "${folder}/${filename%.zip}"
    if [ $? -gt 0 ] ; then echo "Problem converting" >&2 ; exit 22 ; fi
done

#-----------------------------------------------------------------------------
#Delete zip files
#-----------------------------------------------------------------------------
for file in "${filelist[@]}"
do
    rm "${folder}/$file"
    if [ $? -gt 0 ] ; then echo "Problem converting" >&2 ; exit 22 ; fi
done

#-----------------------------------------------------------------------------
#Organize files by type (riv and cat)
#-----------------------------------------------------------------------------
mkdir -p "$folder/cat"
mkdir -p "$folder/riv"

#Move all files beginning with cat
for file in "${folder}/cat"*
do
    #Confirm file exists and is regular
    if [ -f "$file" ]; then
        mv "$file" "$folder/cat/"
        if [ $? -gt 0 ] ; then echo "Problem converting" >&2 ; exit 22 ; fi
    fi
done

#Move all files beginning with riv
for file in "${folder}/riv"*
do
    #Confirm file exists and is regular
    if [ -f "$file" ]; then
        mv "$file" "$folder/riv/"
        if [ $? -gt 0 ] ; then echo "Problem converting" >&2 ; exit 22 ; fi
    fi
done

echo "Success"
echo "********************"

#*****************************************************************************
#Done
#*****************************************************************************


#*****************************************************************************
#Download MeanDRS river files
#*****************************************************************************
echo "- Downloading MeanDRS files"
#-----------------------------------------------------------------------------
Download parameters
#-----------------------------------------------------------------------------
URL="https://zenodo.org/records/10013744/files"
folder="../input/MeanDRS"
list=("riv_pfaf_ii_MERIT_Hydro_v07_Basins_v01_GLDAS_COR.zip" \
      "riv_pfaf_ii_MERIT_Hydro_v07_Basins_v01_GLDAS_ENS.zip"
     )

#-----------------------------------------------------------------------------
#Download process
#-----------------------------------------------------------------------------
mkdir -p $folder
for file in "${list[@]}"
do
    wget -nv -nc $URL/$file -P $folder
    if [ $? -gt 0 ] ; then echo "Problem downloading $file" >&2 ; exit 44 ; fi
done

#-----------------------------------------------------------------------------
#Extract files
#-----------------------------------------------------------------------------
for file in "${list[@]}"
do
    unzip -nq "${folder}/${file}" -d "${folder}/${file%.zip}"
    if [ $? -gt 0 ] ; then echo "Problem converting" >&2 ; exit 22 ; fi
done

#-----------------------------------------------------------------------------
#Delete zip file
#-----------------------------------------------------------------------------
for file in "${list[@]}"
do
    rm "${folder}/${file}"
    if [ $? -gt 0 ] ; then echo "Problem converting" >&2 ; exit 22 ; fi
done

#-----------------------------------------------------------------------------
#Find regions missing from COR dataset
#-----------------------------------------------------------------------------
#Get complete list of regions
regs=$(ls "${folder}/${list[1]%.zip}" | cut -d '_' -f 3 | sort -u)

#Get list of COR regions
regs_cor=$(ls "${folder}/${list[0]%.zip}" | cut -d '_' -f 3 | sort -u)

#Find differences between lists
regs_miss=(`echo ${regs[@]} ${regs_cor[@]} | tr ' ' '\n' | sort | uniq -u`)

#-----------------------------------------------------------------------------
#Move missing region files from ENS to COR
#-----------------------------------------------------------------------------
for reg in ${regs_miss[@]}
do
    mv "${folder}/${list[1]%.zip}/"*${reg}* "${folder}/${list[0]%.zip}"
    if [ $? -gt 0 ] ; then echo "Problem converting" >&2 ; exit 22 ; fi
done

#-----------------------------------------------------------------------------
#Rename moved files from ENS to COR
#-----------------------------------------------------------------------------
for file in "${folder}/${list[0]%.zip}"/*ENS*
do
    new_fp=$(echo "${file}" | sed 's/ENS/COR/')
    mv "${file}" "${new_fp}"
    if [ $? -gt 0 ] ; then echo "Problem converting" >&2 ; exit 22 ; fi
done

#-----------------------------------------------------------------------------
##Move files to MeanDRS folder and delete other folders
#-----------------------------------------------------------------------------
mkdir "${folder}/riv_COR"
mv "${folder}/"*.* "${folder}/riv_COR"
if [ $? -gt 0 ] ; then echo "Problem converting" >&2 ; exit 22 ; fi

rm -rf "${folder}/${list[0]%.zip}"
if [ $? -gt 0 ] ; then echo "Problem converting" >&2 ; exit 22 ; fi

rm -rf "${folder}/${list[1]%.zip}"
if [ $? -gt 0 ] ; then echo "Problem converting" >&2 ; exit 22 ; fi

echo "Success"
echo "********************"

#*****************************************************************************
#Done
#*****************************************************************************


#*****************************************************************************
#Download MeanDRS dissolved catchment files
#*****************************************************************************
echo "- Downloading MeanDRS catchment files"
#-----------------------------------------------------------------------------
#Download parameters
#-----------------------------------------------------------------------------
URL="https://zenodo.org/records/10013744/files"
folder="../input/MeanDRS"
list=("cat_pfaf_ii_MERIT_Hydro_v07_Basins_v01_disso.zip")

#-----------------------------------------------------------------------------
#Download process
#-----------------------------------------------------------------------------
for file in "${list[@]}"
do
    wget -nv -nc $URL/$file -P $folder
    if [ $? -gt 0 ] ; then echo "Problem downloading $file" >&2 ; exit 44 ; fi
done

#-----------------------------------------------------------------------------
#Extract files
#-----------------------------------------------------------------------------
for file in "${list[@]}"
do
    unzip -nq "${folder}/${file}" -d "${folder}/cat_disso"
    if [ $? -gt 0 ] ; then echo "Problem converting" >&2 ; exit 22 ; fi
done

#-----------------------------------------------------------------------------
#Delete zip file
#-----------------------------------------------------------------------------
for file in "${list[@]}"
do
    rm "${folder}/${file}"
    if [ $? -gt 0 ] ; then echo "Problem converting" >&2 ; exit 22 ; fi
done

echo "Success"
echo "********************"

#*****************************************************************************
#Done
#*****************************************************************************

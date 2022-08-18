#!/usr/bin/bash

cowpi_directory="${1}"
cowpi_download_array=("https://zenodo.org/record/1252858/files/CowPi_V1.0_16S_precalculated.tab.gz?download=1" 
"https://zenodo.org/record/1252858/files/CowPi_V1.0_all_rumen_16S_combined.renamed.fas.gz?download=1"
"https://zenodo.org/record/1252858/files/CowPi_V1.0_ko_precalc1.tab.gz?download=1")

for download in "${cowpi_download_array[@]}"
do
    download_name=$(echo "${download}" | awk -F'/' '{print $NF}' | sed 's/?download=1//')

    wget "${download}" -O "${download_name}"
done


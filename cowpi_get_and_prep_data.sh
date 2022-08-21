#!/usr/bin/bash

yaml_config_output_file=$(realpath "${1}") # command line argument for output yaml configuration file for main script
cowpi_directory=$(realpath "${2}") # directory for cowpi output results to go
filter_archaea="${3}" # add a "y" 
echo "${yaml_config_output_file}"
if [ ! -d "${cowpi_directory}" ] # checks if directory is present then produces it
then

    mkdir "${cowpi_directory}"

fi

# links to cowpi files download into array
cowpi_download_array=("https://zenodo.org/record/1252858/files/CowPi_V1.0_16S_precalculated.tab.gz?download=1" 
"https://zenodo.org/record/1252858/files/CowPi_V1.0_all_rumen_16S_combined.renamed.fas.gz?download=1"
"https://zenodo.org/record/1252858/files/CowPi_V1.0_ko_precalc1.tab.gz?download=1")

for download in "${cowpi_download_array[@]}" # loops over link array, downloads them, gives nice name and decompresses
do
    continue
    download_name=$(echo "${download}" | awk -F'/' '{print $NF}' | sed 's/?download=1//')
    download_path="${cowpi_directory}/${download_name}"
    wget "${download}" -O "${download_path}"
    gunzip "${download_path}"


done


cat "${cowpi_directory}/CowPi_V1.0_all_rumen_16S_combined.renamed.fas" | sed 's/-//g' > "${cowpi_directory}/CowPi_V1.0_all_rumen_16S_combined.renamed.fas" # removing the "-" to allow vsearch to work

# array produced to produce configuration file, then adds the downloads produced above to the specific parts of the configuration file.
yaml_configs_array=("copy_number_table_file: ${cowpi_directory}/CowPi_V1.0_ko_precalc1.tab" "ko_table: ${cowpi_directory}/CowPi_V1.0_all_rumen_16s_ko_precalc1.tab" 
"16s_sequence_table: ${cowpi_directory}/CowPi_V1.0_all_rumen_16s_combined.fas" "single_or_multiple_datasets:" "directory_of_datasets:" "threads:")

for config in "${yaml_configs_array[@]}" # for loop going over array to produce configuration file
do
    
    echo "${config}" >> "${yaml_config_output_file}"

done



#!/usr/bin/bash

tool_directory_path=$(realpath "${1}")
qa_test_directory_path=$(realpath "${2}")


if [ ! -d "${qa_test_directory_path}" ]
then
    
    mkdir "${qa_test_directory_path}"

fi


test_exit_code() {
    printf "Testing of script: ${1}:"
    testing_failed="false"
    
    if [ "${2}" != "0" ]
    then
        printf "Failed\n"
        printf "Exiting."
        printf "${2}"
        exit

    fi
    printf "Succeeded.\n"
    printf "Continuing to next test.\n"
    
}

run_tests() {
    test_array=("run_data_gather_test" "run_read_conversion_test" "run_single_read_conversion_test" "run_main_workflow_test" "run_single_workflow_test" "run_single_workflow_without_chimera_and_clustering")
    cowpi_database_dir="${qa_test_directory_path}/cowpi_database_dir/"
    for i in "${test_array[@]}"
    do
        
        result=$("${i}" "${cowpi_database_dir}")

        test_exit_code ${i} "${result}"
    
    done
        
}

run_data_gather_test() {
    config_file="${qa_test_directory_path}/test_config.yaml"

    
    "${tool_directory_path}/cowpi_get_and_prep_data.sh" "${config_file}" "${cowpi_database_dir}" "N" >/dev/null
    
    expected_file_array=("${1}/CowPi_V1.0_16S_precalculated.tab" "${1}/CowPi_V1.0_ko_precalc1.tab" 
    "${1}/CowPi_V1.0_all_rumen_16S_combined.fas" "${config_file}")
    exit_code="0"
    for expect_file_path in "${expected_file_array[@]}"
    do
        if [ ! -f "${expect_file_path}" ]
        then
            exit_code="cowpi_get_and_prep_data script failed, cowpi preparatory data and yaml config file not found."
            break
        fi
    done
    echo "${exit_code}"


}
run_archaea_filtering_test() {
    
    "${tool_directory_path}/filter_archaea.py" "${tool_directory_path}/archaea_names.txt" "${qa_test_directory_path}/cowpi_database_dir/"

    
    archaea_expected_file_array=("${1}/archaea_removed_CowPis/16S_precalculated_copy_num_file.tab" "${1}/archaea_removed_CowPis/16S_precalculated_ko_file.tab"
    "${1}/archaea_removed_CowPis/cowpi_16S_sequences_file.fas")
    exit_code="0"
    for expect_file_path in "${archaea_expected_file_array[@]}"
    do
        echo "expected:${expect_file_path}"
        if [ ! -f "${expect_file_path}" ]
        then
            exit_code="Archaea filtering script failed, could not find output archaea filtered cowpi db files."
            break
        fi
    done
    echo "${exit_code}"


}

run_read_conversion_test() {
    test_data_directory="${tool_directory_path}/tests/datasets/"

    qa_test_data_directory="${qa_test_directory_path}/qa_test_datasets/"
    mkdir "${qa_test_data_directory}"
    "${tool_directory_path}/conversion_of_read_names.py" "${test_data_directory}" "${qa_test_data_directory}" "multiple"
    ls "${qa_test_data_directory}"/*/* > "${qa_test_data_directory}/temp_file.txt"
            
    exit_code="0"
    readarray -t test_data_array < "${qa_test_data_directory}/temp_file.txt"

    for data in "${test_data_array[@]}"
    do
        sequence_name=$(head -n1 "${data}" | cut -c2-)
        data_name=$(echo ${data} | awk -F'/' '{print $NF}' | sed 's/.fastq//')

        
        if [ "${sequence_name}" != "${data_name}" ]
        then   
            exit_code="Error on read conversion script, at least one fastq file does not have correct sample header."
        fi
    
    done
    rm "${qa_test_data_directory}/temp_file.txt"
    echo "${exit_code}"

}

run_single_read_conversion_test() {
    test_data_directory="${tool_directory_path}/tests/datasets/test_data/"
    single_test_data_directory="${qa_test_directory_path}/single_test_data/"
   # mkdir "${single_test_data_directory}"

    "${tool_directory_path}/conversion_of_read_names.py" "${test_data_directory}" "${single_test_data_directory}" "single"
    ls "${test_data_directory}"/* > "${single_test_data_directory}/temp_file.txt"



    exit_code="0"
    readarray -t single_test_data_array < "${qa_test_data_directory}/temp_file.txt"
    for data in "${single_test_data_aray[@]}"
    do
        sequence_name=$(head -n1 "${data}" | cut -c2-)
        data_name=$(echo ${data} | awk -F'/' '{print $NF}' | sed 's/.fastq//')
        
        if [ "${sequence_name}" != "${data_name}" ]
        then   
            exit_code="Error on read conversion script, at least one fastq file does not have correct sample header."

        fi

    done
    rm "${single_test_data_directory}/temp_file.txt"

    echo "${exit_code}"


}


run_main_workflow_test() {
    
    orig_config_file="${qa_test_directory_path}/test_config.yaml"
    main_config_file="${qa_test_directory_path}/main_wf_config.yaml"

    cp "${orig_config_file}" "${main_config_file}"
    
    qa_test_path_for_sed=$(echo "${qa_test_directory_path}/qa_test_datasets/" | sed 's/\//\\\//g')

    sed -i 's/single_or_multiple_datasets:/single_or_multiple_datasets: multiple/' "${main_config_file}"
    sed -i "s/directory_of_datasets:/directory_of_datasets: ${qa_test_path_for_sed}/" "${main_config_file}"
    sed -i 's/threads:/threads: 6/' "${main_config_file}"
    sed -i 's/pre_clustered:/pre_clustered: false/' "${main_config_file}"
    sed -i 's/remove_chimeras:/remove_chimeras: true/' "${main_config_file}"
    
    "${tool_directory_path}/cowpi_main_workflow.py" "${main_config_file}" >/dev/null
    
    produced_all_output_summary_file="${qa_test_directory_path}/qa_test_datasets/all_datasets_summary_file.csv"
    expected_all_output_summary_file="${tool_directory_path}/tests/expected_all_datasets_summary_file.csv" 
    exit_code="0"
    if [ ! -f "${produced_all_output_summary_file}" ]
    then

    exit_code="fail summary file not produced"

    fi
    echo "${exit_code}"
}

run_single_workflow_test() {
    
    orig_config_file="${qa_test_directory_path}/test_config.yaml"
    single_config_file="${qa_test_directory_path}/single_test_config.yaml"
    cp "${orig_config_file}" "${single_config_file}"

    single_qa_test_path_for_sed=$(echo "${qa_test_directory_path}/single_test_data/" | sed 's/\//\\\//g')


    sed -i 's/single_or_multiple_datasets:/single_or_multiple_datasets: single/' "${single_config_file}"
    sed -i "s/directory_of_datasets:/directory_of_datasets: ${single_qa_test_path_for_sed}/" "${single_config_file}"
    sed -i 's/threads:/threads: 6/' "${single_config_file}"
    sed -i 's/pre_clustered:/pre_clustered: false/' "${single_config_file}"
    sed -i 's/remove_chimeras:/remove_chimeras: true/' "${single_config_file}"
    
    "${tool_directory_path}/cowpi_main_workflow.py" "${single_config_file}" >/dev/null

    summary_output_file="${qa_test_directory_path}/single_test_data/summary_output_file.txt"

    exit_code=0
    if [ ! -f "${summary_output_file}" ]
    then


    exit_code="fail summary file not produced"
    fi
    echo "${exit_code}"
}

run_single_workflow_without_chimera_and_clustering() {
    orig_config_file="${qa_test_directory_path}/test_config.yaml"
    no_chim_or_clust_config_file="${qa_test_directory_path}/no_chim_or_clust_config.yaml"

    cp "${orig_config_file}" "${no_chim_or_clust_config_file}"
    cp -r "${qa_test_directory_path}/qa_test_datasets/test_data/clustering_directory/" "${qa_test_directory_path}"
    
    qa_test_path_for_sed=$(echo "${qa_test_directory_path}/clustering_directory/" | sed 's/\//\\\//g')    
    otu_cluster_fasta_path="${qa_test_directory_path}/clustering_directory/cluster_centroids.fasta"
    otu_cluster_table_path="${qa_test_directory_path}/clustering_directory/cluster_table_test.tsv"

    sed -i 's/single_or_multiple_datasets:/single_or_multiple_datasets: single/' "${no_chim_or_clust_config_file}"
    sed -i "s/directory_of_datasets:/directory_of_datasets: ${qa_test_path_for_sed}/" "${no_chim_or_clust_config_file}"
    sed -i 's/threads:/threads: 6/' "${no_chim_or_clust_config_file}"
    sed -i 's/remove_chimeras:/remove_chimeras: false/' "${no_chim_or_clust_config_file}"
    sed -i 's/pre_clustered:/pre_clustered: true/' "${no_chim_or_clust_config_file}"
    echo "pre_clustered_files:" >> "${no_chim_or_clust_config_file}"
    echo "  fastq_cluster_file_path: ${otu_cluster_fasta_path}" >> "${no_chim_or_clust_config_file}"
    echo "  cluster_table_path: ${otu_cluster_table_path}" >> "${no_chim_or_clust_config_file}"

    "${tool_directory_path}/cowpi_main_workflow.py" "${no_chim_or_clust_config_file}" >/dev/null

    summary_output_file="${qa_test_directory_path}/clustering_directory/summary_output_file.txt"

    exit_code=0
    
    if [ ! -f "${summary_output_file}" ]
    
    then


    exit_code="fail summary file not produced"
    
    fi
    
    echo "${exit_code}"



    
}


run_tests
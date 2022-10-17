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
    
    if [ "${2}" = "1" ]
    then
        printf "Failed\n"
        printf "Exiting."
        exit

    fi
    printf "Succeeded.\n"
    printf "Continuing to next test.\n"
    
}

run_tests() {
    test_array=("run_data_gather_test" "run_archaea_filtering_test" "run_read_conversion_test" "run_main_workflow_test")
    cowpi_database_dir="${qa_test_directory_path}/cowpi_database_dir/"
    for i in "${test_array[@]}"
    do
        
        result=$("${i}" "${cowpi_database_dir}")
        echo "${result}"
        test_exit_code ${i} ${result}
    
    done
        
}

run_data_gather_test() {
    config_file="${qa_test_directory_path}/test_config.yaml"
    
    
    "${tool_directory_path}/cowpi_get_and_prep_data.sh" "${config_file}" "${cowpi_database_dir}"
    
    expected_file_array=("${1}/CowPi_V1.0_16S_precalculated.tab" "${1}/CowPi_V1.0_ko_precalc1.tab" 
    "${1}/CowPi_V1.0_all_rumen_16s_combined.fas" "${config_file}")
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


run_main_workflow_test() {
    config_file="${qa_test_directory_path}/test_config.yaml"
    sed -i 's/single_or_multiple_datasets:/single_or_multiple_datasets: multiple/' "${config_file}"
    qa_test_path_for_sed=$(echo "${qa_test_directory_path}/qa_test_datasets/" | sed 's/\//\\\//g')
    sed -i "s/directory_of_datasets:/directory_of_datasets: ${qa_test_path_for_sed}/" "${config_file}"
    sed -i 's/threads:/threads: 6/' "${config_file}"
    python "${tool_directory_path}/cowpi_main_workflow.py" "${config_file}"
    
    produced_all_output_summary_file="${qa_test_directory_path}/qa_test_datasets/all_datasets_summary_file.csv"
    expected_all_output_summary_file="${tool_directory_path}/tests/expected_all_datasets_summary_file.csv" 

    if [ ! -f "${produced_all_output_summary_file}" ]
    then

    cmp -s "${expected_all_output_summry_file}" "${produced_all_output_summary_file}"
    echo $?
    fi
}


run_tests
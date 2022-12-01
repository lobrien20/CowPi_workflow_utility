# CowPi WorkFlow Utility


Tool used to aid the use of the CowPi tool for analysing 16S data. Run in Python 2.

To create conda environment to run this tool:

conda create -n cowpi_workflow_env picrust biom-format vsearch pyyaml pandas


Contains following scripts:
1. 'cowpi_get_and_prep_data.sh'
Bash script taking two arguments. 
First argument is output for a yaml configurations file, used in cowpi workflow script further down. Second argument is output directory to obtain cowpi files.
Script gets the cowpi data from the Zenodo database, and also gunzips them and edits the fasta file to work with vsearch.
yaml configuration file is produced (containing the paths to each required file for CowPi downloaded), which can be used with (after choosing configurations) main Cowpi workflow script.

2. 'filter_archaea.py'
Python script which filters archaea from the initial cowpi data files. Optional if not using archaea data.
Argument 1 is the archaea file list (see 'archaea_file.txt') path, and Argument 2 is the initial CowPi directory.

3. '16s_function_workflow.py'
Main workflow python script. Takes the yaml configuration file as the first argument, then runs each step
of the CowPi workflow and generates functional pathway results, as well as producing a summary file of
each step. Additionally, has ability to run on multiple datasets and can create a multi dataset summary
file.

4. 'conversion_of_read_names.py' (optional)
Depending on headers of fasta sequence file, this can result in problems in output from vsearch stage of cowpi. This adds the file name into the headers and checks for any "."s in file sample name which can cause issues.

If there are any issues, please contact me at lobrien20@qub.ac.uk or open up an issue. Thanks.

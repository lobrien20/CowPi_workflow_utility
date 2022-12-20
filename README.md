# CowPi WorkFlow Utility


Tool used to aid the use of the CowPi tool for analysing 16S data. Run in Python 2.
This can be run on multiple independent datasets (completely separate datasets, only thing that is together is production of a summary file of the stages), or a single dataset.


To create conda environment to run this tool:

conda create -n cowpi_workflow_env picrust biom-format vsearch pyyaml pandas
Please note: Sometimes this may have issues with conda forge, removing the conda forge channel whilst producing this environment should fix this.


To obtain a singularity image running this tool:

singularity pull library://lobrien20/collection/cowpi_workflow_utility




Contains following scripts:

1. 'cowpi_get_and_prep_data.sh'

Script gets the cowpi data from the Zenodo database, and also gunzips them and edits the fasta file to work with vsearch.
yaml configuration file is produced (containing the paths to each required file for CowPi downloaded), which can be used with (after choosing configurations) main Cowpi workflow script.
Argument one: path to produce yaml configurations file.
Argument two: output directory to obtain the CowPi files.
Argument three: is the data you're going to be using preclustered? (Y or N)

2. 'filter_archaea.py' (optional)
Python script which filters archaea from the initial cowpi data files. Optional if not using archaea data.
Argument one: archaea file list (see 'archaea_file.txt') path
Argument Two: The initial CowPi precalculated files directory (produced above)

3. '16s_function_workflow.py'
Main workflow python script. Takes the yaml configuration file as the first argument, then runs each step
of the CowPi workflow and generates functional pathway results, as well as producing a summary file of
each step. 
Argument one: yaml configuration file


4. 'conversion_of_read_names.py' (optional)
Depending on headers of fasta sequence file, this can result in problems in output from vsearch stage of cowpi. This adds the file name into the headers and checks for any "."s in file sample name which can cause issues.


Process:

1. Run "cowpi_get_and_prep_data.sh". This will download and prepare the cowpi precalculated data, as well as produce a yaml file with the paths to the cowpi precalculateds. 
2. Run "conversion_of_read_names.py". this is probably optional depending on the name of fastq sequence headers. This is only for data not preclustered at the moment.
3. Fill in configurations of the yaml file. If running on a single dataset, point the directory_of_datasets path to the directory containing that dataset. If multiple, then directory containing sub directories of that datasets.
4. Run "16s_function_workflow.py" with the argument pointing to the yaml file.



Important Outputs (in each dataset directory)
1. "summary_output_file.txt" - gives various information about results of each stage.
2. "categoried_predictions" - directory containing collapsed pathways at each kegg ortholog.
3. "metagenome_predictions/metagenome_predictions.tsv" - tabulated file containing counts of each ortholog.


If multiple datasets option chosen, "all_datasets_summary_file.csv" file is also produced. This takes the summary output file from each dataset analysis and puts into a simpler table.





If there are any issues, please contact me at lobrien20@qub.ac.uk or open up an issue. Thanks.

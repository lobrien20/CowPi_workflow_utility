#!/usr/bin/env python
import shutil, os
from os import path
import sys
def main():

    if sys.argv[3] == "multiple":
        mega_directory = sys.argv[1]
        fixed_mega_directory = sys.argv[2]

        fastq_directories_dict = get_directories(mega_directory)
        for directory,fastq_paths in fastq_directories_dict.items():
            print("converting samples of directory: %s" % (directory))
            check_for_bad_fastq_names(fastq_paths)
            new_directory = "%s/%s" % (fixed_mega_directory, directory)
            os.mkdir(new_directory)
            initial_directory = "%s/%s" % (mega_directory, directory)
            for fastq in fastq_paths:
                run_sequence_file_fix(initial_directory, new_directory, fastq)

    else:
        initial_directory = sys.argv[1]
        new_directory = sys.argv[2]
        os.mkdir(new_directory)
        initial_directory = "%s/%s" % (mega_directory, directory)
        result = check_for_bad_fastq_names(fastq_paths)
        for fastq in fastq_paths:
            run_sequence_file_fix(initial_directory, new_directory, fastq)





def run_sequence_file_fix(initial_fastq_directory, new_fastq_directory, fastq):
    fastq_file_path = "%s/%s" % (initial_fastq_directory, fastq)

    sequence_line_list = get_all_sequences(fastq_file_path)
    new_sequence_line_list = generate_new_sequence_names(sequence_line_list, fastq_file_path)
    new_path = "%s/%s" % (new_fastq_directory, fastq)
    fix_sequence_file(new_sequence_line_list, new_path)

def get_all_sequences(sequence_file_path):
    sequence_line_list = []
    with open(sequence_file_path, "r") as sequence_file:
        sequence_file_lines = sequence_file.readlines()
        sequence_file_len = len(sequence_file_lines)
        sequence_file_start = 0
        end = 4
        while end <= sequence_file_len:
            sequence_line_list.append(sequence_file_lines[sequence_file_start:end])
            sequence_file_start += 4
            end +=4


    return sequence_line_list

            


def generate_new_sequence_names(sequence_line_list, sequence_file_path):
    sequence_file_name = sequence_file_path.split("/")[-1][:-6]
    sequence_file_name = sequence_file_name.replace("-", "_")

    for sequence_chunk in sequence_line_list:
        sequence_name = "%s\n" % (sequence_file_name)
        sequence_chunk[0] = "@%s" % (sequence_name)
        sequence_chunk[2] = "+\n"

    return sequence_line_list

    
    
def fix_sequence_file(new_sequence_line_list, sequence_file_path):
    with open(sequence_file_path, "w") as new_file:
        for sequence_chunk in new_sequence_line_list:
            for line in sequence_chunk:
                new_file.write(line)


def get_fastq_paths(study_directory):
    directory_paths = os.listdir(study_directory)
    fastq_paths = []
    for path in directory_paths:
        if path[-6:] == '.fastq':
            fastq_paths.append(path)
        if path[-3:] == '.fq':
            fastq_paths.append(path)
    
    return fastq_paths

def check_for_bad_fastq_names(fastq_paths):
	bad_fastq_names = []
	for path in fastq_paths:
		name = path.split("/")[-1]
		if name.count(".") > 1:
			bad_fastq_names.append(path)
	if len(bad_fastq_names) > 0:
		print("The following files have '.' in sample name. Will cause issues with vsearch. Pls fix.")
		for bad in bad_fastq_names:
			print(bad)
		print("Exiting to allow for fixing")
		exit()



def get_directories(mega_directory):
    mega_directory_paths = os.listdir(mega_directory)
    fastq_directories_dict = {}
    for path in mega_directory_paths:
        if os.path.isdir("%s/%s" % (mega_directory, path)) == True:

            fastq_paths = get_fastq_paths("%s/%s" % (mega_directory, path))


            if len(fastq_paths) != 0:
                fastq_directories_dict[path] = fastq_paths

    if len(fastq_directories_dict.keys()) == 0:
        print("unable to find any directories with .fastq extension")
    return fastq_directories_dict







main()




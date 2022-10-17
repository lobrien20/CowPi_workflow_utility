#!/usr/bin/env python
import sys
import os
def main():
    
    archaea_file_list = sys.argv[1]
    cowpi_file_directory = sys.argv[2]
    archaea_removed_directory = "%s/archaea_removed_CowPis" % (cowpi_file_directory)
    os.mkdir(archaea_removed_directory)

    archaea_names = get_list_of_archaea_from_hungates(archaea_file_list)

    copy_num_file,ko_precalc_file,cowpi_fastas_file = get_specific_cowpi_files(cowpi_file_directory)
    print("FOUND FILES")
    remove_archaea_from_copy_num_file(copy_num_file, archaea_names, archaea_removed_directory)
    remove_archaea_from_ko_precalcs(ko_precalc_file, archaea_names, archaea_removed_directory)
    remove_archaea_from_fas(cowpi_fastas_file, archaea_names, archaea_removed_directory)

def get_list_of_archaea_from_hungates(archaea_file_list):
    
    with open(archaea_file_list, "r") as file:
        
        lines = file.readlines()
        archaea_names = [name.strip() for name in lines]
        return archaea_names

def get_specific_cowpi_files(cowpi_file_directory):
    files = os.listdir(cowpi_file_directory)
    found = 0
    for file in files:

        if "16S_precalculated" in file:
            copy_num_file = "%s/%s" % (cowpi_file_directory, file)
            found += 1
        elif "ko_precalc1" in file:
            ko_precalc_file = "%s/%s" % (cowpi_file_directory, file)
            found += 1
        elif "16S_combined" in file:
            cowpi_fastas_file = "%s/%s" % (cowpi_file_directory, file)
            found += 1
        else:
            continue
    if found != 3:
        print("Could not find cowpi files. Ensure copy number file, ko precalc file and cowpi fastas file in directory. Exiting.")
        print(found)
        exit()


    return copy_num_file,ko_precalc_file,cowpi_fastas_file
    

def remove_archaea_from_copy_num_file(copy_num_file, archaea_names, archaea_removed_directory):
    new_copy_nums = []
    with open(copy_num_file, "r") as file:
        while True:
            line = file.readline()
            if not line:
                break
            line = line.strip()
            archaea_found = False
            for name in archaea_names:
                if name in line:
                    archaea_found = True
                    break

            if "Archaea" in line:
                archaea_found = True

            if archaea_found == False:
                new_copy_nums.append(line)

    archaea_removed_copy_num_file = "%s/16S_precalculated_copy_num_file.tab" % (archaea_removed_directory)
    
    with open(archaea_removed_copy_num_file, "w") as new_f:
        
        for new_copy_num in new_copy_nums:
            new_f.write(new_copy_num)
            new_f.write("\n")

def remove_archaea_from_ko_precalcs(ko_precalc_file, archaea_names, archaea_removed_directory):
    ko_precalcs = []
    with open(ko_precalc_file, "r") as file:
        while True:
            line = file.readline()
            if not line:
                break
            line = line.strip()
            archaea_found = False
            for name in archaea_names:
                if name in line:
                    archaea_found = True
                    break

            if "Archaea" in line:
                archaea_found = True

            if archaea_found == False:
                ko_precalcs.append(line)

    archaea_removed_ko_file = "%s/16S_precalculated_ko_file.tab" % (archaea_removed_directory)
    
    with open(archaea_removed_ko_file, "w") as new_f:
        
        for ko_pre in ko_precalcs:
            new_f.write(ko_pre)
            new_f.write("\n")

def remove_archaea_from_fas(cowpi_fasta_file, archaea_names, archaea_removed_directory):
    archaea_removed_fa_file = "%s/cowpi_16S_sequences_file.fas" % (archaea_removed_directory)

    with open(cowpi_fasta_file, "r") as f:
        while True:
            sequence_name = f.readline()
            sequence = f.readline()
            if not sequence_name:
                break
            sequence_name = sequence_name.strip()
            archaea_found = False
            for name in archaea_names:
                if name in sequence_name:
                    archaea_found = True
                    break

            if "Archaea" in sequence_name:
                archaea_found = True

            if archaea_found == False:
                with open(archaea_removed_fa_file, "a+") as new_f:
                    new_f.write("%s\n" % sequence_name)
                    new_f.write("%s\n" % sequence)
                    

    


main()
    

print("Done. Please change the yaml config file to point to the new precalculated files found in the archaea removed directory.")

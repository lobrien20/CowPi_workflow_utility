#!/usr/bin/env python
# Greater workflow manager, read configuration file to get relevant values and generates study workflow objects. As well as deals with summary.
# Methods: Read directory/get study directories, instantiate study object, instantiate tool objects (based on configurations), instantiate summary
# Study object: contains attributes of where fastq files are etc. Methods include interacting with the various tools to produce outputs.
# Methods: activating various steps of process.
# Tool object, inherited by various tools used in the process.
# Methods: Give configuration, run method.


import yaml
import os
import subprocess
import sys
import pandas as pd
from subprocess import Popen, PIPE, STDOUT
import time
import re


class workflow_manager:
    required_configurations = [
        'directory_of_datasets', 'single_or_multiple_datasets']

    def __init__(self, configuration_file_path, start_time):
        self.configuration_file_path = configuration_file_path
        self.config_dict = self.get_configurations()
        self.start_time = start_time
        self.run_datasets()

    # loads yaml file and converts it into one single dictionary with list of configurations unnested
    def get_configurations(self):
        with open(self.configuration_file_path, "r") as file:
            yaml_dict = yaml.load(file, Loader=yaml.FullLoader)
            config_dict = {}
            list_of_dicts = [yaml_dict]

            for a_dict in list_of_dicts:
                for key, value in a_dict.items():

                    if isinstance(value, dict) == True:

                        list_of_dicts.append(value)

                    else:

                        config_dict[key] = value

        return config_dict

    def verify_mandatory_configurations(self):
        print("to do")

    def run_datasets(self):

        directory_of_datasets = self.config_dict['directory_of_datasets']
        if self.config_dict['single_or_multiple_datasets'] == 'single':
            dataset(directory_of_datasets, self.config_dict, self.start_time)

        else:

            list_of_datasets = os.listdir(directory_of_datasets)
            list_of_dataset_paths = [
                "%s/%s" % (directory_of_datasets, dset) for dset in list_of_datasets]
            dataset_obj_dict = {}

            for path, dataset_name in zip(list_of_dataset_paths, list_of_datasets):

                dataset_obj = dataset(path, self.config_dict, self.start_time)
                dataset_obj_dict[dataset_name] = dataset_obj

            multi_dataset_summariser(self.config_dict, dataset_obj_dict)


class multi_dataset_summariser:  # gathers information from datasets to produce as output

    def __init__(self, configuration_dict, multi_dataset_obj_dict):
        self.config_dict = configuration_dict
        self.multi_dataset_summariser = multi_dataset_obj_dict
        self.verify_success_of_all_datasets()
        self.create_success_file()

    def verify_success_of_all_datasets(self):
        dataset_name_success_dict = {}
        dataset_summary_steps_val = 0
        for dataset_name, dataset in self.multi_dataset_summariser.items():
            summary_workflow_outputs = list(dataset.summary_outputs.keys())
            dataset_name_success_dict[dataset_name] = len(
                summary_workflow_outputs)

            if dataset_summary_steps_val < len(summary_workflow_outputs):
                dataset_summary_steps_val = len(summary_workflow_outputs)
        successful_datasets = []
        dataset_fail_file = "%s/datasets_failed.txt" % (
            self.config_dict['directory_of_datasets'])
        with open(dataset_fail_file, "w") as f:
            for dataset_name, dataset_sum_val in dataset_name_success_dict.items():

                if dataset_sum_val < dataset_summary_steps_val:
                    dataset_fail = "%s did not produce all summary output steps. Failed.\n" % (
                        dataset_name)
                    print(dataset_fail)
                    f.write(dataset_fail)
                    successful_datasets.append(dataset_name)

        self.successful_datasets = successful_datasets

    def create_success_file(self):
        all_output_dict = {}
        dataset_order_list = []
        output_ordered = ['Average_number_of_initial_reads', 'Average_percent_non_chimeras', 'Average_percent_chimeras', 'Number_of_reads_after_merging', 'OTU_clusters_found', 'Number_of_OTU_aligned', 'Unique_aligned_OTUs', 'Number_of_predicted_KOs', 'Pathways_at_lvl_1', 'Pathways_at_lvl_2', 'Pathways_at_lvl_3', 'Pathways_at_lvl_4']
        for dataset_name, dataset in self.multi_dataset_summariser.items():
            dataset_order_list.append(dataset_name)
            dataset_dict = dataset.summary_outputs
            for output_name in output_ordered:
                
                if output_name not in all_output_dict.keys():
                    all_output_dict[output_name] = [dataset_dict[output_name]]
                
                else:
                    all_output_dict[output_name].append(dataset_dict[output_name])

        summary_df = pd.DataFrame.from_dict(all_output_dict)
        summary_df['Dataset'] = dataset_order_list
        summary_df = summary_df.set_index(['Dataset'])
        summary_df = summary_df.reindex(columns=output_ordered)
        final_summary_file = "%s/all_datasets_summary_file.csv" % (
            self.config_dict['directory_of_datasets'])
        summary_df.to_csv(final_summary_file, sep='\t')


class workflow_tools:  # runs workflow on individual datasets
    def __init__(self, configuration_dict):
        self.configuration_dict = configuration_dict

    def remove_chimeras(self, sample_name_and_path_dict, chimera_output_directory):
        new_fastq_paths = []
        stdout_dict = {}

        for sample_name, fastq_path in sample_name_and_path_dict.items():

            new_file_path = "%s/chimera_removed_%s.fastq" % (
                chimera_output_directory, sample_name)

            new_fastq_paths.append(new_file_path)
            vsearch_chimera_args = ['vsearch', '--uchime_denovo', fastq_path, '--threads', str(
                self.configuration_dict['threads']), '--nonchimeras', new_file_path]

            p = Popen(vsearch_chimera_args, stdin=PIPE,
                      stdout=PIPE, stderr=STDOUT)
            stdout_dict[sample_name] = str(p.stdout.read())
      #      stdout_dict[sample_name] = subprocess.check_output(['vsearch', '--uchime_denovo', fastq_path, '--threads', str(self.configuration_dict['threads']), '--nonchimeras', new_file_path])

        return new_fastq_paths, stdout_dict

    def merge_fastqs(self, fastq_paths, merged_fastq_path):
        file_lines = []

        for file in fastq_paths:
            with open(file, "r") as sequence_file:
                sequence_list = sequence_file.readlines()
                for sequence_line in sequence_list:
                    file_lines.append(sequence_line)

        with open(merged_fastq_path, "a+") as new_merged_fastq:

            for sequence_lines in file_lines:

                new_merged_fastq.write(sequence_lines)

        return merged_fastq_path

    def cluster_data(self, merged_fastq_path, cluster_output_directory):

        centroid_result = "%s/cluster_centroids.fasta" % cluster_output_directory
        tsv_result = "%s/cluster_table_test.tsv" % cluster_output_directory
        vsearch_cluster2_args = ['vsearch', '--cluster_size', merged_fastq_path, '--id', '0.97', '--threads', str(
            self.configuration_dict['threads']), '--relabel', 'test', '--otutabout', tsv_result, '--centroids', centroid_result]

        subprocess.call(vsearch_cluster2_args)
        return tsv_result, centroid_result

    def align_data(self, cluster_centroids, alignment_directory):
        otu_hits_result = "%s/otu_hits.txt" % (alignment_directory)
        otu_miss_result = "%s/otu_miss.txt" % (alignment_directory)

        vsearch_align_args = ['vsearch', '-usearch_global', cluster_centroids, '-db', self.configuration_dict['16s_sequence_table'], '--id', '0.75', '-strand', 'both', '-userout',
                              otu_hits_result, '-userfields', 'query+target', '-notmatched', otu_miss_result]
        subprocess.call(vsearch_align_args, stdin=PIPE,
                        stdout=PIPE, stderr=STDOUT)

        return otu_hits_result, otu_miss_result

    def convert_biom_to_tsv(self, biom_file):
        file_without_ext = biom_file[:-5]
        tsv_file = "%s.tsv" % (file_without_ext)
        convert_args = ['biom', 'convert', '--to-tsv',
                        '-i', biom_file, '-o', tsv_file]
        subprocess.call(convert_args)
        return tsv_file

    def create_hungate_summarised_table(self, cluster_tsv, otu_hits, otu_misses):

       # cluster_tsv = self.convert_biom_to_tsv(cluster_biom)
        missing_otus = self.get_otu_misses(otu_misses)
        hits_dict = self.generate_hits_dict(otu_hits)
        filtered_table = self.generate_fixed_table(
            cluster_tsv, hits_dict, missing_otus)
        filtered_table_path = "%s/aligned_and_filtered_cluster_table.tsv" % self.dataset_path
        filtered_table.to_csv(filtered_table_path, sep='\t', index=False)
        filtered_biom = self.convert_tsv_to_biom(filtered_table_path)

        return filtered_biom, missing_otus, filtered_table

    def get_otu_misses(self, otu_miss_file):
        with open(otu_miss_file, "r") as f:
            lines = f.readlines()
            missing_otus = []
            for line in lines:
                if ">" in line:
                    missing_otu = line.strip()[1:]
                    missing_otus.append(missing_otu)

        return missing_otus

    def generate_hits_dict(self, hits_file):
        hits_dict = {}
        with open(hits_file, "r") as f:
            hits_list = f.readlines()
            for hits in hits_list:
                hit_opts = hits.split("\t")
                hit_otu = hit_opts[0]
                aligned_otu = hit_opts[1].strip()
                hits_dict[hit_otu] = aligned_otu

        return hits_dict

    def generate_fixed_table(self, cluster_tsv, otu_hits_dict, otu_misses):

        cluster_df = pd.read_csv(cluster_tsv, sep='\t', index_col=[0])
        otu_cluster_names = cluster_df.index.tolist()
        cluster_df = cluster_df.drop(otu_misses)
        otu_hits_df = pd.DataFrame.from_dict(
            otu_hits_dict, orient='index', columns=['aligned_to'])

        fixed_df = cluster_df.join(otu_hits_df)

        fin_df = fixed_df.groupby(by=['aligned_to']).sum().reset_index()
        return fin_df

    def convert_tsv_to_biom(self, tsv_file):
        file_without_ext = tsv_file[:-4]
        biom_file = "%s.biom" % (file_without_ext)
        subprocess.call(['biom', 'convert', '-i', tsv_file, '-o',
                        biom_file, '--table-type=OTU table', '--to-json'])
        return biom_file

    def create_normalised_copy_number_table(self, filtered_biom):
        normalised_otu_table_biom = "%s/clustered_table_normalised_by_copy_number.biom" % (
            self.dataset_path)
        subprocess.call(['normalize_by_copy_number.py', '-i', filtered_biom, '-o',
                        normalised_otu_table_biom, '-c', self.configuration_dict['copy_number_table_file']])
        return normalised_otu_table_biom

    def predict_metagenomes(self, normalised_biom, metagenome_prediction_dir):

        metagenome_predictions_biom = "%s/metagenome_predictions_biom" % metagenome_prediction_dir
        subprocess.call(['predict_metagenomes.py', '-i', normalised_biom, '-o',
                        metagenome_predictions_biom, '-c', self.configuration_dict['ko_table']])

        metagenome_predictions_tsv = self.convert_biom_to_tsv(
            metagenome_predictions_biom)

        return metagenome_predictions_biom, metagenome_predictions_tsv

    def categorize_metagenomes(self, metagenome_predictions_biom, ko_level, categorized_metagenome_dir):
        pathway_result = "%s/lvl_%s_collapsed_pathways.txt" % (
            categorized_metagenome_dir, ko_level)

        subprocess.call(['categorize_by_function.py', '-i', metagenome_predictions_biom, '-c',
                        'KEGG_Pathways', '-l', ko_level, '--format_tab_delimited', '-o', pathway_result])


class summary_tools:

    def __init__(self, configuration_dict):
        self.configuration_dict = configuration_dict
        self.summary_outputs = {}

    def chimera_result_summary(self, chimera_output_dict):
        sample_row_info = [
            "Sample\tNumber of sequences\tnumber of chimeras\tnumber of non chimeras"]
        chimera_info_list = []
        # regex search for percentage chimera and non chimera and total sequences of read
        for sample_name, summary_info in chimera_output_dict.items():

            summary_info = summary_info.split("\n")
            found_both = [False, False]
            for info in summary_info:
                chimera_string_check = re.search("\A[0-9].*chimeras*", info)
                total_seq_string_check = re.findall(
                    ".*in.([0-9]*).*total sequences.", info)
                if chimera_string_check is not None:

                    chimera_string = chimera_string_check.string
                    chimera_info = re.findall(
                        "[(]{1}([^)]*)[)]{1}", chimera_string)

                    found_both = [True, False]

                if len(total_seq_string_check) != 0:
                    total_seq_string = total_seq_string_check[0]

                    if found_both == [True, False]:
                        found_both = [True, True]
                    else:
                        print("error in chimera finding.")
                        exit()
            if found_both == [True, True]:

                chimera_info_list.append([sample_name, float(total_seq_string), float(
                    chimera_info[0][:-1]), float(chimera_info[1][:-1])])

        # get an average for bottom of the list
        sum_of_total_seqs = 0
        sum_of_perc_chimeras = 0
        sum_of_perc_non_chimeras = 0
        for chimera_info in chimera_info_list:

            sum_of_total_seqs += chimera_info[1]
            sum_of_perc_chimeras += chimera_info[2]
            sum_of_perc_non_chimeras += chimera_info[3]

        sums = [sum_of_total_seqs, sum_of_perc_non_chimeras, sum_of_perc_chimeras]
        mean_list = ['average']
        for sum in sums:
            mean_list.append((sum / len(chimera_info_list)))
        chimera_info_list.append(mean_list)

        self.chimera_info_list = chimera_info_list

        self.mean_chimera_info = mean_list[1:]
        self.summary_outputs['Average_number_of_initial_reads'] = mean_list[1]
        self.summary_outputs['Average_percent_non_chimeras'] = mean_list[2]
        self.summary_outputs['Average_percent_chimeras'] = mean_list[3]

        return chimera_info_list

    def merge_fastq_summary(self, merged_fastq_path):
        with open(merged_fastq_path, "r") as merged_fastq:
            fastq_lines = merged_fastq.readlines()
            number_of_reads = len(fastq_lines) / 4

            self.summary_outputs['Number_of_reads_after_merging'] = number_of_reads

    def get_clustering_summary(self, cluster_table):
        # get number of OTU clusters
        with open(cluster_table, "r") as clust_f:
            num_of_clusters = (len(clust_f.readlines()) - 2)

            self.summary_outputs['OTU_clusters_found'] = num_of_clusters

    def get_alignment_and_filter_summary(self, missing_otus, filtered_table):

        self.summary_outputs['Number_of_OTU_aligned'] = self.summary_outputs['OTU_clusters_found'] - \
            len(missing_otus)
        self.summary_outputs['Unique_aligned_OTUs'] = len(
            filtered_table.index.tolist())

    def get_metagenome_prediction_summary(self, metagenome_predictions_table_path):

        pred_df = pd.read_csv(metagenome_predictions_table_path,
                              sep='\t', index_col=[0], header=1)
        self.summary_outputs['Number_of_predicted_KOs'] = len(
            pred_df.index.tolist())

    def get_collapsed_pathway_summary(self, collapsed_pathway_dir, ko_pathway_levels):

        for lvl in ko_pathway_levels:
            try:
                pathway_table_file = "%s/lvl_%s_collapsed_pathways.txt" % (
                    collapsed_pathway_dir, lvl)
                pathway_table = pd.read_csv(
                    pathway_table_file, header=1, sep='\t', index_col=[0])
                self.summary_outputs['Pathways_at_lvl_%s' %
                                     (lvl)] = len(pathway_table.index.tolist())
            except:
                self.summary_outputs['Pathways_at_lvl_%s' % (lvl)] = 0


# dataset object with fastq paths and attributes to be added etc.
class dataset(workflow_tools, summary_tools):

    def __init__(self, dataset_path, configuration_dict, start_time):
        self.dataset_path = dataset_path
        self.initial_fastq_paths = self.get_fastq_paths()
        self.sample_names = self.get_sample_names()
        self.start_time = start_time

        workflow_tools.__init__(self, configuration_dict)
        summary_tools.__init__(self, configuration_dict)

        self.run_workflow()

    def run_workflow(self):

        chimera_removed_fastq_paths = self.chimera_removal_and_summarise()
        merged_fastq_path = self.merge_fastqs_and_summarise(
            chimera_removed_fastq_paths)
        cluster_table, cluster_centroids_path = self.cluster_and_summarise(
            merged_fastq_path)

        filtered_biom = self.align_and_summarise(
            cluster_centroids_path, cluster_table)

        normalised_biom = self.normalise_by_copy_number(filtered_biom)
        self.predict_and_categorise_metagenomes(normalised_biom)

        self.get_post_analysis_summary()

    def get_sample_names(self):
        sample_paths_without_ext = [".".join(fastq.split(
            ".")[:-1]) for fastq in self.initial_fastq_paths]
        sample_names = [path.split("/")[-1]
                        for path in sample_paths_without_ext]
        return sample_names

    def get_fastq_paths(self):
        fastq_paths = ["%s/%s" % (self.dataset_path, file) for file in os.listdir(
            self.dataset_path) if file[-6:] == '.fastq' or file[-3:] == '.fq']
        return fastq_paths

    def get_time_took(self):
        time_took = self.start_time - time.time()
        print(time_took)

    def chimera_removal_and_summarise(self):
        print("running chimera removal.")

        chimera_output_directory = "%s/chimera_removal_directory" % self.dataset_path
        try:
            os.mkdir(chimera_output_directory)
        except:
            print("chimera removal directory already exists.")
        sample_path_dict = {}

        for sample_name, fastq_path in zip(self.sample_names, self.initial_fastq_paths):
            sample_path_dict[sample_name] = fastq_path

        chimera_removed_fastq_paths, chimera_output_dict = self.remove_chimeras(
            sample_path_dict, chimera_output_directory)

        chimera_info_list = self.chimera_result_summary(chimera_output_dict)
        with open("%s/chimera_removal_directory/chimera_removal_summary.csv" % (self.dataset_path), "w") as f:
            f.write(
                "sequence name\tinitial_total_sequences\ttotal_chimeras\ttotal_non_chimeras\n")
            for info in chimera_info_list:
                print(info)
                info_as_line = "%s\t%s\t%s\t%s\n" % (
                    info[0], info[1], info[2], info[3])
                f.write(info_as_line)

        return chimera_removed_fastq_paths

    def merge_fastqs_and_summarise(self, fastq_paths):
        print("merging fastqs.")
        merged_fastq_directory = "%s/merged_fastq_directory" % self.dataset_path
        try:
            os.mkdir(merged_fastq_directory)

        except:
            print("merged fastq dir already exists.")

        merged_fastq_path = "%s/merged_fastq_directory/merged_sequences.fastq" % self.dataset_path
        merged_fastq_path = self.merge_fastqs(fastq_paths, merged_fastq_path)
        self.merge_fastq_summary(merged_fastq_path)

        return merged_fastq_path

    def cluster_and_summarise(self, merged_fastq_path):
        print("clustering sequences.")
        cluster_directory = "%s/clustering_directory" % self.dataset_path
        try:
            os.mkdir(cluster_directory)
        except:
            print("clustering directory already exists.")
        otu_cluster_table, cluster_centroids = self.cluster_data(
            merged_fastq_path, cluster_directory)

        self.get_clustering_summary(cluster_centroids)
        return otu_cluster_table, cluster_centroids

    def align_and_summarise(self, clustered_fasta, clustered_biom):
        print("aligning otu clusters to rumen amplicons.")
        alignment_directory = "%s/alignment_directory" % self.dataset_path
        try:

            os.mkdir(alignment_directory)

        except:

            print("alignment directory already exists.")

        otu_hits, otu_miss = self.align_data(
            clustered_fasta, alignment_directory)
        filtered_biom, missing_otus, filtered_table = self.create_hungate_summarised_table(
            clustered_biom, otu_hits, otu_miss)
        print("Creating filtered data file based on otu alignment.")
        self.get_alignment_and_filter_summary(missing_otus, filtered_table)

        return filtered_biom

    def normalise_by_copy_number(self, filtered_biom):
        print("normalising by copy number.")
        normalised_biom = self.create_normalised_copy_number_table(
            filtered_biom)

        return normalised_biom

    def predict_and_categorise_metagenomes(self, normalised_biom):
        print("predicting and categorising metagenomes")
        metagenome_prediction_directory = "%s/metagenome_predictions" % self.dataset_path

        try:

            os.mkdir(metagenome_prediction_directory)

        except:

            print("metagenome dir already produced.")

        metagenome_predictions_biom, metagenome_prediction_table = self.predict_metagenomes(
            normalised_biom, metagenome_prediction_directory)
        self.get_metagenome_prediction_summary(metagenome_prediction_table)

        categorised_predictions_dir = "%s/categoried_predictions" % self.dataset_path
        try:
            os.mkdir(categorised_predictions_dir)
        except:
            print("categorised predictions dir already produced.")

        ko_pathway_levels = ['1', '2', '3', '4']
        for level in ko_pathway_levels:

            self.categorize_metagenomes(
                metagenome_predictions_biom, level, categorised_predictions_dir)

        self.get_collapsed_pathway_summary(
            categorised_predictions_dir, ko_pathway_levels)

    def get_post_analysis_summary(self):
        print("generating summary file")
        summary_output_file = "%s/summary_output_file.txt" % self.dataset_path
        output_ordered = ['Average_number_of_initial_reads', 'Average_percent_non_chimeras',
                          'Average_percent_chimeras', 'Number_of_reads_after_merging', 'OTU_clusters_found', 'Number_of_OTU_aligned', 'Unique_aligned_OTUs', 'Number_of_predicted_KOs', 'Pathways_at_lvl_1', 'Pathways_at_lvl_2', 'Pathways_at_lvl_3', 'Pathways_at_lvl_4']
        with open(summary_output_file, "w") as file:

            for output_name in output_ordered:

                output_val = self.summary_outputs[output_name]
                output_result = "%s\t%s\n" % (output_name, output_val)
                file.write(output_result)

        print("dataset at %s complete.\nSummary file at %s\n" %
              (self.dataset_path, summary_output_file))


start_time = time.time()
workflow_manager(sys.argv[1], start_time)

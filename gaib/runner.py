# Author: Kent O'Sullivan

# Core Imports
import os
import json
import shutil
import argparse
import csv
import datetime
import importlib.metadata
import socket
import tempfile

# Library Imports
import networkx as nx

# User File Imports

from experiment import Experiment, Evaluator, Task

RESULTS_COLUMNS = ["timestamp", "hostname", "hardware", "library", "backend", "library_versions",
                   "task", "dataset", "gt_granularity", "vertices", "edges", "run_index", "seed",
                   "etl_s", "processing_s", "total_s", "predicted_communities", "nmi"]

class Runner():
    def __init__(self, output_directory:os.path, results_csv:os.path, hardware:str):
        self.evaluator = Evaluator()
        self.output_directory = output_directory
        self.results_csv = results_csv
        self.hardware = hardware
        os.makedirs(output_directory, exist_ok=True)
        

    def calculate_effectiveness(self, final_result:list, interim_results:dict, gt_labels_file:os.path, snap_format:bool=False)->dict:
        #Calculate Effectiveness
        print("CALCULATING EFFECTIVENESS...")
        effectiveness = {'final':{}}
        effectiveness['final']['nmi'] = self.evaluator.evaluate_CD(gt_labels_path=gt_labels_file,pred_labels=final_result,snap_format=snap_format)
        effectiveness['final']['num_communities'] = len(final_result)
        for i, result in enumerate(interim_results.keys()):
            effectiveness[f'interim_{i}']={}
            interim_predictions = self.evaluator.parse_interim_labels(interim_results[result]['results']) 
            effectiveness[f'interim_{i}']['nmi'] = self.evaluator.evaluate_CD(gt_labels_path=gt_labels_file,pred_labels=interim_predictions,snap_format=snap_format)
            effectiveness[f'interim_{i}']['num_communities'] = len(interim_predictions)
            self.experiment.add_time(label=f'result_interim_{i}',time=interim_results[result]['time'])
        return(effectiveness)

    def calculate_efficiency(self):
        #Calculate Efficency:
        print("CALCULATING EFFICIENCY...")
        times = self.experiment.get_times_dict()

        transfer_time = times['END_TX'] - times['START_TX']
        etl_time = times['END_ETL'] - times['START_ETL']
        processing_time = times['END_PROCESS'] - times['START_PROCESS']
        probing_time = times['END_PROBING'] - times['START_PROBING']
        experiment_time = times['END_PROCESS'] - times['START_TX']
        
        try:
            batch_latency = times['interim_0'] - times['START_PROBING']
        except KeyError:
            batch_latency = times['END_PROCESS'] - times['START_PROBING']

        interim_counter = 0
        for key in times.keys():
            if 'interim' in key:
                interim_counter+=1
        
        batch_rate = probing_time/interim_counter

        timing_report= {
                        "Transfer":transfer_time,
                        "ETL":etl_time,
                        "Processing":processing_time,
                        "Probing":probing_time,
                        "Batch_Latency":batch_latency,
                        "Batch_Rate":batch_rate,
                        "Experiment_Length":experiment_time
                        }
        
        return timing_report

    def library_versions(self)->str:
        versions = {"networkx": nx.__version__}
        for dist in importlib.metadata.distributions():
            if dist.metadata["Name"].startswith("nx-cugraph"):
                versions[dist.metadata["Name"]] = dist.version
        return ";".join(f"{name}={version}" for name, version in versions.items())

    def append_results_row(self, row:dict)->None:
        write_header = not os.path.exists(self.results_csv) or os.path.getsize(self.results_csv) == 0
        with open(self.results_csv, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=RESULTS_COLUMNS)
            if write_header:
                writer.writeheader()
            writer.writerow(row)
            f.flush()
            os.fsync(f.fileno())

    def warm_up(self, tasks:set)->None:
        for task in sorted(tasks):
            print(f"WARM-UP {task}")
            with tempfile.TemporaryDirectory() as scratch:
                Task(graph=nx.karate_club_graph(), task=task, seed=0, output_dir=scratch)

    def run_experiment(self, 
                    task:str, 
                    source_data:os.path, 
                    gt_results:os.path,  
                    run_index:int,
                    seed:int,
                    working_directory:os.path=(os.path.join(".","temp_workspace")),
                    gt_granularity:str="standard",
                    weighted:bool=True,
                    snap_format:bool=False):

        self.experiment = Experiment()
        exp_name = self.experiment.get_experiment_name(source_data,task=task,gt_data=gt_granularity,run_index=run_index)
        self.experiment.get_time("START_EXPERIMENT")

        #Transfer The data
        s,e,m,working_path = self.experiment.data_transfer(source=source_data,dest=working_directory)

        if not m:
            self.experiment.save_results(experiment_name=exp_name,
                                    results={"hash_mismatch":True})
            self.experiment.save_metadata(experiment_name=exp_name)
            exit("Hash Mismatch Detected")
        
        dataset_size = (os.stat(working_path)).st_size / (1024 * 1024) #size in Mb

        #Start Probing Window
        self.experiment.get_time("START_PROBING")
        #ETL
        setl, eetl, gm, ns, es, Graph = self.experiment.etl(working_path,weighted=weighted,stats=(None,None),snap_format=snap_format)
        
        # if not gm: #TODO: Re-implement when metadata is reliable
        #     experiment.save_results(experiment_name=exp_name,
        #                             results={"hash_mismatch":False,
        #                                     "graph_mismatch":True})
        #     experiment.save_metadata(experiment_name=exp_name)
        #     exit("Graph Mismatch Detected")

        #Processing
        final_result, interim_results, seed_used = self.experiment.run_process(graph=Graph,task=task,seed=seed)
        #End Probing Window
        self.experiment.get_time("END_PROBING")

        self.experiment.get_time("END_EXPERIMENT")

        effectiveness_report = self.calculate_effectiveness(final_result=final_result,interim_results=interim_results,gt_labels_file=gt_results,snap_format=snap_format)

        efficiency_report = self.calculate_efficiency()

        dataset_report = {  "dataset":source_data,
                            "hash_match":m,
                            "graph_match":gm,
                            "size_on_disk":dataset_size,
                            "node_count": ns,
                            "edge_count": es,
                            "weighted":weighted,
                            "gt_file":gt_results,
                            "gt_community_count":len(self.evaluator.parse_gt_labels(gt_results,snap_format=snap_format)) if gt_results is not None else None
        }

        experiment_report = {"experiment":exp_name,
                             "run_index":run_index,
                             "seed":seed_used,
                             "datasets":dataset_report,
                             "effectiveness":effectiveness_report,
                             "efficiency":efficiency_report}
        
        self.experiment.save_results(experiment_name=exp_name,results=experiment_report,filepath=self.output_directory)

        self.append_results_row({"timestamp":datetime.datetime.now().isoformat(timespec="seconds"),
                                 "hostname":socket.gethostname(),
                                 "hardware":self.hardware,
                                 "library":"networkx",
                                 "backend":"cugraph" if task.endswith("_GPU") else "networkx",
                                 "library_versions":self.library_versions(),
                                 "task":task,
                                 "dataset":os.path.splitext(os.path.basename(source_data))[0],
                                 "gt_granularity":gt_granularity,
                                 "vertices":ns,
                                 "edges":es,
                                 "run_index":run_index,
                                 "seed":seed_used,
                                 "etl_s":efficiency_report["ETL"],
                                 "processing_s":efficiency_report["Processing"],
                                 "total_s":efficiency_report["Experiment_Length"],
                                 "predicted_communities":effectiveness_report["final"]["num_communities"],
                                 "nmi":effectiveness_report["final"]["nmi"]})

        print("\n\n# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #")
        print(    "# # # # # # # # # # EXPERIMENT REPORT # # # # # # # # # # #")
        print(    "# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #")
        print("EXPERIMENT", exp_name)
        print("DATASET\n", dataset_report)
        print("EFFECTIVENESS\n", effectiveness_report)
        print("EFFICIENCY\n", efficiency_report)
        print("\n# # # # # # # # # # # # # # # # # # # #\n\n")

        try:
            shutil.rmtree(working_directory)
            print("Removing temp files")
        except OSError as e:
            print("Error: %s : %s" % (working_path, e.strerror))
        os.makedirs(working_directory)
        print('fresh build complete')

    def run_all_experiments(self, experiment_definition_directory:os.path, repetitions:int, base_seed:int):

        experiment_name_generator = Experiment()

        specs = []
        for f in sorted(os.listdir(experiment_definition_directory)):
            if f.endswith(".json"):
                with open(os.path.join(experiment_definition_directory,f),"r") as infile:
                    specs.append(json.load(infile))

        tasks = [spec["TASK"]+"_GPU" if spec['GPU'] else spec["TASK"] for spec in specs]
        self.warm_up(set(tasks))

        for spec, task in zip(specs, tasks):
            for run_index in range(spec.get("REPETITIONS", repetitions)):
                experiment_name = experiment_name_generator.get_experiment_name(spec["SOURCE_DATA"],task,spec['GT_GRANULARITY'],run_index)+".json"

                if experiment_name in os.listdir(self.output_directory):
                    print(f"{experiment_name} already completed - skipping")
                    continue

                print(f"RUNNING EXPERIMENT {experiment_name}")
                self.run_experiment(task=task,
                                    source_data=spec['SOURCE_DATA'],
                                    gt_results=spec['GT_FILE_PATH'],
                                    run_index=run_index,
                                    seed=base_seed+run_index,
                                    gt_granularity=spec["GT_GRANULARITY"],
                                    weighted=spec['WEIGHTED'],
                                    snap_format=spec['SNAP'])

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hardware", type=str, required=True, help="Hardware label recorded with every run")
    ap.add_argument("--definitions", type=str, default=os.path.join(".","experiment_definitions"), help="Directory of experiment definition JSON files")
    ap.add_argument("--output-directory", type=str, default=os.path.join(".","experiment_results"), help="Directory for per-run JSON reports")
    ap.add_argument("--results-csv", type=str, default=os.path.join(".","experiment_results","results.csv"), help="CSV that gets one row appended per run")
    ap.add_argument("--repetitions", type=int, default=10, help="Runs per definition unless it sets REPETITIONS")
    ap.add_argument("--base-seed", type=int, default=123, help="Seed for run 0; run i uses base seed + i")
    flags = ap.parse_args()

    runner = Runner(output_directory=flags.output_directory, results_csv=flags.results_csv, hardware=flags.hardware)

    runner.run_all_experiments(experiment_definition_directory=flags.definitions, repetitions=flags.repetitions, base_seed=flags.base_seed)

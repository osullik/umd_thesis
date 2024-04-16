# Author: Kent O'Sullivan

# Core Imports
import os
import json
import shutil

# Library Imports

# User File Imports

from experiment import Experiment, Evaluator

class Runner():
    def __init__(self, output_directory:os.path):
        self.experiment = Experiment()
        self.evaluator = Evaluator()
        self.output_directory = output_directory
        

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

        transfer_time = (times['END_TX'] - times['START_TX']).total_seconds()
        etl_time = (times['END_ETL'] - times['START_ETL']).total_seconds()
        processing_time = (times['END_PROCESS'] - times['START_PROCESS']).total_seconds()
        probing_time = (times['END_PROBING'] - times['START_PROBING']).total_seconds()
        experiment_time = (times['END_PROCESS'] - times['START_TX']).total_seconds()
        
        try:
            batch_latency = (times['interim_0'] - times['START_PROBING']).total_seconds()
        except KeyError:
            batch_latency = (times['END_PROCESS'] - times['START_PROBING']).total_seconds()

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

    def run_experiment(self, 
                    task:str, 
                    source_data:os.path, 
                    gt_results:os.path,  
                    working_directory:os.path=(os.path.join(".","temp_workspace")),
                    gt_granularity:str="standard",
                    weighted:bool=True,
                    snap_format:bool=False):

        exp_name = self.experiment.get_experiment_name(source_data,task=task,gt_data=gt_granularity)
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
        final_result, interim_results = self.experiment.run_process(graph=Graph,task=task)
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
                            "gt_community_count":len(self.evaluator.parse_gt_labels(gt_results,snap_format=snap_format))
        }

        experiment_report = {"experiment":exp_name,
                             "datasets":dataset_report,
                             "effectiveness":effectiveness_report,
                             "efficiency":efficiency_report}
        
        self.experiment.save_results(experiment_name=exp_name,results=experiment_report,filepath=self.output_directory)

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

    def run_all_experiments(self, experiment_definition_directory:os.path=(os.path.join(".","experiment_definitions"))):

        experiment_name_generator = Experiment()

        files = sorted(os.listdir(experiment_definition_directory))

        for f in files:
            if f.endswith(".json"):
                experiment_name = f
                with open(os.path.join(experiment_definition_directory,f),"r") as infile:
                    spec = json.load(infile)
                    experiment_name = experiment_name_generator.get_experiment_name(spec["SOURCE_DATA"],spec['TASK'],spec['GT_GRANULARITY'])+".json"

                if experiment_name not in os.listdir(spec["OUTPUT_DIRECTORY"]):
                    print(f"RUNNING EXPERIMENT {experiment_name}")
                    # try:
                    self.run_experiment(task=spec["TASK"],
                                        source_data=spec['SOURCE_DATA'],
                                        gt_results=spec['GT_FILE_PATH'],
                                        gt_granularity=spec["GT_GRANULARITY"],
                                        weighted=spec['WEIGHTED'],
                                        snap_format=spec['SNAP'])
                    # except :
                    #     print(f"EXPERIMENT {experiment_name} FAILED")
                    
                else:
                    print(f"{experiment_name} already completed - skipping")

if __name__ == "__main__":
    OUTPUT_DIRECTORY = os.path.join(".","experiment_results")
    EXPERIMENT_DEFINITION_DIRECTORY = os.path.join(".","experiment_definitions")

    runner = Runner(output_directory=OUTPUT_DIRECTORY)

    runner.run_all_experiments()

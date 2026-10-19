# Author: Kent O'Sullivan -- osullik@umd.edu

#Core Python Imports
import datetime
import sys
import os
import json
import time
import hashlib
import shutil
import threading
import gc
from operator import itemgetter

#Library Imports
from tqdm import tqdm
import networkx as nx
from sklearn.metrics.cluster import normalized_mutual_info_score as nmi

#User imports

class Experiment():
    def __init__(self)->None:
        self._times = {}
        self.set_data_directory(os.path.join("..","datasets")) #self._data_directory
        self.set_results_directory(os.path.join("..","temp_results")) #self._results_directory
        
    def get_time(self, label:str)->dict:
        now = datetime.datetime.now()
        processor_now = time.process_time()
        self._times[label] = now
        self._times[f"processor_{label}"] = processor_now
        return {label:now}
    
    def add_time(self, label:str, time:datetime.datetime):
        self._times[label] = time
        return {label:time}
    
    def get_times_dict(self)->dict:
        return self._times
    
    def get_data_directory(self)->os.path:
        return self._data_directory
    
    def get_results_directory(self)->os.path:
        return self._results_directory
    
    def set_data_directory(self, directory:os.path)->None:
        if not os.path.exists(directory):
            os.makedirs(directory)
        self._data_directory = directory
        print(f"Data directory is {self._data_directory}")

    def set_results_directory(self, directory:os.path)->None:
        if not os.path.exists(directory):
            os.makedirs(directory)
        self._results_directory = directory
        print(f"Results directory is {self._data_directory}")

    def load_file(self, file_name:str)->dict:
        
        #Handle filename only and 
        if os.path.exists(os.path.join(self._data_directory,file_name)):
            fn = os.path.abspath(os.path.join(self._data_directory,file_name))
        elif os.path.exists(os.path.join(file_name)):
            fn = os.path.abspath(os.path.join(file_name))
        else:
            exit("File not found.")

        with open(fn,"r") as f:
            try:
                source_data = json.load(f)
            except ValueError:
                exit("Not a valid JSON file")
        
        return source_data
    
    def get_experiment_name(self, filename:os.path, task:str, gt_data:str, type:str="RESULTS")->str:

        base_file_name = os.path.basename(filename)

        name = base_file_name.split(".")[:-1][0]
        extension = base_file_name.split(".")[-1]

        output_name = f"{name}_{task}_{gt_data}_{type}"
        
        return output_name
    
    def save_results(self, experiment_name:str, results:dict, filepath:os.path=None)->None:
        print(f"SAVING EXPERIMENT REPORT TO {filepath}.{experiment_name.replace('.txt','')}.json")
        if filepath is None:
            output_file = os.path.join(self.get_results_directory())
        else:
            output_file = filepath

        if os.path.exists(output_file):
            save_name = os.path.join(filepath,experiment_name.replace(".txt",'')+".json")

        else:
            save_name = output_file
            

        with open(save_name, 'w') as f:
            json.dump(results,f,indent=2)
            print(f"Saved results to {save_name}")

    def generate_metadata(self, experiment_name):

        times = self.get_times_dict()

        times["total_wall"] = times['END'] - times['START']
        times['total_wall'] =  times['total_wall'].total_seconds()
        times['START'] = times['START'].isoformat()
        times['END'] = times['END'].isoformat()

        times["total_processor"] = times['processor_END'] - times['processor_START']

        return {"metadata":{
            "experiment_name":experiment_name,
            "times":times
        }}

    def save_metadata(self, experiment_name:str)->None:

        metadata = self.generate_metadata(experiment_name=experiment_name)

        experiment_name = self.get_experiment_name(filename=experiment_name,type="METADATA")

        output_file = os.path.join(self.get_results_directory(),experiment_name)

        if os.path.exists(output_file):
            experiment_name = self.get_experiment_name(filename=output_file)
            save_name = os.path.join(self.get_results_directory(),experiment_name)
        else:
            save_name = output_file
            
        with open(save_name, 'w') as f:
            json.dump(metadata,f,indent=2)
            print(f"Saved metadata to {save_name}")

    def run_experiment(self, data:dict, experiment_name:str)->dict:        
        self.get_time("START")
        # total=0        

        self.get_time("END")

        self.save_results(experiment_name=experiment_name, results=data)
        self.save_metadata(experiment_name=experiment_name)

    def get_hash(self, path_to_file)->hashlib.sha256:
        
        sha256 = hashlib.sha256()

        # Open the file in binary mode and read it in chunks
        with open(path_to_file, 'rb') as file:
            for chunk in iter(lambda: file.read(4096), b''):
                sha256.update(chunk)

        return sha256.hexdigest()
    
    def copy_data(self,source:os.path, dest:os.path):
        try:
            # Copy the file from source to destination
            shutil.copy(source, os.path.join(dest,os.path.basename(source)))
            print(f"Successfully copied '{os.path.basename(dest)}' from '{os.path.realpath(source)}' to '{os.path.realpath(dest)}'")
        except FileNotFoundError:
            print(f"Error: File '{os.path.basename(dest)}' not found in '{os.path.realpath(source)}'")
        except PermissionError:
            print(f"Error: Permission denied to copy '{source}'")


    def data_transfer(self, source:os.path, dest:os.path)->tuple:
        file_name = os.path.basename(source)
        original_hash = self.get_hash(os.path.join(source))
        start_tx = self.get_time("START_TX")
        self.copy_data(source=source,dest=dest)
        end_tx = self.get_time("END_TX")
        new_hash = self.get_hash(os.path.join(dest,file_name))
        return(start_tx,end_tx,original_hash==new_hash,os.path.join(dest,file_name))
    
    def load_weighted_graph(self,source:os.path)->nx.Graph:

        G = nx.Graph()

        with open(source,'r') as f:
            data = f.readlines()
        
        for line in data:
            if not line.strip() or line.startswith("#"):
                continue
            u, *neighbours = line.split()
            for v, w in zip(neighbours[0::2], neighbours[1::2]):
                G.add_edge(u_of_edge=u, v_of_edge=v, weight=float(w))

        return(G)
    
    def etl(self, source:os.path, weighted:bool, stats:tuple[str],snap_format:bool=False)->tuple:
        graphs_match = False
        num_nodes, num_edges = stats 

        start_etl = self.get_time("START_ETL")
        if weighted:

            G = self.load_weighted_graph(source)
        
        elif snap_format:
            G = nx.read_edgelist(path=source, comments="#")
            print(f"GRAPH has {len(G.nodes())} nodes and {len(G.edges())} Edges")

        else:
            G = nx.read_adjlist(path=source, comments="#")

        
        end_etl = self.get_time("END_ETL")

        
        if len(G.nodes) == num_nodes and len(G.edges) == num_edges:
            graphs_match = True

        return(start_etl,end_etl,graphs_match, len(G.nodes),len(G.edges),G)
    
    def collect_interim_results(self):
        interim_results = {}
        for i, file in enumerate(os.listdir(self._results_directory)):
            with open(os.path.join(self._results_directory,file),'r') as f:
                result = f.read()
            interim_results[i] = {}
            time = os.path.basename(file).split("_")[-1].replace(".txt","")
            time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%f")
            interim_results[i]['time'] = time
            interim_results[i]['results'] = result
        
        print("Purging temporary results...")
        try:
            shutil.rmtree(self._results_directory)
        except OSError as e:
            print("Error: %s : %s" % (self._results_directory, e.strerror))
        os.makedirs(self._results_directory)

        return interim_results
    
    def run_process(self,graph:nx.Graph,task:str):
        start_processing = self.get_time("START_PROCESS")
        tasker= Task(graph=graph,task=task,output_dir=self._results_directory)
        final_result = tasker.result
        del(tasker)
        gc.collect

        end_processing = self.get_time("END_PROCESS")
        interim_results = self.collect_interim_results()

        return final_result, interim_results

class Task():

    # stop_event = threading.Event()

    def __init__(self, graph:nx.graph,task:str,output_dir:os.path=(os.path.join(".","temp_results")),sample_time=10):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        os.makedirs(os.path.join(".","cache"), exist_ok=True)
        self.output_dir = output_dir
        self.graph = graph
        self.task = task
        self.result = "None"
        self.sample_time = sample_time #How often to probe for information

        if self.task == "DIAMETER":
            self.task_get_diameter()
            return
        elif self.task == "NX_LOUVAIN":
            self.task_networkx_louvain()
        elif self.task == "NX_LOUVAIN_INCREMENTAL":
            self.task_networkx_louvain_incremental()
            return
        elif self.task == "NX_LOUVAIN_GPU":
            self.task_networkx_louvain_GPU()
            return 
        elif self.task == "NX_LOUVAIN_INCREMENTAL_GPU":
            self.task_networkx_louvain_incremental_GPU()
        else:
            return None

    def write_interim_result(self):
        #Runs as a daemon periodically writing results
        # while True:
        # while not Task.stop_event.is_set():    #Alternate to the Daemon config, 
        now = datetime.datetime.now()
        FILENAME = os.path.join(self.output_dir,(self.task+"_"+str(now.isoformat())+".txt"))
        print(f"Writing Interim Result: to {FILENAME}")

        with open(FILENAME, 'w') as f:
            try:
                f.write(str(self.result))
            except TypeError:
                f.write("")
        #Cache the results in case of failure
        with open(os.path.join(".","cache",(self.task+"_"+str(now.isoformat())+".txt")), 'w') as f:
            try:
                f.write(str(self.result))
            except TypeError:
                f.write("")

        # time.sleep(self.sample_time)

        return

    def task_get_diameter(self):
        print(f"Calculating diameter")
        # thread = threading.Thread(target=self.write_interim_result, 
                            #   args=())
        # thread.daemon = True
        # thread.start()
        self.result = nx.diameter(self.graph)
        self.write_interim_result()
        # Task.stop_event.set()
        # thread.join()
        return
    
    def task_networkx_louvain(self):
        print("Calculating Communities")
        self.result = nx.community.louvain_communities(self.graph, 
                                                       weight=None,
                                                       resolution=1,
                                                       threshold=0.0000001,
                                                       seed=123)
        
        self.write_interim_result()
        return
    
    def task_networkx_louvain_incremental(self):
        print("Calculating Communities Incrementally")
        community_generator = nx.community.louvain_partitions(self.graph, 
                                                    weight=None,
                                                    resolution=1,
                                                    threshold=0.0000001,
                                                    seed=123
                                                    )
        
        for iteration in community_generator:
            self.result = iteration
            self.write_interim_result()
        
        return
    
    def task_networkx_louvain_GPU(self):
        print("Calculating Communities with GPU")
        self.result = nx.community.louvain_communities(self.graph, 
                                                       weight=None,
                                                       resolution=1,
                                                       threshold=0.0000001,
                                                       seed=123,
                                                       backend='cugraph')
        
        self.write_interim_result()
        return
    
    def task_networkx_louvain_incremental_GPU(self):
        print("Calculating Communities Incrementally with GPU")
        community_generator = nx.community.louvain_partitions(self.graph, 
                                                    weight=None,
                                                    resolution=1,
                                                    threshold=0.0000001,
                                                    seed=123,
                                                    backend='cugraph'
                                                    )
        
        for iteration in community_generator:
            self.result = iteration
            self.write_interim_result()
        
        return

class Evaluator():
    def __init__(self):
        pass 
    
    def calculate_nmi(self, gt_labels:list,pred_labels:list):

        return (nmi(gt_labels,pred_labels))
    
    def parse_gt_labels(self, gt_labels_path:os.path,snap_format:bool):
        delimiters = [" ", "\t"]

        with open(gt_labels_path,'r') as f:
            data = f.readlines()

        results_dict = {}
        results_dict["<UNK>"] = []
        for line in data:
            if line.startswith("#"):
                continue
            # print(line)
            if snap_format:
                line=line.strip()
                for delimiter in delimiters:
                    line = " ".join(line.split(delimiter))
                lines = line.split(" ",1)

                try:
                    results_dict[lines[1]].append(lines[0])
                except KeyError:
                    results_dict[lines[1]] = [lines[0]]
                except IndexError:
                    results_dict["<UNK>"].append(lines[0])

                # for i, node in enumerate(line):
                #     # print(i, node)
                #     if i == 0:
                #         val = node
                #     else:
                #         try:
                #             results_dict[node].append(val)
                #         except KeyError:
                #             results_dict[node]=[val]


            else:

                line = line.strip()
                key_value_pair = line.split(' [', 1)
                    
                if len(key_value_pair) != 2:
                    continue  # Skip lines that don't match expected format
                
                key = key_value_pair[0]
                values_str = key_value_pair[1].rstrip(']')  # Remove trailing ']'
                
                # Split values string into individual values
                values = [val.strip() for val in values_str.split(',')]
                
                # Store key-value pair in the dictionary
                results_dict[key] = values
        # print("RESULTS",results_dict)
        return results_dict
    
    def parse_interim_labels(self, interim_labels:str):
        
        results_dict = {}
        labs = interim_labels
        labs = labs.strip()
        labs = labs.replace('[','')
        labs = labs.replace(']','')
        labs = labs.replace("\'", '')
        
        sets = labs.split('{')
        for i, this_set in enumerate(sets):
            key = str(i)
            this_set = this_set.replace("\'",'')
            this_set = this_set.replace("},",'')
            this_set = this_set.replace("}",'')

            # Split values string into individual values
            values = [val.strip() for val in this_set.split(',')]
            if values == ['']:
                continue
            # Store key-value pair in the dictionary
            results_dict[key] = values

        return results_dict

    def prepare_community_labels(self, input)->list:
        labels = []
        nodes = []
        result = []
        if type(input) is dict:
            for label in input.keys():
                for node in input[label]:
                    labels.append(str(label))
                    nodes.append(str(node))
        
        elif type(input) is list:
            for i, label in enumerate(input):
                for node in label:
                    labels.append(str(i))
                    nodes.append(str(node))
        elif type(input) is str:
            dict_labels = self.prepare_community_labels(input)
        else:
            print("INPUT TYPE IS", type(input))
            # print("INPUT IS", input)
            exit("Input problem, check that it is a dict of lists, or a list of sets")
        
        nodes, labels = [list(x) for x in zip(*sorted(zip(nodes, labels),
                                         key = itemgetter(0)))]
        
        return(labels)
        
    def evaluate_CD(self, gt_labels_path:os.path, pred_labels:list, snap_format:bool=False):
        if gt_labels_path is None:
            return None
        gt = self.parse_gt_labels(gt_labels_path,snap_format=snap_format)
        
        prepared_gt = self.prepare_community_labels(gt)
        prepared_pred = self.prepare_community_labels(pred_labels)

        NMI = self.calculate_nmi(prepared_gt,prepared_pred)        
        
        return NMI
    

    

        



        


    

        


    

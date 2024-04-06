# Author: Kent O'Sullivan -- osullik@umd.edu

#Core Python Imports
import unittest
import datetime
import time
import os
import sys
import shutil
import hashlib

#Library Imports
import networkx as nx

#User imports
sys.path.append(os.path.join(".."))
from experiment import Experiment


class Test_experiment_framework(unittest.TestCase):
    def setUp(self) -> None:
        self.default_data_directory = os.path.join("..","..","..","data")
        self.experiment = Experiment()
        
        return super().setUp()
    
    def tearDown(self) -> None:
        return super().tearDown()
    
    def test_experiment_exists(self):
        self.assertTrue(self.experiment)

    def test_get_time(self):
        start_time = datetime.datetime.now()
        start_exp = self.experiment.get_time("START")
        time.sleep(0.1)
        end_time = datetime.datetime.now()
        end_exp = self.experiment.get_time("END")

        self.assertTrue("START" in start_exp)
        self.assertTrue("END" in end_exp)
        self.assertAlmostEqual(start_exp["START"].timestamp(), start_time.timestamp(), places=4)
        self.assertAlmostEqual(end_exp["END"].timestamp(), end_time.timestamp(), places=4)
        self.assertNotAlmostEqual(start_exp["START"].timestamp(), end_exp["END"].timestamp(), places=4)

    def test_get_times_dict(self):

        times = {}

        self.assertDictEqual(self.experiment.get_times_dict(),times)
        self.experiment.get_time("START")
        self.assertTrue("START" in self.experiment.get_times_dict())
        self.assertTrue("END" not in self.experiment.get_times_dict())
        self.experiment.get_time("END")
        self.assertTrue("START" in self.experiment.get_times_dict())
        self.assertTrue("END" in self.experiment.get_times_dict())

    def test_get_data_directory(self):

        data_directory = os.path.join("..","datasets")
        test_data_directory = os.path.join("..","datasets","test")
        not_exist_directory = os.path.join("..","datasets","temp_test")
        
        #Check default setting:
        self.assertEqual(self.experiment.get_data_directory(), data_directory)

        #Check custom setting:
        self.experiment.set_data_directory(test_data_directory)
        self.assertEqual(self.experiment.get_data_directory(), test_data_directory)
        
        #Check creates directory:
        self.assertFalse(os.path.exists(not_exist_directory))
        self.experiment.set_data_directory(not_exist_directory)
        self.assertTrue(os.path.exists(not_exist_directory))

        os.rmdir(not_exist_directory)

    def test_load_data_file(self):

        data_directory = os.path.join("..","datasets","test")

        self.experiment.set_data_directory(data_directory)

        #Put loading code in here. 
        
        # with self.assertRaises(SystemExit):
        #     self.experiment.load_file(os.path.join(data_directory,"test_secrets_do_not_exist.json"))
        
        # with self.assertRaises(SystemExit):
        #     self.experiment.load_file(os.path.join(data_directory,"test_not_json.txt"))

        # self.experiment.set_data_directory(self.default_data_directory)

    def test_get_experiment_name(self):
        input_file = "test_cd.txt"
        experiment_name = "test_cd_RESULTS.txt"
        self.assertEqual(self.experiment.get_experiment_name(filename=input_file),experiment_name)

    
    def test_get_results_directory(self):
        #Test default
        results_directory = os.path.join("..","temp_results")
        self.assertEqual(self.experiment.get_results_directory(), results_directory)
        os.rmdir(results_directory)
        
        #Test Custom Directory
        data_directory = os.path.join("..","datasets","test")
        self.experiment.set_data_directory(data_directory)
        self.experiment.set_results_directory(os.path.join("..","temp_results"))
        results_directory = os.path.join("..","temp_results")
        self.assertEqual(self.experiment.get_results_directory(), results_directory)

        self.experiment.set_data_directory(self.default_data_directory)
        
    def test_save_file(self):
        
        data_directory = os.path.join("..","datasets","test")
        results_directory = os.path.join("..","temp_results")
        experiment_name = "test_cd_RESULTS.json"
        experiment_name2 = "test_cd_RESULTS_RESULTS.json"
        save_path = os.path.join(results_directory,experiment_name)
        save_path2 = os.path.join(results_directory,experiment_name2)
        results = {}

        self.experiment.set_data_directory(data_directory)
        self.experiment.set_results_directory(results_directory)
        self.assertFalse(os.path.exists(save_path))
        self.experiment.save_results(experiment_name=experiment_name, results=results)
        self.assertTrue(os.path.exists(save_path))
        self.experiment.save_results(experiment_name=experiment_name, results=results)
        self.assertTrue(os.path.exists(save_path2))

        os.remove(save_path)
        os.remove(save_path2)

    def test_get_hash(self):
        REF_FILE = os.path.join("..","datasets","Massapequa","Massapequa_adj_list.txt")
        REF_HASH = "faf7e59f676c00c340b68a69257c41d8a98c56d6cddbdb3ae90e268ad3f82074"

        self.assertEqual(self.experiment.get_hash(REF_FILE),REF_HASH)

    def test_copy_file(self):
        FILE = "Massapequa_adj_list.txt"
        SOURCE_FILE = os.path.join("..","datasets","Massapequa",FILE)
        TARGET_DIR = os.path.join("..","temp_workspace")

        #Clean up the test area()
        try:
            shutil.rmtree(TARGET_DIR)
        except OSError as e:
            print("Error: %s : %s" % (TARGET_DIR, e.strerror))
        os.makedirs(TARGET_DIR)

        self.assertFalse(os.path.exists(os.path.join(TARGET_DIR,FILE)))
        self.assertTrue(os.path.exists(SOURCE_FILE))
        self.experiment.copy_data(source=SOURCE_FILE,dest=TARGET_DIR)
        self.assertTrue(os.path.exists(os.path.join(TARGET_DIR,FILE)))

    def test_data_transfer(self):
        #Hash local copy
        #Start the timer
        #Copy a file from the datasets to temp_workspace
        #Stop the timer when copying complete. 
        #Hash remote copy
        #Compare hashes
        FILE = "Massapequa_adj_list.txt"
        SOURCE_FILE = os.path.join("..","datasets","Massapequa",FILE)
        TARGET_DIR = os.path.join("..","temp_workspace")
        start_time, end_time, hash_match = self.experiment.data_transfer(source=SOURCE_FILE,dest=TARGET_DIR)
        self.assertTrue(hash_match)

    def test_load_weighted_graph(self):
        FILE_WEIGHTED = os.path.join("..","datasets","test","test_weighted.txt")

        ref_nodes = ['1','2','3','4','5']
        ref_edges = [('1','2',1.0),('2','3',1.0),('2','4',1.0),('3','5',1.0),('4','5',1.0)]

        G = nx.Graph()
        G.add_weighted_edges_from(ref_edges)
        # for u,v,w in ref_edges:
        #     G.add_edge(u_of_edge=u,v_of_edge=v,weight=w)

        H = self.experiment.load_weighted_graph(FILE_WEIGHTED)

        self.assertTrue(set(G.nodes()) == set(H.nodes()))
        self.assertTrue(set(G.edges()) == set(H.edges()))

    def test_etl(self):
        #Start Timer
        #Wait for summary stats
        #Stop Timer

        FILE_UNWEIGHTED = "test_unweighted.txt"
        FILE_WEIGHTED = "test_weighted.txt"
        SOURCE_FILE_UNWEIGHTED = os.path.join("..","datasets","Test",FILE_UNWEIGHTED)
        SOURCE_FILE_WEIGHTED = os.path.join("..","datasets","Test",FILE_WEIGHTED)
        STATS = (5,5)

        self.assertTrue(self.experiment.etl(source=SOURCE_FILE_UNWEIGHTED, stats=STATS, weighted=False))
        self.assertTrue(self.experiment.etl(source=SOURCE_FILE_WEIGHTED, stats=STATS, weighted=True))

        FILE_WEIGHTED_LARGE = os.path.join("..","datasets","Massapequa","Massapequa_adj_list.txt")
        stats_massapequa = (2063,2572)
        self.assertTrue(self.experiment.etl(source=FILE_WEIGHTED_LARGE, stats=stats_massapequa, weighted=True)[2])
        self.assertFalse(self.experiment.etl(source=FILE_WEIGHTED_LARGE, stats=STATS, weighted=True)[2])

    def test_run_process(self):
        #Start timer
        #Start Process
            #Write results with timestamp to results folder
        #Finish Process
        #Finish Time
        #Collect Results
        ref_edges = [('1','2'),('2','3'),('2','4'),('3','5'),('4','5')]
        G = nx.Graph()
        G.add_edges_from(ref_edges)
        REF_RESULT = 3

        final, interim = self.experiment.run_process(graph=G,task="DIAMETER")

        print("INTERIM RESULTS", interim)
        print("FINAL RESULTS", final)
        
        self.assertEqual(final,REF_RESULT)







if __name__ == "__main__":
    unittest.main()


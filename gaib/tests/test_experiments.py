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
from experiment import Experiment, Evaluator


class Test_experiment_framework(unittest.TestCase):
    def setUp(self) -> None:
        self.default_data_directory = os.path.join("..","datasets")
        self.experiment = Experiment()
        self.evaluator = Evaluator()
        
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
        
        self.assertEqual(final,REF_RESULT)

        FILE_WEIGHTED_LARGE = os.path.join("..","datasets","Massapequa","Massapequa_adj_list.txt")
        stats_massapequa = (2063,2572)
        start_time, end_time, status, H = self.experiment.etl(source=FILE_WEIGHTED_LARGE, stats=stats_massapequa, weighted=True)
        REF_RESULT_large = 134
        final_large, interim_large = self.experiment.run_process(graph=H,task="DIAMETER")
        print(final_large)
        print(interim_large)
        self.assertEqual(final_large,REF_RESULT_large)

        # FILE_WEIGHTED_HUGE = os.path.join("..","datasets","District of Columbia","District of Columbia_adj_list.txt")
        # stats_massapequa = (147599,163156)
        # start_time, end_time, status, HG = self.experiment.etl(source=FILE_WEIGHTED_HUGE, stats=stats_massapequa, weighted=True)
        # REF_RESULT_HUGE = 433
        # final_huge, interim_huge = self.experiment.run_process(graph=HG,task="DIAMETER")
        # print(final_huge)
        # print(interim_huge)
        # self.assertEqual(final_huge,REF_RESULT_HUGE)

    # def test_louvain(self):
    #     FILE_WEIGHTED_LARGE = os.path.join("..","datasets","Massapequa","Massapequa_adj_list.txt")
    #     stats_massapequa = (2063,2572)
    #     start_time, end_time, status, H = self.experiment.etl(source=FILE_WEIGHTED_LARGE, stats=stats_massapequa, weighted=True)

    #     final, interim = self.experiment.run_process(H,task="NX_LOUVAIN")

    #     FILE_WEIGHTED_HUGE = os.path.join("..","datasets","District of Columbia","District of Columbia_adj_list.txt")
    #     stats_DC = (147599,163156)
    #     start_time, end_time, status, HG = self.experiment.etl(source=FILE_WEIGHTED_HUGE, stats=stats_DC, weighted=True)

    #     final, interim = self.experiment.run_process(HG,task="NX_LOUVAIN")
    #     # print(len(final))


    #     print("COMMUNITIES DETECTED",len(final))

    # def test_louvain_incremental(self):
    #     FILE_WEIGHTED_LARGE = os.path.join("..","datasets","Massapequa","Massapequa_adj_list.txt")
    #     stats_massapequa = (2063,2572)
    #     start_time, end_time, status, H = self.experiment.etl(source=FILE_WEIGHTED_LARGE, stats=stats_massapequa, weighted=True)

    #     final, interim = self.experiment.run_process(H,task="NX_LOUVAIN_INCREMENTAL")

    #     FILE_WEIGHTED_HUGE = os.path.join("..","datasets","District of Columbia","District of Columbia_adj_list.txt")
    #     stats_DC = (147599,163156)
    #     start_time, end_time, status, HG = self.experiment.etl(source=FILE_WEIGHTED_HUGE, stats=stats_DC, weighted=True)

    #     final, interim = self.experiment.run_process(HG,task="NX_LOUVAIN_INCREMENTAL")
    #     # print(len(final))

    #     print("COMMUNITIES DETECTED",len(final))


    def test_prepare_community_labels(self):

        communities_1 = [set(['1','3','5','7']),set(['2','4','6','8'])]

        communities_2 = {"0":['1','3','5','7'],
                         "1":['2','4','6','8']}
        
        output = ['0','1','0','1','0','1','0','1']

        self.assertEqual(self.evaluator.prepare_community_labels(input=communities_1), output)
        self.assertEqual(self.evaluator.prepare_community_labels(input=communities_2), output)

    def test_calculate_nmi(self):

        gt_1 = [0, 0, 1, 1]
        pr_1 = [0, 0, 1, 1]
        nmi_1 = 1.0
        gt_2 = ["cat", "cat", 0, 0]
        pr_2 = [0, 0, "cat", "cat"]
        nmi_2 = 1.0
        gt_3 = [0, 0, 0, 0]
        pr_3 = [0, 1, 2, 3]
        nmi_3 = 0.0

        self.assertEqual(self.evaluator.calculate_nmi(gt_1,pr_1),nmi_1)
        self.assertEqual(self.evaluator.calculate_nmi(gt_2,pr_2),nmi_2)
        self.assertEqual(self.evaluator.calculate_nmi(gt_3,pr_3),nmi_3)

    def test_load_gt_labels(self):
        TEST_LABEL_PATH = os.path.join("..","datasets","test","test_gt_labels.txt")
        expected_results = {
                            "A": ["1", "2"],
                            "B": ["4", "5", "7"],
                            "C": ["3", "6", "8"]
        }

        self.assertDictEqual(self.evaluator.parse_gt_labels(TEST_LABEL_PATH),expected_results)

    def test_evaluate_CD(self):

        GT_FILE_PATH_CITY = os.path.join("..","datasets","Massapequa","Massapequa_gt_communities_city.txt")
        GT_FILE_PATH_COUNTY = os.path.join("..","datasets","Massapequa","Massapequa_gt_communities_county.txt")

        FILE_WEIGHTED_LARGE = os.path.join("..","datasets","Massapequa","Massapequa_adj_list.txt")
        stats_massapequa = (2063,2572)
        start_time, end_time, status, H = self.experiment.etl(source=FILE_WEIGHTED_LARGE, stats=stats_massapequa, weighted=True)

        final, interim = self.experiment.run_process(H,task="NX_LOUVAIN")

        print("NMI@CITY", self.evaluator.evaluate_CD(gt_labels_path=GT_FILE_PATH_CITY,pred_labels=final))
        print("NMI@COUNTY",self.evaluator.evaluate_CD(gt_labels_path=GT_FILE_PATH_COUNTY,pred_labels=final))


if __name__ == "__main__":
    unittest.main()


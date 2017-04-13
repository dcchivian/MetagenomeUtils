# -*- coding: utf-8 -*-
import unittest
import os  # noqa: F401
import json  # noqa: F401
import time
import requests  # noqa: F401
import shutil
import zipfile

from os import environ
try:
    from ConfigParser import ConfigParser  # py2
except:
    from configparser import ConfigParser  # py3

from pprint import pprint  # noqa: F401

from biokbase.workspace.client import Workspace as workspaceService
from MetagenomeUtils.MetagenomeUtilsImpl import MetagenomeUtils
from MetagenomeUtils.MetagenomeUtilsServer import MethodContext
from MetagenomeUtils.authclient import KBaseAuth as _KBaseAuth
from MetagenomeUtils.Utils.MetagenomeFileUtils import MetagenomeFileUtils
from DataFileUtil.DataFileUtilClient import DataFileUtil
from AssemblyUtil.AssemblyUtilClient import AssemblyUtil


class MetagenomeUtilsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        token = environ.get('KB_AUTH_TOKEN', None)
        config_file = environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('MetagenomeUtils'):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'MetagenomeUtils',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = workspaceService(cls.wsURL)
        cls.serviceImpl = MetagenomeUtils(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']
        suffix = int(time.time() * 1000)
        wsName = "test_kb_maxbin_" + str(suffix)
        cls.ws_info = cls.wsClient.create_workspace({'workspace': wsName})
        cls.dfu = DataFileUtil(os.environ['SDK_CALLBACK_URL'], token=token)
        cls.au = AssemblyUtil(os.environ['SDK_CALLBACK_URL'], token=token)
        cls.binned_contig_builder = MetagenomeFileUtils(cls.cfg)
        cls.prepare_data()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')

    @classmethod
    def prepare_data(cls):
        test_directory_name = 'test_MetagenomeFileUtils'
        cls.test_directory_path = os.path.join(cls.scratch, test_directory_name)
        os.makedirs(cls.test_directory_path)

        for item in os.listdir(os.path.join("Data", "MaxBin_Result_Sample")):
            shutil.copy(os.path.join("Data", "MaxBin_Result_Sample", item),
                        os.path.join(cls.test_directory_path, item))

        # building Assembly
        cls.assembly_filename = 'small_bin_contig_file.fasta'
        cls.assembly_fasta_file_path = os.path.join(cls.scratch, cls.assembly_filename)
        shutil.copy(os.path.join("Data", cls.assembly_filename), cls.assembly_fasta_file_path)

        assembly_params = {
            'file': {'path': cls.assembly_fasta_file_path},
            'workspace_name': cls.ws_info[1],
            'assembly_name': 'MyAssembly'
        }
        cls.assembly_ref = cls.au.save_assembly_from_fasta(assembly_params)

    def getWsClient(self):
        return self.__class__.wsClient

    def getWsName(self):
        return self.ws_info[1]

    def getImpl(self):
        return self.__class__.serviceImpl

    def getContext(self):
        return self.__class__.ctx

    def test_bad_binned_contigs_to_file_params(self):
        invalidate_input_params = {
            'missing_input_ref': 'input_ref'
        }
        with self.assertRaisesRegexp(
                    ValueError, '"input_ref" parameter is required, but missing'):
            self.getImpl().binned_contigs_to_file(self.getContext(), invalidate_input_params)

    def test_bad_file_to_binned_contigs_params(self):
        invalidate_input_params = {
            'missing_assembly_ref': 'assembly_ref',
            'file_directory': 'file_directory',
            'binned_contig_name': 'binned_contig_name',
            'workspace_name': 'workspace_name'

        }
        with self.assertRaisesRegexp(
                    ValueError, '"assembly_ref" parameter is required, but missing'):
            self.getImpl().file_to_binned_contigs(self.getContext(), invalidate_input_params)

        invalidate_input_params = {
            'assembly_ref': 'assembly_ref',
            'missing_file_directory': 'file_directory',
            'binned_contig_name': 'binned_contig_name',
            'workspace_name': 'workspace_name'

        }
        with self.assertRaisesRegexp(
                    ValueError, '"file_directory" parameter is required, but missing'):
            self.getImpl().file_to_binned_contigs(self.getContext(), invalidate_input_params)

        invalidate_input_params = {
            'assembly_ref': 'assembly_ref',
            'file_directory': 'file_directory',
            'missing_binned_contig_name': 'binned_contig_name',
            'workspace_name': 'workspace_name'

        }
        with self.assertRaisesRegexp(
                    ValueError, '"binned_contig_name" parameter is required, but missing'):
            self.getImpl().file_to_binned_contigs(self.getContext(), invalidate_input_params)

        invalidate_input_params = {
            'assembly_ref': 'assembly_ref',
            'file_directory': 'file_directory',
            'binned_contig_name': 'binned_contig_name',
            'missing_workspace_name': 'workspace_name'

        }
        with self.assertRaisesRegexp(
                    ValueError, '"workspace_name" parameter is required, but missing'):
            self.getImpl().file_to_binned_contigs(self.getContext(), invalidate_input_params)

    def test_MetagenomeFileUtils_get_bin_ids(self):

        file_directory = self.test_directory_path
        bin_ids = self.binned_contig_builder._get_bin_ids(file_directory)

        expect_bin_ids_set = set(['out_header.001.fasta',
                                  'out_header.002.fasta',
                                  'out_header.003.fasta'])

        self.assertEquals(set(bin_ids), expect_bin_ids_set)

    def test_MetagenomeFileUtil_generate_contig_bin_summary(self):

        bin_id = 'out_header.003.fasta'
        file_directory = self.test_directory_path

        gc, sum_contig_len, cov = self.binned_contig_builder._generate_contig_bin_summary(
                                                                                    bin_id,
                                                                                    file_directory)

        self.assertEquals(gc, 54.8)
        self.assertEquals(sum_contig_len, 2452188)
        self.assertEquals(cov, 92.5)

        bin_id = 'out_header.001.fasta'
        file_directory = self.test_directory_path

        gc, sum_contig_len, cov = self.binned_contig_builder._generate_contig_bin_summary(
                                                                                    bin_id,
                                                                                    file_directory)

        self.assertEquals(gc, 52.9)
        self.assertEquals(sum_contig_len, 2674902)
        self.assertEquals(cov, 100.0)

    def test_MetagenomeFileUtil_generate_string_contigs(self):

        bin_id = 'small_bin_contig_file.fasta'

        test_directory_name = 'test_MetagenomeFileUtils_generate_string_contigs'
        test_directory_path = os.path.join(self.scratch, test_directory_name)
        os.makedirs(test_directory_path)

        shutil.copy(os.path.join("Data", bin_id), os.path.join(test_directory_path, bin_id))

        string_contigs = self.binned_contig_builder._generate_string_contigs(bin_id,
                                                                             test_directory_path)

        self.assertEquals(len(string_contigs), 8)

    def test_MetagenomeFileUtil_generate_contig_summary(self):

        string_contig = '>NODE_9_length_4254_cov_19.036436\n'
        string_contig += 'TTAAGGCC\n'
        string_contig += 'TTAAGGCCTTAAGGCC\n'

        contig_id, contig_gc, contig_len = self.binned_contig_builder._generate_contig_summary(
                                                                                    string_contig)

        self.assertEquals(contig_id, 'NODE_9_length_4254_cov_19.036436')
        self.assertEquals(contig_gc, 0.5)
        self.assertEquals(contig_len, 24)

    def test_MetagenomeFileUtil_generate_contig_bin(self):
        bin_id = 'out_header.003.fasta'
        file_directory = self.test_directory_path

        contig_bin = self.binned_contig_builder._generate_contig_bin(bin_id, file_directory)

        expect_bin_keys = ['contigs', 'bid', 'gc', 'sum_contig_len', 'cov']
        self.assertItemsEqual(contig_bin.keys(), expect_bin_keys)
        self.assertEquals(contig_bin.get('bid'), bin_id)

        expect_contig_bin_keys = ['gc', 'id', 'len']
        self.assertItemsEqual(contig_bin.get('contigs')[0].keys(), expect_contig_bin_keys)

    def test_MetagenomeFileUtil_get_contig_file(self):
        contig_file = self.binned_contig_builder._get_contig_file(self.assembly_ref)

        with open(contig_file, 'r') as file:
            contig_file_content = file.readlines()

        with open(self.assembly_fasta_file_path, 'r') as file:
            expect_contig_file_content = file.readlines()

        self.assertItemsEqual(contig_file_content, expect_contig_file_content)

    def test_MetagenomeFileUtil_get_contig_string(self):
        target_contig_id = 'NODE_1_length_28553_cov_19.031240'
        contig_string = self.binned_contig_builder._get_contig_string(target_contig_id,
                                                                      self.assembly_fasta_file_path)

        expect_contig_string = '>NODE_1_length_28553_cov_19.031240\n'
        expect_contig_string += 'TCGGCGTCACAAAACTCGGAATCGTCGGACAGGAACAGTTCGCTGACGGTAAGTTATAAGGGAGACTCTC\n'
        expect_contig_string += 'TCTTTAGGAATATTTGCTTAAAGAGAGAGCCACCTTGAGGGCAGGTTAAAGAAAAGCATATTTATTTTGT\n'

        self.assertEquals(contig_string, expect_contig_string)

        target_contig_id = 'NODE_9_length_4254_cov_19.036436'
        contig_string = self.binned_contig_builder._get_contig_string(target_contig_id,
                                                                      self.assembly_fasta_file_path)

        expect_contig_string = '>NODE_9_length_4254_cov_19.036436\n'
        expect_contig_string += 'ACAAAGTACAACCCTCACGTGCCACTCTCAGGGCTTAACTGACGACACGCCGTAATAGTATTTATTGGTT\n'
        expect_contig_string += 'CACAGAAGGGTTGTACATCGGGTTAGATTATGAAAAAG\n'

        self.assertEquals(contig_string, expect_contig_string)

    def test_MetagenomeFileUtil_pack_file_to_shock(self):
        result_files = [self.assembly_fasta_file_path, self.assembly_fasta_file_path]

        shock_id = self.binned_contig_builder._pack_file_to_shock(result_files)

        output_directory = os.path.join(self.scratch, 'test_pack_file_to_shock')
        os.makedirs(output_directory)
        shock_to_file_params = {
            'shock_id': shock_id,
            'file_path': output_directory
        }
        result_file = self.dfu.shock_to_file(shock_to_file_params).get('file_path')

        expect_files = [self.assembly_filename, self.assembly_filename]
        with zipfile.ZipFile(result_file) as z:
            self.assertEqual(set(z.namelist()), set(expect_files))

    def test_file_to_binned_contigs(self):

        binned_contig_name = 'MyBinnedContig'
        params = {
            'assembly_ref': self.assembly_ref,
            'file_directory': self.test_directory_path,
            'binned_contig_name': binned_contig_name,
            'workspace_name': self.dfu.ws_name_to_id(self.getWsName())
        }

        resultVal = self.getImpl().file_to_binned_contigs(self.getContext(), params)[0]
        self.assertTrue('binned_contig_obj_ref' in resultVal)

        binned_contig_object = self.dfu.get_objects(
                        {'object_refs': [self.getWsName() + '/MyBinnedContig']})['data'][0]

        binned_contig_info = binned_contig_object.get('info')

        self.assertEquals(binned_contig_info[1], binned_contig_name)
        expect_binned_contig_info_list = ['assembly_ref', 'total_contig_len', 'n_bins']
        self.assertItemsEqual(binned_contig_info[-1], expect_binned_contig_info_list)
        self.assertEquals(int(binned_contig_info[-1].get('n_bins')), 3)
        self.assertEquals(binned_contig_info[-1].get('assembly_ref'), self.assembly_ref)
        self.assertEquals(int(binned_contig_info[-1].get('total_contig_len')), 8397583)

        binned_contig_data = binned_contig_object.get('data')
        epxect_binned_contig_keys = ['total_contig_len', 'assembly_ref', 'bins']
        self.assertItemsEqual(binned_contig_data.keys(), epxect_binned_contig_keys)
        self.assertEquals(binned_contig_data.get('total_contig_len'), 8397583)
        self.assertEquals(binned_contig_data.get('assembly_ref'), self.assembly_ref)

        expect_bin_keys = ['contigs', 'bid', 'gc', 'sum_contig_len', 'cov']
        self.assertItemsEqual(binned_contig_data.get('bins')[0].keys(), expect_bin_keys)

    def test_binned_contigs_to_file(self):

        assembly_filename = '20x.fna'
        assembly_fasta_file_path = os.path.join(self.scratch, assembly_filename)
        shutil.copy(os.path.join("Data", assembly_filename), assembly_fasta_file_path)

        assembly_params = {
            'file': {'path': assembly_fasta_file_path},
            'workspace_name': self.ws_info[1],
            'assembly_name': 'MyAssembly'
        }
        assembly_ref = self.au.save_assembly_from_fasta(assembly_params)

        binned_contig_name = 'MyBinnedContig'
        params = {
            'assembly_ref': assembly_ref,
            'file_directory': self.test_directory_path,
            'binned_contig_name': binned_contig_name,
            'workspace_name': self.dfu.ws_name_to_id(self.getWsName())
        }

        resultVal = self.getImpl().file_to_binned_contigs(self.getContext(), params)[0]
        binned_contig_obj_ref = resultVal.get('binned_contig_obj_ref')

        params = {
            'input_ref': binned_contig_obj_ref
        }
        resultVal = self.getImpl().binned_contigs_to_file(self.getContext(), params)[0]
        self.assertTrue('shock_id' in resultVal)

        output_directory = os.path.join(self.scratch, 'test_binned_contigs_to_file')
        os.makedirs(output_directory)
        shock_to_file_params = {
            'shock_id': resultVal.get('shock_id'),
            'file_path': output_directory
        }
        result_file = self.dfu.shock_to_file(shock_to_file_params).get('file_path')

        expect_files = ['out_header.001.fasta', 'out_header.002.fasta', 'out_header.003.fasta']
        with zipfile.ZipFile(result_file) as z:
            self.assertEqual(set(z.namelist()), set(expect_files))
            for filename in z.namelist():
                data = z.read(filename)
                with open(os.path.join(self.test_directory_path, filename), 'r') as origin_file:
                    self.assertEqual(data.replace('\n', ''), origin_file.read().replace('\n', ''))

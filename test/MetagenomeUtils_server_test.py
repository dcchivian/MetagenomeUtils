# -*- coding: utf-8 -*-
import os  # noqa: F401
import shutil
import time
import unittest
import zipfile
from configparser import ConfigParser
from os import environ
from pprint import pprint  # noqa: F401
import json

from Bio import SeqIO

from MetagenomeUtils.MetagenomeUtilsImpl import MetagenomeUtils
from MetagenomeUtils.MetagenomeUtilsServer import MethodContext
from MetagenomeUtils.Utils.MetagenomeFileUtils import MetagenomeFileUtils
from MetagenomeUtils.authclient import KBaseAuth as _KBaseAuth
from installed_clients.AssemblyUtilClient import AssemblyUtil
from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.WorkspaceClient import Workspace as workspaceService
from installed_clients.WsLargeDataIOClient import WsLargeDataIO


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

        # building small Assembly
        cls.assembly_filename = 'small_bin_contig_file.fasta'
        cls.assembly_fasta_file_path = os.path.join(cls.scratch, cls.assembly_filename)
        shutil.copy(os.path.join("Data", cls.assembly_filename), cls.assembly_fasta_file_path)

        assembly_params = {
            'file': {'path': cls.assembly_fasta_file_path},
            'workspace_name': cls.ws_info[1],
            'assembly_name': 'MyAssembly'
        }
        cls.assembly_ref = cls.au.save_assembly_from_fasta(assembly_params)

        # building real Assembly
        large_assembly_filename = '20x.fna'
        large_assembly_fasta_file_path = os.path.join(cls.scratch, large_assembly_filename)
        shutil.copy(os.path.join("Data", large_assembly_filename), large_assembly_fasta_file_path)

        large_assembly_params = {
            'file': {'path': large_assembly_fasta_file_path},
            'workspace_name': cls.ws_info[1],
            'assembly_name': 'MyAssembly_Large'
        }
        cls.large_assembly_ref = cls.au.save_assembly_from_fasta(large_assembly_params)

    def getWsClient(self):
        return self.__class__.wsClient

    def getWsName(self):
        return self.ws_info[1]

    def getImpl(self):
        return self.__class__.serviceImpl

    def getContext(self):
        return self.__class__.ctx

    def test_bad_merge_bins_from_binned_contig_params(self):
        invalidate_input_params = {
            'missing_old_binned_contig_ref': 'old_binned_contig_ref',
            'bin_merges': [{'new_bin_id': 'new_bin_id',
                            'bin_to_merge': ['bin_id_1', 'bin_id_2']}],
            'output_binned_contig_name': 'output_binned_contig_name',
            'workspace_name': 'workspace_name'
        }
        with self.assertRaisesRegex(
                ValueError, '"old_binned_contig_ref" parameter is required, but missing'):
            self.getImpl().merge_bins_from_binned_contig(self.getContext(),
                                                         invalidate_input_params)

        invalidate_input_params = {
            'old_binned_contig_ref': 'old_binned_contig_ref',
            'missing_bin_merges': [{'new_bin_id': 'new_bin_id',
                                    'bin_to_merge': ['bin_id_1', 'bin_id_2']}],
            'output_binned_contig_name': 'output_binned_contig_name',
            'workspace_name': 'workspace_name'
        }
        with self.assertRaisesRegex(
                ValueError, '"bin_merges" parameter is required, but missing'):
            self.getImpl().merge_bins_from_binned_contig(self.getContext(),
                                                         invalidate_input_params)

        invalidate_input_params = {
            'old_binned_contig_ref': 'old_binned_contig_ref',
            'bin_merges': [{'new_bin_id': 'new_bin_id',
                            'bin_to_merge': ['bin_id_1', 'bin_id_2']}],
            'missing_output_binned_contig_name': 'output_binned_contig_name',
            'workspace_name': 'workspace_name'
        }
        with self.assertRaisesRegex(
                ValueError, '"output_binned_contig_name" parameter is required, but missing'):
            self.getImpl().merge_bins_from_binned_contig(self.getContext(),
                                                         invalidate_input_params)

        invalidate_input_params = {
            'old_binned_contig_ref': 'old_binned_contig_ref',
            'bin_merges': [{'new_bin_id': 'new_bin_id',
                            'bin_to_merge': ['bin_id_1', 'bin_id_2']}],
            'output_binned_contig_name': 'output_binned_contig_name',
            'missing_workspace_name': 'workspace_name'
        }
        with self.assertRaisesRegex(
                ValueError, '"workspace_name" parameter is required, but missing'):
            self.getImpl().merge_bins_from_binned_contig(self.getContext(),
                                                         invalidate_input_params)

        invalidate_input_params = {
            'old_binned_contig_ref': 'old_binned_contig_ref',
            'bin_merges': 'not a list',
            'output_binned_contig_name': 'output_binned_contig_name',
            'workspace_name': 'workspace_name'
        }
        with self.assertRaisesRegex(
               ValueError,
               "expecting a list for bin_merges param, but getting a \[\<class 'str'\>\]"):
            self.getImpl().merge_bins_from_binned_contig(self.getContext(),
                                                         invalidate_input_params)

        invalidate_input_params = {
            'old_binned_contig_ref': 'old_binned_contig_ref',
            'bin_merges': [{'missing_new_bin_id': 'new_bin_id',
                            'bin_to_merge': ['bin_id_1', 'bin_id_2']}],
            'output_binned_contig_name': 'output_binned_contig_name',
            'workspace_name': 'workspace_name'
        }
        with self.assertRaisesRegex(
                ValueError, '"new_bin_id" key is required in bin_merges, but missing'):
            self.getImpl().merge_bins_from_binned_contig(self.getContext(),
                                                         invalidate_input_params)

        invalidate_input_params = {
            'old_binned_contig_ref': 'old_binned_contig_ref',
            'bin_merges': [{'new_bin_id': 'new_bin_id',
                            'missing_bin_to_merge': ['bin_id_1', 'bin_id_2']}],
            'output_binned_contig_name': 'output_binned_contig_name',
            'workspace_name': 'workspace_name'
        }
        with self.assertRaisesRegex(
                ValueError, '"bin_to_merge" key is required in bin_merges, but missing'):
            self.getImpl().merge_bins_from_binned_contig(self.getContext(),
                                                         invalidate_input_params)

        invalidate_input_params = {
            'old_binned_contig_ref': 'old_binned_contig_ref',
            'bin_merges': [{'new_bin_id': 'new_bin_id',
                            'bin_to_merge': 'not a list'}],
            'output_binned_contig_name': 'output_binned_contig_name',
            'workspace_name': 'workspace_name'
        }
        with self.assertRaisesRegex(
               ValueError,
               "expecting a list for bin_to_merge, but getting a \[\<class 'str'\>\]"):
            self.getImpl().merge_bins_from_binned_contig(self.getContext(),
                                                         invalidate_input_params)

    def test_bad_remove_bins_from_binned_contig_params(self):
        invalidate_input_params = {
            'missing_old_binned_contig_ref': 'old_binned_contig_ref',
            'bins_to_remove': ['bin_id1', 'bin_id2'],
            'output_binned_contig_name': 'output_binned_contig_name',
            'workspace_name': 'workspace_name'
        }
        with self.assertRaisesRegex(
                ValueError, '"old_binned_contig_ref" parameter is required, but missing'):
            self.getImpl().remove_bins_from_binned_contig(self.getContext(),
                                                          invalidate_input_params)

        invalidate_input_params = {
            'old_binned_contig_ref': 'old_binned_contig_ref',
            'missing_bins_to_remove': ['bin_id1', 'bin_id2'],
            'output_binned_contig_name': 'output_binned_contig_name',
            'workspace_name': 'workspace_name'
        }
        with self.assertRaisesRegex(
                ValueError, '"bins_to_remove" parameter is required, but missing'):
            self.getImpl().remove_bins_from_binned_contig(self.getContext(),
                                                          invalidate_input_params)

        invalidate_input_params = {
            'old_binned_contig_ref': 'old_binned_contig_ref',
            'bins_to_remove': ['bin_id1', 'bin_id2'],
            'missing_output_binned_contig_name': 'output_binned_contig_name',
            'workspace_name': 'workspace_name'
        }
        with self.assertRaisesRegex(
                ValueError, '"output_binned_contig_name" parameter is required, but missing'):
            self.getImpl().remove_bins_from_binned_contig(self.getContext(),
                                                          invalidate_input_params)

        invalidate_input_params = {
            'old_binned_contig_ref': 'old_binned_contig_ref',
            'bins_to_remove': ['bin_id1', 'bin_id2'],
            'output_binned_contig_name': 'output_binned_contig_name',
            'missing_workspace_name': 'workspace_name'
        }
        with self.assertRaisesRegex(
                ValueError, '"workspace_name" parameter is required, but missing'):
            self.getImpl().remove_bins_from_binned_contig(self.getContext(),
                                                          invalidate_input_params)

        invalidate_input_params = {
            'old_binned_contig_ref': 'old_binned_contig_ref',
            'bins_to_remove': 'not a list',
            'output_binned_contig_name': 'output_binned_contig_name',
            'workspace_name': 'workspace_name'
        }
        with self.assertRaisesRegex(
               ValueError,
               "expecting a list for bins_to_remove param, but getting a \[\<class 'str'\>\]"):
            self.getImpl().remove_bins_from_binned_contig(self.getContext(),
                                                          invalidate_input_params)

    def test_bad_extract_binned_contigs_as_assembly_params(self):

        invalidate_input_params = {
            'missing_binned_contig_obj_ref': 'binned_contig_obj_ref',
            'extracted_assemblies': "bin_id",
            'assembly_suffix': '_assembly',
            'assembly_set_name': 'this_is_a_test',
            'workspace_name': 'workspace_name'
        }
        with self.assertRaisesRegex(
                ValueError, '"binned_contig_obj_ref" parameter is required, but missing'):
            self.getImpl().extract_binned_contigs_as_assembly(self.getContext(),
                                                              invalidate_input_params)
        invalidate_input_params = {
            'binned_contig_obj_ref': 'binned_contig_obj_ref',
            'missing_extracted_assemblies': "bin_id",
            'assembly_suffix': '_assembly',
            'assembly_set_name': 'invalid_assembly_set',
            'workspace_name': 'workspace_name'
        }
        with self.assertRaisesRegex(
                ValueError, '"extracted_assemblies" parameter is required, but missing'):
            self.getImpl().extract_binned_contigs_as_assembly(self.getContext(),
                                                              invalidate_input_params)
        invalidate_input_params = {
            'binned_contig_obj_ref': 'binned_contig_obj_ref',
            'extracted_assemblies': 'bin_id',
            'assembly_suffix': '_assembly',
            'assembly_set_name': 'invalid_assembly_set',
            'missing_workspace_name': 'workspace_name'
        }
        with self.assertRaisesRegex(
                ValueError, '"workspace_name" parameter is required, but missing'):
            self.getImpl().extract_binned_contigs_as_assembly(self.getContext(),
                                                              invalidate_input_params)

        invalidate_input_params = {
            'binned_contig_obj_ref': 'binned_contig_obj_ref',
            'extracted_assemblies': "bin_id",
            'missing_assembly_suffix': 'invalid_assembly_suffix',
            'assembly_set_name': 'invalid_assembly_set_name',
            'workspace_name': 'workspace_name'
        }
        with self.assertRaisesRegex(
                ValueError, '"assembly_suffix" parameter is required, but missing'):
            self.getImpl().extract_binned_contigs_as_assembly(self.getContext(),
                                                              invalidate_input_params)
        invalidate_input_params = {
            'binned_contig_obj_ref': 'binned_contig_obj_ref',
            'extracted_assemblies': 'bin_id1,bin_id2',
            'assembly_suffix': '_assembly',
            'missing_assembly_set_name': 'invalid_assembly_set',
            'workspace_name': 'workspace_name'
        }
        with self.assertRaisesRegex(
                ValueError,
                '"assembly_set_names" parameter is required for more than one extracted assembly'):
            self.getImpl().extract_binned_contigs_as_assembly(self.getContext(),
                                                              invalidate_input_params)

    def test_bad_binned_contigs_to_file_params(self):
        invalidate_input_params = {
            'missing_input_ref': 'input_ref'
        }
        with self.assertRaisesRegex(
                ValueError, '"input_ref" parameter is required, but missing'):
            self.getImpl().binned_contigs_to_file(self.getContext(), invalidate_input_params)

    def test_bad_export_binned_contigs_as_excel_params(self):
        invalidate_input_params = {
            'missing_input_ref': 'input_ref'
        }
        with self.assertRaisesRegex(
                ValueError, '"input_ref" parameter is required, but missing'):
            self.getImpl().export_binned_contigs_as_excel(self.getContext(),
                                                          invalidate_input_params)

    def test_bad_import_excel_as_binned_contigs_params(self):
        invalidate_input_params = {
            'missing_shock_id': 'shock_id',
            'workspace_name': 'workspace_name'
        }
        with self.assertRaisesRegex(
                ValueError, '"shock_id" parameter is required, but missing'):
            self.getImpl().import_excel_as_binned_contigs(self.getContext(),
                                                          invalidate_input_params)

        invalidate_input_params = {
            'shock_id': 'shock_id',
            'missing_workspace_name': 'workspace_name'
        }
        with self.assertRaisesRegex(
                ValueError, '"workspace_name" parameter is required, but missing'):
            self.getImpl().import_excel_as_binned_contigs(self.getContext(),
                                                          invalidate_input_params)

    def test_bad_file_to_binned_contigs_params(self):
        invalidate_input_params = {
            'missing_assembly_ref': 'assembly_ref',
            'file_directory': 'file_directory',
            'binned_contig_name': 'binned_contig_name',
            'workspace_name': 'workspace_name'

        }
        with self.assertRaisesRegex(
                ValueError, '"assembly_ref" parameter is required, but missing'):
            self.getImpl().file_to_binned_contigs(self.getContext(), invalidate_input_params)

        invalidate_input_params = {
            'assembly_ref': 'assembly_ref',
            'missing_file_directory': 'file_directory',
            'binned_contig_name': 'binned_contig_name',
            'workspace_name': 'workspace_name'

        }
        with self.assertRaisesRegex(
                ValueError, '"file_directory" parameter is required, but missing'):
            self.getImpl().file_to_binned_contigs(self.getContext(), invalidate_input_params)

        invalidate_input_params = {
            'assembly_ref': 'assembly_ref',
            'file_directory': 'file_directory',
            'missing_binned_contig_name': 'binned_contig_name',
            'workspace_name': 'workspace_name'

        }
        with self.assertRaisesRegex(
                ValueError, '"binned_contig_name" parameter is required, but missing'):
            self.getImpl().file_to_binned_contigs(self.getContext(), invalidate_input_params)

        invalidate_input_params = {
            'assembly_ref': 'assembly_ref',
            'file_directory': 'file_directory',
            'binned_contig_name': 'binned_contig_name',
            'missing_workspace_name': 'workspace_name'

        }
        with self.assertRaisesRegex(
                ValueError, '"workspace_name" parameter is required, but missing'):
            self.getImpl().file_to_binned_contigs(self.getContext(), invalidate_input_params)

    def test_MetagenomeFileUtils_get_bin_ids(self):

        file_directory = self.test_directory_path
        bin_ids = self.binned_contig_builder._get_bin_ids(file_directory)

        expect_bin_ids_set = {'out_header.001.fasta', 'out_header.002.fasta',
                              'out_header.003.fasta'}

        self.assertEqual(set(bin_ids), expect_bin_ids_set)

    def test_MetagenomeFileUtil_generate_contig_bin_summary(self):

        bin_id = 'out_header.003.fasta'
        file_directory = self.test_directory_path

        gc, sum_contig_len, cov = self.binned_contig_builder._generate_contig_bin_summary(
            bin_id,
            file_directory)

        self.assertEqual(gc, 0.548)
        self.assertEqual(sum_contig_len, 2452188)
        self.assertEqual(cov, 0.925)

        bin_id = 'out_header.001.fasta'
        file_directory = self.test_directory_path

        gc, sum_contig_len, cov = self.binned_contig_builder._generate_contig_bin_summary(
            bin_id,
            file_directory)

        self.assertEqual(gc, 0.529)
        self.assertEqual(sum_contig_len, 2674902)
        self.assertEqual(cov, 1)

    def test_MetagenomeFileUtil_generate_contigs(self):

        ws_large_data = WsLargeDataIO(self.callback_url, service_ver="beta")
        res = ws_large_data.get_objects({'objects': [{"ref": self.assembly_ref}]})['data'][0]
        data = json.load(open(res['data_json_file']))
        assembly_contigs = data.get('contigs')
        # testing contigs can be found in assembly object
        contigs = self.binned_contig_builder._generate_contigs(
            self.assembly_filename,
            os.path.dirname(self.assembly_fasta_file_path),
            assembly_contigs)

        self.assertEqual(len(contigs), 8)

        expect_keys = ['NODE_1_length_28553_cov_19.031240', 'NODE_2_length_14959_cov_18.663614',
                       'NODE_3_length_165496_cov_18.840721', 'NODE_4_length_21162_cov_19.108355',
                       'NODE_5_length_52980_cov_18.578840', 'NODE_7_length_59665_cov_19.042957',
                       'NODE_8_length_44057_cov_18.808838', 'NODE_9_length_4254_cov_19.036436']

        self.assertEqual(set(contigs.keys()), set(expect_keys))

        expect_keys = ['gc', 'len']
        self.assertEqual(set(contigs.get('NODE_8_length_44057_cov_18.808838').keys()),
                         set(expect_keys))

        # testing contigs not in assembly object
        assembly_filename = 'small_bin_contig_file.fasta'
        assembly_fasta_file_path = os.path.join(self.scratch, 'fake_' + assembly_filename)
        shutil.copy(os.path.join("Data", assembly_filename), assembly_fasta_file_path)

        contig_string = '>test_contig_id\nTTAACCGG\nTTAACCGGTTAACCGG\n'
        with open(assembly_fasta_file_path, 'a') as file:
            file.write(contig_string)

        contigs = self.binned_contig_builder._generate_contigs(
            'fake_' + assembly_filename,
            os.path.dirname(assembly_fasta_file_path),
            assembly_contigs)

        self.assertEqual(len(contigs), 9)

        expect_keys = ['NODE_1_length_28553_cov_19.031240', 'NODE_2_length_14959_cov_18.663614',
                       'NODE_3_length_165496_cov_18.840721', 'NODE_4_length_21162_cov_19.108355',
                       'NODE_5_length_52980_cov_18.578840', 'NODE_7_length_59665_cov_19.042957',
                       'NODE_8_length_44057_cov_18.808838', 'NODE_9_length_4254_cov_19.036436',
                       'test_contig_id']
        self.assertEqual(set(contigs.keys()), set(expect_keys))

        expect_dic = {'gc': 0.5, 'len': 24}
        self.assertDictEqual(contigs.get('test_contig_id'), expect_dic)

    def test_MetagenomeFileUtil_generate_contig_bin(self):
        bin_id = 'out_header.003.fasta'
        file_directory = self.test_directory_path

        ws_large_data = WsLargeDataIO(self.callback_url, service_ver="beta")
        res = ws_large_data.get_objects({'objects': [{"ref": self.large_assembly_ref}]})['data'][0]
        data = json.load(open(res['data_json_file']))
        assembly_contigs = data.get('contigs')

        contig_bin = self.binned_contig_builder._generate_contig_bin(bin_id,
                                                                     file_directory,
                                                                     assembly_contigs)

        expect_bin_keys = ['contigs', 'bid', 'gc', 'sum_contig_len', 'cov', 'n_contigs']
        self.assertCountEqual(list(contig_bin.keys()), expect_bin_keys)
        self.assertEqual(contig_bin.get('bid'), bin_id)
        self.assertEqual(contig_bin.get('gc'), 0.548)
        self.assertEqual(contig_bin.get('sum_contig_len'), 2452188)
        self.assertEqual(contig_bin.get('cov'), 0.925)
        self.assertEqual(contig_bin.get('n_contigs'), 472)

    def test_MetagenomeFileUtil_get_contig_file(self):
        contig_file = self.binned_contig_builder._get_contig_file(self.assembly_ref)

        with open(contig_file, 'r') as file:
            contig_file_content = file.readlines()

        with open(self.assembly_fasta_file_path, 'r') as file:
            expect_contig_file_content = file.readlines()

        self.assertCountEqual(contig_file_content, expect_contig_file_content)

    def test_MetagenomeFileUtil_get_contig_string(self):
        target_contig_id = 'NODE_1_length_28553_cov_19.031240'
        parsed_assembly = SeqIO.to_dict(SeqIO.parse(self.assembly_fasta_file_path, "fasta"))
        contig_string = self.binned_contig_builder._get_contig_string(
                                                                target_contig_id,
                                                                self.assembly_fasta_file_path,
                                                                parsed_assembly)

        expect_contig_string = '>NODE_1_length_28553_cov_19.031240\n'
        expect_contig_string += 'TCGGCGTCACAAAACTCGGAATCGTCGGACAGGAACAGTTCGCTGACGGTAAGTTATAAGGG'
        expect_contig_string += 'AGACTCTCTCTTTAGGAATATTTGCTTAAAGAGAGAGCCACCTTGAGGGCAGGTTAAAGAAA'
        expect_contig_string += 'AGCATATTTATTTTGT\n'

        self.assertEqual(contig_string, expect_contig_string)

        target_contig_id = 'NODE_9_length_4254_cov_19.036436'
        contig_string = self.binned_contig_builder._get_contig_string(
                                                                target_contig_id,
                                                                self.assembly_fasta_file_path,
                                                                parsed_assembly)

        expect_contig_string = '>NODE_9_length_4254_cov_19.036436\n'
        expect_contig_string += 'ACAAAGTACAACCCTCACGTGCCACTCTCAGGGCTTAACTGACGACACGCCGTAATAGTA'
        expect_contig_string += 'TTTATTGGTTCACAGAAGGGTTGTACATCGGGTTAGATTATGAAAAAG\n'

        self.assertEqual(contig_string, expect_contig_string)

        target_contig_id = 'fake_id'
        with self.assertRaisesRegex(
                ValueError,
                'Cannot find contig \[fake_id\] from file \[{}\].'.format(
                    self.assembly_fasta_file_path)):
            self.binned_contig_builder._get_contig_string(target_contig_id,
                                                          self.assembly_fasta_file_path,
                                                          parsed_assembly)

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

    def test_MetagenomeFileUtil_download_file_from_shock(self):

        binned_contigs_file_name = 'MyBinnedContig.xlsx'
        binned_contigs_file_path = os.path.join(self.scratch, binned_contigs_file_name)
        shutil.copy(os.path.join("Data", binned_contigs_file_name), binned_contigs_file_path)

        shock_id = self.dfu.file_to_shock({'file_path': binned_contigs_file_path}).get('shock_id')

        file_path, file_name = self.binned_contig_builder._download_file_from_shock(shock_id)

        self.assertEqual(binned_contigs_file_name, file_name)
        self.assertEqual(binned_contigs_file_name, os.path.basename(file_path))

    def test_MetagenomeFileUtil_merge_bins(self):
        new_bin_id = 'MyNewBin_ID'
        bin_objects_to_merge = []

        bin_object_1_to_merge = {
            'bid': 'Bin_1',
            'contigs': {
                'contig_1': {
                    'gc': 0.5,
                    'len': 10
                },
                'contig_2': {
                    'gc': 0.5,
                    'len': 2
                }
            },
            'n_contigs': 2,
            'gc': 0.5,
            'sum_contig_len': 12,
            'cov': 0.8
        }

        bin_object_2_to_merge = {
            'bid': 'Bin_1',
            'contigs': {
                'contig_3': {
                    'gc': 0.5,
                    'len': 6
                }
            },
            'n_contigs': 1,
            'gc': 0.5,
            'sum_contig_len': 6,
            'cov': 0.5
        }

        bin_objects_to_merge.append(bin_object_1_to_merge)
        bin_objects_to_merge.append(bin_object_2_to_merge)

        new_contig_bin = self.binned_contig_builder._merge_bins(new_bin_id, bin_objects_to_merge)

        expect_new_contig_bin = {
            'bid': new_bin_id,
            'contigs': {
                'contig_1': {
                    'gc': 0.5,
                    'len': 10
                },
                'contig_2': {
                    'gc': 0.5,
                    'len': 2
                },
                'contig_3': {
                    'gc': 0.5,
                    'len': 6
                }
            },
            'n_contigs': 3,
            'gc': 0.5,
            'sum_contig_len': 18,
            'cov': 0.7
        }

        self.assertDictEqual(expect_new_contig_bin, new_contig_bin)

    def test_file_to_binned_contigs(self):

        binned_contig_name = 'MyBinnedContig'
        params = {
            'assembly_ref': self.large_assembly_ref,
            'file_directory': self.test_directory_path,
            'binned_contig_name': binned_contig_name,
            'workspace_name': self.dfu.ws_name_to_id(self.getWsName())
        }

        resultVal = self.getImpl().file_to_binned_contigs(self.getContext(), params)[0]
        self.assertTrue('binned_contig_obj_ref' in resultVal)

        binned_contig_object = self.dfu.get_objects(
            {'object_refs': [self.getWsName() + '/MyBinnedContig']})['data'][0]

        binned_contig_info = binned_contig_object.get('info')

        self.assertEqual(binned_contig_info[1], binned_contig_name)
        expect_binned_contig_info_list = ['assembly_ref', 'total_contig_len', 'n_bins']
        self.assertCountEqual(binned_contig_info[-1], expect_binned_contig_info_list)
        self.assertEqual(int(binned_contig_info[-1].get('n_bins')), 3)
        self.assertEqual(binned_contig_info[-1].get('assembly_ref'), self.large_assembly_ref)
        self.assertEqual(int(binned_contig_info[-1].get('total_contig_len')), 8397583)

        binned_contig_data = binned_contig_object.get('data')
        epxect_binned_contig_keys = ['total_contig_len', 'assembly_ref', 'bins']
        self.assertCountEqual(binned_contig_data.keys(), epxect_binned_contig_keys)
        self.assertEqual(binned_contig_data.get('total_contig_len'), 8397583)
        self.assertEqual(binned_contig_data.get('assembly_ref'), self.large_assembly_ref)

        expect_bin_keys = ['contigs', 'bid', 'gc', 'sum_contig_len', 'cov', 'n_contigs']
        self.assertCountEqual(list(binned_contig_data.get('bins')[0].keys()), expect_bin_keys)

    def test_binned_contigs_to_file(self):

        binned_contig_name = 'MyBinnedContig'
        params = {
            'assembly_ref': self.large_assembly_ref,
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
                    self.assertEqual(''.join(sorted(data.decode().replace('\n', ''))),
                                     ''.join(sorted(origin_file.read().replace('\n', ''))))

    def test_binned_contigs_to_file_save_to_shock(self):

        binned_contig_name = 'MyBinnedContig'
        params = {
            'assembly_ref': self.large_assembly_ref,
            'file_directory': self.test_directory_path,
            'binned_contig_name': binned_contig_name,
            'workspace_name': self.dfu.ws_name_to_id(self.getWsName())
        }

        resultVal = self.getImpl().file_to_binned_contigs(self.getContext(), params)[0]
        binned_contig_obj_ref = resultVal.get('binned_contig_obj_ref')

        params = {
            'input_ref': binned_contig_obj_ref,
            'save_to_shock': False
        }
        resultVal = self.getImpl().binned_contigs_to_file(self.getContext(), params)[0]
        self.assertTrue('shock_id' in resultVal)
        self.assertTrue('bin_file_directory' in resultVal)

        self.assertIsNone(resultVal.get('shock_id'))

        bin_file_directory = resultVal.get('bin_file_directory')
        bin_files = os.listdir(bin_file_directory)
        self.assertEqual(len(bin_files), 3)

        expect_files = ['out_header.001.fasta', 'out_header.002.fasta', 'out_header.003.fasta']
        self.assertCountEqual(list(map(os.path.basename, bin_files)), expect_files)

    def test_export_binned_contigs_as_excel(self):

        binned_contig_name = 'MyBinnedContig'
        params = {
            'assembly_ref': self.large_assembly_ref,
            'file_directory': self.test_directory_path,
            'binned_contig_name': binned_contig_name,
            'workspace_name': self.dfu.ws_name_to_id(self.getWsName())
        }

        resultVal = self.getImpl().file_to_binned_contigs(self.getContext(), params)[0]
        binned_contig_obj_ref = resultVal.get('binned_contig_obj_ref')

        params = {
            'input_ref': binned_contig_obj_ref
        }
        resultVal = self.getImpl().export_binned_contigs_as_excel(self.getContext(), params)[0]
        self.assertTrue('shock_id' in resultVal)

        output_directory = os.path.join(self.scratch, 'test_export_binned_contigs_as_excel')
        os.makedirs(output_directory)
        shock_to_file_params = {
            'shock_id': resultVal.get('shock_id'),
            'file_path': output_directory
        }
        result_file = self.dfu.shock_to_file(shock_to_file_params).get('file_path')

        print('original_result_file: ' + resultVal.get('bin_file_directory'))
        print('shock_result_file: ' + result_file)

        expect_files = [binned_contig_name + '.xlsx']
        with zipfile.ZipFile(result_file) as z:
            self.assertEqual(set(z.namelist()), set(expect_files))

    def test_import_excel_as_binned_contigs(self):
        binned_contigs_file_name = 'MyBinnedContig.xlsx'
        binned_contigs_file_path = os.path.join(self.scratch, binned_contigs_file_name)
        shutil.copy(os.path.join("Data", binned_contigs_file_name), binned_contigs_file_path)

        shock_id = self.dfu.file_to_shock({'file_path': binned_contigs_file_path}).get('shock_id')

        params = {
            'shock_id': shock_id,
            'workspace_name': self.getWsName()
        }

        resultVal = self.getImpl().import_excel_as_binned_contigs(self.getContext(), params)[0]
        self.assertTrue('binned_contigs_ref' in resultVal)
        binned_contigs_ref = resultVal['binned_contigs_ref']

        binned_contig_data = self.dfu.get_objects({'object_refs':
                                                  [binned_contigs_ref]})['data'][0]['data']

        # self.assertEquals(binned_contig_data.get('assembly_ref'), '16106/2/1')
        self.assertEqual(len(binned_contig_data.get('bins')), 3)
        self.assertEqual(binned_contig_data.get('total_contig_len'), 6116280)

    def test_extract_binned_contigs_as_assembly(self):

        binned_contig_name = 'MyBinnedContig'
        params = {
            'assembly_ref': self.large_assembly_ref,
            'file_directory': self.test_directory_path,
            'binned_contig_name': binned_contig_name,
            'workspace_name': self.getWsName()
        }

        resultVal = self.getImpl().file_to_binned_contigs(self.getContext(), params)[0]
        binned_contig_obj_ref = resultVal.get('binned_contig_obj_ref')

        params = {
            'binned_contig_obj_ref': binned_contig_obj_ref,
            'extracted_assemblies': 'out_header.001.fasta,out_header.002.fasta',
            'assembly_suffix': '_assembly',
            'assembly_set_name': 'test2_assembly_set',
            'workspace_name': self.getWsName()
        }

        resultVal = self.getImpl().extract_binned_contigs_as_assembly(self.getContext(),
                                                                      params)[0]

        self.assertTrue('assembly_ref_list' in resultVal)
        self.assertTrue('report_name' in resultVal)
        self.assertTrue('report_ref' in resultVal)
        self.assertTrue('assembly_set_ref' in resultVal)

        # check report object for presence of created_objects
        report_object = self.dfu.get_objects(
                           {'object_refs': [resultVal.get('report_ref')]})['data'][0]['data']
        self.assertTrue('objects_created' in report_object)

        invalidate_input_params = {
            'binned_contig_obj_ref': binned_contig_obj_ref,
            'extracted_assemblies': 'nonexisting_bin_id',
            'assembly_suffix': '_assembly',
            'assembly_set_name': 'test3_assembly_set',
            'workspace_name': self.getWsName()
        }
        with self.assertRaisesRegex(
               ValueError,
               'bin_id \[nonexisting_bin_id\] cannot be found in BinnedContig \[{}\]'.format(
                  binned_contig_obj_ref)):
            self.getImpl().extract_binned_contigs_as_assembly(self.getContext(),
                                                              invalidate_input_params)

    def test_empty_extract_binned_contigs_as_assembly(self):

        binned_contig_name = 'MyBinnedContig'
        params = {
            'assembly_ref': self.large_assembly_ref,
            'file_directory': self.test_directory_path,
            'binned_contig_name': binned_contig_name,
            'assembly_set_name': 'empty_assembly_set',
            'workspace_name': self.getWsName()
        }

        resultVal = self.getImpl().file_to_binned_contigs(self.getContext(), params)[0]
        binned_contig_obj_ref = resultVal.get('binned_contig_obj_ref')

        params = {
            'binned_contig_obj_ref': binned_contig_obj_ref,
            'extracted_assemblies':  "",
            'assembly_suffix':       '_assembly',
            'assembly_set_name':     'another_empty_assembly_set',
            'workspace_name':         self.getWsName()
        }

        resultVal = self.getImpl().extract_binned_contigs_as_assembly(self.getContext(),
                                                                      params)[0]

        self.assertTrue('assembly_ref_list' in resultVal)
        self.assertTrue('report_name' in resultVal)
        self.assertTrue('report_ref' in resultVal)
        self.assertTrue('assembly_set_ref' in resultVal)  # assumes my binned contig has >1 bins

        # also test for replacement with default name if assembly_set_name is ''
        params = {
            'binned_contig_obj_ref': binned_contig_obj_ref,
            'extracted_assemblies':  "",
            'assembly_suffix':       '_assembly',
            'assembly_set_name':     '',
            'workspace_name':         self.getWsName()
        }

        resultVal = self.getImpl().extract_binned_contigs_as_assembly(self.getContext(),
                                                                      params)[0]

        self.assertTrue('assembly_ref_list' in resultVal)
        self.assertTrue('report_name' in resultVal)
        self.assertTrue('report_ref' in resultVal)
        self.assertTrue('assembly_set_ref' in resultVal)  # assumes my binned contig has >1 bins

        pprint(resultVal.get('assembly_set_ref'))
        aso = self.dfu.get_objects(
                            {'object_refs': [resultVal.get('assembly_set_ref')]})['data'][0]
        aso_name = aso.get('info')[1]
        self.assertEqual(aso_name, 'extracted_bins.AssemblySet')

    def test_remove_bins_from_binned_contig_single_bin(self):

        binned_contig_name = 'MyBinnedContig'
        params = {
            'assembly_ref': self.large_assembly_ref,
            'file_directory': self.test_directory_path,
            'binned_contig_name': binned_contig_name,
            'workspace_name': self.dfu.ws_name_to_id(self.getWsName())
        }

        resultVal = self.getImpl().file_to_binned_contigs(self.getContext(), params)[0]
        old_binned_contig_ref = resultVal.get('binned_contig_obj_ref')

        output_binned_contig_name = 'MyNewBinnedContig'
        remove_bins_params = {
            'old_binned_contig_ref': old_binned_contig_ref,
            'bins_to_remove': ['out_header.002.fasta'],
            'output_binned_contig_name': output_binned_contig_name,
            'workspace_name': self.getWsName()
        }

        resultVal = self.getImpl().remove_bins_from_binned_contig(self.getContext(),
                                                                  remove_bins_params)[0]

        self.assertTrue('new_binned_contig_ref' in resultVal)

        binned_contig_object = self.dfu.get_objects(
            {'object_refs': [self.getWsName() + '/' + output_binned_contig_name]})['data'][0]

        binned_contig_info = binned_contig_object.get('info')

        self.assertEqual(binned_contig_info[1], output_binned_contig_name)
        expect_binned_contig_info_list = ['assembly_ref', 'total_contig_len', 'n_bins']
        self.assertCountEqual(binned_contig_info[-1], expect_binned_contig_info_list)
        self.assertEqual(int(binned_contig_info[-1].get('n_bins')), 2)
        self.assertEqual(binned_contig_info[-1].get('assembly_ref'), self.large_assembly_ref)
        self.assertEqual(int(binned_contig_info[-1].get('total_contig_len')), 5127090)

        binned_contig_data = binned_contig_object.get('data')
        epxect_binned_contig_keys = ['total_contig_len', 'assembly_ref', 'bins']
        self.assertCountEqual(binned_contig_data.keys(), epxect_binned_contig_keys)
        self.assertEqual(binned_contig_data.get('total_contig_len'), 5127090)
        self.assertEqual(binned_contig_data.get('assembly_ref'), self.large_assembly_ref)

        bins = binned_contig_data.get('bins')
        bin_ids = [item.get('bid') for item in bins]
        expect_bin_ids = ['out_header.001.fasta', 'out_header.003.fasta']
        self.assertCountEqual(bin_ids, expect_bin_ids)

    def test_remove_bins_from_binned_contig_multiple_bins(self):

        binned_contig_name = 'MyBinnedContig'
        params = {
            'assembly_ref': self.large_assembly_ref,
            'file_directory': self.test_directory_path,
            'binned_contig_name': binned_contig_name,
            'workspace_name': self.dfu.ws_name_to_id(self.getWsName())
        }

        resultVal = self.getImpl().file_to_binned_contigs(self.getContext(), params)[0]
        old_binned_contig_ref = resultVal.get('binned_contig_obj_ref')

        output_binned_contig_name = 'MyNewBinnedContig'
        remove_bins_params = {
            'old_binned_contig_ref': old_binned_contig_ref,
            'bins_to_remove': ['out_header.001.fasta', 'out_header.003.fasta'],
            'output_binned_contig_name': output_binned_contig_name,
            'workspace_name': self.getWsName()
        }

        resultVal = self.getImpl().remove_bins_from_binned_contig(self.getContext(),
                                                                  remove_bins_params)[0]

        self.assertTrue('new_binned_contig_ref' in resultVal)

        binned_contig_object = self.dfu.get_objects(
            {'object_refs': [self.getWsName() + '/' + output_binned_contig_name]})['data'][0]

        binned_contig_info = binned_contig_object.get('info')

        self.assertEqual(binned_contig_info[1], output_binned_contig_name)
        expect_binned_contig_info_list = ['assembly_ref', 'total_contig_len', 'n_bins']
        self.assertCountEqual(binned_contig_info[-1], expect_binned_contig_info_list)
        self.assertEqual(int(binned_contig_info[-1].get('n_bins')), 1)
        self.assertEqual(binned_contig_info[-1].get('assembly_ref'), self.large_assembly_ref)
        self.assertEqual(int(binned_contig_info[-1].get('total_contig_len')), 3270493)

        binned_contig_data = binned_contig_object.get('data')
        epxect_binned_contig_keys = ['total_contig_len', 'assembly_ref', 'bins']
        self.assertCountEqual(binned_contig_data.keys(), epxect_binned_contig_keys)
        self.assertEqual(binned_contig_data.get('total_contig_len'), 3270493)
        self.assertEqual(binned_contig_data.get('assembly_ref'), self.large_assembly_ref)

        bins = binned_contig_data.get('bins')
        bin_ids = [item.get('bid') for item in bins]
        expect_bin_ids = ['out_header.002.fasta']
        self.assertCountEqual(bin_ids, expect_bin_ids)

    def test_merge_bins_from_binned_contig(self):

        binned_contig_name = 'MyBinnedContig'
        params = {
            'assembly_ref': self.large_assembly_ref,
            'file_directory': self.test_directory_path,
            'binned_contig_name': binned_contig_name,
            'workspace_name': self.dfu.ws_name_to_id(self.getWsName())
        }

        resultVal = self.getImpl().file_to_binned_contigs(self.getContext(), params)[0]
        old_binned_contig_ref = resultVal.get('binned_contig_obj_ref')

        output_binned_contig_name = 'MyNewBinnedContig'

        merge_bins_params = {
            'old_binned_contig_ref': old_binned_contig_ref,
            'bin_merges': [{
                'new_bin_id': 'out_header.004.fasta',
                'bin_to_merge': ['nonexisting_bin_id', 'out_header.003.fasta']
            }],
            'output_binned_contig_name': output_binned_contig_name,
            'workspace_name': self.getWsName()
        }
        with self.assertRaisesRegex(
                ValueError,
                "bin_id: \[nonexisting_bin_id\] is not listed in BinnedContig object"):
            self.getImpl().merge_bins_from_binned_contig(self.getContext(),
                                                         merge_bins_params)

        merge_bins_params = {
            'old_binned_contig_ref': old_binned_contig_ref,
            'bin_merges': [{
                'new_bin_id': 'out_header.004.fasta',
                'bin_to_merge': ['out_header.003.fasta']
            }],
            'output_binned_contig_name': output_binned_contig_name,
            'workspace_name': self.getWsName()
        }
        with self.assertRaisesRegex(
               ValueError,
               "Please provide at least two bin_ids to merge"):
            self.getImpl().merge_bins_from_binned_contig(self.getContext(),
                                                         merge_bins_params)

        merge_bins_params = {
            'old_binned_contig_ref': old_binned_contig_ref,
            'bin_merges': [
                {
                    'new_bin_id': 'out_header.004.fasta',
                    'bin_to_merge': ['out_header.002.fasta', 'out_header.003.fasta']},
                {
                    'new_bin_id': 'out_header.005.fasta',
                    'bin_to_merge': ['out_header.001.fasta', 'out_header.003.fasta']
                }],
            'output_binned_contig_name': output_binned_contig_name,
            'workspace_name': self.getWsName()
        }
        with self.assertRaisesRegex(
               ValueError,
               "Same bin \[out_header.003.fasta\] appears in multiple merges"):
            self.getImpl().merge_bins_from_binned_contig(self.getContext(),
                                                         merge_bins_params)

        merge_bins_params = {
            'old_binned_contig_ref': old_binned_contig_ref,
            'bin_merges': [
                {
                    'new_bin_id': 'out_header.004.fasta',
                    'bin_to_merge': ['out_header.002.fasta', 'out_header.003.fasta']},
                {
                    'new_bin_id': 'out_header.004.fasta',
                    'bin_to_merge': ['out_header.001.fasta', 'out_header.004.fasta']
                }],
            'output_binned_contig_name': output_binned_contig_name,
            'workspace_name': self.getWsName()
        }
        with self.assertRaisesRegex(
                ValueError,
                "Same new Bin ID \[out_header.004.fasta\] appears in multiple merges"):
            self.getImpl().merge_bins_from_binned_contig(self.getContext(),
                                                         merge_bins_params)

        merge_bins_params = {
            'old_binned_contig_ref': old_binned_contig_ref,
            'bin_merges': [{
                'new_bin_id': 'out_header.004.fasta',
                'bin_to_merge': ['out_header.002.fasta', 'out_header.003.fasta']
            }],
            'output_binned_contig_name': output_binned_contig_name,
            'workspace_name': self.getWsName()
        }

        resultVal = self.getImpl().merge_bins_from_binned_contig(self.getContext(),
                                                                 merge_bins_params)[0]

        self.assertTrue('new_binned_contig_ref' in resultVal)

        binned_contig_object = self.dfu.get_objects(
            {'object_refs': [self.getWsName() + '/' + output_binned_contig_name]})['data'][0]

        binned_contig_info = binned_contig_object.get('info')

        self.assertEqual(binned_contig_info[1], output_binned_contig_name)
        expect_binned_contig_info_list = ['assembly_ref', 'total_contig_len', 'n_bins']
        self.assertCountEqual(binned_contig_info[-1], expect_binned_contig_info_list)
        self.assertEqual(int(binned_contig_info[-1].get('n_bins')), 2)
        self.assertEqual(binned_contig_info[-1].get('assembly_ref'), self.large_assembly_ref)
        self.assertEqual(int(binned_contig_info[-1].get('total_contig_len')), 8397583)

        binned_contig_data = binned_contig_object.get('data')
        epxect_binned_contig_keys = ['total_contig_len', 'assembly_ref', 'bins']
        self.assertCountEqual(binned_contig_data.keys(), epxect_binned_contig_keys)
        self.assertEqual(binned_contig_data.get('total_contig_len'), 8397583)
        self.assertEqual(binned_contig_data.get('assembly_ref'), self.large_assembly_ref)

        bins = binned_contig_data.get('bins')
        bin_ids = [item.get('bid') for item in bins]
        expect_bin_ids = ['out_header.001.fasta', 'out_header.004.fasta']
        self.assertCountEqual(bin_ids, expect_bin_ids)

    def test_edit_bins_from_binned_contig(self):

        binned_contig_name = 'MyBinnedContig'
        params = {
            'assembly_ref': self.large_assembly_ref,
            'file_directory': self.test_directory_path,
            'binned_contig_name': binned_contig_name,
            'workspace_name': self.dfu.ws_name_to_id(self.getWsName())
        }

        resultVal = self.getImpl().file_to_binned_contigs(self.getContext(), params)[0]
        old_binned_contig_ref = resultVal.get('binned_contig_obj_ref')

        output_binned_contig_name = 'MyNewBinnedContig'

        edit_bins_params = {
            'old_binned_contig_ref': old_binned_contig_ref,
            'bins_to_remove': ['out_header.001.fasta'],
            'bin_merges': [{
                'new_bin_id': 'out_header.004.fasta',
                'bin_to_merge': ['out_header.002.fasta', 'out_header.003.fasta']
            }],
            'output_binned_contig_name': output_binned_contig_name,
            'workspace_name': self.getWsName()
        }

        resultVal = self.getImpl().edit_bins_from_binned_contig(self.getContext(),
                                                                edit_bins_params)[0]

        self.assertTrue('new_binned_contig_ref' in resultVal)
        self.assertTrue('report_name' in resultVal)
        self.assertTrue('report_ref' in resultVal)

        binned_contig_object = self.dfu.get_objects(
            {'object_refs': [self.getWsName() + '/' + output_binned_contig_name]})['data'][0]

        binned_contig_info = binned_contig_object.get('info')

        self.assertEqual(binned_contig_info[1], output_binned_contig_name)
        expect_binned_contig_info_list = ['assembly_ref', 'total_contig_len', 'n_bins']
        self.assertCountEqual(binned_contig_info[-1], expect_binned_contig_info_list)
        self.assertEqual(int(binned_contig_info[-1].get('n_bins')), 1)
        self.assertEqual(binned_contig_info[-1].get('assembly_ref'), self.large_assembly_ref)
        self.assertEqual(int(binned_contig_info[-1].get('total_contig_len')), 5722681)

        binned_contig_data = binned_contig_object.get('data')
        epxect_binned_contig_keys = ['total_contig_len', 'assembly_ref', 'bins']
        self.assertCountEqual(binned_contig_data.keys(), epxect_binned_contig_keys)
        self.assertEqual(binned_contig_data.get('total_contig_len'), 5722681)
        self.assertEqual(binned_contig_data.get('assembly_ref'), self.large_assembly_ref)

        bins = binned_contig_data.get('bins')
        bin_ids = [item.get('bid') for item in bins]
        expect_bin_ids = ['out_header.004.fasta']
        self.assertCountEqual(bin_ids, expect_bin_ids)

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import os

import mock
import unittest

from yardstick.benchmark.core import task
from yardstick.common import constants as consts


class TaskTestCase(unittest.TestCase):

    @mock.patch.object(task, 'Context')
    def test_parse_nodes_with_context_same_context(self, mock_context):
        scenario_cfg = {
            "nodes": {
                "host": "node1.LF",
                "target": "node2.LF"
            }
        }
        server_info = {
            "ip": "10.20.0.3",
            "user": "root",
            "key_filename": "/root/.ssh/id_rsa"
        }
        mock_context.get_server.return_value = server_info

        context_cfg = task.parse_nodes_with_context(scenario_cfg)

        self.assertEqual(context_cfg["host"], server_info)
        self.assertEqual(context_cfg["target"], server_info)

    def test_set_dispatchers(self):
        t = task.Task()
        output_config = {"DEFAULT": {"dispatcher": "file, http"}}
        t._set_dispatchers(output_config)
        self.assertEqual(output_config, output_config)

    @mock.patch.object(task, 'DispatcherBase')
    def test__do_output(self, mock_dispatcher):
        t = task.Task()
        output_config = {"DEFAULT": {"dispatcher": "file, http"}}

        dispatcher1 = mock.MagicMock()
        dispatcher1.__dispatcher_type__ = 'file'

        dispatcher2 = mock.MagicMock()
        dispatcher2.__dispatcher_type__ = 'http'

        mock_dispatcher.get = mock.MagicMock(return_value=[dispatcher1,
                                                           dispatcher2])
        self.assertEqual(None, t._do_output(output_config, {}))

    @mock.patch.object(task, 'Context')
    def test_parse_networks_from_nodes(self, mock_context):
        nodes = {
            'node1': {
                'interfaces': {
                    'mgmt': {
                        'network_name': 'mgmt',
                    },
                    'xe0': {
                        'network_name': 'uplink_0',
                    },
                    'xe1': {
                        'network_name': 'downlink_0',
                    },
                },
            },
            'node2': {
                'interfaces': {
                    'mgmt': {
                        'network_name': 'mgmt',
                    },
                    'uplink_0': {
                        'network_name': 'uplink_0',
                    },
                    'downlink_0': {
                        'network_name': 'downlink_0',
                    },
                },
            },
        }

        mock_context.get_network.side_effect = iter([
            None,
            {
                'name': 'mgmt',
                'network_type': 'flat',
            },
            {},
            {
                'name': 'uplink_0',
                'subnet_cidr': '10.20.0.0/16',
            },
            {
                'name': 'downlink_0',
                'segmentation_id': '1001',
            },
            {
                'name': 'uplink_1',
            },
        ])

        # one for each interface
        expected_get_network_calls = 6
        expected = {
            'mgmt': {'name': 'mgmt', 'network_type': 'flat'},
            'uplink_0': {'name': 'uplink_0', 'subnet_cidr': '10.20.0.0/16'},
            'uplink_1': {'name': 'uplink_1'},
            'downlink_0': {'name': 'downlink_0', 'segmentation_id': '1001'},
        }

        networks = task.get_networks_from_nodes(nodes)
        self.assertEqual(mock_context.get_network.call_count, expected_get_network_calls)
        self.assertDictEqual(networks, expected)

    @mock.patch.object(task, 'Context')
    @mock.patch.object(task, 'base_runner')
    def test_run(self, mock_base_runner, *args):
        scenario = {
            'host': 'athena.demo',
            'target': 'ares.demo',
            'runner': {
                'duration': 60,
                'interval': 1,
                'type': 'Duration'
            },
            'type': 'Ping'
        }

        t = task.Task()
        runner = mock.Mock()
        runner.join.return_value = 0
        runner.get_output.return_value = {}
        runner.get_result.return_value = []
        mock_base_runner.Runner.get.return_value = runner
        t._run([scenario], False, "yardstick.out")
        self.assertTrue(runner.run.called)

    @mock.patch.object(os, 'environ')
    def test_check_precondition(self, mock_os_environ):
        cfg = {
            'precondition': {
                'installer_type': 'compass',
                'deploy_scenarios': 'os-nosdn',
                'pod_name': 'huawei-pod1'
            }
        }

        t = task.TaskParser('/opt')
        mock_os_environ.get.side_effect = ['compass',
                                           'os-nosdn',
                                           'huawei-pod1']
        result = t._check_precondition(cfg)
        self.assertTrue(result)

    def test_parse_suite_no_constraint_no_args(self):
        SAMPLE_SCENARIO_PATH = "no_constraint_no_args_scenario_sample.yaml"
        t = task.TaskParser(self._get_file_abspath(SAMPLE_SCENARIO_PATH))
        with mock.patch.object(os, 'environ',
                        new={'NODE_NAME': 'huawei-pod1', 'INSTALLER_TYPE': 'compass'}):
            task_files, task_args, task_args_fnames = t.parse_suite()

        self.assertEqual(task_files[0], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc037.yaml'))
        self.assertEqual(task_files[1], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc043.yaml'))

        self.assertIsNone(task_args[0])
        self.assertIsNone(task_args[1])
        self.assertIsNone(task_args_fnames[0])
        self.assertIsNone(task_args_fnames[1])

    def test_parse_suite_no_constraint_with_args(self):
        SAMPLE_SCENARIO_PATH = "no_constraint_with_args_scenario_sample.yaml"
        t = task.TaskParser(self._get_file_abspath(SAMPLE_SCENARIO_PATH))
        with mock.patch.object(os, 'environ',
                        new={'NODE_NAME': 'huawei-pod1', 'INSTALLER_TYPE': 'compass'}):
            task_files, task_args, task_args_fnames = t.parse_suite()

        self.assertEqual(task_files[0], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc037.yaml'))
        self.assertEqual(task_files[1], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc043.yaml'))
        self.assertIsNone(task_args[0])
        self.assertEqual(task_args[1],
                         '{"host": "node1.LF","target": "node2.LF"}')
        self.assertIsNone(task_args_fnames[0])
        self.assertIsNone(task_args_fnames[1])

    def test_parse_suite_with_constraint_no_args(self):
        SAMPLE_SCENARIO_PATH = "with_constraint_no_args_scenario_sample.yaml"
        t = task.TaskParser(self._get_file_abspath(SAMPLE_SCENARIO_PATH))
        with mock.patch.object(os, 'environ',
                        new={'NODE_NAME': 'huawei-pod1', 'INSTALLER_TYPE': 'compass'}):
            task_files, task_args, task_args_fnames = t.parse_suite()
        self.assertEqual(task_files[0], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc037.yaml'))
        self.assertEqual(task_files[1], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc043.yaml'))
        self.assertIsNone(task_args[0])
        self.assertIsNone(task_args[1])
        self.assertIsNone(task_args_fnames[0])
        self.assertIsNone(task_args_fnames[1])

    def test_parse_suite_with_constraint_with_args(self):
        SAMPLE_SCENARIO_PATH = "with_constraint_with_args_scenario_sample.yaml"
        t = task.TaskParser(self._get_file_abspath(SAMPLE_SCENARIO_PATH))
        with mock.patch('os.environ',
                        new={'NODE_NAME': 'huawei-pod1', 'INSTALLER_TYPE': 'compass'}):
            task_files, task_args, task_args_fnames = t.parse_suite()

        self.assertEqual(task_files[0], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc037.yaml'))
        self.assertEqual(task_files[1], self.change_to_abspath(
                         'tests/opnfv/test_cases/opnfv_yardstick_tc043.yaml'))
        self.assertIsNone(task_args[0])
        self.assertEqual(task_args[1],
                         '{"host": "node1.LF","target": "node2.LF"}')
        self.assertIsNone(task_args_fnames[0])
        self.assertIsNone(task_args_fnames[1])

    def test_parse_options(self):
        options = {
            'openstack': {
                'EXTERNAL_NETWORK': '$network'
            },
            'nodes': ['node1', '$node'],
            'host': '$host'
        }

        t = task.Task()
        t.outputs = {
            'network': 'ext-net',
            'node': 'node2',
            'host': 'server.yardstick'
        }

        expected_result = {
            'openstack': {
                'EXTERNAL_NETWORK': 'ext-net'
            },
            'nodes': ['node1', 'node2'],
            'host': 'server.yardstick'
        }

        actual_result = t._parse_options(options)
        self.assertEqual(expected_result, actual_result)


    def test_change_server_name_host_str(self):
        scenario = {'host': 'demo'}
        suffix = '-8'
        task.change_server_name(scenario, suffix)
        self.assertEqual('demo-8', scenario['host'])

    def test_change_server_name_host_dict(self):
        scenario = {'host': {'name': 'demo'}}
        suffix = '-8'
        task.change_server_name(scenario, suffix)
        self.assertEqual('demo-8', scenario['host']['name'])

    def test_change_server_name_target_str(self):
        scenario = {'target': 'demo'}
        suffix = '-8'
        task.change_server_name(scenario, suffix)
        self.assertEqual('demo-8', scenario['target'])

    def test_change_server_name_target_dict(self):
        scenario = {'target': {'name': 'demo'}}
        suffix = '-8'
        task.change_server_name(scenario, suffix)
        self.assertEqual('demo-8', scenario['target']['name'])

    @mock.patch('six.moves.builtins.open', side_effect=mock.mock_open())
    @mock.patch.object(task, 'utils')
    @mock.patch('logging.root')
    def test_set_log(self, mock_logging_root, *args):
        task_obj = task.Task()
        task_obj.task_id = 'task_id'
        task_obj._set_log()
        mock_logging_root.addHandler.assert_called()

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path

    def change_to_abspath(self, filepath):
        return os.path.join(consts.YARDSTICK_ROOT_PATH, filepath)


def main():
    unittest.main()


if __name__ == '__main__':
    main()

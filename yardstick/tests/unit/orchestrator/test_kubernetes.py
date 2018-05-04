##############################################################################
# Copyright (c) 2017 Intel Corporation
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import copy

import mock

from yardstick.common import exceptions
from yardstick.common import kubernetes_utils
from yardstick.orchestrator import kubernetes
from yardstick.tests.unit import base


class GetTemplateTestCase(base.BaseUnitTestCase):

    def test_get_template(self):
        output_t = {
            "apiVersion": "v1",
            "kind": "ReplicationController",
            "metadata": {
                "name": "host-k8s-86096c30"
            },
            "spec": {
                "replicas": 1,
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "host-k8s-86096c30"
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "args": [
                                    "-c",
                                    "chmod 700 ~/.ssh; chmod 600 ~/.ssh/*; \
service ssh restart;while true ; do sleep 10000; done"
                                ],
                                "command": [
                                    "/bin/bash"
                                ],
                                "image": "openretriever/yardstick",
                                "name": "host-k8s-86096c30-container",
                                "volumeMounts": [
                                    {
                                        "mountPath": "/tmp/.ssh/",
                                        "name": "k8s-86096c30-key",
                                        "readOnly": False
                                    }
                                ]
                            }
                        ],
                        "volumes": [
                            {
                                "configMap": {
                                    "name": "k8s-86096c30-key"
                                },
                                "name": "k8s-86096c30-key"
                            }
                        ],
                        "nodeSelector": {
                            "kubernetes.io/hostname": "node-01"
                        }
                    }
                }
            }
        }
        input_s = {
            'command': '/bin/bash',
            'args': ['-c', 'chmod 700 ~/.ssh; chmod 600 ~/.ssh/*; \
service ssh restart;while true ; do sleep 10000; done'],
            'ssh_key': 'k8s-86096c30-key',
            'nodeSelector': {'kubernetes.io/hostname': 'node-01'},
            'volumes': []
        }
        name = 'host-k8s-86096c30'
        output_r = kubernetes.KubernetesObject(name, **input_s).get_template()
        self.assertEqual(output_r, output_t)


class GetRcPodsTestCase(base.BaseUnitTestCase):

    @mock.patch('yardstick.orchestrator.kubernetes.k8s_utils.get_pod_list')
    def test_get_rc_pods(self, mock_get_pod_list):
        servers = {
            'host': {
                'image': 'openretriever/yardstick',
                'command': '/bin/bash',
                'args': ['-c', 'chmod 700 ~/.ssh; chmod 600 ~/.ssh/*; \
service ssh restart;while true ; do sleep 10000; done']
            },
            'target': {
                'image': 'openretriever/yardstick',
                'command': '/bin/bash',
                'args': ['-c', 'chmod 700 ~/.ssh; chmod 600 ~/.ssh/*; \
service ssh restart;while true ; do sleep 10000; done']
            }
        }
        k8s_template = kubernetes.KubernetesTemplate('k8s-86096c30', servers)
        mock_get_pod_list.return_value.items = []
        pods = k8s_template.get_rc_pods()
        self.assertEqual(pods, [])


class KubernetesObjectTestCase(base.BaseUnitTestCase):

    def test__add_volumes(self):
        volume1 = {'name': 'fake_sshkey',
                   'configMap': {'name': 'fake_sshkey'}}
        volume2 = {'name': 'volume2',
                   'configMap': 'data'}
        k8s_obj = kubernetes.KubernetesObject('name', ssh_key='fake_sshkey',
                                              volumes=[volume2])
        k8s_obj._add_volumes()
        volumes = k8s_obj.template['spec']['template']['spec']['volumes']
        self.assertEqual(sorted([volume1, volume2], key=lambda k: k['name']),
                         sorted(volumes, key=lambda k: k['name']))

    def test__add_volumes_no_volumes(self):
        volume1 = {'name': 'fake_sshkey',
                   'configMap': {'name': 'fake_sshkey'}}
        k8s_obj = kubernetes.KubernetesObject('name', ssh_key='fake_sshkey')
        k8s_obj._add_volumes()
        volumes = k8s_obj.template['spec']['template']['spec']['volumes']
        self.assertEqual([volume1], volumes)

    def test__create_ssh_key_volume(self):
        expected = {'name': 'fake_sshkey',
                    'configMap': {'name': 'fake_sshkey'}}
        k8s_obj = kubernetes.KubernetesObject('name', ssh_key='fake_sshkey')
        self.assertEqual(expected, k8s_obj._create_ssh_key_volume())

    def test__create_volume_item(self):
        for vol_type in kubernetes_utils.get_volume_types():
            volume = {'name': 'vol_name',
                      vol_type: 'data'}
            self.assertEqual(
                volume,
                kubernetes.KubernetesObject._create_volume_item(volume))

    def test__create_volume_item_invalid_type(self):
        volume = {'name': 'vol_name',
                  'invalid_type': 'data'}
        with self.assertRaises(exceptions.KubernetesTemplateInvalidVolumeType):
            kubernetes.KubernetesObject._create_volume_item(volume)

    def test__create_volume_mounts(self):
        volume_mount = {'name': 'fake_name',
                        'mountPath': 'fake_path'}
        ssh_vol = {'name': kubernetes.KubernetesObject.SSHKEY_DEFAULT,
                   'mountPath': kubernetes.KubernetesObject.SSH_MOUNT_PATH,
                   'readOnly': False}
        expected = copy.deepcopy(volume_mount)
        expected['readOnly'] = False
        expected = [expected, ssh_vol]
        k8s_obj = kubernetes.KubernetesObject('name',
                                              volumeMounts=[volume_mount])
        output = k8s_obj._create_volume_mounts()
        self.assertEqual(expected, output)

    def test__create_volume_mounts_no_volume_mounts(self):
        ssh_vol = {'name': kubernetes.KubernetesObject.SSHKEY_DEFAULT,
                   'mountPath': kubernetes.KubernetesObject.SSH_MOUNT_PATH,
                   'readOnly': False}
        k8s_obj = kubernetes.KubernetesObject('name')
        output = k8s_obj._create_volume_mounts()
        self.assertEqual([ssh_vol], output)

    def test__create_volume_mounts_item(self):
        volume_mount = {'name': 'fake_name',
                        'mountPath': 'fake_path'}
        expected = copy.deepcopy(volume_mount)
        expected['readOnly'] = False
        output = kubernetes.KubernetesObject._create_volume_mounts_item(
            volume_mount)
        self.assertEqual(expected, output)

    def test__create_container_item(self):
        volume_mount = {'name': 'fake_name',
                        'mountPath': 'fake_path'}
        args = ['arg1', 'arg2']
        k8s_obj = kubernetes.KubernetesObject(
            'cname', ssh_key='fake_sshkey', volumeMount=[volume_mount],
            args=args)
        expected = {'args': args,
                    'command': [kubernetes.KubernetesObject.COMMAND_DEFAULT],
                    'image': kubernetes.KubernetesObject.IMAGE_DEFAULT,
                    'name': 'cname-container',
                    'volumeMounts': k8s_obj._create_volume_mounts()}
        self.assertEqual(expected, k8s_obj._create_container_item())

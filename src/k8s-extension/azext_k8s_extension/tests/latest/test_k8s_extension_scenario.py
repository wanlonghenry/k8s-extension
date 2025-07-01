# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import os
import json
from azure.cli.testsdk import (ScenarioTest, record_only)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

class K8sExtensionScenarioTest(ScenarioTest):
    @record_only()
    def test_k8s_extension(self):
        extension_type = 'microsoft.dapr'
        self.kwargs.update({
            'name': 'dapr',
            'rg': 'azurecli-tests',
            'cluster_name': 'arc-cluster',
            'cluster_type': 'connectedClusters',
            'extension_type': extension_type,
            'release_train': 'stable',
            'version': '1.6.0',
        })

        self.cmd('k8s-extension create -g {rg} -n {name} -c {cluster_name} --cluster-type {cluster_type} '
                 '--extension-type {extension_type} --release-train {release_train} --version {version} '
                 '--configuration-settings "skipExistingDaprCheck=true" --no-wait --auto-upgrade false')

        # Update requires agent running in k8s cluster that is connected to Azure - so no update tests here
        # self.cmd('k8s-extension update -g {rg} -n {name} --tags foo=boo', checks=[
        #     self.check('tags.foo', 'boo')
        # ])

        installed_exts = self.cmd('k8s-extension list -c {cluster_name} -g {rg} --cluster-type {cluster_type}').get_output_in_json()
        found_extension = False
        for item in installed_exts:
            if item['extensionType'] == extension_type:
                found_extension = True
                break
        self.assertTrue(found_extension)

        self.cmd('k8s-extension show -c {cluster_name} -g {rg} -n {name} --cluster-type {cluster_type}', checks=[
            self.check('name', '{name}'),
            self.check('releaseTrain', '{release_train}'),
            self.check('version', '{version}'),
            self.check('resourceGroup', '{rg}'),
            self.check('extensionType', '{extension_type}')
        ])

        self.cmd('k8s-extension delete -g {rg} -c {cluster_name} -n {name} --cluster-type {cluster_type} --force -y')

        installed_exts = self.cmd('k8s-extension list -c {cluster_name} -g {rg} --cluster-type {cluster_type}').get_output_in_json()
        found_extension = False
        for item in installed_exts:
            if item['extensionType'] == extension_type:
                found_extension = True
                break
        self.assertFalse(found_extension)


class ContainerInsightsExtensionTest(ScenarioTest):
    @record_only()
    def test_container_insights_high_log_scale(self):
        from azure.core.exceptions import ResourceNotFoundError
        
        self.kwargs.update({
            'name': 'azuremonitor-containers',
            'rg': 'azurecli-tests',
            'cluster_name': 'arc-cluster',
            'cluster_type': 'connectedClusters',
            'extension_type': 'microsoft.azuremonitor.containers',
            'config_settings': '"amalogs.useAADAuth=true amalogs.enableHighLogScaleMode=true ' + 
                             'dataCollectionSettings=' + json.dumps({
                                 'interval': '1m',
                                 'enableContainerLogV2': True,
                                 'streams': ['Microsoft-ContainerLogV2']
                             }) + '"'
        })
        # Test creating extension with high log scale enabled
        with self.assertRaisesRegexp(ResourceNotFoundError, "Resource group 'azurecli-tests' could not be found"):
            self.cmd('k8s-extension create -g {rg} -n {name} -c {cluster_name} --cluster-type {cluster_type} '
                    '--extension-type {extension_type} --configuration-settings {config_settings}')

    @record_only()
    def test_container_insights_invalid_high_log_scale(self):
        self.kwargs.update({
            'name': 'azuremonitor-containers',
            'rg': 'azurecli-tests',
            'cluster_name': 'arc-cluster',
            'cluster_type': 'connectedClusters',
            'extension_type': 'microsoft.azuremonitor.containers'
        })

        # Test that invalid high log scale mode value is rejected
        with self.assertRaisesRegexp(Exception, 'amalogs.enableHighLogScaleMode value MUST be either true or false'):
            self.cmd('k8s-extension create -g {rg} -n {name} -c {cluster_name} --cluster-type {cluster_type} '
                    '--extension-type {extension_type} '
                    '--configuration-settings '
                    'amalogs.useAADAuth=true '
                    'amalogs.enableHighLogScaleMode=invalid')

    @record_only()
    def test_container_insights_high_log_scale_streams(self):
        from azure.core.exceptions import ResourceNotFoundError
        
        self.kwargs.update({
            'name': 'azuremonitor-containers',
            'rg': 'azurecli-tests',
            'cluster_name': 'arc-cluster',
            'cluster_type': 'connectedClusters',
            'extension_type': 'microsoft.azuremonitor.containers',
            'config_settings': '"amalogs.useAADAuth=true amalogs.enableHighLogScaleMode=true ' +
                             'dataCollectionSettings=' + json.dumps({
                                 'interval': '1m',
                                 'enableContainerLogV2': True,
                                 'streams': ['Microsoft-ContainerLogV2', 'Microsoft-ContainerLog']
                             }) + '"'
        })

        # Test creating extension with high log scale enabled and multiple streams
        with self.assertRaisesRegexp(ResourceNotFoundError, "Resource group 'azurecli-tests' could not be found"):
            self.cmd('k8s-extension create -g {rg} -n {name} -c {cluster_name} --cluster-type {cluster_type} '
                    '--extension-type {extension_type} --configuration-settings {config_settings}')

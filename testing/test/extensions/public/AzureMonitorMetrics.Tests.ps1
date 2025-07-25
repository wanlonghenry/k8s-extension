Describe 'Azure Monitor Metrics Testing' {
    Describe 'Azure Monitor Metrics Testing' {
        BeforeAll {
            $extensionType = "microsoft.azuremonitor.containers.metrics"
            $extensionName = "azuremonitor-metrics"
            $extensionAgentName = "ama-metrics"
            $extensionAgentNamespace = "kube-system"
            $workspaceResourceGroup = $null  # Initialize here for shared scope

            . $PSScriptRoot/../../helper/Constants.ps1
            . $PSScriptRoot/../../helper/Helper.ps1
        }

        It 'Creates the extension and checks that it onboards correctly' {
            az $Env:K8sExtensionName create -c $($ENVCONFIG.arcClusterName) -g $($ENVCONFIG.resourceGroup) --cluster-type connectedClusters --extension-type $extensionType -n $extensionName --no-wait
            $? | Should -BeTrue

            $output = az $Env:K8sExtensionName show -c $($ENVCONFIG.arcClusterName) -g $($ENVCONFIG.resourceGroup) --cluster-type connectedClusters -n $extensionName
            $? | Should -BeTrue

            $isAutoUpgradeMinorVersion = ($output | ConvertFrom-Json).autoUpgradeMinorVersion
            $isAutoUpgradeMinorVersion.ToString() -eq "True" | Should -BeTrue

            # Loop and retry until the extension installs
            $n = 0
            do {
                if (Has-ExtensionData $extensionName) {
                    break
                }
                Start-Sleep -Seconds 10
                $n += 1
            } while ($n -le $MAX_RETRY_ATTEMPTS)
            $n | Should -BeLessOrEqual $MAX_RETRY_ATTEMPTS
        }

        It "Performs a show on the extension" {
            $output = az $Env:K8sExtensionName show -c $($ENVCONFIG.arcClusterName) -g $($ENVCONFIG.resourceGroup) --cluster-type connectedClusters -n $extensionName
            $? | Should -BeTrue
            $output | Should -Not -BeNullOrEmpty
        }

        It "Lists the extensions on the cluster" {
            $output = az $Env:K8sExtensionName list -c $($ENVCONFIG.arcClusterName) -g $($ENVCONFIG.resourceGroup) --cluster-type connectedClusters
            $? | Should -BeTrue

            $output | Should -Not -BeNullOrEmpty
            $extensionExists = $output | ConvertFrom-Json | Where-Object { $_.extensionType -eq $extensionType }
            $extensionExists | Should -Not -BeNullOrEmpty
        }

        It 'Verifies rule groups were created' {
            $clusterName = $ENVCONFIG.arcClusterName
            $expectedRuleGroupNames = @(
                "KubernetesRecordingRulesRuleGroup-$clusterName",
                "NodeRecordingRulesRuleGroup-$clusterName"
            )

            $ruleGroups = az resource list --resource-group $($ENVCONFIG.resourceGroup) --resource-type "Microsoft.AlertsManagement/prometheusRuleGroups" --query "[].{name:name, location:location, id:id}" | ConvertFrom-Json
            $ruleGroups | Should -Not -BeNullOrEmpty -Because "Rule groups may take time to be created after extension onboarding"
        
            foreach ($expectedName in $expectedRuleGroupNames) {
                $matchingGroup = $ruleGroups | Where-Object { $_.name -eq $expectedName }
                $matchingGroup | Should -Not -BeNullOrEmpty -Because "Rule group '$expectedName' should have been created by create.py"
            }
        }


        It "Deletes the extension from the cluster" {
            $output = az $Env:K8sExtensionName delete -c $($ENVCONFIG.arcClusterName) -g $($ENVCONFIG.resourceGroup) --cluster-type connectedClusters -n $extensionName --force
            $? | Should -BeTrue

            # Extension should not be found on the cluster
            $output = az $Env:K8sExtensionName show -c $($ENVCONFIG.arcClusterName) -g $($ENVCONFIG.resourceGroup) --cluster-type connectedClusters -n $extensionName
            $? | Should -BeFalse
            $output | Should -BeNullOrEmpty
        }

        It "Performs another list after the delete" {
            $output = az $Env:K8sExtensionName list -c $($ENVCONFIG.arcClusterName) -g $($ENVCONFIG.resourceGroup) --cluster-type connectedClusters
            $? | Should -BeTrue
            $output | Should -Not -BeNullOrEmpty

            $extensionExists = $output | ConvertFrom-Json | Where-Object { $_.extensionType -eq $extensionName }
            $extensionExists | Should -BeNullOrEmpty
        }
    }
}

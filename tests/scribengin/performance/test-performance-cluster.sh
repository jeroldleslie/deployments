#!/bin/bash

NEVERWINTERDP_HOME="/home/neverwinterdp/NeverwinterDP"
NEVERWINTERDP_DEPLOYMENTS_HOME="/home/neverwinterdp/neverwinterdp-deployments"

$NEVERWINTERDP_DEPLOYMENTS_HOME/tools/cluster/clusterCommander.py digitalocean \
  --launch --neverwinterdp-home $NEVERWINTERDP_HOME \
  --create-containers $NEVERWINTERDP_DEPLOYMENTS_HOME/tools/cluster/digitalOceanConfigs/scribenginPerformance.yml --subdomain perfcluster

#LogSampleChainPerformanceCluster.sh --stop --clean --build --deploy --restart --profile-type=performance 2>&1 | tee ~/log-sample-performance-cluster-10Mx512.txt

$NEVERWINTERDP_DEPLOYMENTS_HOME/tests/scribengin/performance/LogSampleChainPerformanceCluster.sh \
  --stop --clean --build --deploy --start --profile-type=performance 2>&1 | tee ~/log-sample-performance-cluster-10Mx512.txt

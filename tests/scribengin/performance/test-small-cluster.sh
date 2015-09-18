#!/bin/bash

NEVERWINTERDP_HOME="/home/neverwinterdp/NeverwinterDP"
NEVERWINTERDP_DEPLOYMENTS_HOME="/home/neverwinterdp/neverwinterdp-deployments"

$NEVERWINTERDP_DEPLOYMENTS_HOME/tools/cluster/clusterCommander.py digitalocean \
  --launch --neverwinterdp-home $NEVERWINTERDP_HOME \
  --create-containers $NEVERWINTERDP_DEPLOYMENTS_HOME/tools/cluster/digitalOceanConfigs/scribenginSmall.yml --subdomain smallcluster


#$NEVERWINTERDP_DEPLOYMENTS_HOME/tests/scribengin/performance/LogSampleChainSmallCluster.sh \
#  --stop --clean --build --deploy --start --profile-type=small 2>&1 | tee ~/log-sample-small-cluster-25Mx512.txt

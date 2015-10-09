#!/bin/bash

NEVERWINTERDP_HOME="/home/neverwinterdp/NeverwinterDP"
NEVERWINTERDP_DEPLOYMENTS_HOME="/home/neverwinterdp/neverwinterdp-deployments"

$NEVERWINTERDP_DEPLOYMENTS_HOME/tests/scribengin/stability2/LogSampleChainStabilityCluster.sh --build --deploy --start --profile-type=small 2>&1 | tee log-sample-stability-cluster.txt

#!/bin/bash

NEVERWINTERDP_HOME="/home/neverwinterdp/NeverwinterDP"
NEVERWINTERDP_DEPLOYMENTS_HOME="/home/neverwinterdp/neverwinterdp-deployments"

$NEVERWINTERDP_DEPLOYMENTS_HOME/tests/scribengin/stability2/LogSampleChainStabilityCluster.sh --stop --clean --build --deploy --start --profile-type=stability 2>&1 | tee log-sample-stability-cluster.txt 

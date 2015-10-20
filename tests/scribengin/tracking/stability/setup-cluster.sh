#!/bin/bash

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
ROOT=$SCRIPT_DIR/../../../..

clusterCommander="$ROOT/tools/cluster/clusterCommander.py"

$clusterCommander digitalocean \
  --launch --neverwinterdp-home $NEVERWINTERDP_HOME \
  --create-containers $NEVERWINTERDP_DEPLOYMENTS_HOME/tools/cluster/digitalOceanConfigs/scribenginStability.yml --subdomain stability


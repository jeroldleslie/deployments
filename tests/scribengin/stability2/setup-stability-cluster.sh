#!/bin/bash

NEVERWINTERDP_HOME="/home/neverwinterdp/NeverwinterDP"
NEVERWINTERDP_DEPLOYMENTS_HOME="/home/neverwinterdp/neverwinterdp-deployments"

$NEVERWINTERDP_DEPLOYMENTS_HOME/tools/cluster/clusterCommander.py digitalocean \
  --launch --neverwinterdp-home $NEVERWINTERDP_HOME \
  --create-containers $NEVERWINTERDP_DEPLOYMENTS_HOME/tools/cluster/digitalOceanConfigs/scribenginStability.yml --subdomain stability


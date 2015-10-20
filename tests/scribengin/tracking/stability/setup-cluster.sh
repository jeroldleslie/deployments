#!/bin/bash

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
ROOT=$SCRIPT_DIR/../../../..
INVENTORY=/tmp/scribengininventoryDO
SUBDOMAIN=stability

clusterCommander="$ROOT/tools/cluster/clusterCommander.py"
serviceCommander="$ROOT/tools/serviceCommander/serviceCommander.py"

$clusterCommander digitalocean \
  --launch --neverwinterdp-home $NEVERWINTERDP_HOME \
  --ansible-inventory-location $INVENTORY \
  --create-containers $ROOT/ansible/profile/stability.yml --subdomain $SUBDOMAIN
$serviceCommander -e "common" --install --configure -i $INVENTORY
$serviceCommander --cluster --install --configure -i $INVENTORY
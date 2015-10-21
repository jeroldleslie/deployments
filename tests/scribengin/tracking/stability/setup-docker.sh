#!/bin/bash

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
ROOT=$SCRIPT_DIR/../../../..
INVENTORY=/tmp/scribengininventory

clusterCommander="$ROOT/tools/cluster/clusterCommander.py"

$ROOT/docker/scribengin/docker.sh cluster --clean-containers --run-containers 
$clusterCommander ansible --write-inventory-file --inventory-file $INVENTORY

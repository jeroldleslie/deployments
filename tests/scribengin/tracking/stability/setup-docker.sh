#!/bin/bash

function get_opt() {
  OPT_NAME=$1
  DEFAULT_VALUE=$2
  shift
  
  #Par the parameters
  for i in "$@"; do
    index=$(($index+1))
    if [[ $i == $OPT_NAME* ]] ; then
      value="${i#*=}"
      echo "$value"
      return
    fi
  done
  echo $DEFAULT_VALUE
}

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
ROOT=$SCRIPT_DIR/../../../..
INVENTORY=$(get_opt --inventory '' $@)

clusterCommander="$ROOT/tools/cluster/clusterCommander.py"

if [ ! -z "$INVENTORY" -a "$INVENTORY" != " " ]; then
  INVENTORY_ARGS="--inventory-file $INVENTORY"
fi
        

$ROOT/docker/scribengin/docker.sh cluster --clean-containers --run-containers 
$clusterCommander ansible --write-inventory-file $INVENTORY_ARGS


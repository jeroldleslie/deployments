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
INVENTORY=$(get_opt --inventory '/tmp/scribengininventory' $@)
SUBDOMAIN=$(get_opt --subdomain 'stability' $@)

clusterCommander="$ROOT/tools/cluster/clusterCommander.py"
serviceCommander="$ROOT/tools/serviceCommander/serviceCommander.py"

$clusterCommander digitalocean \
  --launch --neverwinterdp-home $NEVERWINTERDP_HOME \
  --ansible-inventory-location $INVENTORY \
  --create-containers $ROOT/ansible/profile/stability.yml --subdomain $SUBDOMAIN

$clusterCommander digitalocean --ansible-inventory --ansible-inventory-location $INVENTORY --subdomain $SUBDOMAIN

$serviceCommander -e "common" --install --configure -i $INVENTORY

$serviceCommander --cluster --install --configure -i $INVENTORY

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
SUBDOMAIN=$(get_opt --subdomain 'stability' $@)


if [ ! -z "$INVENTORY" -a "$INVENTORY" != " " ]; then
  INVENTORY_ARGS="-i $INVENTORY"
  ANSIBLE_INVENTORY_LOCATION="--ansible-inventory-location $INVENTORY"
fi

clusterCommander="$ROOT/tools/cluster/clusterCommander.py"
serviceCommander="$ROOT/tools/serviceCommander/serviceCommander.py"

$clusterCommander digitalocean \
  --launch --neverwinterdp-home $NEVERWINTERDP_HOME \
  $ANSIBLE_INVENTORY_LOCATION \
  --create-containers $ROOT/ansible/profile/stability.yml --subdomain $SUBDOMAIN

$clusterCommander digitalocean --ansible-inventory $ANSIBLE_INVENTORY_LOCATION --subdomain $SUBDOMAIN

$serviceCommander --cluster --install --configure $INVENTORY_ARGS

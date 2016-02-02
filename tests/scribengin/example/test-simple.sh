#!/bin/bash

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

ROOT=$SCRIPT_DIR/../../..

INVENTORY="/tmp/cluster-stability.inventory"

serviceCommander="$ROOT/tools/serviceCommander/serviceCommander.py"
statusCommander="$ROOT/tools/statusCommander/statusCommander.py"

$serviceCommander -i $INVENTORY --cluster --force-stop --clean

#ansible-playbook -i $INVENTORY $ROOT/ansible/yourkit.yml

$serviceCommander -i $INVENTORY -e "scribengin" --install
$serviceCommander -i $INVENTORY --cluster --configure --profile-type=stability
$serviceCommander -i $INVENTORY --cluster --start
$statusCommander  -i $INVENTORY

NEVERWINTERDP_BUILD=$NEVERWINTERDP_HOME/release/build/release/neverwinterdp


SHELL=$NEVERWINTERDP_BUILD/scribengin/bin/shell.sh
  
chmod +x $NEVERWINTERDP_BUILD/dataflow/*/bin/*.sh

$SHELL vm info

#################################################################################################################################
#Launch Dataflow                                                                                                                #
#################################################################################################################################

time $NEVERWINTERDP_BUILD/dataflow/example/bin/run-simple.sh --zk-connect zookeeper-1:2181

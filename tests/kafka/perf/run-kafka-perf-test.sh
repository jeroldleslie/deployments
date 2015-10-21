#!/bin/bash

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

ROOT=$SCRIPT_DIR/../../..
INVENTORY=/tmp/scribengininventory

serviceCommander="$ROOT/tools/serviceCommander/serviceCommander.py"
statusCommander="$ROOT/tools/statusCommander/statusCommander.py"

$serviceCommander --cluster --force-stop -i $INVENTORY
$serviceCommander --services "zookeeper,kafka" --force-stop --clean --configure --start --profile-type=stability -i $INVENTORY
$statusCommander -i $INVENTORY

#################################################################################################################################
#Launch Dataflow                                                                                                                #
#################################################################################################################################
NEVERWINTERDP_BUILD=$NEVERWINTERDP_HOME/release/build/release/neverwinterdp


$NEVERWINTERDP_BUILD/scribengin/bin/kafka-perf.sh
  

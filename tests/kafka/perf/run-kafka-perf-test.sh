#!/bin/bash

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

ROOT=$SCRIPT_DIR/../../..
INVENTORY=$(get_opt --inventory '' $@)
if [ ! -z "$INVENTORY" -a "$INVENTORY" != " " ]; then
  INVENTORY_ARGS="-i $INVENTORY"
fi

serviceCommander="$ROOT/tools/serviceCommander/serviceCommander.py"
statusCommander="$ROOT/tools/statusCommander/statusCommander.py"

$serviceCommander --cluster --force-stop $INVENTORY_ARGS
$serviceCommander --services "zookeeper,kafka" --force-stop --clean --configure --start --profile-type=stability $INVENTORY_ARGS
$statusCommander $INVENTORY_ARGS

#################################################################################################################################
#Launch Dataflow                                                                                                                #
#################################################################################################################################
NEVERWINTERDP_BUILD=$NEVERWINTERDP_HOME/release/build/release/neverwinterdp


$NEVERWINTERDP_BUILD/scribengin/bin/kafka-perf.sh
  

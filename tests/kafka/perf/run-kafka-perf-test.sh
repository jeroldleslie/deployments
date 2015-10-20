#!/bin/bash

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

ROOT=$SCRIPT_DIR/../../..

clusterCommander="$ROOT/tools/cluster/clusterCommander.py"

$clusterCommander cluster --execute "pkill -9 java" status
$clusterCommander cluster --clean status
$clusterCommander zookeeper --start kafka --start  --profile-type=stability status

#################################################################################################################################
#Launch Dataflow                                                                                                                #
#################################################################################################################################
NEVERWINTERDP_BUILD=$NEVERWINTERDP_HOME/release/build/release/neverwinterdp


$NEVERWINTERDP_BUILD/scribengin/bin/kafka-perf.sh
  

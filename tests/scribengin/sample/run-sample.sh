#!/bin/bash

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

ROOT=$SCRIPT_DIR/../../..

INVENTORY="$HOME/inventory"

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

SAMPLE_OPTS="\
  --zk-connect zookeeper-1:2181 \
  --generator-num-of-web-events 100000 \
  --dataflow-num-of-worker 4 --dataflow-num-of-executor-per-worker 2 --dataflow-output-es-addresses elasticsearch-1:9300"

function runTest() {
  time $NEVERWINTERDP_BUILD/dataflow/sample/bin/run-sample.sh $SAMPLE_OPTS 
}


runTest

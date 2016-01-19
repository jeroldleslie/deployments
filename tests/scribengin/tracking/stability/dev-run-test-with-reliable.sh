#!/bin/bash

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

ROOT=$SCRIPT_DIR/../../../..

INVENTORY="/tmp/cluster-stability.inventory"

serviceCommander="$ROOT/tools/serviceCommander/serviceCommander.py"
statusCommander="$ROOT/tools/statusCommander/statusCommander.py"

$serviceCommander -i $INVENTORY --cluster --force-stop --clean

#ansible-playbook -i $INVENTORY $ROOT/ansible/yourkit.yml

$serviceCommander -i $INVENTORY -e "scribengin" --install
$serviceCommander -i $INVENTORY --cluster --configure --profile-type=stability
$serviceCommander -i $INVENTORY --cluster --start
$statusCommander  -i $INVENTORY


#################################################################################################################################
#Launch Dataflow                                                                                                                #
#################################################################################################################################
NEVERWINTERDP_BUILD=$NEVERWINTERDP_HOME/release/build/release/neverwinterdp


SHELL=$NEVERWINTERDP_BUILD/scribengin/bin/shell.sh
  

chmod +x $NEVERWINTERDP_BUILD/dataflow/*/bin/*.sh

$SHELL vm info

GENERATOR_OPTS="\
  --generator-num-of-chunk 60 --generator-num-of-message-per-chunk 100000000 --generator-num-of-writer 1 --generator-break-in-period 75 \
  --generator-kafka-num-of-partition 5 --generator-kafka-num-of-replication 3 \
  --generator-max-wait-time 30000"

VALIDATOR_OPTS="--validator-num-of-reader 1 --validator-max-run-time 1000000000"


DATAFLOW_OPTS="\
  --dataflow-storage kafka --dataflow-num-of-worker 5 --dataflow-num-of-executor-per-worker 2 \
  --dataflow-tracking-window-size 50000 --dataflow-sliding-window-size 300 \
  --dataflow-default-parallelism 5 --dataflow-default-replication 3"

time $NEVERWINTERDP_BUILD/dataflow/tracking-sample/bin/run-tracking.sh $GENERATOR_OPTS $DATAFLOW_OPTS $VALIDATOR_OPTS 


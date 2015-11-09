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
  --generator-num-of-chunk=50 --generator-num-of-message-per-chunk=50000000 --generator-num-of-writer=1 --generator-break-in-period=-1 \
  --generator-num-of-kafka-partition=8 --generator-num-of-kafka-replication=2 \
  --generator-max-wait-time=30000"

#VALIDATOR_OPTS="--validator-disable"
VALIDATOR_OPTS="--validator-num-of-reader=1 $VALIDATOR_OPTS"


DATAFLOW_OPTS="--dataflow-num-of-worker=8 --dataflow-num-of-executor-per-worker=2"
DATAFLOW_STORAGE_OPTS="--dataflow-storage=hdfs"
DATAFLOW_LOG_OPTS="--dataflow-worker-enable-gc"
#DATAFLOW_KILL_OPTS="--dataflow-kill-worker-random=true --dataflow-kill-worker-max=50 --dataflow-kill-worker-period=600000"
DATAFLOW_OPTS="$DATAFLOW_OPTS $DATAFLOW_STORAGE_OPTS $DATAFLOW_LOG_OPTS $DATAFLOW_KILL_OPTS"

time $NEVERWINTERDP_BUILD/dataflow/tracking-sample/bin/run-tracking.sh $GENERATOR_OPTS $DATAFLOW_OPTS $VALIDATOR_OPTS 


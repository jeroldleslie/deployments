#!/bin/bash

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

ROOT=$SCRIPT_DIR/../../../..

INVENTORY="/tmp/scribengininventory"


clusterCommander="$ROOT/tools/cluster/clusterCommander.py"
serviceCommander="$ROOT/tools/serviceCommander/serviceCommander.py"
statusCommander="$ROOT/tools/statusCommander/statusCommander.py"

$serviceCommander --cluster --force-stop --clean -i $INVENTORY
ansible-playbook -i $INVENTORY $ROOT/ansible/yourkit.yml

$serviceCommander -e "scribengin" --install -i $INVENTORY
$serviceCommander --cluster --configure --start --profile-type=stability -i $INVENTORY
$statusCommander -i $INVENTORY


#################################################################################################################################
#Launch Dataflow                                                                                                                #
#################################################################################################################################
NEVERWINTERDP_BUILD=$NEVERWINTERDP_HOME/release/build/release/neverwinterdp


SHELL=$NEVERWINTERDP_BUILD/scribengin/bin/shell.sh
  

chmod +x $NEVERWINTERDP_BUILD/dataflow/*/bin/*.sh

$SHELL vm info

GENERATOR_OPTS="\
  --generator-num-of-chunk=50 --generator-num-of-message-per-chunk=100000000 --generator-num-of-writer=2 --generator-break-in-period=-1 \
  --generator-num-of-kafka-partition=8 --generator-num-of-kafka-replication=2 \
  --generator-max-wait-time=10000"

VALIDATOR_OPTS='--validator-num-of-reader=1'


DATAFLOW_OPTS="--dataflow-num-of-worker=8 --dataflow-num-of-executor-per-worker=2"
DATAFLOW_STORAGE_OPTS="--dataflow-storage=kafka"
DATAFLOW_LOG_OPTS="--dataflow-worker-enable-gc"
#DATAFLOW_KILL_OPTS="--dataflow-kill-worker-random=true --dataflow-kill-worker-max=3 --dataflow-kill-worker-period=60000"
DATAFLOW_OPTS="$DATAFLOW_OPTS $DATAFLOW_STORAGE_OPTS $DATAFLOW_LOG_OPTS $DATAFLOW_KILL_OPTS"

time $NEVERWINTERDP_BUILD/dataflow/tracking-sample/bin/run-tracking.sh $GENERATOR_OPTS $DATAFLOW_OPTS $VALIDATOR_OPTS 


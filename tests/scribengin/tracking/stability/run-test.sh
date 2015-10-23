#!/bin/bash

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

ROOT=$SCRIPT_DIR/../../../..

clusterCommander="$ROOT/tools/cluster/clusterCommander.py"

$clusterCommander cluster --execute "pkill -9 java" status
$clusterCommander cluster --clean status
$clusterCommander ansible --write-inventory-file --deploy-scribengin
$clusterCommander cluster --start --profile-type=stability status

#################################################################################################################################
#Launch Dataflow                                                                                                                #
#################################################################################################################################
NEVERWINTERDP_BUILD=$NEVERWINTERDP_HOME/release/build/release/neverwinterdp


SHELL=$NEVERWINTERDP_BUILD/scribengin/bin/shell.sh
  

chmod +x $NEVERWINTERDP_BUILD/dataflow/log-sample/bin/*.sh

$SHELL vm info

GENERATOR_OPTS="\
  --generator-num-of-chunk=30 --generator-num-of-message-per-chunk=50000000 --generator-num-of-writer=1 --generator-break-in-period=50 \
  --generator-num-of-kafka-partition=8 --generator-num-of-kafka-replication=2 \
  --generator-max-wait-time=5000"

VALIDATOR_OPTS='--validator-num-of-reader=1'

STORAGE_OPTS="--dataflow-storage=kafka"
KILL_WORKER_OPTS='--dataflow-kill-worker-random=true --dataflow-kill-worker-period=300000 --dataflow-kill-worker-max=500'
DATAFLOW_OPTS="--dataflow-num-of-worker=8 --dataflow-num-of-executor-per-worker=2"
DATAFLOW_OPTS="$STORAGE_OPTS $DATAFLOW_OPTS $KILL_WORKER_OPTS"

time $NEVERWINTERDP_BUILD/dataflow/tracking-sample/bin/run-tracking.sh $GENERATOR_OPTS $DATAFLOW_OPTS $VALIDATOR_OPTS


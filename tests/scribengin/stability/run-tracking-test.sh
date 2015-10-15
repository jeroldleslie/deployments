#!/bin/bash

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

ROOT=$SCRIPT_DIR/../../..

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

$SHELL scribengin info

GENERATOR_OPTS="\
  --generator-num-of-chunk=30 --generator-num-of-message-per-chunk=10000000 --generator-num-of-writer=1 --generator-break-in-period=60 \
  --generator-num-of-kafka-partition=8 --generator-num-of-kafka-replication=2 \
  --generator-max-wait-time=15000"

#VALIDATOR_OPTS='--validator-disable'
VALIDATOR_OPTS='--validator-num-of-reader=2'

STORAGE_OPTS="--dataflow-storage=kafka"
#KILL_WORKER_OPTS='--kill-worker-random=true --kill-worker-period=120000 --kill-worker-max=30'
DATAFLOW_OPTS="--dataflow-num-of-worker=2 --dataflow-num-of-executor-per-worker=2"
DATAFLOW_OPTS="$STORAGE_OPTS $DATAFLOW_OPTS $KILL_WORKER_OPTS"

time $NEVERWINTERDP_BUILD/dataflow/log-sample/bin/run-tracking.sh $GENERATOR_OPTS $DATAFLOW_OPTS $VALIDATOR_OPTS


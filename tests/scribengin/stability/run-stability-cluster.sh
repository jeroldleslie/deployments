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

GENERATOR_OPTS="--generator-max-wait-time=60000 --generator-send-period=1"

#VALIDATOR_OPTS='--validator-disable'

STORAGE_OPTS="--storage=kafka"
#KILL_WORKER_OPTS='--kill-worker-random=true --kill-worker-period=120000 --kill-worker-max=30'
DATAFLOW_OPTS="--dedicated-executor=false --num-of-worker=2 --num-of-executor-per-worker=2 --num-of-stream=8 --num-of-message=500000000 --message-size=512 --dump-period=30000"
DATAFLOW_OPTS="$STORAGE_OPTS $DATAFLOW_OPTS $KILL_WORKER_OPTS"

time $NEVERWINTERDP_BUILD/dataflow/log-sample/bin/run-dataflow-chain.sh $GENERATOR_OPTS $DATAFLOW_OPTS $VALIDATOR_OPTS


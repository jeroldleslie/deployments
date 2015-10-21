#!/bin/bash

function get_opt() {
  OPT_NAME=$1
  DEFAULT_VALUE=$2
  shift
  
  #Par the parameters
  for i in "$@"; do
    index=$(($index+1))
    if [[ $i == $OPT_NAME* ]] ; then
      value="${i#*=}"
      echo "$value"
      return
    fi
  done
  echo $DEFAULT_VALUE
}

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

ROOT=$SCRIPT_DIR/../../../..
INVENTORY=/tmp/scribengininventory

clusterCommander="$ROOT/tools/cluster/clusterCommander.py"
serviceCommander="$ROOT/tools/serviceCommander/serviceCommander.py"
statusCommander="$ROOT/tools/statusCommander/statusCommander.py"
MONITOR_MAX_RUNTIME=$(get_opt --monitor-max-runtime '0' $@)


$serviceCommander -e "scribengin" --install -i $INVENTORY
$serviceCommander --cluster --force-stop --clean --configure --start --profile-type=stability -i $INVENTORY
$statusCommander -i $INVENTORY


#################################################################################################################################
#Launch Dataflow                                                                                                                #
#################################################################################################################################
NEVERWINTERDP_BUILD=$NEVERWINTERDP_HOME/release/build/release/neverwinterdp


SHELL=$NEVERWINTERDP_BUILD/scribengin/bin/shell.sh
  

chmod +x $NEVERWINTERDP_BUILD/dataflow/*/bin/*.sh

$SHELL vm info

GENERATOR_OPTS="\
  --generator-num-of-chunk=10 --generator-num-of-message-per-chunk=100000 --generator-num-of-writer=1 --generator-break-in-period=75 \
  --generator-num-of-kafka-partition=8 --generator-num-of-kafka-replication=2 \
  --generator-max-wait-time=15000"

VALIDATOR_OPTS='--validator-num-of-reader=1'

STORAGE_OPTS="--dataflow-storage=kafka"
#KILL_WORKER_OPTS='--dataflow-kill-worker-random=true --dataflow-kill-worker-period=300000 --dataflow-kill-worker-max=500'
DATAFLOW_OPTS="--dataflow-num-of-worker=8 --dataflow-num-of-executor-per-worker=2"
DATAFLOW_OPTS="$STORAGE_OPTS $DATAFLOW_OPTS $KILL_WORKER_OPTS"

MONITOR_OPTS="--monitor-max-runtime=MONITOR_MAX_RUNTIME"

time $NEVERWINTERDP_BUILD/dataflow/tracking-sample/bin/run-tracking.sh $GENERATOR_OPTS $DATAFLOW_OPTS $VALIDATOR_OPTS $MONITOR_OPTS








#!/bin/bash

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

ROOT=$SCRIPT_DIR/../../../..

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

INVENTORY=$(get_opt --inventory '' $@)
if [ ! -z "$INVENTORY" -a "$INVENTORY" != " " ]; then
  INVENTORY_ARGS="-i $INVENTORY"
fi

clusterCommander="$ROOT/tools/cluster/clusterCommander.py"
serviceCommander="$ROOT/tools/serviceCommander/serviceCommander.py"
statusCommander="$ROOT/tools/statusCommander/statusCommander.py"

$serviceCommander --cluster --force-stop --clean $INVENTORY_ARGS
if [ ! -z "$INVENTORY_ARGS" -a "$INVENTORY_ARGS" != " " ]; then
  ansible-playbook $ROOT/ansible/yourkit.yml $INVENTORY_ARGS
fi

$serviceCommander -e "scribengin" --install $INVENTORY_ARGS
$serviceCommander --cluster --configure --start --profile-type=stability $INVENTORY_ARGS
$statusCommander $INVENTORY_ARGS


#################################################################################################################################
#Launch Dataflow                                                                                                                #
#################################################################################################################################
NEVERWINTERDP_BUILD=$NEVERWINTERDP_HOME/release/build/release/neverwinterdp


SHELL=$NEVERWINTERDP_BUILD/scribengin/bin/shell.sh
  

chmod +x $NEVERWINTERDP_BUILD/dataflow/*/bin/*.sh

$SHELL vm info

GENERATOR_OPTS="\
  --generator-num-of-chunk=50 --generator-num-of-message-per-chunk=100000000 --generator-num-of-writer=1 --generator-break-in-period=-1 \
  --generator-num-of-kafka-partition=14 --generator-num-of-kafka-replication=2 \
  --generator-max-wait-time=30000"

VALIDATOR_OPTS='--validator-num-of-reader=1'


DATAFLOW_OPTS="--dataflow-num-of-worker=8 --dataflow-num-of-executor-per-worker=2"
DATAFLOW_STORAGE_OPTS="--dataflow-storage=kafka"
DATAFLOW_LOG_OPTS="--dataflow-worker-enable-gc"
#DATAFLOW_KILL_OPTS="--dataflow-kill-worker-random=true --dataflow-kill-worker-max=3 --dataflow-kill-worker-period=60000"
DATAFLOW_OPTS="$DATAFLOW_OPTS $DATAFLOW_STORAGE_OPTS $DATAFLOW_LOG_OPTS $DATAFLOW_KILL_OPTS"

time $NEVERWINTERDP_BUILD/dataflow/tracking-sample/bin/run-tracking.sh $GENERATOR_OPTS $DATAFLOW_OPTS $VALIDATOR_OPTS 


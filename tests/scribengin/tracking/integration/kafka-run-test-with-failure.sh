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

function has_opt() {
  OPT_NAME=$1
  shift
  #Par the parameters
  for i in "$@"; do
    if [[ $i == $OPT_NAME ]] ; then
      echo "true"
      return
    fi
  done
  echo "false"
}

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

ROOT=$SCRIPT_DIR/../../../..

STOP_CLEAN_DISABLE=$(has_opt "--stop-clean-disable" $@ )

clusterCommander="$ROOT/tools/cluster/clusterCommander.py"
serviceCommander="$ROOT/tools/serviceCommander/serviceCommander.py"
statusCommander="$ROOT/tools/statusCommander/statusCommander.py"

MONITOR_MAX_RUNTIME=$(get_opt --monitor-max-runtime '0' $@)
INVENTORY=$(get_opt --inventory '' $@)

if [ ! -z "$INVENTORY" -a "$INVENTORY" != " " ]; then
  INVENTORY_ARGS="-i $INVENTORY"
fi

JUNIT_REPORT_FILE=$(get_opt --junit-report-file '' $@)
JUNIT_PRE_SLEEP=$(get_opt --junit-pre-sleep '0' $@)

DATAFLOW_STORAGE=$(get_opt --dataflow-storage 'kafka' $@)

DATAFLOW_KILL_WORKER_RANDOM=$(get_opt --dataflow-kill-worker-random 'false' $@)
DATAFLOW_KILL_WORKER_MAX=$(get_opt --dataflow-kill-worker-max '5' $@)
DATAFLOW_KILL_WORKER_PERIOD=$(get_opt --dataflow-kill-worker-period '60000' $@)

$serviceCommander -e "scribengin" --install $INVENTORY_ARGS
if [ $STOP_CLEAN_DISABLE == "false" ] ; then
  $serviceCommander --cluster --force-stop --clean --configure --start --profile-type=stability $INVENTORY_ARGS
else
  $serviceCommander --cluster --configure --start --profile-type=stability $INVENTORY_ARGS
fi
$statusCommander $INVENTORY_ARGS


#################################################################################################################################
#Launch Dataflow                                                                                                                #
#################################################################################################################################
NEVERWINTERDP_BUILD=$NEVERWINTERDP_HOME/release/build/release/neverwinterdp


SHELL=$NEVERWINTERDP_BUILD/scribengin/bin/shell.sh
  

chmod +x $NEVERWINTERDP_BUILD/dataflow/*/bin/*.sh

$SHELL vm info

GENERATOR_OPTS="\
  --generator-num-of-chunk=10 --generator-num-of-message-per-chunk=100000 --generator-num-of-writer=1 --generator-break-in-period=50 \
  --generator-num-of-kafka-partition=8 --generator-num-of-kafka-replication=2 \
  --generator-max-wait-time=5000"

VALIDATOR_OPTS='--validator-num-of-reader=1'

STORAGE_OPTS="--dataflow-storage=$DATAFLOW_STORAGE"

DATAFLOW_OPTS="--dataflow-num-of-worker=8 --dataflow-num-of-executor-per-worker=2"

MONITOR_OPTS="--monitor-max-runtime=$MONITOR_MAX_RUNTIME"

JUNIT_OPTS="--junit-report-file=$JUNIT_REPORT_FILE --junit-pre-sleep=$JUNIT_PRE_SLEEP"

DATAFLOW_KILL_OPTS="--dataflow-kill-worker-random=$DATAFLOW_KILL_WORKER_RANDOM \
  --dataflow-kill-worker-max=$DATAFLOW_KILL_WORKER_MAX --dataflow-kill-worker-period=$DATAFLOW_KILL_WORKER_PERIOD"


time $NEVERWINTERDP_BUILD/dataflow/tracking-sample/bin/run-tracking.sh $GENERATOR_OPTS $STORAGE_OPTS $DATAFLOW_OPTS $VALIDATOR_OPTS $MONITOR_OPTS $JUNIT_OPTS $DATAFLOW_KILL_OPTS








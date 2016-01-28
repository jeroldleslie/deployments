#!/bin/bash

COMMAND=$1
shift

if [ "$COMMAND" = "" ] ; then
  echo ""
  echo "Available test commands"
  echo "  basic  :  Run basic kafka tracking dataflow test"
  echo "  failure:  Run kafka tracking dataflow test with failure scenario kill master, kill worker, start/stop/resume, kill all master and worker"
  echo ""
  echo "Available options"
  echo "  --storage=[kafka, hdfs, s3] specify the storga to test"
  echo ""
  exit 0
fi

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

NEVERWINTERDP_BUILD=$NEVERWINTERDP_HOME/release/build/release/neverwinterdp


SHELL=$NEVERWINTERDP_BUILD/scribengin/bin/shell.sh
  
chmod +x $NEVERWINTERDP_BUILD/dataflow/*/bin/*.sh

$SHELL vm info

#################################################################################################################################
#Launch Dataflow                                                                                                                #
#################################################################################################################################

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

TEST_STORAGE=$(get_opt --storage 'kafka' $@)

GENERATOR_OPTS="\
  --generator-num-of-chunk 60 --generator-num-of-message-per-chunk 100000000 --generator-num-of-writer 1 --generator-break-in-period 500 \
  --generator-kafka-num-of-partition 5 --generator-kafka-num-of-replication 3 \
  --generator-max-wait-time 30000"

VALIDATOR_OPTS="--validator-num-of-reader 1 --validator-max-run-time 1000000000 --validator-message-wait-timeout 300000"

DATAFLOW_OPTS="\
  --dataflow-storage $TEST_STORAGE --dataflow-num-of-worker 5 --dataflow-num-of-executor-per-worker 2 \
  --dataflow-tracking-window-size 50000 --dataflow-sliding-window-size 100 \
  --dataflow-default-parallelism 5 --dataflow-default-replication 3"

SIMULATION_OPTS="\
  --simulation-period 450000 --simulation-max  200  --simulation-report-period 90000"

function runTest() {
  time $NEVERWINTERDP_BUILD/dataflow/tracking-sample/bin/run-tracking.sh $GENERATOR_OPTS $DATAFLOW_OPTS $VALIDATOR_OPTS 
}


function runWithFailureTest() {
  time $NEVERWINTERDP_BUILD/dataflow/tracking-sample/bin/run-tracking-with-simulation.sh $GENERATOR_OPTS $DATAFLOW_OPTS $VALIDATOR_OPTS $SIMULATION_OPTS
}

if [ "$COMMAND" = "basic" ] ; then
  runTest
elif [ "$COMMAND" = "failure" ] ; then
  runWithFailureTest
fi

#!/bin/bash


COMMAND=$1
shift

if [ "$COMMAND" = "" ] ; then
  echo ""
  echo "Available commands"
  echo "  quick  :  Run a quick analytics test"
  echo "  monitor:  Run a long test  with min/max visit time that simulate the real web environment"
  exit 0
fi

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

ROOT=$SCRIPT_DIR/../../..

INVENTORY="$HOME/inventory"

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
if [ "$COMMAND" = "quick" ] ; then
  ANALYTICS_OPTS="\
    --zk-connect zookeeper-1:2181 --hadoop-master-connect hadoop-master \
    --generator-odyssey-num-of-events 10000 --generator-web-num-of-events 100000 \
    --dataflow-num-of-workers 5 --dataflow-num-of-executor-per-worker 4 --wait-for-input"
  time $NEVERWINTERDP_BUILD/dataflow/analytics/bin/run-analytics.sh $ANALYTICS_OPTS
elif [ "$COMMAND" = "monitor" ] ; then
  ANALYTICS_OPTS="\
    --zk-connect zookeeper-1:2181 --hadoop-master-connect hadoop-master \
    --generator-odyssey-num-of-events 10000 --generator-web-num-of-events 10000000 \
    --dataflow-num-of-workers 5 --dataflow-num-of-executor-per-worker 4 \
    --generator-web-num-of-threads 1 --generator-web-max-visit-time 300000 --generator-web-min-visit-time 5000 --wait-for-input"
  time $NEVERWINTERDP_BUILD/dataflow/analytics/bin/run-analytics.sh $ANALYTICS_OPTS
fi


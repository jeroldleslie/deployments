#SCRIPT_DIR is the directory this script is in.  Allows us to execute without relative paths
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

#This Script will set root directory and Neverwinter_home
source $SCRIPT_DIR/setupEnvironment.sh $@


ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "cd /opt/neverwinterdp && ./scribengin/bin/shell.sh vm info"


ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "chmod +x /opt/neverwinterdp/dataflow/log-sample/bin/*.sh"

GENERATOR_OPTS="--generator-max-wait-time=60000 --generator-send-period=1"

#VALIDATOR_OPTS='--validator-disable'

STORAGE_OPTS="--storage=kafka"
KILL_WORKER_OPTS="--kill-worker-random=true --kill-worker-period=30000 --kill-worker-max=15"
DATAFLOW_OPTS="$STORAGE_OPTS --dedicated-executor=false --num-of-worker=8 --num-of-executor-per-worker=2 --num-of-stream=8 --num-of-message=10000000 --message-size=512 $KILL_WORKER_OPTS"

ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master \
   "cd /opt/neverwinterdp &&  time ./dataflow/log-sample/bin/run-dataflow.sh $GENERATOR_OPTS $DATAFLOW_OPTS $VALIDATOR_OPTS"

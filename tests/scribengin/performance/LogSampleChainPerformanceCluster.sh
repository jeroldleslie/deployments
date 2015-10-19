#SCRIPT_DIR is the directory this script is in.  Allows us to execute without relative paths
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

#This Script will set root directory and Neverwinter_home
source $SCRIPT_DIR/../setupEnvironment.sh $@


ssh -o 'StrictHostKeyChecking no' neverwinterdp@hadoop-master 'cd /opt/neverwinterdp && ./scribengin/bin/shell.sh scribengin info'


ssh -o 'StrictHostKeyChecking no' neverwinterdp@hadoop-master 'chmod +x /opt/neverwinterdp/dataflow/log-sample/bin/*.sh'

STORAGE_OPTS="--storage=hdfs"
DATAFLOW_OPTS="--dedicated-executor=false --num-of-worker=2 --num-of-executor-per-worker=4 --num-of-stream=16 --num-of-message=25000000 --message-size=512"
KILL_WORKER_OPTS="--kill-worker-random=true --kill-worker-max=25"

ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master \
   "cd /opt/neverwinterdp &&  time ./dataflow/log-sample/bin/run-dataflow-chain.sh $STORAGE_OPTS $DATAFLOW_OPTS $KILL_WORKER_OPTS"

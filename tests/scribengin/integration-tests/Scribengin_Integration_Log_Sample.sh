#SCRIPT_DIR is the directory this script is in.  Allows us to execute without relative paths
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

#This Script will set root directory and Neverwinter_home
source $SCRIPT_DIR/setupEnvironment.sh $@


ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "cd /opt/neverwinterdp && ./scribengin/bin/shell.sh scribengin info"


ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "chmod +x /opt/neverwinterdp/dataflow/log-sample/bin/*.sh"


#RUN_OPTS="--profile=performance --storage=s3 --dedicated-executor=false --num-of-message=1000000 --message-size=512"
RUN_OPTS="--profile=dataflow-worker-failure --kill-max=5 --kill-period=180000 --storage=hdfs --dedicated-executor=false --num-of-message=10000000 --message-size=512"

ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master  "cd /opt/neverwinterdp &&  time ./dataflow/log-sample/bin/run.sh $RUN_OPTS"

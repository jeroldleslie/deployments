#SCRIPT_DIR is the directory this script is in.  Allows us to execute without relative paths
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

#This Script will set root directory and Neverwinter_home
source $SCRIPT_DIR/setupEnvironment.sh $@


ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "cd /opt/neverwinterdp && ./scribengin/bin/shell.sh scribengin info"


ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "chmod +x /opt/neverwinterdp/dataflow/log-sample/bin/*.sh"


#RUN_OPTS="--profile=performance --storage=kafka --dedicated-executor=false --num-of-message=1000000 --message-size=512"
#RUN_OPTS="--profile=dataflow-worker-failure --execution-max=3 --execution-period=180000 --storage=kafka --dedicated-executor=false --num-of-message=3000000 --message-size=512"
RUN_OPTS="--profile=dataflow-start-stop --execution-max=3 --execution-period=90000 --storage=kafka --dedicated-executor=false --num-of-message=3000000 --message-size=512"

ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master  "cd /opt/neverwinterdp &&  time ./dataflow/log-sample/bin/run-chain.sh $RUN_OPTS"

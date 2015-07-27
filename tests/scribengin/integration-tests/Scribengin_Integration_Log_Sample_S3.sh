#SCRIPT_DIR is the directory this script is in.  Allows us to execute without relative paths
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

#This Script will set root directory and Neverwinter_home
source $SCRIPT_DIR/setupEnvironment.sh $@


ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "cd /opt/neverwinterdp && ./scribengin/bin/shell.sh scribengin info"


ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "chmod +x /opt/neverwinterdp/dataflow/log-sample/bin/*.sh"
ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master \ 
  "cd /opt/neverwinterdp && ./dataflow/log-sample/bin/run-s3.sh --profile=performance --dedicated-executor=false --num-of-message=2500000 --message-size=256"

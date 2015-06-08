#SCRIPT_DIR is the directory this script is in.  Allows us to execute without relative paths
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

#This Script will set root directory and Neverwinter_home
source $SCRIPT_DIR/setupEnvironment.sh $@

#Set up docker images
$ROOT/docker/scribengin/docker.sh cluster --clean-containers --run-containers --deploy-scribengin --start-cluster --neverwinterdp-home=$NEVERWINTER_HOME

#make folder for test results
mkdir testresults

#Give everything time to come up
sleep 5

ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "cd /opt/scribengin/scribengin && ./bin/shell.sh scribengin info"
ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "cd /opt/scribengin/scribengin && ./bin/shell.sh vm info"

#Clean up
#$ROOT/docker/scribengin/docker.sh cluster --clean-containers --neverwinterdp-home=$NEVERWINTER_HOME


#SCRIPT_DIR is the directory this script is in.  Allows us to execute without relative paths
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

#This Script will set root directory and Neverwinter_home
source $SCRIPT_DIR/setupEnvironment.sh $@

scp -r $ROOT/docker/scribengin/bootstrap/post-install/kafka neverwinterdp@hadoop-master:/opt

ssh -o StrictHostKeyChecking=no neverwinterdp@hadoop-master "export NEVERWINTERDP_HOME=$NEVERWINTER_HOME && cd /opt/cluster && python clusterCommander.py zookeeper --start kafka --start"



ssh -o StrictHostKeyChecking=no neverwinterdp@hadoop-master "cd /opt/cluster && python test/testReassignPartitions.py"

#Get results
scp -o stricthostkeychecking=no neverwinterdp@hadoop-master:/opt/cluster/junit-reports/*.xml $TEST_RESULTS_LOCATION


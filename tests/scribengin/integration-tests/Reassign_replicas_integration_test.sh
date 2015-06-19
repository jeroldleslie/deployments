#SCRIPT_DIR is the directory this script is in.  Allows us to execute without relative paths
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

#This Script will set root directory and Neverwinter_home
source $SCRIPT_DIR/setupEnvironment.sh $@

#Set up docker images
$ROOT/docker/scribengin/docker.sh cluster --clean-containers --run-containers --kafka-server=6  --monitoring-server=0 --ansible-inventory --deploy-scribengin --start --neverwinterdp-home=$NEVERWINTER_HOME

scp -r $ROOT/docker/scribengin/bootstrap/post-install/kafka neverwinterdp@hadoop-master:/opt

ssh -o StrictHostKeyChecking=no neverwinterdp@hadoop-master "export NEVERWINTERDP_HOME=$NEVERWINTER_HOME && cd /opt/cluster && python clusterCommander.py zookeeper --start kafka --start"


#make folder for test results
 if [ ! -d testresults ] ; then
   mkdir testresults 
 fi

#Give everything time to come up
sleep 5

ssh -o StrictHostKeyChecking=no neverwinterdp@hadoop-master "cd /opt/cluster && python test/testReassignPartitions.py"

#Get results
scp -o stricthostkeychecking=no neverwinterdp@hadoop-master:/opt/cluster/junit-reports/*.xml ./testresults/

#Clean up
#$ROOT/docker/scribengin/docker.sh cluster --clean-containers --neverwinterdp-home=$NEVERWINTER_HOME

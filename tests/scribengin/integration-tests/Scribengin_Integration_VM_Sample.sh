#SCRIPT_DIR is the directory this script is in.  Allows us to execute without relative paths
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

#This Script will set root directory and Neverwinter_home
source $SCRIPT_DIR/setupEnvironment.sh $@

#Set up docker images
$ROOT/docker/scribengin/docker.sh cluster --clean-containers --run-containers --ansible-inventory --deploy-scribengin --start --neverwinterdp-home=$NEVERWINTER_HOME

#make folder for test results
mkdir testresults

#Give everything time to come up
sleep 5
ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "cd /opt/neverwinterdp && ./scribengin/bin/shell.sh vm info"

ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master \
   "cd /opt/neverwinterdp && \
    ./scribengin/bin/shell.sh vm submit --upload-app /opt/neverwinterdp/vm-sample \
      --registry-connect zookeeper-1:2181 --registry-db-domain /NeverwinterDP --registry-implementation com.neverwinterdp.registry.zk.RegistryImpl \
      --name vm-sample-1 --role vm-sample --vm-application com.neverwinterdp.vm.sample.VMSampleApp"

ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master \
   "cd /opt/neverwinterdp && \
    ./scribengin/bin/shell.sh vm submit --dfs-app-home /applications/vm-sample \
      --registry-connect zookeeper-1:2181 --registry-db-domain /NeverwinterDP --registry-implementation com.neverwinterdp.registry.zk.RegistryImpl \
      --name vm-sample-2 --role vm-sample --vm-application com.neverwinterdp.vm.sample.VMSampleApp"

sleep 25
ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "cd /opt/neverwinterdp && ./scribengin/bin/shell.sh registry dump"
#Clean up
#$ROOT/docker/scribengin/docker.sh cluster --clean-containers --neverwinterdp-home=$NEVERWINTER_HOME


#SCRIPT_DIR is the directory this script is in.  Allows us to execute without relative paths
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

#This Script will set root directory and Neverwinter_home
source $SCRIPT_DIR/setupEnvironment.sh $@

#Set up docker images
$ROOT/docker/scribengin/docker.sh cluster --clean-containers --run-containers --ansible-inventory --deploy --start --neverwinterdp-home=$NEVERWINTER_HOME

#make folder for test results
mkdir testresults

#Give everything time to come up
sleep 5

ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "cd /opt/scribengin/scribengin && ./bin/shell.sh scribengin info"
ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "cd /opt/scribengin/scribengin && ./bin/shell.sh vm info"



#Run dataflow
ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "cd /opt/scribengin/scribengin && \
          ./bin/shell.sh dataflow-test hdfs-to-hdfs \
                 --dataflow-name  hdfs-to-hdfs \
                 --dataflow-id    hdfs-to-hdfs-1 \
                 --worker 3 \
                 --executor-per-worker 1 \
                 --duration 90000 \
                 --task-max-execute-time 1000 \
                 --source-name output \
                 --source-num-of-stream 10 \
                 --source-write-period 5 \
                 --source-max-records-per-stream 100 \
                 --sink-name output \
                 --print-dataflow-info -1 \
                 --debug-dataflow-task  \
                 --debug-dataflow-vm  \
                 --debug-dataflow-activity  \
                 --junit-report HDFS_IntegrationTest.xml \
                 --dump-registry"

#Get results
scp -o stricthostkeychecking=no neverwinterdp@hadoop-master:/opt/scribengin/scribengin/HDFS_IntegrationTest.xml ./testresults/

#Clean up
$ROOT/docker/scribengin/docker.sh cluster --clean-containers --neverwinterdp-home=$NEVERWINTER_HOME
#SCRIPT_DIR is the directory this script is in.  Allows us to execute without relative paths
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

#This Script will set root directory and Neverwinter_home
source $SCRIPT_DIR/setupEnvironment.sh $@

#Set up docker images
$ROOT/docker/scribengin/docker.sh cluster --clean-containers --run-containers --ansible-inventory --deploy-scribengin --start --neverwinterdp-home=$NEVERWINTER_HOME

scp -o "StrictHostKeyChecking no" -r /root/.aws neverwinterdp@hadoop-master:/home/neverwinterdp/

#make folder for test results
mkdir testresults

#Give everything time to come up
sleep 5

  echo "testing existence of .aws folder on local host"
  if [ "$(ls -A /root/.aws)" ] ; then 
    echo "Credentials exist on host !!!!"
  else
    echo "Credentials dont exist on host."
  fi


 echo "testing existence of .aws folder on remote host"
is_exists=`ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "if [ -e /home/neverwinterdp/.aws/credentials ] ; then echo '0';else echo '1'; fi"`
if [ $is_exists == '0' ]; then
  echo "Credentials file exists on remote"
else
  echo "credentials file does not exists on remote"
fi

  echo "testing existence of sunjce file on remote host."
is_exists2=`ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "if [ -e /usr/lib/jvm/java-7-openjdk-amd64/jre/lib/ext/sunjce_provider.jar ] ; then echo '0';else echo '1'; fi"`
  if [ $is_exists2 == '0' ] ; then 
    echo "sunjce exists !!!!"
  else
    echo "sunjce exists not."
  fi


ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "cd /opt/scribengin/scribengin && ./bin/shell.sh scribengin info"
ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "cd /opt/scribengin/scribengin && ./bin/shell.sh vm info"


#Run dataflow
UUID=$(cat /proc/sys/kernel/random/uuid)
ssh -o "StrictHostKeyChecking no" neverwinterdp@hadoop-master "cd /opt/scribengin/scribengin && \
          ./bin/shell.sh dataflow-test s3-to-s3 \
                 --dataflow-name  s3-to-s3 \
                 --dataflow-id    s3-to-s3-1 \
                 --worker 3 \
                 --executor-per-worker 1 \
                 --duration 90000 \
                 --task-max-execute-time 10000 \
                 --source-location jenkins-dataflow-test-$UUID \
                 --source-name dataflow-test \
                 --source-num-of-stream 1    \
                 --source-max-records-per-stream 1000 \
                 --source-auto-create-bucket \
                 --sink-location jenkins-dataflow-test-$UUID  \
                 --sink-name dataflow-test  \
                 --sink-auto-delete-bucket  \
                 --print-dataflow-info -1 \
                 --debug-dataflow-task  \
                 --debug-dataflow-vm  \
                 --debug-dataflow-activity  \
                 --junit-report S3_IntegrationTest.xml \
                 --dump-registry"

#Get results
scp -o stricthostkeychecking=no neverwinterdp@hadoop-master:/opt/scribengin/scribengin/S3_IntegrationTest.xml ./testresults/

#Clean up
#$ROOT/docker/scribengin/docker.sh cluster --clean-containers --neverwinterdp-home=$NEVERWINTER_HOME

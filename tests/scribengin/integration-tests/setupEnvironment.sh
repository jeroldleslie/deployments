function usage(){
  echo "  Usage: "
  echo "       ./integrationScript.sh --neverwinterdp-home=/path/to/NeverwinterDP/"
  echo "     Or you can set an environment variable:"
  echo "       export NEVERWINTERDP_HOME=/path/to/NeverwinterDP/"
  echo "       ./integrationScript.sh"
  echo "     Options: "
  echo "           --neverwinterdp-home      - Where NeverwinterDP is locally"
  echo "           --test-results-location   - Where to store test results (default is ./testresults)"
  echo "     Flags that can be set: "
  echo "           --clean    - Clean the cluster with clusterCommander"
  echo "           --stop     - Stop the cluster with clusterCommander"
  echo "           --start    - Start the cluster with clusterCommander"
  echo "           --restart  - Restart the cluster with clusterCommander"
  echo "           --deploy   - Build then deploy scribengin with clusterCommander"
  echo "           --kafka-config-file        - Kafka config file to use when restarting cluster"
  echo "           --zookeeper-config-file    - Zookeeper config filt to use when restarting cluster"
  
}

function has_opt() {
  OPT_NAME=$1
  shift
  #Par the parameters
  for i in "$@"; do
    if [[ $i == $OPT_NAME ]] ; then
      echo "true"
      return
    fi
  done
  echo "false"
}

function get_opt() {
  OPT_NAME=$1
  DEFAULT_VALUE=$2
  shift
  
  #Par the parameters
  for i in "$@"; do
    index=$(($index+1))
    if [[ $i == $OPT_NAME* ]] ; then
      value="${i#*=}"
      echo "$value"
      return
    fi
  done
  echo $DEFAULT_VALUE
}


#ROOT dir for neverwinterdp-deployments
ROOT=$( dirname $( dirname $( dirname $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ))))

NEVERWINTER_HOME=$(get_opt --neverwinterdp-home $NEVERWINTERDP_HOME $@)
TEST_RESULTS_LOCATION=$(get_opt --test-results-location './testresults/' $@)
KAFKA_CONFIG_FILE=$(get_opt --kafka-config-file $ROOT/configs/bootstrap/post-install/kafka/config/server.properties $@)
ZOOKEEPER_CONFIG_FILE=$(get_opt --zookeeper-config-file $ROOT/configs/bootstrap/post-install/zookeeper/conf/zoo.cfg $@)
CLEAN=$(has_opt --clean $@)
START=$(has_opt --start $@)
STOP=$(has_opt --stop $@)
RESTART=$(has_opt --restart $@)
DEPLOY=$(has_opt --deploy $@)
HELP=$(has_opt --help $@)


if [ $HELP == "true" ] ; then
  usage
  exit
fi

if [ $RESTART == "true" ] ; then
  START="true"
  STOP="true"
fi


if [ ! -d $NEVERWINTER_HOME ] ; then
  echo "$NEVERWINTER_HOME is not a valid directory!"
  usage
  exit
elif [ "$NEVERWINTER_HOME" = "" ] ; then
  echo "NEVERWINTERDP_HOME is not set!"
  usage
  exit
fi




export ANSIBLE_HOST_KEY_CHECKING=False
export NEVERWINTERDP_HOME=$NEVERWINTER_HOME
export SKIP_DOCKER=$SKIP_DOCKER
export TEST_RESULTS_LOCATION=$TEST_RESULTS_LOCATION
export CLEAN=$CLEAN
export START=$START
export STOP=$STOP
export RESTART=$RESTART
export DEPLOY=$DEPLOY

#make folder for test results
if [ ! -d $TEST_RESULTS_LOCATION ] ; then
  mkdir $TEST_RESULTS_LOCATION
fi

clusterCommander="$ROOT/tools/cluster/clusterCommander.py"
if [ $STOP == "true" ] ; then
  $clusterCommander cluster --force-stop
fi
if [ $DEPLOY == "true" ] ; then
  $clusterCommander ansible --write-inventory-file --deploy-scribengin
fi
if [ $CLEAN == "true" ] ; then
  $clusterCommander cluster --clean
fi
if [ $START == "true" ] ; then
  $clusterCommander cluster --kafka-server-config $KAFKA_CONFIG_FILE --zookeeper-server-config $ZOOKEEPER_CONFIG_FILE --start
  #Give everything time to come up
  sleep 5
fi



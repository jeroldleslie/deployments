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
  echo "           --clean         - Clean the cluster with clusterCommander"
  echo "           --stop          - Stop the cluster with clusterCommander"
  echo "           --start         - Start the cluster with clusterCommander"
  echo "           --restart       - Restart the cluster with clusterCommander"
  echo "           --deploy        - Build then deploy scribengin with clusterCommander"
  echo "           --profile-type  - Profile type (default/performance)"
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
CLEAN=$(has_opt --clean $@)
START=$(has_opt --start $@)
STOP=$(has_opt --stop $@)
RESTART=$(has_opt --restart $@)
DEPLOY=$(has_opt --deploy $@)
HELP=$(has_opt --help $@)
PROFILE_TYPE=$(get_opt --profile-type 'default' $@)

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
serviceCommander="$ROOT/tools/serviceCommander/serviceCommander.py"
inventoryFile="/tmp/scribengininventory"
if [ $STOP == "true" ] ; then
  $serviceCommander --cluster --force-stop -i $inventoryFile
fi
if [ $DEPLOY == "true" ] ; then
  $clusterCommander ansible --write-inventory-file --inventory-file $inventoryFile
  $serviceCommander -i $inventoryFile -e "scribengin" --install --configure
fi
if [ $CLEAN == "true" ] ; then
  $serviceCommander --cluster --clean -i $inventoryFile
fi
if [ $START == "true" ] ; then
  $serviceCommander --cluster --start -i $inventoryFile  --profile-type $PROFILE_TYPE
  #Give everything time to come up
  sleep 5
fi



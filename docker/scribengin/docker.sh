#!/bin/bash

function h1() {
  echo ""
  echo "###########################################################################################################"
  echo "$@"
  echo "###########################################################################################################"
}

function has_opt() {
  OPT_NAME=$1
  shift
  #Par the parameters
  for i in "$@"; do
    if [[ $i == $OPT_NAME* ]] ; then
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

function login_ssh_port() {
  docker port $1 22 | sed 's/.*://'
}

function container_ids() {
  echo $(docker ps -q  | tr '\n' ' ')
}

function all_container_ids() {
  echo $(docker ps -a -q | tr '\n' ' ')
}

function ip_route() {
  if [[ $OSTYPE == *"darwin"* ]] ; then
    h1 "Updating route for OSX"
    sudo route -n add 172.17.0.0/16 `boot2docker ip`
  fi
}

function container_update_hosts() {
  h1 "Update /etc/hosts file on containers"
  HOSTS=$'## scribengin server ##\n'
  HOSTS+=$'127.0.0.1 localhost\n\n'
  
  for container_id in $(container_ids); do
    #extract the container name
    container_name=$(docker inspect -f {{.Config.Hostname}} $container_id)
    container_domain=$(docker inspect -f {{.Config.Domainname}} $container_id)
    #extract the container ip
    container_ip=$(docker inspect -f "{{ .NetworkSettings.IPAddress }}" $container_id)
    #extract the container running state
    container_running=$(docker inspect -f {{.State.Running}} $container_id)
    HOSTS+="$container_ip $container_name"
    HOSTS+=$'\n'
    #echo "container id = $container_id, container name = $container_name, container ip = $container_ip, container running = $container_running"
  done

  echo ""
  echo "Insert Content:"
  echo ""
  echo "-----------------------------------------------------------------------------------------------"
  echo "$HOSTS"
  echo "-----------------------------------------------------------------------------------------------"
  for container_id in $(container_ids); do
    #extract the container name
    container_name=$(docker inspect -f {{.Config.Hostname}} $container_id)
    
    #Update ssh key while we're at it
    echo "ssh-keygen -R $container_name"
    ssh-keygen -R $container_name
    
    echo "Update /etc/hosts for $container_name"
    ssh -o StrictHostKeyChecking=no -p $(login_ssh_port $container_id) root@$HOST_IP "echo '$HOSTS'  > /etc/hosts"
  done
}

function host_machine_update_hosts() {
  h1 "Updating host machine's /etc/hosts file"
  #Updating /etc/hosts file on host machine
  h1 "Updating /etc/hosts file of host machine"
  
  startString="##SCRIBENGIN CLUSTER START##"
  endString="##SCRIBENGIN CLUSTER END##"
  
  #Build entry to add to /etc/hosts by reading info from Docker
  hostString="$hostString\n$startString\n"
  for container_id in $(container_ids); do
    hostname=$(docker inspect -f '{{ .Config.Hostname }}' $container_id)
    hostString="$hostString$(docker inspect -f "{{ .NetworkSettings.IPAddress }}" $hostname)    $hostname\n"
  done
  hostString="$hostString$endString\n"
  
  if [ ! -f /etc/hosts ] ; then
    echo -e "\nERROR!!!\nYou don't have write permissions for /etc/hosts!!!\nManually add this to your /etc/hosts file:"
    echo -e "$hostString"
    return
  fi
  
  #Strip out old entry
  out=`sed "/$startString/,/$endString/d" /etc/hosts`
  #write new hosts file
  echo -e "$out\n$hostString" > /etc/hosts
  echo -e "$hostString"
  
  ip_route
}


function clean_image() {
  h1 "Clean the images"
  docker rmi -f ubuntu:scribengin
}

function build_image() {
  h1 "Building Image"
  
  #Direcotry this script is in
  DOCKERSCRIBEDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
  mkdir $DOCKERSCRIBEDIR/tmp
  
  cp ~/.ssh/id_rsa      $DOCKERSCRIBEDIR/tmp/id_rsa
  cp ~/.ssh/id_rsa.pub  $DOCKERSCRIBEDIR/tmp/id_rsa.pub
  cp ~/.ssh/id_rsa.pub $DOCKERSCRIBEDIR/tmp/authorized_keys
  
  docker build -t ubuntu:scribengin $BIN_DIR
  
  rm -rf $DOCKERSCRIBEDIR/tmp
}

function clean_containers() {
  h1 "Cleaning Containers"
  for container_id in $(all_container_ids); do
    container_name=$(docker inspect -f {{.Config.Hostname}} $container_id)
    docker rm -f $container_id
    echo "Remove the instance $container_name"
  done
}

function launch_containers() {
  h1 "Launching Containers"
  #Checks to make sure images exist
  #If they don't exist, then create them
  scribeImageLine=$(docker images | grep scribengin)
  if [ "$scribeImageLine" == "" ] ; then
    clean_image
    build_image $@
  fi
  
  NUM_KAFKA_BROKER=$(get_opt --kafka-server '3' $@)
  NUM_ZOOKEEPER_SERVER=$(get_opt --zk-server 1 $@)
  NUM_HADOOP_WORKER=$(get_opt --hadoop-worker 3 $@)
  
  NUM_ELASTICSEARCH_SERVER=$(get_opt --elasticsearch-server 1 $@)
  
  NUM_MONITORING=$(get_opt --monitoring-server 1 $@)
  
  h1 "Launch hadoop-master containers"
  docker run -d -p 22 -p 50070:50070 -p 9000:9000 -p 8030:8030 -p 8032:8032 -p 8088:8088 --privileged -h hadoop-master --name hadoop-master  ubuntu:scribengin
  
  h1 "Launch hadoop-worker containers"
  for (( i=1; i<="$NUM_HADOOP_WORKER"; i++ ))
  do
    NAME="hadoop-worker-"$i
    docker run -d -p 22 --privileged -h "$NAME" --name "$NAME" ubuntu:scribengin
  done

  h1 "Launch zookeeper containers"
  for (( i=1; i<="$NUM_ZOOKEEPER_SERVER"; i++ ))
  do
    NAME="zookeeper-"$i
    PORT_NUM=`expr 2181 - 1 + $i`
    docker run -d -p 22 -p $PORT_NUM:2181 --privileged -h "$NAME" --name "$NAME"  ubuntu:scribengin
  done  

  h1 "Launch kafka containers"
  for (( i=1; i<="$NUM_KAFKA_BROKER"; i++ ))
  do
    NAME="kafka-"$i
    docker run -d -p 22 -p 9092 --privileged -h "$NAME" --name "$NAME"  ubuntu:scribengin
  done

  h1 "Launch elasticsearch containers"
  for (( i=1; i<="$NUM_ELASTICSEARCH_SERVER"; i++ ))
  do
    NAME="elasticsearch-"$i
    PORT_NUM=`expr 9300 - 1 + $i`
    docker run -d -p 22 -p $PORT_NUM:9300 --privileged -h "$NAME" --name "$NAME"  ubuntu:scribengin
  done
  
  h1 "Launch monitoring containers"
  for (( i=1; i<="$NUM_MONITORING"; i++ ))
  do
    NAME="monitoring-"$i
    docker run -d -p 22 -p 3000 -p 5601 --privileged -h "$NAME" --name "$NAME"  ubuntu:scribengin
  done
  
  docker ps
}

function ansible_inventory(){
  h1 "Creating ansible inventory file"
  ANSIBLE_USER=$(get_opt    --ansible-user    'neverwinterdp' $@)
  ANSIBLE_SSH_KEY=$(get_opt --ansible-ssh-key '~/.ssh/id_rsa' $@)
  INVENTORY_FILE_LOCATION=$(get_opt --inventory-file-location 'scribengininventory' $@)
  
  #list of container regex's - these must match the ansible group names
  regexList=("monitoring"
             "kafka"
             "hadoop-master"
             "hadoop-worker"
             "zookeeper"
             "elasticsearch")
  #File contents we'll write to $INVENTORY_FILE_LOCATION
  filecontents=""
  
  #Do all the work to get container names
  #Doing it here so we only have to do it once
  container_ids=$(container_ids)
  container_names=()
  for container_id in ${container_ids[@]}; do
    container_names+=($(docker inspect -f {{.Config.Hostname}} $container_id))
  done
  
  #Go through all docker images, see if it matches the regex, and add it to the inventory
  for regex in ${regexList[@]}; do
    #our ansible groups use _ instead of - character to help differentiate the groups from containers
    ansiblegroup=$(echo $regex | sed -e 's/-/_/g')
    #Write the ansible group header
    filecontents="$filecontents\n[$ansiblegroup]\n"
    for container_name in ${container_names[@]}; do
      #If the hostname matches the header, then add it to the ansible group
      if [[ $container_name =~ $regex.* ]] ; then
        filecontents="$filecontents$container_name ansible_ssh_user=$ANSIBLE_USER ansible_ssh_private_key_file=$ANSIBLE_SSH_KEY\n"
      fi
    done
  done
  echo "Writing ansible inventory file to $INVENTORY_FILE_LOCATION"
  echo -e $filecontents > $INVENTORY_FILE_LOCATION
  echo -e $filecontents
}

function deploy(){
  h1 "Provisioning with Ansible"
  #SCRIPT_DIR is the directory this script is in.  Allows us to execute without relative paths
  SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
  INVENTORY_FILE_LOCATION=$(get_opt --inventory-file-location 'scribengininventory' $@)
  PLAYBOOK_FILE_LOCATION="$(get_opt --playbook-file-location "$SCRIPT_DIR/../../ansible/scribenginCluster.yml" $@)"
  ANSIBLE_FORKS=$(get_opt --ansible-forks 10 $@)
  NEVERWINTERDP_HOME=$(get_opt --neverwinterdp-home '' $@)
  
  if [[ $NEVERWINTEDP_HOME == "" ]] ; then
    ansible-playbook $PLAYBOOK_FILE_LOCATION -i $INVENTORY_FILE_LOCATION -f $ANSIBLE_FORKS
  else
    ansible-playbook $PLAYBOOK_FILE_LOCATION -i $INVENTORY_FILE_LOCATION -f $ANSIBLE_FORKS --extra-vars "neverwinterdp_home_override=$NEVERWINTERDP_HOME"
  fi
}

function startCluster(){
  h1 "Starting cluster"
  ssh -o StrictHostKeyChecking=no neverwinterdp@hadoop-master "cd /opt/cluster && python clusterCommander.py cluster --start --clean status"
}

function cluster(){
  CLEAN_IMAGE=$(has_opt "--clean-image" $@ )
  BUILD_IMAGE=$(has_opt "--build-image" $@ )
  CLEAN_CONTAINERS=$(has_opt "--clean-containers" $@ )
  RUN_CONTAINERS=$(has_opt "--run-containers" $@ )
  ANSIBLE_INVENTORY=$(has_opt "--ansible-inventory" $@ )
  DEPLOY=$(has_opt "--deploy" $@)
  STOP_CLUSTER=$(has_opt "--stop-cluster" $@ )
  FORCE_STOP_CLUSTER=$(has_opt "--force-stop-cluster" $@ )
  START=$(has_opt "--start" $@)
  LAUNCH=$(has_opt "--launch" $@ )
  
  
  if [ $CLEAN_CONTAINERS == "true" ] || [ $LAUNCH == "true" ] ; then
    clean_containers
  fi
  
  if [ $CLEAN_IMAGE == "true" ] || [ $LAUNCH == "true" ]  ; then
    clean_image
  fi
  
  if [ $BUILD_IMAGE == "true" ] || [ $LAUNCH == "true" ] ; then
    build_image $@
  fi
  
  
  if [ $RUN_CONTAINERS == "true" ] || [ $LAUNCH == "true" ] ; then
    launch_containers $@
    host_machine_update_hosts
    container_update_hosts $@
  fi
  
  if [ $ANSIBLE_INVENTORY == "true" ] || [ $LAUNCH == "true" ] ; then
    ansible_inventory $@
  fi
  
  if [ $DEPLOY == "true" ] || [ $LAUNCH == "true" ] ; then
    deploy $@
  fi
  
  if [ $START == "true" ] || [ $LAUNCH == "true" ] ; then
    startCluster $@
  fi
  
  if [ $STOP_CLUSTER == "true" ] ; then
    ssh -o StrictHostKeyChecking=no neverwinterdp@hadoop-master "cd /opt/cluster && python clusterCommander.py cluster --stop status"
  fi
  
  if [ $FORCE_STOP_CLUSTER == "true" ] ; then
    ssh -o StrictHostKeyChecking=no neverwinterdp@hadoop-master "cd /opt/cluster && python clusterCommander.py cluster --force-stop status"
  fi
  
  
}

function printUsage() {
  echo "Cluster command options: "
  echo "  Command \"image\" consists of the sub commands: "
  echo "      build                      : To build the ubuntu os image with the required components"
  echo "      clean                      : To remove the image"
  echo "    Examples:"
  echo "       ./docker.sh image build"
  echo "  Command \"container\" consists of the sub commands: "
  echo "      run                        : To run the containers(hadoop, zookeeper, kafka...)"
  echo "      clean                      : To remove and destroy all the running containers"
  echo "      update-hosts               : To update the /etc/hosts in all the running containers"
  echo "    Examples:"
  echo "       ./docker.sh container run"
  echo "  Command \"cluster\" consists of the following options: "
  echo "       Options: "
  echo "         --clean-image         : Cleans docker images"
  echo "         --build-image         : Builds the docker image for Scribengin"
  echo "         --clean-containers    : Cleans docker containers"
  echo "         --run-containers      : Runs docker containers"
  echo "         --ansible-inventory   : Creates ansible inventory file"
  echo "         --deploy              : Run ansible playbook"
  echo "         --start               : Starts services"
  echo "         --stop-cluster        : Stops cluster services"
  echo "         --force-stop-cluster  : Force stops cluster services"
  echo "         --launch              : Cleans docker image and containers, Builds image and container, and starts"
  echo "    Examples:"
  echo "        ./docker.sh cluster [options]"
  echo "       ./docker.sh cluster --launch"
  echo "  Extra options for cluster --deploy: "
  echo "         --inventory-file-location : Path to ansible inventory file.                 Default='scribengininventory'"
  echo "         --playbook-file-location  : Path to playbook to run.                        Default='SCRIPT_DIR/./../ansible/playbooks/scribenginCluster.yml'"
  echo "         --ansible-forks           : Number of number of parallel processes to use.  Default=10 "
  echo "         --neverwinterdp-home      : Path to NeverwinterDP home"
  echo "  Other commands:"
  echo "    ip-route                   : If you are running macos, use this command to route the 127.17.0.0 ip range to the boot2docker host. It allows to access the docker container directly from the MAC"
  echo "    ansible-inventory          : Creates ansible inventory file"
  
}


##########################################################
# Start script                                           #
##########################################################
HOST_IP="127.0.0.1"
OS=`uname`
if [[ "$OS" == 'Linux' ]]; then
   OS='linux'
elif [[ "$OS" == 'FreeBSD' ]]; then
   platform='freebsd'
elif [[ "$OS" == 'Darwin' ]]; then
   platform='macos'
   HOST_IP=$(boot2docker ip)
fi

BIN_DIR=`dirname "$0"`
BIN_DIR=`cd "$BIN_DIR"; pwd`


# get command
COMMAND=$1
shift
 
if [ "$COMMAND" = "image" ] ; then
  # get subcommand
  SUB_COMMAND=$1
  shift
  if [ "$SUB_COMMAND" = "build" ] ; then
    build_image $@
  elif [ "$SUB_COMMAND" = "clean" ] ; then
    clean_image $@
  else
    printUsage
  fi
elif [ "$COMMAND" = "container" ] ; then
  # get subcommand
  SUB_COMMAND=$1
  shift
  if [ "$SUB_COMMAND" = "clean" ] ; then
    clean_containers $@
  elif [ "$SUB_COMMAND" = "run" ] ; then
    launch_containers $@
    host_machine_update_hosts $@
    container_update_hosts $@
  elif [ "$SUB_COMMAND" = "update-hosts" ] ; then
    host_machine_update_hosts $@
    container_update_hosts $@
  else
    printUsage
  fi
elif [ "$COMMAND" = "ansible-inventory" ] ; then
  ansible_inventory $@
elif [ "$COMMAND" = "cluster" ] ; then
  cluster $@
elif [ "$COMMAND" = "ip-route" ] ; then
  ip_route
elif [ "$COMMAND" = "update-hosts" ] ; then
  host_machine_update_hosts
else
  h1 "Docker Images"
  docker images
  h1 "Docker Running Containers"
  docker ps
  h1 "docker.sh usage"
  printUsage
fi



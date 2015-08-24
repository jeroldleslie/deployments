#!/bin/bash

function h1() {
  echo ""
  echo "###########################################################################################################"
  echo "$@"
  echo "###########################################################################################################"
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

function login_ssh_port() {
  docker port $1 22 | sed 's/.*://'
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
  hostString="$startString\n"
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


h1 "Launch first part of cluster"
../scribengin/docker.sh cluster --run-containers --ansible-inventory --start  --monitoring-server=0 --elasticsearch-server=0
h1 "Kill Scribengin and VMmaster"
../../tools/cluster/clusterCommander.py scribengin --force-stop
../../tools/cluster/clusterCommander.py vmmaster --force-stop

h1 "Launch storm cluster"
docker run  -ti -v /sys/fs/cgroup:/sys/fs/cgroup -d -p 22 --privileged=true -h storm-zookeeper --name storm-zookeeper centos:scribengin 
docker run  -ti -v /sys/fs/cgroup:/sys/fs/cgroup -d -p 22 --privileged=true -h storm-nimbus --name storm-nimbus centos:scribengin
docker run  -ti -v /sys/fs/cgroup:/sys/fs/cgroup -d -p 22 --privileged=true -h storm-supervisor-1 --name storm-supervisor-1 centos:scribengin
docker run  -ti -v /sys/fs/cgroup:/sys/fs/cgroup -d -p 22 --privileged=true -h storm-supervisor-2 --name storm-supervisor-2 centos:scribengin
docker run  -ti -v /sys/fs/cgroup:/sys/fs/cgroup -d -p 22 --privileged=true -h storm-supervisor-3 --name storm-supervisor-3 centos:scribengin

container_update_hosts
host_machine_update_hosts

ansible-playbook ../../ansible/flinkStormTestplaybook.yml -i ./testInventory

h1 "Start services"
ssh -o "StrictHostKeyChecking no" neverwinterdp@storm-zookeeper /opt/storm-zookeeper/bin/zkServer.sh start-foreground &
ssh -o "StrictHostKeyChecking no" neverwinterdp@storm-nimbus /opt/storm/bin/storm nimbus &
ssh -o "StrictHostKeyChecking no" neverwinterdp@storm-nimbus /opt/storm/bin/storm ui &
ssh -o "StrictHostKeyChecking no" neverwinterdp@storm-supervisor-1 /opt/storm/bin/storm supervisor &
ssh -o "StrictHostKeyChecking no" neverwinterdp@storm-supervisor-2 /opt/storm/bin/storm supervisor &
ssh -o "StrictHostKeyChecking no" neverwinterdp@storm-supervisor-3 /opt/storm/bin/storm supervisor &



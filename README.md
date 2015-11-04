# Neverwinterdp Deployments

This project automates the installation, configuration, starting, stopping, force stopping and cleaning specific service or group of services or pre-defined cluster related services (currently scribengin related services are pre-defined in as a cluster). It works independently.

Also this project automates integration tests of scribengin. To launch scribengin cluster, it need  to set NEVERWINTERDP_HOME env variable or you can give --neverwinterdp-home option when running the commands.

All the deployment automations are build on top of ansible playbooks, so neverwinterdp deployments require ansible inventory file to run. 

##Components 

####[ansible](ansible/README.md) 

####[docker](docker/scribengin/README.md)
####[clusterCommander](tools/cluster/README.md)
####[serviceCommander](tools/serviceCommander/README.md)
####[statusCommander](tools/statusCommander/README.md)
####[clusterExec](tools/clusterExec/README.md)



##Installation
###Prerequisites
You need to install python (Python 2.7.6 recomanded), ansible (ansible 1.9.3 recomanded) and other dependencies like tabulate, click, paramiko

```
#Install required modules
sudo easy_install --upgrade nose==1.3.4 tabulate paramiko junit-xml click requests pip
sudo pip install pyopenssl==0.15.1 ndg-httpsclient pyasn1 kazoo elasticsearch python-digitalocean pyyaml --upgrade
```

###Checkout locally

```
git clone https://<username>@bitbucket.org/nventdata/neverwinterdp-deployments.git
cd neverwinterdp-deployments
```

##Usage

###Service Commander
#####Examples

```
#Assumes inventory file is at ~/inventory, or you can pass inventory file location to override ~/inventory using -i option
#Start all cluster services
./serviceCommander.py --cluster --start
#Install, configure, force-stop, clean, restart cluster
./serviceCommander.py --cluster --install --configure --force-stop --clean --start
#Start all cluster services and also two extra services called serviceX and serviceY
./serviceCommander.py --cluster --services serviceX,serviceY  --start
#Install, configure, and start kafka and zookeeper
./serviceCommander.py --services kafka,zookeeper --install --configure --start 
#Start zookeeper
./serviceCommander.py --services zookeeper --start
#Start kafka and point to a non-default ansible-root-dir
./serviceCommander.py --services kafka --start --ansible-root-dir /etc/ansible/
```

###Status Commander
#####Examples

```
#Assumes inventory file is at ~/inventory, or you can pass inventory file location to override ~/inventory using -i option
#Normal usage.
./statusCommander.py
#To change the number of threads to run at a time
./statusCommander.py -i inventoryFile --threads 5
#To change the amount of time on an ssh connection before timing out
./statusCommander.py -i inventoryFile --timeout 45
```

###Cluster Exec
#####Examples

```
#See below for sample inventory file
#Execute command on all hosts in the hadoop_worker group.  Assumes inventory file is at ~/inventory
./clusterExec.py -g hadoop_worker -c "ls -la"
#Execute command on all hosts in the zookeeper group
./clusterExec.py -g zookeeper -c "ls -la"
#Execute command on all hosts in the kafka group, set the SSH timeout to 10 seconds, specify inventory file
./clusterExec.py -i /tmp/scribengininventoryDO -g kafka -c "ls -la" -t 10
#Special case: Execute command on all hosts in the inventory file
./clusterExec.py -g cluster -c "ls -la"
#Special case: Execute command on hosts in hadoop_worker and hadoop_master group
./clusterExec.py -g hadoop -c "ls -la"
```
###Log Grep
#####Examples
```
#Search kafka logs(This assumes your ansible inventory file is found at ~/inventory)
./loggrep.py kafka
#Search kafka and zookeeper logs, specify an inventory file
./loggrep.py -i /tmp/scribengininventoryDO kafka zookeeper
#Search the whole cluster's logs (kafka, zk, and hadoop)
./loggrep.py -i /tmp/scribengininventoryDO cluster
#Search Kafka logs for "info"
./loggrep.py -i /tmp/scribengininventoryDO kafka -s info
#Search Kafka logs, use custom grep options
./loggrep.py -i /tmp/scribengininventoryDO kafka -g "-i -c"
#Change up the search.  The following command will run on all your kafka machines:
#find /opt/new_kafka_folder \( -iname "*.log" \) -exec grep -i -c 'searchString' {} \; -print
./loggrep.py -i /tmp/scribengininventoryDO kafka --find-folder /opt/new_kafka_folder --find-iname "*.log" --grep-option "-i -c" --grep-string "searchString"
#Search all cluster logs with custom search string and grep optoins
./loggrep.py -i /tmp/scribengininventoryDO cluster -g "-i -c" -s searchString
```

##Developer Tools
Neverwinterdp Deployment tools can be installed on any of your cluster machines using ```./serviceCommander.py --developer-tools --inventory-file $INVENTORY_FILE```

Currently ```monitoring``` is the default group of hosts to install developer tools. It can be modified as your choice in ```/neverwinterdp-deployments/ansible/developer_tools.yml```

###Developer Tools Usage
Login into any one of the machine which installed developer tools ```ex: ssh monitoring-1```

You can run neverwinterdp components form anywhere in the machine (ie., from any directory) using ```ndpservice, ndpstatus, ndploggrep, ndpexec```

#####Examples
```
$ndpservice --cluster --start
$ndpstatus -i inventoryFile
$ndpexec -g hadoop_worker -c "ls -la"
$ndploggrep kafka
```


##Quick launch scribengin clusters and tests

###1. Run cluster
#####Launch Docker containers
```
#./neverwinterdp-deployments/tests/scribengin/tracking/stability/setup-docker.sh
```

or
#####Launch digitakocean cluster
```
#./neverwinterdp-deployments/tests/scribengin/tracking/stability/setup-cluster.sh --subdomain=test
```

###2. Run dev test

```
#./neverwinterdp-deployments/tests/scribengin/tracking/stability/dev-run-test.sh
```

##NeverwinterDP Deployments Structure
- You must have a directory structure to support Service Commander
- Each service must have its own playbook
- Each service you attempt to use must correspond to a role in your [ansible-root-dir]
- Example: 

```
./neverwinterdp-deployments
|-- ansible
|   |-- common.yml
|   |-- zookeeper.yml
|   |-- profile
|   |   |-- default.yml
|   |   |-- performance.yml
|   |   |-- small.yml
|   |   `-- stability.yml
|   |-- programs
|   |   |-- openjdk7_java.yml
|   |   `-- wget.yml
|   |-- roles
|   |   |-- common
|   |   |   `-- tasks
|   |   |       `-- main.yml
|   |   `-- zookeeper
|   |       |-- files
|   |       |   |-- conf
|   |       |   |   `-- log4j.properties
|   |       |   `-- zookeeper-server
|   |       |-- handlers
|   |       |   `-- main.yml
|   |       |-- meta
|   |       |   `-- main.yml
|   |       |-- tasks
|   |       |   `-- main.yml
|   |       `-- templates
|   |           |-- java.env.j2
|   |           |-- myid.j2
|   |           |-- zoo.cfg.j2
|   |           |-- zookeeper-env.sh.j2
|   |           `-- zookeeper.service.j2
|-- docker
|   |-- scribengin
|   |   |-- dockerfile
|   |   |   |-- centos
|   |   |   |   `-- Dockerfile
|   |   |   `-- ubuntu
|   |   |       `-- Dockerfile
|   |   |-- docker.sh
|-- tests
|   |-- kafka
|   |   `-- perf
|   |       `-- run-kafka-perf-test.sh
|   `-- scribengin
|       `-- tracking
|           `-- stability
|               |-- run-test.sh
|               |-- setup-cluster.sh
|               `-- setup-docker.sh
`-- tools
    |-- cluster
    |   |-- clusterCommander.py
    |-- clusterExec
    |   |-- clusterExec.py
    |-- loggrep
    |   |-- loggrep.py
    |-- serviceCommander
    |   `-- serviceCommander.py
    `-- statusCommander
        `-- statusCommander.py                                 
```


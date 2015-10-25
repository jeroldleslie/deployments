# Neverwinterdp Deployments

This project automates the installation, configuration, starting, stopping, force stopping and cleaning specific service or group of services or pre-defined cluster related services (currently scribengin related services are pre-defined in as a cluster). It works independently.

Also this project automates integration tests of scribengin. To launch scribengin cluster, it need  to set NEVERWINTERDP_HOME env variable or you can give --neverwinterdp-home option when running the commands.

All the deployment automations are build on top of ansible playbooks, so neverwinterdp deployments require ansible inventory file to run. 




###Setup

```
user@machine: $ sudo pip install ansible tabulate click paramiko
```



##Components 

###[ansible](ansible/README.md) 

###[docker](docker/scribengin/README.md)
###[clusterCommander](tools/cluster/README.md)
###[serviceCommander](tools/serviceCommander/README.md)
###[statusCommander](tools/statusCommander/README.md)
###[clusterExec](tools/clusterExec/README.md)


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


##Usage

###Setup neverwinterdp_home

- Checkout Scribengin into neverwinterdp_home

```
git clone https://github.com/Nventdata/NeverwinterDP
```

- Set NEVERWINTERDP_HOME environment variable (optional) or you can give --neverwinterdp-home option value in the commandline arguments.

```
export NEVERWINTERDP_HOME=/your/path/to/NeverwinterDP
```
   
***  

###Running neverwinterdp deployments - SIMPLE STEPS

```
#Checkout neverwinterdp-deployments project 
git clone git clone https://<bitbucket_user>@bitbucket.org/nventdata/neverwinterdp-deployments.git
cd /path/to/neverwinterdp-deployments
```
####Build docker image with scribengin in one step
```
#Build images, launch containers, run ansible
$cd /path/to/neverwinterdp-deployments
$docker/scribengin/docker.sh  cluster --launch --neverwinterdp-home=/your/path/to/NeverwinterDP
```

####Build/destroy digital ocean containers with scribengin in one step
```
cd neverwinterdp-deployments/tools/cluster/

#Create cluster


/path/to/neverwinterdp-deployments/tools/clusterCommander/clusterCommander.py digitalocean --launch --neverwinterdp-home $NEVERWINTERDP_HOME --ansible-inventory-location $INVENTORY --create-containers /path/to/neverwinterdp-deployments/ansible/profile/stability.yml --subdomain test

/path/to/neverwinterdp-deployments/tools/serviceCommander/serviceCommander.py --cluster --install --configure --clean --start -i $INVENTORY    
  
#Destroy cluster
./clusterCommander.py digitalocean --destroy --subdomain test
```

####Build digital ocean container for development in one step
```
cd neverwinterdp-deployments/tools/cluster/

#Create it
./clusterCommander.py digitaloceandevsetup --name [name of your machine] --create

#Destroy it
./clusterCommander.py digitaloceandevsetup --name [name of your machine] --destroy
```


***  



Running neverwinterdp deployments - DETAIL
======

####Build docker image with scribengin (explained)

```
#Clean docker image (optional)
docker/scribengin/docker.sh cluster --clean-image

#Build docker image

#if env variable NEVERWINTERDP_HOME is available run 
docker/scribengin/docker.sh cluster --build-image

#if env variable NEVERWINTERDP_HOME is not available run 
docker/scribengin/docker.sh cluster --build-image --neverwinterdp-home=/neverwinterdp/home/path
```

####Sync scribengin with all containers

```
#if env variable NEVERWINTERDP_HOME is available run 
/path/to/neverwinterdp-deployments/tools/serviceCommander/serviceCommander.py --services "scribengin" --install -i $INVENTORY  


#if env variable NEVERWINTERDP_HOME is not available run 
/path/to/neverwinterdp-deployments/tools/serviceCommander/serviceCommander.py --services "scribengin" --install -i $INVENTORY --extra-vars "neverwinterdp_home_override=/neverwinterdp/home/path"

```

####Clean-run-deploy 
```
#To clean containers, run containers ,build scribengin and deploy scribengin 
#into running containers
#if env variable NEVERWINTERDP_HOME is available
docker/scribengin/docker.sh cluster --clean-containers --run-containers --deploy --start-cluster

#if env variable NEVERWINTERDP_HOME is not available
docker/scribengin/docker.sh cluster --clean-containers --run-containers --deploy --start-cluster --neverwinterdp-home=/path/to/neverwinterdp_home
```
 
 [repository](https://bitbucket.org/nventdata/neverwinterdp-deployments)
[documentation](https://bitbucket.org/nventdata/neverwinterdp-deployments/wiki/Home)

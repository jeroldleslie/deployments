# neverwinter deployments

This project automates the installation, configuration and integration tests of scribengin. It works independently. To launch scribengin cluster, it need  to set NEVERWINTERDP_HOME env variable or you can give --neverwinterdp-home option when running the commands.


Components
======
###ansible
Used for provisioning, configuring
###docker.sh
Used to build and configure docker images, and launch containers
###clusterCommander.py
Is used to start/stop/restart cluster or specific processes with the given hostmachine. Also used to monitor running and none running processes in the cluster.

Usage
======
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




Running neverwinterdp deployments - SIMPLE STEPS
======


```
#Checkout neverwinterdp-deployments project 
git clone git clone https://<bitbucket_user>@bitbucket.org/nventdata/neverwinterdp-deployments.git
cd /path/to/neverwinterdp-deployments
```
####Build docker image with scribengin in one step
```
#Build images, launch containers, run ansible
docker/scribengin/docker.sh  cluster --launch --neverwinterdp-home=/your/path/to/NeverwinterDP
```

####Build digital ocean containers with scribengin in one step
```
cd neverwinterdp-deployments/tools/cluster/
./clusterCommander.py digitalocean --launch --neverwinterdp-home /your/path/to/NeverwinterDP/   \
  --create-containers ./digitalOceanConfigs/scribenginPerformance.yml  cluster --start          \
  --kafka-server-config ../../configs/bootstrap/post-install/kafka/config/server.properties     \
  --zookeeper-server-config ../../configs/bootstrap/post-install/zookeeper/conf/zoo.cfg
```



***  



Running neverwinterdp deployments - DETAIL
======

####Build docker image with scribengin (explained)

```
#Clean docker image (optional)
docker/scribengin/docker.sh image clean

#Build docker image

#if env variable NEVERWINTERDP_HOME is available run 
docker/scribengin/docker.sh image build

#if env variable NEVERWINTERDP_HOME is not available run 
docker/scribengin/docker.sh image build --neverwinterdp-home=/neverwinterdp/home/path
```

####Sync scribengin with all containers

```
#if env variable NEVERWINTERDP_HOME is available run 
docker/scribengin/docker.sh cluster --deploy-scribengin

#if env variable NEVERWINTERDP_HOME is not available run 
docker/scribengin/docker.sh cluster --deploy-scribengin --neverwinterdp-home=/neverwinterdp/home/path
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

####Build Scribengin from cluster commander
```
cd /path/to/neverwinterdp-deployments

#if env variable NEVERWINTERDP_HOME is available
./tools/cluster/clusterCommander.py scribengin --build
    

#if env variable NEVERWINTERDP_HOME is not available
./tools/cluster/clusterCommander.py --neverwinterdp-home /path/to/neverwinterdp_home scribengin --build
```

    
 
 [repository](https://bitbucket.org/nventdata/neverwinterdp-deployments)
[documentation](https://bitbucket.org/nventdata/neverwinterdp-deployments/wiki/Home)

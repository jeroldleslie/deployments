# neverwinter deployments

This project automates the installation, configuration and integration tests of scribengin. It works independently. To launch scribengin cluster, it need  to set NEVERWINTERDP_HOME env variable or you can give --neverwinterdp-home option when running the commands.


##Three important components in neverwinter deployments
###ansible
Not yet done, is in progress
###docker.sh
docker.sh is used for several functionalities.

1. Build docker image with hadoop, zookeeper, kafka, scribengin installed.
2. Launch docker containers for hadoop-master, hadoop-workers, zookeeper, kafka.

###clusterCommander.py

Is used to start/stop/restart cluster or specific processes with the given hostmachine. Also used to monitor running and none running processes in the cluster.

##Usage
###Setup neverwinterdp_home
- Create a directory for NeverwinterDP home

```
mkdir neverwinterdp
```

- Checkout Scribengin into neverwinterdp_home

```
cd neverwinterdp
git clone https://github.com/DemandCube/Scribengin
```

- Set NEVERWINTERDP_HOME environment variable (optional) or you can give --neverwinterdp-home option value in the commandline arguments.
   


###Running neverwinterdp deployments
Checkout neverwinterdp-deployments project into any of your directory.
	
```
git clone git clone https://<bitbucket_user>@bitbucket.org/nventdata/neverwinterdp- deployments.git
cd /path/to/neverwinterdp-deployments
```
	
####Build docker image with scribengin

```
#Clean docker image (optional)
docker/scribengin/docker.sh image clean

#Build docker image

#if env variable NEVERWINTERDP_HOME is available run 
docker/scribengin/docker.sh image build

#if env variable NEVERWINTERDP_HOME is not available run 
docker/scribengin/docker.sh image build --neverwinterdp-home /neverwinterdp/home/path
```

####Sync scribengin with all containers

```
#if env variable NEVERWINTERDP_HOME is available run 
docker/scribengin/docker.sh host-sync

#if env variable NEVERWINTERDP_HOME is not available run 
docker/scribengin/docker.sh host-sync --neverwinterdp-home /neverwinterdp/home/path
```

####Clean-run-deploy 
```
#To clean containers, run containers ,build scribengin and deploy scribengin 
#into running containers
docker/scribengin/docker.sh cluster --clean-containers --run-containers --deploy-scribengin --start-cluster
```

####Build Scribengin from cluster commander
```
cd /path/to/neverwinterdp-deployments

#if env variable NEVERWINTERDP_HOME is available
./tools/cluster/clusterCommander.py scribengin --build
    

#if env variable NEVERWINTERDP_HOME is not available
./tools/cluster/clusterCommander.py --neverwinterdp-home /path/to/neverwinterdp_home scribengin --build
```
   
####Deploy Scribengin from cluster commander

```
cd /path/to/neverwinterdp-deployments``

#if env variable NEVERWINTERDP_HOME is available 
./tools/cluster/clusterCommander.py scribengin --deploy

#if env variable NEVERWINTERDP_HOME is not available 
./tools/cluster/clusterCommander.py --neverwinterdp-home /path/to/neverwinterdp_home scribengin --deploy
```
    
 
 [repository](https://bitbucket.org/nventdata/neverwinterdp-deployments)
[documentation](https://bitbucket.org/nventdata/neverwinterdp-deployments/wiki/Home)

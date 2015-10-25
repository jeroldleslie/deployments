Docker component is used to build and run docker containers for development environment


###Easy Setup

####Dependencies
1. [Install Docker according to the documentation](https://docs.docker.com/installation/)
2. [Make sure git is set up](http://git-scm.com/downloads)
3. Make sure your user can edit your /etc/hosts file
4. Make sure your ssh keys are set up (no password)
    ```
    ssh-keygen -p
    # Start the SSH key creation process
    # Enter file in which the key is (/Users/you/.ssh/id_rsa): [Hit enter]
    # Key has comment '/Users/you/.ssh/id_rsa'
    # Enter new passphrase (empty for no passphrase): [Type new passphrase]
    # Enter same passphrase again: [One more time for luck]
    # Your identification has been saved with the new passphrase.
    ```

5. Checkout Neverwinterdp-Deployments

    ```git clone git@bitbucket.org:nventdata/neverwinterdp-deployments.git```


###Usage
```
Usage: docker.sh cluster [OPTIONS]

Command "cluster" consists of the following options: 
       Options: 
         --clean-image         : Cleans docker images
         --build-image         : Builds the docker image for Scribengin
         --clean-containers    : Cleans docker containers
         --run-containers      : Runs docker containers
         --ansible-inventory   : Creates ansible inventory file
         --deploy              : Run ansible playbook
         --deploy-scribengin   : Run ansible playbook to install Scribengin
         --deploy-tools        : Run ansible playbook to install neverwinterdp-deployments
         --start               : Starts services
         --stop-cluster        : Stops cluster services
         --force-stop-cluster  : Force stops cluster services
         --neverwinterdp-home  : /Path/To/Neverwinterdp
         --launch              : Cleans docker image and containers, Builds image and container, and starts
         --kafka-server        : Number of kafka containers to start
         --zk-server           : Number of zookeeper containers to start
         --hadoop-worker       : Number of hadoop worker containers to start
         --os-type             : Operating System distribution type [ubuntu,centos], default is ubuntu
         --idle-kafka-brokers  : Number of ideal kafka containers initially


```

###Some important examples

```
cd path/to/neverwinterdp-deployments

#clean and build docker image
#Note: you need to set NEVERWINTERDP_HOME env variable
$./docker/scribengin/docker.sh cluster --clean-image --build-image


#clean, run docker containers and create ansible inventory file
$/docker/scribengin/docker.sh cluster --clean-containers --run-containers --ansible-inventory

#create ansible inventory file
$/docker/scribengin/docker.sh cluster --ansible-inventory

```

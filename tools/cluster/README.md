#clusterCommander
This component is now mostly used to launch digitalocean machines for both development and for cluster

###Example

```
$NEVERWINTERDP_DEPLOYMENT_HOME/tools/clusterCommander/clusterCommander.py digitalocean --launch --neverwinterdp-home $NEVERWINTERDP_HOME --ansible-inventory-location $INVENTORY --create-containers path/to/ansible/profile/default.yml --subdomain test

```
###Some of the important usages of clusterCommander

```
###########
./clusterCommander.py digitalocean --help
Usage: clusterCommander.py digitalocean [OPTIONS]

  commands pertaining to digital-ocean droplets

Options:
  --launch                        Create containers, deploy, and run ansible
  --create-containers TEXT        create the container using specified config
  --update-local-host-file        clean the container
  --update-host-file              clean the container
  --setup-neverwinterdp-user      Sets up the neverwinterdp user
  --ansible-inventory             Creates ansible inventory file
  --ansible-inventory-location TEXT
                                  Where to save ansible inventory file
  --region [lon1|sgp1|nyc1|nyc2|nyc3|sfo1]
                                  Region to spawn droplet in
  --deploy                        Run ansible
  --destroy                       destroys all scribengin containers
  --reboot                        reboots all scribengin containers
  --neverwinterdp-home TEXT       neverwinterdp home
  --digitaloceantoken TEXT        digital ocean token in plain text
  --digitaloceantokenfile TEXT    digital ocean token file location
  --subdomain TEXT                Subdomain to name hosts with in DO - i.e.
                                  hadoop-master.dev
  --help                          Show this message and exit.
  
###########
./clusterCommander.py ansible --help
Usage: clusterCommander.py ansible [OPTIONS]

  commands to help with ansible

Options:
  --write-inventory-file
  --inventory-file TEXT
  --deploy-cluster
  --deploy-scribengin
  --deploy-tools
  --deploy-kibana-chart
  --neverwinterdp-home TEXT  neverwinterdp home
  --help                     Show this message and exit.


###########
Usage: clusterCommander.py kafkafailure [OPTIONS]

  Failure Simulation for Kafka

Options:
  --failure-interval INTEGER      Time interval (in seconds) to fail server
  --wait-before-start INTEGER     Time to wait (in seconds) before starting
                                  server
  --servers TEXT                  Servers to effect.  Command separated list
                                  (i.e. --servers zk1,zk2,zk3)
  --min-servers INTEGER           Minimum number of servers that must stay up
  --servers-to-fail-simultaneously INTEGER
                                  Number of servers to kill simultaneously
  --kill-method [restart|kill|random]
                                  Server kill method.  Restart is clean, kill
                                  uses kill -9, random switches randomly
  --initial-clean                 If enabled, will run a clean operation
                                  before starting the failure simulation
  --junit-report TEXT             If set, will write the junit-report to the
                                  specified file
  --help                          Show this message and exit.


###########
Usage: clusterCommander.py zookeeperfailure [OPTIONS]

  Failure Simulation for Zookeeper

Options:
  --failure-interval INTEGER      Time interval (in seconds) to fail server
  --wait-before-start INTEGER     Time to wait (in seconds) before starting
                                  server
  --servers TEXT                  Servers to effect.  Command separated list
                                  (i.e. --servers zk1,zk2,zk3)
  --min-servers INTEGER           Minimum number of servers that must stay up
  --servers-to-fail-simultaneously INTEGER
                                  Number of servers to kill simultaneously
  --kill-method [restart|kill|random]
                                  Server kill method.  Restart is clean, kill
                                  uses kill -9, random switches randomly
  --initial-clean                 If enabled, will run a clean operation
                                  before starting the failure simulation
  --junit-report TEXT             If set, will write the junit-report to the
                                  specified file
  --help                          Show this message and exit.

```
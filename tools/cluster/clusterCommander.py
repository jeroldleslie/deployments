#! /bin/sh
""":"
exec python $0 ${1+"$@"}
"""

import click, logging, multiprocessing, signal, os, subprocess
from digitalocean import Droplet
from sys import stdout, exit
from time import sleep
from os.path import join, expanduser, dirname, realpath

from failure.FailureSimulator import ZookeeperFailure,KafkaFailure,DataFlowFailure
from Cluster import Cluster
from scribengindigitalocean.ScribenginDigitalOcean import ScribenginDigitalOcean
from scribenginansible.ScribenginAnsible import ScribenginAnsible
from kibana.Kibana import Kibana

_debug = False
_logfile = ''
_jobs = []
_neverwinterdp_home = ''

@click.group(chain=True)
@click.option('--debug/--no-debug', default=False, help="Turn debugging on")
@click.option('--logfile', default='/tmp/clustercommander.log', help="Log file to write to")
@click.option('--neverwinterdp-home', default='', help="NEVERWINTERDP_HOME path for neverwinterdp projects")
def mastercommand(debug, logfile, neverwinterdp_home):
  global _debug, _logfile, _neverwinterdp_home
  _debug = debug
  _logfile = logfile
  _neverwinterdp_home = neverwinterdp_home
  
  #Setting paramiko's logger to be quiet, otherwise too much noise
  logging.getLogger("paramiko").setLevel(logging.WARNING)
  if _debug:
      #Set logging file, overwrite file, set logging level to DEBUG
      logging.basicConfig(filename=_logfile, filemode="w", level=logging.DEBUG)
      logging.getLogger().addHandler(logging.StreamHandler(stdout))
      click.echo('Debug mode is %s' % ('on' if debug else 'off'))
  else:
    #Set logging file, overwrite file, set logging level to INFO
    logging.basicConfig(filename=_logfile, filemode="w", level=logging.INFO)
  
  #Quiet down the other loggers
  logging.getLogger("urllib3").setLevel(logging.WARNING)
  logging.getLogger("requests").setLevel(logging.WARNING)
  logging.getLogger("digitalocean.baseapi").setLevel(logging.WARNING)

@mastercommand.command(help="Get Cluster status")
@click.option('--role',  default="",  help="Which role to check on (i.e. kafka, zookeeper, hadoop-master, hadoop-worker)")
def status(role):
  cluster = Cluster()
  if len(role) > 0 :
    cluster = cluster.getServersByRole(role)
  
  click.echo(cluster.getReport())

@mastercommand.command("vmmaster", help="VmMaster commands")
@click.option('--restart',           is_flag=True, help="restart VmMaster")
@click.option('--start',             is_flag=True, help="start VmMaster")
@click.option('--stop',              is_flag=True, help="stop VmMaster")
@click.option('--force-stop',        is_flag=True, help="kill VmMaster")
@click.option('--wait-before-start', default=0,    help="Time to wait before restarting VmMaster (seconds)")
@click.option('--wait-before-report', default=5,    help="Time to wait before restarting reporting cluster status (seconds)")
def vmmaster(restart, start, stop,force_stop, wait_before_start, wait_before_report):
  cluster = Cluster()
  
  if(restart or stop):
    logging.debug("Shutting down VmMaster")
    cluster.shutdownVmMaster()
  
  if(force_stop):
    logging.debug("Killing VmMaster")
    cluster.killVmMaster()
  
  if(restart or start):
    logging.debug("Waiting for "+str(wait_before_start)+" seconds")
    sleep(wait_before_start)
    logging.debug("Starting VmMaster")
    cluster.startVmMaster()
  
  logging.debug("Waiting for "+str(wait_before_report)+" seconds")
  sleep(wait_before_report)
  #click.echo(cluster.getReport())  


@mastercommand.command("elasticsearch", help="Elasticsearch commands")
@click.option('--restart',           is_flag=True, help="restart Elasticsearch")
@click.option('--start',             is_flag=True, help="start Elasticsearch")
@click.option('--stop',              is_flag=True, help="stop Elasticsearch")
@click.option('--force-stop',        is_flag=True, help="kill Elasticsearch")
def elasticsearch(restart, start, stop, force_stop):
  cluster = Cluster()
  
  if(restart or stop):
    logging.debug("Shutting down Elasticsearch")
    cluster.shutdownElasticSearch()
  
  if(force_stop):
    logging.debug("Killing Elasticsearch")
    cluster.killElasticSearch()
    
  if(restart or start):
    logging.debug("Starting Elasticsearch")
    cluster.startElasticSearch()
    

@mastercommand.command("scribengin", help="Scribengin commands")
@click.option('--restart',           is_flag=True, help="restart Scribengin")
@click.option('--start',             is_flag=True, help="start Scribengin")
@click.option('--stop',              is_flag=True, help="stop Scribengin")
@click.option('--force-stop',        is_flag=True, help="kill Scribengin")
@click.option('--wait-before-start', default=0,    help="Time to wait before restarting Scribengin (seconds)")
def scribengin(restart, start, stop, force_stop, wait_before_start):
  cluster = Cluster()
  neverwinterdp_home = _neverwinterdp_home
  if neverwinterdp_home == '':
    neverwinterdp_home = os.getenv('NEVERWINTERDP_HOME', 0)
    if neverwinterdp_home == 0:
      raise click.BadParameter("or set environment variable NEVERWINTERDP_HOME", param_hint = "--neverwinterdp-home")

  if(restart or stop):
    logging.debug("Shutting down Scribengin")
    cluster.shutdownScribengin()
  
  if(force_stop):
    logging.debug("Killing Scribengin")
    cluster.killScribengin()
    
  if(restart or start):
    logging.debug("Waiting for "+str(wait_before_start)+" seconds")
    sleep(wait_before_start)
    logging.debug("Starting Scribengin")
    cluster.startScribengin()
    

@mastercommand.command("cluster", help="Cluster commands")
@click.option('--restart',             is_flag=True, help="restart cluster")
@click.option('--start',               is_flag=True, help="start cluster")
@click.option('--stop',                is_flag=True, help="stop cluster")
@click.option('--force-stop',          is_flag=True, help="kill cluster")
@click.option('--clean',               is_flag=True, help="Clean old cluster data")
@click.option('--wait-before-start',   default=0,    help="Time to wait before restarting cluster (seconds)")
@click.option('--wait-before-kill',    default=0,    help="Time to wait before force killing cluster (seconds)")
@click.option('--execute',                           help='execute given command on all nodes')
@click.option('--idle-kafka-brokers',  default=0,    help="Number of idle kafka brokers initially")
@click.option('--profile-type',     default='default',  help="Cluster profile type, you can create and specify your own profile on neverwinterdp-deployments-home/profile, have default as an example")
def cluster(restart, start, stop, force_stop, clean, wait_before_start, wait_before_kill, execute, idle_kafka_brokers, profile_type):
  cluster = Cluster()
  cluster.setProfile(profile_type)
  if(execute is not None):
    cluster.sshExecute(execute)
    
  if(restart or stop):
    logging.debug("Shutting down Cluster")
    cluster.shutdownCluster()
  
  if(force_stop):
    logging.debug("Waiting for "+str(wait_before_kill)+" seconds")
    sleep(wait_before_kill)
    logging.debug("Force Killing Cluster")
    cluster.killCluster()

  if(clean):
    logging.debug("Cleaning Cluster")
    cluster.cleanCluster()

  if(restart or start):
    logging.debug("Waiting for "+str(wait_before_start)+" seconds")
  
    sleep(wait_before_start)
    logging.debug("Starting Cluster")
    #cluster.paramDict["server_config"] = kafka_server_config
    #cluster.paramDict["zoo_cfg"] = zookeeper_server_config
    cluster.startCluster(idleKafkaBrokers=idle_kafka_brokers)
    
  #click.echo(cluster.getReport())  
  
@mastercommand.command("kafka", help="Kafka commands")
@click.option('--restart',           is_flag=True, help="restart kafka brokers")
@click.option('--start',             is_flag=True, help="start kafka brokers")
@click.option('--stop',              is_flag=True, help="stop kafka brokers")
@click.option('--force-stop',        is_flag=True, help="kill -9 kafka on brokers")
@click.option('--clean',             is_flag=True, help="Clean old kafka data")
@click.option('--brokers',           default="",   help="Which kafka brokers to effect (command separated list)")
@click.option('--wait-before-start', default=0,    help="Time to wait before restarting kafka server (seconds)")
@click.option('--wait-before-kill',  default=0,    help="Time to wait before force killing Kafka process (seconds)")
@click.option('--idle-kafka-brokers',  default=0,    help="Number of idle kafka brokers initially")
@click.option('--profile-type',     default='default',  help="Kafka profile type, you can create and specify your own profile on neverwinterdp-deployments-home/profile, have default as an example")
def kafka(restart, start, stop, force_stop, clean, brokers, wait_before_start, wait_before_kill, idle_kafka_brokers, profile_type):
  cluster = Cluster()
  cluster.setProfile(profile_type)
  logging.debug("Just a test message.")
  
  if len(brokers) > 0 :
    brokerList = brokers.split(",")
    cluster = cluster.getServersByHostname(brokerList)
  
  if(restart or stop):
    logging.debug("Shutting down Kafka")
    cluster.shutdownKafka()
    
  if(force_stop):
    logging.debug("Waiting for "+str(wait_before_kill)+" seconds")
    sleep(wait_before_kill)
    logging.debug("Force Killing Kafka")
    cluster.killKafka()
  
  if(clean):
    logging.debug("Cleaning Kafka")
    cluster.cleanKafka()
  
  if(restart or start):
    logging.debug("Waiting for "+str(wait_before_start)+" seconds")
    sleep(wait_before_start)
    logging.debug("Starting Kafka")
    cluster.startKafka(idleKafkaBrokers=idle_kafka_brokers)
  #click.echo(cluster.getReport())

@mastercommand.command("zookeeper",help="Zookeeper commands")
@click.option('--restart',           is_flag=True, help="restart ZK nodes")
@click.option('--start',             is_flag=True, help="start ZK nodes")
@click.option('--stop',              is_flag=True, help="stop ZK nodes")
@click.option('--force-stop',        is_flag=True, help="kill -9 ZK on brokers")
@click.option('--clean',             is_flag=True, help="Clean old ZK data")
@click.option('--zk-servers',        is_flag=True, help="Which ZK nodes to effect (command separated list)")
@click.option('--wait-before-start', default=0,     help="Time to wait before starting ZK server (seconds)")
@click.option('--wait-before-kill',  default=0,     help="Time to wait before force killing ZK process (seconds)")
@click.option('--profile-type',     default='default',  help="Zookeeper profile type, you can create and specify your own profile on neverwinterdp-deployments-home/profile, have default as an example")
def zookeeper(restart, start, stop, force_stop, clean, zk_servers, wait_before_start, wait_before_kill, profile_type):
  cluster = Cluster()
  cluster.setProfile(profile_type)
  if(restart or stop):
    logging.debug("Shutting down Zookeeper")
    cluster.shutdownZookeeper()
  
  if(force_stop):
    logging.debug("Waiting for "+str(wait_before_kill)+" seconds")
    sleep(wait_before_kill)
    logging.debug("Force Killing Zookeeper")
    cluster.killZookeeper()
  
  if(clean):
    logging.debug("Cleaning Zookeeper")
    cluster.cleanZookeeper()
  
  if(restart or start):
    logging.debug("Waiting for "+str(wait_before_start)+" seconds")
    sleep(wait_before_start)
    logging.debug("Starting Zookeeper")
    cluster.startZookeeper()
  #click.echo(cluster.getReport())

@mastercommand.command("hadoop",help="Hadoop commands")
@click.option('--restart',           is_flag=True, help="restart hadoop nodes")
@click.option('--start',             is_flag=True, help="start hadoop nodes")
@click.option('--stop',              is_flag=True, help="stop hadoop nodes")
@click.option('--force-stop',        is_flag=True, help="kill -9 hadoop on brokers")
@click.option('--clean',             is_flag=True, help="Clean old hadoop data")
@click.option('--hadoop-nodes',      is_flag=True, help="Which hadoop nodes to effect (command separated list)")
@click.option('--wait-before-start', default=0,    help="Time to wait before starting ZK server (seconds)")
@click.option('--wait-before-kill',  default=0,    help="Time to wait before force killing ZK process (seconds)")
@click.option('--servers',           default="",   help="Which hadoop servers to effect (command separated list)")
@click.option('--grep-app-log',      is_flag=True,   help="Prints app log from hadoop cluster, or it can be restricted for specified hadoop nodes using --servers option")
@click.option('--grep-app-stdout',   is_flag=True,   help="Prints stdout log from hadoop cluster, or it can be restricted for specified hadoop nodes using --servers option")
@click.option('--grep-app-stderr',   is_flag=True,   help="Prints stderr log from hadoop cluster, or it can be restricted for specified hadoop nodes using --servers option")
@click.option('--profile-type',      default='default',  help="Hadoop profile type, you can create and specify your own profile on neverwinterdp-deployments-home/profile, have default as an example")
def hadoop(restart, start, stop, force_stop, clean, hadoop_nodes, wait_before_start, wait_before_kill,servers,grep_app_log,grep_app_stdout,grep_app_stderr,profile_type):
  cluster = Cluster()
  
  cluster = cluster.getServersByRole("hadoop-master,hadoop-worker");
  cluster.setProfile(profile_type)
  
  if len(servers) > 0 :
    serverList = servers.split(",")
    cluster = cluster.getServersByHostname(serverList)
    
  if(grep_app_log):
    cluster.sshExecute("find /opt/hadoop -name \"vm.log\" -exec grep -A 5 -B5 \"INFO\" {} \; -print")
    
  if(grep_app_stdout):
    cluster.sshExecute("find /opt/hadoop -name \"stderr\" -exec grep -A 5 -B5 \"INFO\" {} \; -print")
    
  if(grep_app_stderr):
    cluster.sshExecute("find /opt/hadoop -name \"stdout\" -exec grep -A 5 -B5 \"INFO\" {} \; -print")
    
  if(restart or stop):
    logging.debug("Shutting down Hadoop")
    cluster.shutdownHadoopWorker()
    cluster.shutdownHadoopMaster()
  
  if(force_stop):
    logging.debug("Waiting for "+str(wait_before_kill)+" seconds")
    sleep(wait_before_kill)
    logging.debug("Force Killing Hadoop")
    cluster.killHadoopWorker()
    cluster.killHadoopMaster()
  
  if(clean):
    logging.debug("Cleaning Hadoop")
    cluster.cleanHadoopWorker()
    cluster.cleanHadoopMaster()
  
  if(restart or start):
    logging.debug("Waiting for "+str(wait_before_start)+" seconds")
    sleep(wait_before_start)
    logging.debug("Starting Hadoop")
    cluster.cleanHadoopDataAtFirst()
    cluster.startHadoop()
  
  #click.echo(cluster.getReport())

@mastercommand.command("kafkafailure",help="Failure Simulation for Kafka")
@click.option('--failure-interval',               default=180,  help="Time interval (in seconds) to fail server")
@click.option('--wait-before-start',              default=180,  help="Time to wait (in seconds) before starting server")
@click.option('--servers',                        default="",   help="Servers to effect.  Command separated list (i.e. --servers zk1,zk2,zk3)")
@click.option('--min-servers',                    default=1,    help="Minimum number of servers that must stay up")
@click.option('--servers-to-fail-simultaneously', default=1,    help="Number of servers to kill simultaneously")
@click.option('--kill-method',                    default='kill', type=click.Choice(['shutdown', 'kill', "random"]), help="Server kill method. Shutdown is clean, kill uses kill -9, random switches randomly")
@click.option('--initial-clean',                  is_flag=True, help="If enabled, will run a clean operation before starting the failure simulation")
@click.option('--junit-report',                   default="",   help="If set, will write the junit-report to the specified file")
@click.option('--restart-method',                 default='random', type=click.Choice(["flipflop", "random"]), help="Server restart method. 'flipflop' - it starts spare node if normal node killed and vise versa, 'random' - it starts any random node when failure occurs")
@click.option('--profile-type',      default='default',  help="Kafka profile type, you can create and specify your own profile on neverwinterdp-deployments-home/profile, have default as an example")
#use-spare before junit report
def kafkafailure(failure_interval, wait_before_start, servers, min_servers, servers_to_fail_simultaneously, kill_method, initial_clean, junit_report, restart_method, profile_type):
  global _jobs
  
  kf = KafkaFailure()
  
  p = multiprocessing.Process(name="KafkaFailure",
                              target=kf.failureSimulation, 
                              args=(failure_interval, wait_before_start, servers, min_servers, 
                                    servers_to_fail_simultaneously, kill_method, initial_clean, junit_report, restart_method, profile_type))
  _jobs.append(p)
  p.start()
  

@mastercommand.command("zookeeperfailure",help="Failure Simulation for Zookeeper")
@click.option('--failure-interval',               default=180,  help="Time interval (in seconds) to fail server")
@click.option('--wait-before-start',              default=180,  help="Time to wait (in seconds) before starting server")
@click.option('--servers',                        default="",   help="Servers to effect.  Command separated list (i.e. --servers zk1,zk2,zk3)")
@click.option('--min-servers',                    default=1,    help="Minimum number of servers that must stay up")
@click.option('--servers-to-fail-simultaneously', default=1,    help="Number of servers to kill simultaneously")
@click.option('--kill-method',                    default='kill', type=click.Choice(['shutdown', 'kill', "random"]), help="Server kill method. Shutdown is clean, kill uses kill -9, random switches randomly")
@click.option('--initial-clean',                  is_flag=True, help="If enabled, will run a clean operation before starting the failure simulation")
@click.option('--junit-report',                   default="",    help="If set, will write the junit-report to the specified file")
@click.option('--restart-method',                 default='random', type=click.Choice(["random"]), help="Server restart method. 'random' - it starts any random node when failure occurs")
def zookeeperfailure(failure_interval, wait_before_start, servers, min_servers, servers_to_fail_simultaneously, kill_method, initial_clean, junit_report, restart_method):
  global _jobs
  
  zf = ZookeeperFailure()
  p = multiprocessing.Process(name="ZookeeperFailure",
                              target=zf.failureSimulation, 
                              args=(failure_interval, wait_before_start, servers, min_servers, 
                                    servers_to_fail_simultaneously, kill_method, initial_clean, junit_report, restart_method))
  _jobs.append(p)
  p.start()


@mastercommand.command("ansible", help="commands to help with ansible")
@click.option('--write-inventory-file',    is_flag=True,  help='')
@click.option('--inventory-file',          default="",  help='')
@click.option('--deploy-cluster',          is_flag=True, help='')
@click.option('--deploy-scribengin',       is_flag=True, help='')
@click.option('--deploy-tools',            is_flag=True, help='')
@click.option('--deploy-kibana-chart',     is_flag=True, help='')
@click.option('--neverwinterdp-home',      default=None, help='neverwinterdp home')
def ansible(write_inventory_file, inventory_file, deploy_cluster,
            deploy_scribengin, deploy_tools, deploy_kibana_chart, neverwinterdp_home):
  cluster = Cluster()
  
  if neverwinterdp_home is None:
    neverwinterdp_home = os.environ.get('NEVERWINTERDP_HOME')
    
  if neverwinterdp_home is None or neverwinterdp_home == "":
      raise click.BadParameter("--neverwinterdp-home is needed to deploy", param_hint = "--neverwinterdp-home")
  
  
  ans = ScribenginAnsible()
  if write_inventory_file:
    ans.writeAnsibleInventory(hostsAndIps=cluster.getHostsAndIpsFromCluster(),inventoryFileLocation=inventory_file)
  
  deploymentRootDir = dirname(dirname(dirname(realpath(__file__))))
  ansibleRootDir = join(deploymentRootDir, "ansible")
  
  if deploy_cluster:
    ans.deploy(join(ansibleRootDir, "scribenginCluster.yml"),inventory_file, neverwinterdp_home)
  if deploy_scribengin:
    ans.deploy(join(ansibleRootDir, "scribengin.yml"),inventory_file, neverwinterdp_home)
  if deploy_tools:
    ans.deploy(join(ansibleRootDir, "scribenginTools.yml"),inventory_file, neverwinterdp_home)
  if deploy_kibana_chart:
    monitorServers = cluster.getServersByRole("elasticsearch")
    if monitorServers.servers[0].getProcess("elasticsearch").isRunning():
      ans.deploy(join(ansibleRootDir, "kibana.yml"),inventory_file, neverwinterdp_home)
    else:
      print "Please start elasticsearch before deploying kibana charts"
      
@mastercommand.command("digitalocean", help="commands pertaining to digital-ocean droplets")
@click.option('--launch',                   is_flag=True,  help='Create containers, deploy, and run ansible')
@click.option('--create-containers',        default=None,  help='create the container using specified config')
@click.option('--update-local-host-file',   is_flag=True,  help='clean the container')
@click.option('--update-host-file',         is_flag=True,  help='clean the container')
@click.option('--setup-neverwinterdp-user', is_flag=True,  help='Sets up the neverwinterdp user')
@click.option('--ansible-inventory',        is_flag=True,  help='Creates ansible inventory file')
@click.option('--ansible-inventory-location', default="",  help='Where to save ansible inventory file')
@click.option('--region',                    default="lon1",  type=click.Choice(['lon1','sgp1','nyc1','nyc2','nyc3','sfo1']), help='Region to spawn droplet in')
@click.option('--deploy',                   is_flag=True,  help='Run ansible')
@click.option('--destroy',                  is_flag=True,  help='destroys all scribengin containers')
@click.option('--reboot',                  is_flag=True,  help='reboots all scribengin containers')
@click.option('--neverwinterdp-home',       default=None, help='neverwinterdp home')
@click.option('--digitaloceantoken',        default=None,  help='digital ocean token in plain text')
@click.option('--digitaloceantokenfile',    default='~/.digitaloceantoken', help='digital ocean token file location')
@click.option('--subdomain',                default="dev",  help='Subdomain to name hosts with in DO - i.e. hadoop-master.dev')
def digitalocean(launch, create_containers, update_local_host_file, update_host_file, setup_neverwinterdp_user,
                 ansible_inventory, ansible_inventory_location, region, deploy, destroy, reboot,
                 neverwinterdp_home, digitaloceantoken, digitaloceantokenfile,
                 subdomain):
  
  #Make sure neverwinterdp_home is set
  if (deploy or launch) and neverwinterdp_home is None:
    if os.environ.get('NEVERWINTERDP_HOME') == "":
      raise click.BadParameter("--neverwinterdp-home is needed to deploy", param_hint = "--neverwinterdp-home")
    else:
      neverwinterdp_home = os.environ.get('NEVERWINTERDP_HOME')
      if neverwinterdp_home is None or neverwinterdp_home == "":
        raise click.BadParameter("--neverwinterdp-home is needed to deploy", param_hint = "--neverwinterdp-home")
  
  if launch and create_containers is None:
    raise click.BadParameter("--create-containers is needed to deploy", param_hint = "--create_containers")
  
  digitalOcean = ScribenginDigitalOcean(digitalOceanToken=digitaloceantoken, digitalOceanTokenFileLocation=digitaloceantokenfile)
  
  if create_containers is not None or launch:
    click.echo("Creating containers")
    digitalOcean.launchContainers(create_containers, region, subdomain)
  
  #Adding a sleep because DO is unreliable
  #and could report that the machines are ready
  #when in fact they're not.  :(
  sleep(30)

  if update_local_host_file or launch:
    click.echo("Updating local hosts file")
    digitalOcean.updateLocalHostsFile(subdomain)
  if update_host_file or launch:
    click.echo("Updating remote hosts file")
    digitalOcean.updateRemoteHostsFile(subdomain)
  
  if setup_neverwinterdp_user or launch:
    click.echo("Setting up neverwinterdp user")
    digitalOcean.setupNeverwinterdpUser()
  
  if ansible_inventory or launch:
    click.echo("Writing ansible inventory file")
    digitalOcean.writeAnsibleInventory(inventoryFileLocation=ansible_inventory_location, subdomain=subdomain)
  
  #if deploy or launch:
  #  click.echo("Running ansible")
  #  digitalOcean.deploy(neverwinterdp_home)
  
  if reboot:
    click.echo("Rebooting Scribengin droplets")
    digitalOcean.rebootAllScribenginDroplets(subdomain)
  
  if destroy:
    click.echo("Destroying Scribengin droplets")
    digitalOcean.destroyAllScribenginDroplets(subdomain)

@mastercommand.command("digitaloceandevsetupubuntu", help="commands to help launch a developer box in digital ocean")
@click.option('--name',     required=True,  help='Name of droplet to create or destroy')
@click.option('--size',     default="16gb",  type=click.Choice(['512mb', '1gb', '2gb', '4gb', '8gb', '16gb', '32gb', '48gb', '64gb']),  help='Size of machine to spawn')
@click.option('--region',   default="lon1",  type=click.Choice(['lon1','sgp1','nyc1','nyc2','nyc3','sfo1']), help='Region to spawn droplet in')
@click.option('--image',   default="ubuntu-14-04-x64",  help='Which image to launch from (Choose an ubuntu image)')
@click.option('--private-networking',   default="true",  type=click.Choice(["true","false"]),help='Whether to turn on private networking')
@click.option('--create',  is_flag=True,    help='Create image')
@click.option('--destroy',  is_flag=True,    help='Destroy image')
@click.option('--branch',        default="dev/master",  help='Branch of NeverwinterDP to check out')
@click.option('--digitaloceantoken',        default=None,  help='digital ocean token in plain text')
@click.option('--digitaloceantokenfile',    default='~/.digitaloceantoken', help='digital ocean token file location')
@click.option('--sshKeyPath',    default='~/.ssh/id_rsa', help='path to private key')
@click.option('--sshKeyPathPublic',    default='~/.ssh/id_rsa.pub', help='path to public key')
@click.option('--awsCredentialFile',    default='~/.aws/credentials', help='path to AWS credentials file')
def digitaloceandevsetupubuntu(name, size, region, image, private_networking, create, destroy, branch,
                         digitaloceantoken, digitaloceantokenfile, sshkeypath, sshkeypathpublic, awscredentialfile):
  #Python can't properly interpret the ~/ directive, so fix file paths
  if "~/" in sshkeypath:
      sshkeypath = join( expanduser("~"), sshkeypath.replace("~/",""))
  if "~/" in sshkeypathpublic:
      sshkeypathpublic = join( expanduser("~"), sshkeypathpublic.replace("~/",""))
  if "~/" in awscredentialfile:
      awscredentialfile = join( expanduser("~"), awscredentialfile.replace("~/",""))
  
  
  digitalOcean = ScribenginDigitalOcean(digitalOceanToken=digitaloceantoken, digitalOceanTokenFileLocation=digitaloceantokenfile)
  
  droplet = Droplet(token=digitalOcean.token,
                    name=name,
                    region=region,
                    image=image,
                    size_slug=size,
                    backups=False,
                    ssh_keys=digitalOcean.defaultDropletConfig["ssh_keys"],
                    private_networking=private_networking,)
  if create:
    digitalOcean.createAndWait(droplet)
    print "Setting up neverwinterdp user"
    sshHandle = digitalOcean.setupNeverwinterdpUser(serverName=name)
    print "Setting up keys"
    with open (sshkeypath, "r") as myfile:
      privateKeyContent = myfile.read()
    with open (sshkeypathpublic, "r") as myfile:
      publicKeyContent = myfile.read()
    sshHandle.sshExecute("mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo \""+privateKeyContent+
                         "\" > ~/.ssh/id_rsa && echo \""+publicKeyContent+
                         "\" > ~/.ssh/id_rsa.pub && chmod 600 ~/.ssh/id_rsa ~/.ssh/id_rsa.pub && "+
                         "sudo chmod 777 /etc/hosts")
    
    print "Install wget, git, nano, java, vim"
    sshHandle.sshExecute("sudo apt-get update && sudo apt-get install wget git nano openjdk-7-jdk vim -y")
    sshHandle.sshExecute(r'echo -e "JAVA_HOME=/usr/lib/jvm/java-7-openjdk-amd64\\n" >> /etc/environment', "root")
    print "Install gradle"
    sshHandle.sshExecute("sudo add-apt-repository ppa:cwchien/gradle -y && sudo apt-get update && sudo apt-get install gradle-1.12 -y ")
    print "Install Docker"
    sshHandle.sshExecute("wget -qO- https://get.docker.com/ | sudo sh")
    print "Configure neverwinterdp user for Docker"
    sshHandle.sshExecute("sudo gpasswd -a neverwinterdp docker && sudo service docker restart")
    print "Install Ansible"
    sshHandle.sshExecute("sudo apt-get install software-properties-common -y && sudo apt-add-repository ppa:ansible/ansible-1.9 -y && sudo apt-get update && sudo apt-get install ansible=1.9.4-1ppa~trusty -y")
    
    print "Copy AWS credentials file"
    try:
      with open(awscredentialfile, 'r') as f:
        awsCreds = f.read()
      sshHandle.sshExecute("mkdir ~/.aws && echo \""+awsCreds+"\" > ~/.aws/credentials")
    except Exception as e:
      print "Problem copying AWS credentials file: "+str(e)
      
    
    print "Check out NeverwinterDP"
    sshHandle.sshExecute("git clone https://github.com/Nventdata/NeverwinterDP/ && cd NeverwinterDP && git checkout "+branch)
    sshHandle.sshExecute(r'echo -e "NEVERWINTERDP_HOME=/home/neverwinterdp/NeverwinterDP\\n" >> ~/.bashrc')
    print "Check out neverwinterdp-deployments"
    sshHandle.sshExecute("echo -e \"StrictHostKeyChecking no\\n\" >> ~/.ssh/config")
    sshHandle.sshExecute("git clone git@bitbucket.org:nventdata/neverwinterdp-deployments.git")
    
    print "Your droplet "+name+" is ready at 'ssh neverwinterdp@"+digitalOcean.getDropletIp(droplet.name)+"'"
  
  if destroy:
    import re
    doNotDestroy = [ re.compile('.*jenkins.*'),
                    re.compile('.*crucible.*'), ]
    
    if any(regex.match(name) for regex in doNotDestroy):
      click.echo(name+" matches a machine that will not be destroyed.  Returning")
      return
    
    click.echo("Are you SURE you wish to destroy "+name+"? (yes/no) ", nl=False)
    yes = set(['yes','y', 'ye'])
    no = set(['no','n'])
    
    choice = raw_input().lower()
    if choice in yes:
       digitalOcean.destroyDropletAndWait(digitalOcean.getDroplet(name))
    elif choice in no:
       click.echo("Skipping destruction")
    else:
       click.echo("Please respond with 'yes' or 'no'.  Returning.")

@mastercommand.command("digitaloceandevsetupcentos", help="commands to help launch a developer box in digital ocean")
@click.option('--name',     required=True,  help='Name of droplet to create or destroy')
@click.option('--size',     default="16gb",  type=click.Choice(['512mb', '1gb', '2gb', '4gb', '8gb', '16gb', '32gb', '48gb', '64gb']),  help='Size of machine to spawn')
@click.option('--region',   default="lon1",  type=click.Choice(['lon1','sgp1','nyc1','nyc2','nyc3','sfo1']), help='Region to spawn droplet in')
@click.option('--image',   default="centos-7-0-x64",  help='Which image to launch from (Choose a centos image)')
@click.option('--private-networking',   default="true",  type=click.Choice(["true","false"]),help='Whether to turn on private networking')
@click.option('--create',  is_flag=True,    help='Create image')
@click.option('--destroy',  is_flag=True,    help='Destroy image')
@click.option('--branch',        default="dev/master",  help='Branch of NeverwinterDP to check out')
@click.option('--digitaloceantoken',        default=None,  help='digital ocean token in plain text')
@click.option('--digitaloceantokenfile',    default='~/.digitaloceantoken', help='digital ocean token file location')
@click.option('--sshKeyPath',    default='~/.ssh/id_rsa', help='path to private key')
@click.option('--sshKeyPathPublic',    default='~/.ssh/id_rsa.pub', help='path to public key')
@click.option('--awsCredentialFile',    default='~/.aws/credentials', help='path to AWS credentials file')
def digitaloceandevsetupcentos(name, size, region, image, private_networking, create, destroy, branch,
                         digitaloceantoken, digitaloceantokenfile, sshkeypath, sshkeypathpublic, awscredentialfile):
  #Python can't properly interpret the ~/ directive, so fix file paths
  if "~/" in sshkeypath:
      sshkeypath = join( expanduser("~"), sshkeypath.replace("~/",""))
  if "~/" in sshkeypathpublic:
      sshkeypathpublic = join( expanduser("~"), sshkeypathpublic.replace("~/",""))
  if "~/" in awscredentialfile:
      awscredentialfile = join( expanduser("~"), awscredentialfile.replace("~/",""))
  
  
  digitalOcean = ScribenginDigitalOcean(digitalOceanToken=digitaloceantoken, digitalOceanTokenFileLocation=digitaloceantokenfile)
  
  droplet = Droplet(token=digitalOcean.token,
                    name=name,
                    region=region,
                    image=image,
                    size_slug=size,
                    backups=False,
                    ssh_keys=digitalOcean.defaultDropletConfig["ssh_keys"],
                    private_networking=private_networking,)
  if create:
    digitalOcean.createAndWait(droplet)

    print "Setting up neverwinterdp user"
    sshHandle = digitalOcean.setupNeverwinterdpUser(serverName=name)


    print "Remove sudo tty requirement"
    sshHandle.sshExecute("sed -i '/Defaults\s*requiretty/d' /etc/sudoers", "root")
    sshHandle.sshExecute("sed -i '/Defaults\s!visiblepw/d' /etc/sudoers ", "root")


    print "Setting up keys"
    with open (sshkeypath, "r") as myfile:
      privateKeyContent = myfile.read()
    with open (sshkeypathpublic, "r") as myfile:
      publicKeyContent = myfile.read()
    sshHandle.sshExecute("mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo \""+privateKeyContent+
                         "\" > ~/.ssh/id_rsa && echo \""+publicKeyContent+
                         "\" > ~/.ssh/id_rsa.pub && chmod 600 ~/.ssh/id_rsa ~/.ssh/id_rsa.pub && "+
                         "touch ~/.ssh/config && chmod 600 ~/.ssh/config && "+
                         "chown -R neverwinterdp:neverwinterdp ~/.ssh && " +
                         "sudo chmod 777 /etc/hosts")
    
    
    
    print "Install wget, git, nano, java, vim"
    sshHandle.sshExecute("yum -y update && sudo yum install wget git nano java-1.7.0-openjdk-devel vim epel-release git unzip -y", "root")
    sshHandle.sshExecute(r'echo -e "JAVA_HOME=/usr/lib/jvm/java-1.7.0-openjdk\\n" >> /etc/environment', "root")
    print "Install gradle"
    sshHandle.sshExecute("wget -q -N http://services.gradle.org/distributions/gradle-1.12-all.zip && sudo unzip -o -q  gradle-1.12-all.zip -d /opt/gradle && sudo ln -sfn gradle-1.12 /opt/gradle/latest && sudo printf \"export GRADLE_HOME=/opt/gradle/latest\nexport PATH=\$PATH:\$GRADLE_HOME/bin\" > /etc/profile.d/gradle.sh && . /etc/profile.d/gradle.sh", "root")


    print "Install Docker"
    sshHandle.sshExecute("curl -sSL https://get.docker.com/ | sh")
    sshHandle.sshExecute("sudo systemctl enable docker")
    print "Configure neverwinterdp user for Docker"
    sshHandle.sshExecute("sudo usermod -aG docker neverwinterdp")
    #Workaround for https://github.com/docker/docker/issues/17653
    sshHandle.sshExecute("sudo sed -i '/ExecStart=\/usr\/bin\/docker daemon -H fd:\/\//c\ExecStart=/usr/bin/docker daemon --exec-opt native.cgroupdriver=systemd -H fd:\/\/' /etc/systemd/system/multi-user.target.wants/docker.service")
    sshHandle.sshExecute("sudo systemctl stop docker")
    sshHandle.sshExecute("sudo systemctl start docker")
    sshHandle.sshExecute("sudo systemctl status docker")
    

    print "Install Ansible"
    sshHandle.sshExecute("sudo yum -y install ansible")
    
    
    print "Copy AWS credentials file"
    try:
      with open(awscredentialfile, 'r') as f:
        awsCreds = f.read()
      sshHandle.sshExecute("mkdir ~/.aws && echo \""+awsCreds+"\" > ~/.aws/credentials")
    except Exception as e:
      print "Problem copying AWS credentials file: "+str(e)
    
    print "Setup github credentials"
    try:
      gitUser = subprocess.Popen('git config --global user.name', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.readlines()[0].rstrip()
      gitEmail = subprocess.Popen('git config --global user.email', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.readlines()[0].rstrip()
      sshHandle.sshExecute("git config --global user.name \""+gitUser+"\"")
      sshHandle.sshExecute("git config --global user.email \""+gitEmail+"\"")
    except Exception as e:
      print "Problem getting github credentials: "+str(e)

    print "Check out NeverwinterDP"
    sshHandle.sshExecute("git clone https://github.com/Nventdata/NeverwinterDP/ && cd NeverwinterDP && git checkout "+branch)
    sshHandle.sshExecute(r'echo -e "NEVERWINTERDP_HOME=/home/neverwinterdp/NeverwinterDP\\n" >> /etc/environment', "root")
    print "Check out neverwinterdp-deployments"
    sshHandle.sshExecute("echo -e \"StrictHostKeyChecking no\\n\" >> ~/.ssh/config")
    sshHandle.sshExecute("git clone git@bitbucket.org:nventdata/neverwinterdp-deployments.git")
    
    print "Set up pip and python required libraries"
    sshHandle.sshExecute("sudo yum -y group install \"Development Tools\"")
    sshHandle.sshExecute("sudo yum -y install python-devel libffi-devel openssl-devel")
    sshHandle.sshExecute("sudo easy_install --upgrade nose==1.3.4 tabulate paramiko junit-xml click requests pip")
    sshHandle.sshExecute("sudo pip install pyopenssl==0.15.1 ndg-httpsclient pyasn1 kazoo elasticsearch python-digitalocean pyyaml --upgrade")

    print "Your droplet "+name+" is ready at 'ssh neverwinterdp@"+digitalOcean.getDropletIp(droplet.name)+"'"
  
  if destroy:
    import re
    doNotDestroy = [ re.compile('.*jenkins.*'),
                    re.compile('.*crucible.*'), ]
    
    if any(regex.match(name) for regex in doNotDestroy):
      click.echo(name+" matches a machine that will not be destroyed.  Returning")
      return
    
    click.echo("Are you SURE you wish to destroy "+name+"? (yes/no) ", nl=False)
    yes = set(['yes','y', 'ye'])
    no = set(['no','n'])
    
    choice = raw_input().lower()
    if choice in yes:
       digitalOcean.destroyDropletAndWait(digitalOcean.getDroplet(name))
    elif choice in no:
       click.echo("Skipping destruction")
    else:
       click.echo("Please respond with 'yes' or 'no'.  Returning.")
    
@mastercommand.command("kibana", help="commands to help import/export kibana visualizations")
@click.option('--import-kibana',  is_flag=True,    help='Import kibana')
@click.option('--import-kibana-from-host',  is_flag=True,    help='Import kibana from host machine')
@click.option('--export-kibana',  is_flag=True,    help='Export kibana')
@click.option('--elasticsearch-url',        default="http://elasticsearch-1:9200",  help='Elasticsear Url (with port) to connect, Ex: http://elasticsearch-1:9200')
@click.option('--temp-path',        default="/tmp/",  help='Temporary Path to save kibana json file')
def kibana(import_kibana, import_kibana_from_host, export_kibana, elasticsearch_url, temp_path):
  print "digitalocean"
  kibana = Kibana(elasticsearch_url, temp_path)
  
  if import_kibana:
    kibana.import_kibana()
    
  if import_kibana_from_host:
    kibana.import_kibana_from_host()
    
  if export_kibana:
    kibana.export_kibana()
  
@mastercommand.command("dataflowfailure",help="Failure Simulation for dataflow")
@click.option('--role',                           default='dataflow-worker', type=click.Choice(['dataflow-worker', 'dataflow-master']), help="'dataflow-worker' will run failure simulation on dataflow-worker, 'dataflow-master' will run failure simulation on dataflow-master,")
@click.option('--failure-interval',               default=180,  help="Time interval (in seconds) to fail server")
@click.option('--junit-report',                   default="",    help="If set, will write the junit-report to the specified file")
def dataflowfailure(role, failure_interval, junit_report):
  global _jobs
  
  dataflowFailure = DataFlowFailure(role)
  p = multiprocessing.Process(name="DataflowFailure",
                              target=dataflowFailure.dataflowFailureSimulation, 
                              args=(failure_interval, junit_report))
  _jobs.append(p)
  p.start()
  


@mastercommand.command("monitor",help="Monitor Cluster status")
@click.option('--update-interval', default=30, help="Time interval (in seconds) to wait between updating cluster status")
def monitor(update_interval):
  """
  Prints the cluster report
  """
  global _jobs
  p = multiprocessing.Process(name="Monitor",
                              target=doMonitor, 
                              args=(update_interval,))
  _jobs.append(p)
  p.start()

def doMonitor(interval):
  while True:
    try:
      cluster = Cluster()
      click.echo(cluster.getReport())
      click.echo("\n\n")
    except:
      click.echo("Error getting cluster report")
    sleep(interval)
    
def catchSignal(signal, frame):
  """
  Make sure we clean up when ctrl+c is hit
  """
  global _jobs
  for job in _jobs:
    try:
      job.terminate()
    except:
      pass
    try:
      job.join()
    except:
      pass
  exit(0)    


if __name__ == '__main__':
  #Set the signal handler
  signal.signal(signal.SIGINT, catchSignal)
  #Parse commands and run
  mastercommand()
  
  for job in _jobs:
    job.join()

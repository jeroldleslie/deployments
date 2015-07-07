#! /bin/sh
""":"
exec python $0 ${1+"$@"}
"""

import click, logging, multiprocessing, signal, os
from digitalocean import Droplet
from sys import stdout, exit
from time import sleep
from os.path import join, expanduser

from failure.FailureSimulator import ZookeeperFailure,KafkaFailure,DataFlowFailure
from Cluster import Cluster
from scribengindigitalocean.ScribenginDigitalOcean import ScribenginDigitalOcean

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

@mastercommand.command("scribengin", help="Scribengin commands")
@click.option('--restart',           is_flag=True, help="restart Scribengin")
@click.option('--start',             is_flag=True, help="start Scribengin")
@click.option('--stop',              is_flag=True, help="stop Scribengin")
@click.option('--force-stop',        is_flag=True, help="kill Scribengin")
@click.option('--wait-before-start', default=0,    help="Time to wait before restarting Scribengin (seconds)")
@click.option('--wait-before-report', default=5,    help="Time to wait before restarting reporting cluster status (seconds)")
@click.option('--build',   is_flag=True, help="Build Scribengin")
@click.option('--with-test',   is_flag=True, help="Build Scribengin with test")
@click.option('--deploy',   is_flag=True, help="Deploy Scribengin")
@click.option('--aws-credential-path', default="", help="Deploy Scribengin with aws credential. (--aws-credential-path='/root/.aws')")
@click.option('--clean',   is_flag=True, help="Clean cluster")
def scribengin(restart, start, stop, force_stop, wait_before_start, wait_before_report, build, with_test, deploy, aws_credential_path, clean):
  cluster = Cluster()
  neverwinterdp_home = _neverwinterdp_home
  if neverwinterdp_home == '':
    neverwinterdp_home = os.getenv('NEVERWINTERDP_HOME', 0)
    if neverwinterdp_home == 0:
      raise click.BadParameter("or set environment variable NEVERWINTERDP_HOME", param_hint = "--neverwinterdp-home")

  if(build):
    cluster.scribenginBuild(with_test, neverwinterdp_home)
    
  if(deploy):
    cluster.scribenginDeploy("hadoop-master", aws_credential_path, clean, neverwinterdp_home)
      
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
  
  logging.debug("Waiting for "+str(wait_before_report)+" seconds")
  sleep(wait_before_report)
  #click.echo(cluster.getReport())  

@mastercommand.command("cluster", help="Cluster commands")
@click.option('--restart',             is_flag=True, help="restart cluster")
@click.option('--start',               is_flag=True, help="start cluster")
@click.option('--stop',                is_flag=True, help="stop cluster")
@click.option('--force-stop',          is_flag=True, help="kill cluster")
@click.option('--clean',               is_flag=True, help="Clean old cluster data")
@click.option('--sync',                default="",   help="Sync cluster datas from the given hostname")
@click.option('--wait-before-start',   default=0,    help="Time to wait before restarting cluster (seconds)")
@click.option('--wait-before-kill',    default=0,    help="Time to wait before force killing cluster (seconds)")
@click.option('--kafka-server-config', default='/opt/kafka/config/default.properties', help='Kafka server configuration template path, default is /opt/kafka/config/default.properties', type=click.Path(exists=False))
@click.option('--zookeeper-server-config',  default='/opt/zookeeper/conf/zoo_sample.cfg', help='Zookeeper configuration template path, default is /opt/zookeeper/conf/zoo_sample.cfg', type=click.Path(exists=False))
@click.option('--execute',                           help='execute given command on all nodes')
def cluster(restart, start, stop, force_stop, clean, sync, wait_before_start, wait_before_kill, kafka_server_config, zookeeper_server_config, execute):
  cluster = Cluster()
      
  if(sync != ""):
    #Validating hostname
    hostname = sync
    if hostname in cluster.getHostnames():
      cluster.sync(sync)
    else:
      raise click.BadParameter("Host \"" + sync + "\" does not exist in the cluster.", param_hint = "--sync")
    
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
    logging.debug("Cleaning Kafka")
    cluster.cleanCluster()

  if(restart or start):
    logging.debug("Waiting for "+str(wait_before_start)+" seconds")
    if not os.path.exists(kafka_server_config):
      raise click.BadParameter("Path \"" + kafka_server_config + "\" does not exist.", param_hint = "--kafka-server-config")
    
    if not os.path.exists(zookeeper_server_config):
      raise click.BadParameter("Path \"" + zookeeper_server_config + "\" does not exist.", param_hint = "--zookeeper-server-config")
  
    sleep(wait_before_start)
    logging.debug("Starting Cluster")
    cluster.paramDict["server_config"] = kafka_server_config
    cluster.paramDict["zoo_cfg"] = zookeeper_server_config
    cluster.startCluster()
    
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
@click.option('--server-config',     default='/opt/kafka/config/default.properties', help='Kafka server configuration template path, default is /opt/kafka/config/default.properties', type=click.Path(exists=True))
#idle-servers comes after clean
def kafka(restart, start, stop, force_stop, clean, brokers, wait_before_start, wait_before_kill, server_config):
  cluster = Cluster()
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
    cluster.paramDict["server_config"] = server_config
    cluster.startKafka()
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
@click.option('--zoo-cfg',           default='/opt/zookeeper/conf/zoo_sample.cfg', help='Zookeeper configuration template path, default is /opt/zookeeper/conf/zoo_sample.cfg', type=click.Path(exists=True))
def zookeeper(restart, start, stop, force_stop, clean, zk_servers, wait_before_start, wait_before_kill, zoo_cfg):
  cluster = Cluster()
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
    cluster.paramDict["zoo_cfg"] = zoo_cfg
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
def hadoop(restart, start, stop, force_stop, clean, hadoop_nodes, wait_before_start, wait_before_kill,servers,grep_app_log,grep_app_stdout,grep_app_stderr):
  cluster = Cluster()
  
  cluster = cluster.getServersByRole("hadoop-master,hadoop-worker");
  
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
    cluster.startHadoopMaster()
    cluster.startHadoopWorker()
  
  #click.echo(cluster.getReport())

@mastercommand.command("kafkafailure",help="Failure Simulation for Kafka")
@click.option('--failure-interval',               default=180,  help="Time interval (in seconds) to fail server")
@click.option('--wait-before-start',              default=180,  help="Time to wait (in seconds) before starting server")
@click.option('--servers',                        default="",   help="Servers to effect.  Command separated list (i.e. --servers zk1,zk2,zk3)")
@click.option('--min-servers',                    default=1,    help="Minimum number of servers that must stay up")
@click.option('--servers-to-fail-simultaneously', default=1,    help="Number of servers to kill simultaneously")
@click.option('--kill-method',                    default='kill', type=click.Choice(['shutdown', 'kill', "random"]), help="Server kill method. Shutdown is clean, kill uses kill -9, random switches randomly")
@click.option('--initial-clean',                  is_flag=True, help="If enabled, will run a clean operation before starting the failure simulation")
@click.option('--server-config',                  default='/opt/kafka/config/default.properties', help='Kafka server configuration template path, default is /opt/kafka/config/default.properties', type=click.Path(exists=True))
@click.option('--junit-report',                   default="",   help="If set, will write the junit-report to the specified file")
@click.option('--restart-method',                 default='random', type=click.Choice(["flipflop", "random"]), help="Server restart method. 'flipflop' - it starts spare node if normal node killed and vise versa, 'random' - it starts any random node when failure occurs")
#use-spare before junit report
def kafkafailure(failure_interval, wait_before_start, servers, min_servers, servers_to_fail_simultaneously, kill_method, initial_clean, server_config, junit_report, restart_method):
  global _jobs
  
  kf = KafkaFailure()
  
  p = multiprocessing.Process(name="KafkaFailure",
                              target=kf.failureSimulation, 
                              args=(failure_interval, wait_before_start, servers, min_servers, 
                                    servers_to_fail_simultaneously, kill_method, initial_clean, server_config, junit_report, restart_method))
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
@click.option('--zoo-cfg',                        default='/opt/zookeeper/conf/zoo_sample.cfg', help='Zookeeper configuration template path, default is /opt/zookeeper/conf/zoo_sample.cfg', type=click.Path(exists=True))
@click.option('--junit-report',                   default="",    help="If set, will write the junit-report to the specified file")
@click.option('--restart-method',                 default='random', type=click.Choice(["random"]), help="Server restart method. 'random' - it starts any random node when failure occurs")
def zookeeperfailure(failure_interval, wait_before_start, servers, min_servers, servers_to_fail_simultaneously, kill_method, initial_clean, zoo_cfg, junit_report, restart_method):
  global _jobs
  
  zf = ZookeeperFailure()
  p = multiprocessing.Process(name="ZookeeperFailure",
                              target=zf.failureSimulation, 
                              args=(failure_interval, wait_before_start, servers, min_servers, 
                                    servers_to_fail_simultaneously, kill_method, initial_clean, zoo_cfg, junit_report, restart_method))
  _jobs.append(p)
  p.start()

@mastercommand.command("digitalocean", help="commands pertaining to digital-ocean droplets")
@click.option('--launch',                   is_flag=True,  help='Create containers, deploy, and run ansible')
@click.option('--create-containers',        default=None,  help='create the container using specified config')
@click.option('--update-local-host-file',   is_flag=True,  help='clean the container')
@click.option('--update-host-file',         is_flag=True,  help='clean the container')
@click.option('--setup-neverwinterdp-user', is_flag=True,  help='Sets up the neverwinterdp user')
@click.option('--ansible-inventory',        is_flag=True,  help='Creates ansible inventory file')
@click.option('--ansible-inventory-location', default="/tmp/scribengininventoryDO",  help='Where to save ansible inventory file')
@click.option('--region',                    default="lon1",  type=click.Choice(['lon1','sgp1','nyc1','nyc2','nyc3','sfo1']), help='Region to spawn droplet in')
@click.option('--deploy',                   is_flag=True,  help='Run ansible')
@click.option('--destroy',                  is_flag=True,  help='destroys all scribengin containers')
@click.option('--neverwinterdp-home',       default=None, help='neverwinterdp home')
@click.option('--digitaloceantoken',        default=None,  help='digital ocean token in plain text')
@click.option('--digitaloceantokenfile',    default='~/.digitaloceantoken', help='digital ocean token file location')
@click.option('--subdomain',                default="dev",  help='Subdomain to name hosts with in DO - i.e. hadoop-master.dev')
def digitalocean(launch, create_containers, update_local_host_file, update_host_file, setup_neverwinterdp_user,
                 ansible_inventory, ansible_inventory_location, region, deploy, destroy, 
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
  
  if deploy or launch:
    click.echo("Running ansible")
    digitalOcean.deploy(neverwinterdp_home)
  
  if destroy:
    click.echo("Destroying Scribengin droplets")
    digitalOcean.destroyAllScribenginDroplets(subdomain)
  
  
@mastercommand.command("digitaloceandevsetup", help="commands to help launch a developer box in digital ocean")
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
def digitaloceandevsetup(name, size, region, image, private_networking, create, destroy, branch,
                         digitaloceantoken, digitaloceantokenfile, sshkeypath, sshkeypathpublic):
  if "~/" in sshkeypath:
      sshkeypath = join( expanduser("~"), sshkeypath.replace("~/",""))
  if "~/" in sshkeypathpublic:
      sshkeypathpublic = join( expanduser("~"), sshkeypathpublic.replace("~/",""))
  
  
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
    sshHandle.sshExecute("sudo apt-get install software-properties-common -y && sudo apt-add-repository ppa:ansible/ansible -y && sudo apt-get update && sudo apt-get install ansible -y")
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

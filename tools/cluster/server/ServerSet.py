from tabulate import tabulate
from multiprocessing import Pool
import os, sys, re, yaml, click
from os.path import expanduser, join, abspath, dirname, realpath
from multiprocessing.pool import ThreadPool
from scribenginansible.ScribenginAnsible import ScribenginAnsible
from pydoc import Doc

#This function is outside the ServerSet class
#because otherwise it wouldn't be pickleable 
#http://stackoverflow.com/questions/1816958/cant-pickle-type-instancemethod-when-using-pythons-multiprocessing-pool-ma

def frameDictionary(process, processID, processIdentifier, running):
  return {
          "Role" : process.role,
          "Hostname": process.hostname,
          "HomeDir" : process.homeDir,
          "Status" : running,
          "ProcessIdentifier" : processIdentifier,
          "processID" : processID
        }

def getReportOnServer(server):
  omitStoppedProcesses = ["scribengin-master-*", "vm-master-*", "dataflow-master-*", 
                          "dataflow-worker-*", "grafana-server", "kibana", "influxdb" ]
  scribenginRoles = ["vmmaster", "scribengin", "dataflow-master", "dataflow-worker", "elasticsearch", "generic"]
  
  result = [] #list for individual process report
  report = [] #list for server report
  serverReportDict = server.getReportDict()
  
  if serverReportDict is not None and serverReportDict["Hostname"] :
    result.append([serverReportDict["Role"], serverReportDict["Hostname"], "", "", "",""])
    procs = server.getProcesses()
    
    #collecting process commands from all available processes from server
    processCommand = []
    for proc in procs:
      processCommand.append(procs[proc].getProcessCommand())
    
    
    #ssh to run process command and get pid and process name
    stdout,stderr = procs.values()[0].sshExecute(";".join(processCommand))
    
    #print serverReportDict["Hostname"] +" /// "+";".join(processCommand)+" /// "+stdout+ " /// "+stderr
    
    #extract pid and process name from stdout
    runningProcesses = {}
    for line in stdout.splitlines():
      pid_and_name = line.split(" ")
      runningProcesses[pid_and_name[0]] = pid_and_name[1]
    
    
    
    #adding none running process status
    for proc in procs:
      process = procs[proc]
      if process.processIdentifier not in runningProcesses.values():
        report.append(frameDictionary(process, "", process.processIdentifier, "None"))
    
    #adding running process status
    addedPids = [] #list to keep added pid's to report
    for proc in procs:
      process = procs[proc] 
      #filter process with the same name
      filtered_dict = {k:v for (k,v) in runningProcesses.items() if process.processIdentifier in v}
      for pid in filtered_dict:
        report.append(frameDictionary(process, pid, filtered_dict[pid], "Running"))
        addedPids.append(pid)
     
    #adding scribengin related process 
    for proc in procs:
      process = procs[proc]  
      if process.role in scribenginRoles:
        for pid in runningProcesses:
          if pid not in addedPids:
            report.append(frameDictionary(process, pid, runningProcesses[pid], "Running"))
            addedPids.append(pid)
    
    for procDict in report:
      if not (procDict["Status"] == "None" and procDict["ProcessIdentifier"] in omitStoppedProcesses):
        result.append(["","",procDict["ProcessIdentifier"], procDict["processID"], procDict["HomeDir"], procDict["Status"]])
  
  return result

class ServerSet(object):
  def __init__(self, name, numProcessesForStatus=30):
    self.role = name 
    self.servers = []
    self.paramDict = {}
    self.numProcessesForStatus = numProcessesForStatus
    
    deploymentRootDir = dirname(dirname(dirname(dirname(realpath(__file__)))))
    self.ansibleRootDir = join(deploymentRootDir, "ansible")
    
    self.scribenginAnsible = ScribenginAnsible()
    self.configurations = None
    
    self.inventoryFileLocation = "/tmp/scribengininventory"
    
        
  def clear(self):
    self.servers = []
  
  def printTitle(self, message):
    print "***********************************************************************"
    print message 
    print "***********************************************************************"  
  
  def setProfile(self, profile_type):
    profilePath = join(self.module_path(),"..","..","..","ansible","profile", profile_type+".yml")
    
    if os.path.isfile(profilePath):
      with open(profilePath, 'r') as f:
        self.configurations = yaml.load(f)
    else:
      raise click.BadParameter("--profile-type is not valid", param_hint = "--profile-type")
      
  def addServer(self, server):
    self.servers.append(server)
  
  def sshExecute(self, command, user="neverwinterdp", enableConsoleOutput = True, numThreads=10, timeout_sec=60):
    output = {}
    threads = []
    pool = ThreadPool(processes=numThreads)
    for server in self.servers :
      threads.append([server.getHostname(), pool.apply_async(server.sshExecute, (command, user))] )
      #output[server.getHostname()] = server.sshExecute(command, user)
    
    for t in threads:
      output[ t[0] ] = t[1].get(timeout=timeout_sec)
    return output 
    
  def startProcessOnHost(self, processName, hostname, setupClusterEnv = False):
    for server in self.servers :
      if server.getHostname() == hostname:
        server.startProcess(processName, self.paramDict, setupClusterEnv)
    
  def cleanProcessOnHost(self, processName, hostname):
    for server in self.servers :
      if server.getHostname() == hostname:
        server.cleanProcess(processName)
  
  def shutdownProcessOnHost(self, processName, hostname):
    for server in self.servers :
      if server.getHostname() == hostname:
        server.shutdownProcess(processName)
  
  def killProcessOnHost(self, processName, hostname):
    for server in self.servers :
      if server.getHostname() == hostname:
        server.killProcess(processName)
  
  def startProcess(self, processNames, setupClusterEnv = True, idleKafkaBrokers=0):
    for processName in processNames.split(","):
      for server in self.servers :
        if server.getRole() == "kafka":
          if idleKafkaBrokers == 0:
            server.startProcess(processName, self.paramDict, False)
          else:
            print "Skipping " +processName+" on "+ server.getHostname()
            idleKafkaBrokers -= 1
        else:
          server.startProcess(processName, self.paramDict, False)
    
  def cleanProcess(self, processNames):
    for processName in processNames.split(","):
      for server in self.servers : 
        server.cleanProcess(processName)
  
  def shutdownProcess(self, processNames):
    for processName in processNames.split(","):
      for server in self.servers :
        server.shutdownProcess(processName)
  
  def killProcess(self, processNames):
    for processName in processNames.split(","):
      for server in self.servers :
        server.killProcess(processName)
    
  def isProcessRunning(self, processName):
    for server in self.servers :
      process = server.getProcess(processName)
      if process is None:
        pass
      elif process.isRunning():
        return True
    return False
  
  def isProcessRunningOnHost(self, processName, hostname):
    for server in self.servers :
      if server.getHostname() == hostname:
        return server.getProcess(processName).isRunning()
    return False
        
  def getNumServers(self):
    return len(self.servers)
  
  def getServersByHostname(self, hostnames):
    serverSet = ServerSet("subset")
    serverSet.paramDict = self.paramDict
    for server in self.servers :
      if(server.getHostname().strip() in hostnames) :
        serverSet.addServer(server)
    return serverSet
  
  def getServersByRole(self, role):
    """
    Returns a subset of the ServerSet that has the role passed in
    """
    roles = role.split(",")
    serverSet = ServerSet("subset")
    serverSet.paramDict = self.paramDict
    
    serverSet.configurations=self.configurations 
    
    for server in self.servers :
      if(server.getRole() in roles) :
        serverSet.addServer(server)
    return serverSet
  
  def getHostnames(self):
    hostnames = []
    for server in self.servers :
      hostnames.append(server.hostname)
    return hostnames
  
  def startVmMaster(self):
    hadoopMasterServers = self.getServersByRole("hadoop-worker")
    if hadoopMasterServers.servers:
      return self.startProcessOnHost("vmmaster", hadoopMasterServers.servers[0].getHostname())
  
  def startScribengin(self):
    hadoopMasterServers = self.getServersByRole("hadoop-worker")
    if hadoopMasterServers.servers:
      return self.startProcessOnHost("scribengin", hadoopMasterServers.servers[0].getHostname())
  
  def startElasticSearch(self):
    self.startProcess("elasticsearch")
    self.scribenginAnsible.deploy(join(self.ansibleRootDir, "kibana.yml"),self.inventoryFileLocation)
  
  def shutdownElasticSearch(self):
    return self.shutdownProcess("elasticsearch")
  
  def killElasticSearch(self):
    return self.killProcess("elasticsearch")
  
  def startGrafana(self):
    return self.startProcess("grafana")
  
  def startGeneric(self):
    self.startProcess("grafana")
    self.startProcess("kibana")
    self.startProcess("influxdb")
  
  def runSetupEnvAnsible(self,role,profilelevel):
    extra_vars=self.getExtraVarsDict(self.configurations[profilelevel]["software"])
    self.scribenginAnsible.deploy(join(self.ansibleRootDir, role+"_env.yml"),self.inventoryFileLocation,extra_vars=extra_vars)
    
  def startZookeeper(self):
    self.runSetupEnvAnsible("zookeeper","zookeeper")
    return self.startProcess("zookeeper")
  
  def startKafka(self, idleKafkaBrokers=0):
    self.runSetupEnvAnsible("kafka","kafka")
    return self.startProcess("kafka",idleKafkaBrokers=idleKafkaBrokers)
  
  def cleanHadoopDataAtFirst(self):
    serverSet = self.getServersByRole("hadoop-worker")
    if not ( serverSet.servers and len(serverSet.servers) > 1 and serverSet.servers[0].getProcess("datanode").isDataDirExists() ):
      self.cleanHadoopMaster()
      self.cleanHadoopWorker()
    
  def startNameNode(self):
    return self.startProcess("namenode", setupClusterEnv = True)
  
  def startSecondaryNameNode(self):
    return self.startProcess("secondarynamenode", setupClusterEnv = False)
  
  def startResourceManager(self):
    return self.startProcess("resourcemanager", setupClusterEnv = False)
  
  def startDataNode(self):
    return self.startProcess("datanode", setupClusterEnv = True)
  
  def startNodeManager(self):
    return self.startProcess("nodemanager", setupClusterEnv = False)
  
  def startHadoopMaster(self):
    return self.startProcess("namenode,secondarynamenode,resourcemanager")
  
  def startHadoopWorker(self):
    return self.startProcess("datanode,nodemanager")
  
  def startHadoop(self):
    self.runSetupEnvAnsible("hadoop","hadoop-master")
    self.startHadoopMaster()
    self.startHadoopWorker()
    
  def startCluster(self,idleKafkaBrokers=0):
    self.startElasticSearch()
    self.startZookeeper()
    self.startKafka(idleKafkaBrokers)
    self.cleanHadoopDataAtFirst()
    self.startHadoop()
    self.startVmMaster()
    #self.startScribengin()
    self.startGeneric()
    
  def shutdownVmMaster(self):
    hadoopMasterServers = self.getServersByRole("hadoop-worker")
    if hadoopMasterServers.servers:
      return self.shutdownProcessOnHost("vmmaster", hadoopMasterServers.servers[0].getHostname())
  
  def shutdownScribengin(self):
    hadoopMasterServers = self.getServersByRole("hadoop-worker")
    if hadoopMasterServers.servers:
      return self.shutdownProcessOnHost("scribengin", hadoopMasterServers.servers[0].getHostname())
  
  def shutdownZookeeper(self):
    return self.shutdownProcess("zookeeper")
  
  def shutdownKafka(self):
    return self.shutdownProcess("kafka")
  
  def shutdownNameNode(self):
    return self.shutdownProcess("namenode")
  
  def shutdownSecondaryNameNode(self):
    return self.shutdownProcess("secondarynamenode")
  
  def shutdownResourceManager(self):
    return self.shutdownProcess("resourcemanager")
  
  def shutdownDataNode(self):
    return self.shutdownProcess("datanode")
  
  def shutdownNodeManager(self):
    return self.shutdownProcess("nodemanager")
  
  def shutdownHadoopMaster(self):
    return self.shutdownProcess("namenode,secondarynamenode,resourcemanager")
  
  def shutdownHadoopWorker(self):
    return self.shutdownProcess("datanode,nodemanager")
    
  def shutdownCluster(self):
    self.killScribengin()
    self.killVmMaster()
    self.shutdownKafka()
    self.shutdownZookeeper()
    self.shutdownHadoopWorker()
    self.shutdownHadoopMaster()
    
  def killScribengin(self):
    return self.killProcess("scribengin")
  
  def killVmMaster(self):
    return self.killProcess("vmmaster")
  
  def killZookeeper(self):
    return self.killProcess("zookeeper")
  
  def killKafka(self):
    return self.killProcess("kafka")
  
  def killNameNode(self):
    return self.killProcess("namenode")
  
  def killSecondaryNameNode(self):
    return self.killProcess("secondarynamenode")
  
  def killResourceManager(self):
    return self.killProcess("resourcemanager")
  
  def killDataNode(self):
    return self.killProcess("datanode")
  
  def killNodeManager(self):
    return self.killProcess("nodemanager")
  
  def killHadoopMaster(self):
    return self.killProcess("namenode,secondarynamenode,resourcemanager")
  
  def killHadoopWorker(self):
    return self.killProcess("datanode,nodemanager")  
  
  def killKibana(self):
    return self.killProcess("kibana")
  
  def killCluster(self):
    #self.shutdownScribengin()
    self.shutdownVmMaster()
    self.killKafka()
    self.killZookeeper()
    self.killHadoopWorker()
    self.killHadoopMaster()
    self.killElasticSearch()
    self.killKibana()
    
  def cleanKafka(self):
    return self.cleanProcess("kafka")
  
  def cleanZookeeper(self):
    return self.cleanProcess("zookeeper")
  
  def cleanHadoopMaster(self):
    return self.cleanProcess("namenode")
  
  def cleanHadoopWorker(self):
    return self.cleanProcess("datanode")

  def cleanElasticsearch(self):
    return self.cleanProcess("elasticsearch")
  
  def cleanCluster(self):
    self.cleanKafka()
    self.cleanZookeeper()
    self.cleanHadoopWorker()
    self.cleanHadoopMaster()
    self.cleanElasticsearch()
    
  def getReport(self):
    serverReport = []
    asyncresults = []
    pool = Pool(processes=self.numProcessesForStatus)
    sorted_servers = sorted(self.servers, key=lambda server: server.role)
    for server in sorted_servers:
      asyncresults.append( pool.apply_async(getReportOnServer, [server])) 
    
    for async in asyncresults:
      result = async.get(timeout=30)
      if result: 
        for row in result:
          serverReport.append(row)

    headers = ["Role", "Hostname", "ProcessIdentifier", "ProcessID", "HomeDir", "Status"]
    pool.close()
    pool.join()
    return tabulate(serverReport, headers=headers)

  def report(self) :
    print self.getReport()
  
  def createAnsibleInventory(self, ansible_ssh_user='neverwinterdp', ansible_ssh_private_key_file='~/.ssh/id_rsa'):
    self.scribenginAnsible.writeAnsibleInventory(hostsAndIps=self.getHostsAndIpsFromCluster(),inventoryFileLocation=self.inventoryFileLocation,ansibleSshUser=ansible_ssh_user, ansibleSshKey=ansible_ssh_private_key_file)
    
  def getHostsAndIpsFromCluster(self):
    import socket
    hostsAndIps = []
    for server in self.servers:
      hostsAndIps.append({
                          "name":server.hostname,
                          "ip": socket.gethostbyname(server.hostname)
                          })
    return hostsAndIps
  
    
  def we_are_frozen(self):
      # All of the modules are built-in to the interpreter, e.g., by py2exe
      return hasattr(sys, "frozen")
  
  def module_path(self):
      encoding = sys.getfilesystemencoding()
      if self.we_are_frozen():
          return os.path.dirname(unicode(sys.executable, encoding))
      return os.path.dirname(unicode(__file__, encoding))
  
  def getExtraVarsDict(self,profile):
    extra_vars={}
    for k in profile:
      extra_vars.update(profile[k])
    return extra_vars

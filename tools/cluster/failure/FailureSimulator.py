from sys import exit
from time import sleep,time
from random import randint, sample, choice
from junit_xml import TestSuite, TestCase
import logging
import os, re

from Cluster import Cluster  #@UnresolvedImport

class FailureSimulator():
  def __init__(self, role=None):
    self.roleName = role
    self.mainCluster = Cluster()
    self.cluster = None
        
  def failureSimulation(self,failure_interval, wait_before_start, servers, min_servers, servers_to_fail_simultaneously, kill_method, initial_clean, junit_report, restart_method):
    """
    Run the failure loop for a given role
    """
    logging.debug("Failure interval: " + str(failure_interval))
    logging.debug("Wait before start: " + str(wait_before_start)) 
    logging.debug("Minimum number of servers: " + str(min_servers))
    logging.debug("Number of servers to fail simultaneously: " + str(servers_to_fail_simultaneously)) 
    logging.debug("Kill method: " + kill_method)
    logging.debug("Initial clean: " + str(initial_clean)) 
    logging.debug("Role name: "+ self.roleName)
    logging.debug("Junit Report: "+ junit_report)
    
    testCases = []
    testNum = 0
        
    serverArray = []
    if(servers == ""):
      self.cluster = self.mainCluster.getServersByRole(self.roleName)
      for server in self.cluster.servers:
        serverArray.append(server.getHostname())
    else:
      serverArray = servers.split(",")
      self.cluster = self.mainCluster.getServersByHostname(serverArray)
    
    logging.debug("Servers selected for failure simulation: " + ",".join(serverArray))
    logging.debug("Cluster length : " + str(len(self.cluster.servers)))
          
    if min_servers >= self.cluster.getNumServers():
      raise ValueError("Minimum Number of servers is too high!\nMinimum Servers to stay up: "
                       +str(min_servers)+"\nNumber of "+self.roleName+" servers in cluster: "+str(self.cluster.getNumServers()))
      exit(-1)
    
    if servers_to_fail_simultaneously > self.cluster.getNumServers() - min_servers:
      raise ValueError("--servers_to_fail_simultaneously is set too high")
      exit(-1)   
    
    if initial_clean:
      logging.debug("Initial clean")
      self.cluster.cleanProcess(self.roleName)
    
    #Find running and Idle servers initially    
    runningServers = []
    idleServers = []
    
    for server in self.cluster.servers:
      hostname = server.getHostname()
      if server.getProcess(self.roleName).isRunning():
        runningServers.append(hostname)
      else:
        idleServers.append(hostname)
    
    
    while True:
      logging.debug("**************************Killing Process**************************")
      logging.debug("Running servers before kill/shutdown: " + str(runningServers))
      logging.debug("Idle servers before kill/shutdown: "+str(idleServers))
      logging.debug("Sleeping for "+str(failure_interval)+" seconds")
      start = time()
      sleep(failure_interval)
      
      serversToKill=[]
      #pick random servers to kill
      serversToKill = sample(runningServers, servers_to_fail_simultaneously)
      serversInReplicasList = runningServers[:]
      
      logging.debug("Servers selected to kill: "+ ','.join(serversToKill))
      
      #Stop the running process based on kill_method
      #currentExecutingCluster = None
      for hostname in serversToKill:
        if kill_method == "shutdown" :
          #Shutting down process
          self.cluster.shutdownProcessOnHost(self.roleName, hostname)
        elif kill_method == "kill":
          #Killing process
          self.cluster.killProcessOnHost(self.roleName, hostname)
        else:
          if randint(0,1) == 0:
            #Shutting down process
            self.cluster.shutdownProcessOnHost(self.roleName, hostname)
          else:
            #Killing process
            self.cluster.killProcessOnHost(self.roleName, hostname)
      
      #Allow kafka to kill/shutdown
      sleep(5)
      
      #Ensure the process has stopped
      for hostname in serversToKill:
        #Create basis for test case
        tc = TestCase('Test'+str(testNum), self.roleName+'FailureSimulator', time()-start, 
                      'Shutting down '+self.roleName+" with kill_method "+kill_method+" on host "+hostname, '')
        #If the process is still running, then try killing it one more time
        if(self.cluster.isProcessRunningOnHost(self.roleName, hostname)):
          logging.debug("Killing "+self.roleName + " on " +hostname+" one last time")
          self.cluster.killProcessOnHost(self.roleName, hostname)
          #If the process is *still* running then report a failure
          if(self.cluster.isProcessRunningOnHost(self.roleName, hostname)):
            tc.add_failure_info(self.roleName+" process is still running on"+hostname, "")
            logging.debug(self.roleName+" process is still running on"+hostname, "")
          else:
            #update running and idle server list
            runningServers.remove(hostname)
            idleServers.append(hostname)
        else:
          #update running and idle server list
          runningServers.remove(hostname)
          idleServers.append(hostname)
          
        testCases.append(tc)
        testNum+=1
        
      logging.debug("Running servers after kill/shutdown: " + str(runningServers))
      logging.debug("Idle servers after kill/shutdown: "+str(idleServers))
      logging.debug("********************************************************************")
      logging.debug("**************************Starting Process**************************")
      logging.debug("Running servers before starting: " + str(runningServers))
      logging.debug("Idle servers before starting: "+str(idleServers))
      #Start the process again
      logging.debug("Sleeping for "+str(failure_interval)+" seconds")
      start = time()
      sleep(wait_before_start)
      newServers = []
      
      serversToStart=[]
      if len(idleServers) > 0:
        serversToStart = sample(idleServers, servers_to_fail_simultaneously)

      logging.debug("Servers selected to start: "+','.join(serversToStart))
      for hostname in serversToStart:
        if hostname not in serversInReplicasList:
          newServers.append(hostname)
          self.cluster.cleanProcessOnHost(self.roleName, hostname)
        #starting process
        self.cluster.startProcessOnHost(self.roleName, hostname, False)
        
      #Ensure the process has started, otherwise report a failure
      for hostname in serversToStart:
        tc = TestCase('Test'+str(testNum), self.roleName+'FailureSimulator', time()-start, 
                      'Starting '+self.roleName+" on host: "+hostname, '')
        if( not self.cluster.isProcessRunningOnHost(self.roleName, hostname)):
          tc.add_failure_info(self.roleName+" process is still running on"+hostname, "")
        else:
          #update running and idle server list
          runningServers.append(hostname)
          idleServers.remove(hostname)
        testCases.append(tc)
        testNum+=1
      
      logging.debug("Running servers after started: " + str(runningServers))
      logging.debug("Idle servers after started: "+str(idleServers))
      logging.debug("************************************************************************")
      logging.debug("**************************Reassignment Process**************************")
      logging.debug("Servers in replicas list: "+ ",".join(serversInReplicasList))
      logging.debug("New Servers: "+ ",".join(newServers))
      #Reassign replicas processes
      if len(newServers) > 0:
        #Getting new broker list
        if self.roleName == "kafka":
          newBrokers = []
          for hostname in newServers:
            brokerID = int(re.search(r'\d+', hostname).group())
            newBrokers.append(str(brokerID))
          logging.debug("Reassigning replicas for "+",".join(newBrokers))
          #start run reassigning replicas
          self.cluster.servers[0].getProcess(self.roleName).reassignReplicas(self.cluster.paramDict["zkList"], ",".join(newBrokers))
        elif self.roleName == "zookeeper":
          '''
          TODO if any required
          '''
      logging.debug("************************************************************************")
      
      if(not junit_report == "" ):
        logging.debug("Writing junit report to: "+junit_report)
        if(not os.path.exists(os.path.dirname(junit_report))):
          os.makedirs(os.path.dirname(junit_report))
        f = open(junit_report,'w')
        ts = TestSuite(self.roleName+" Test Suite", testCases)
        f.write(TestSuite.to_xml_string([ts]))
        f.close()

class KafkaFailure(FailureSimulator):
  def __init__(self):
    FailureSimulator.__init__(self, "kafka");

class ZookeeperFailure(FailureSimulator):
  def __init__(self):
    FailureSimulator.__init__(self, "zookeeper");

class DataFlowFailure(FailureSimulator):
  def __init__(self, role):
    FailureSimulator.__init__(self, role);

  def getServerArray(self, cluster):
    serverArray = []
    for server in cluster.servers:
      serverArray.append(server.getHostname())
    return serverArray
  
  def sshExecuteOnHost(self, cluster, hostname, command):
    for server in cluster.servers:
      if server.getHostname() == hostname:
        return server.sshExecute(command, False)
  
  def getRunningDataflowProcessNamesOnHost(self, cluster, hostname, processName):
    command = "jps -m | grep '" + processName + "' | awk '{print $4}'"
    return self.sshExecuteOnHost(cluster, hostname, command)[0].strip().split("\n")

  def killProcessOnHost(self, cluster, hostname, processName):
    command = "jps -m | grep '" + processName + "' | awk '{print $1}' | xargs kill -9"
    return self.sshExecuteOnHost(cluster, hostname, command)
    
  def isProcessRunningOnHost(self, cluster, hostname, processName):
    processNames = self.getRunningDataflowProcessNamesOnHost(cluster, hostname, processName)
    if processNames[0] != '':
      return True
    else:
      return False
  
  def dataflowFailureSimulation(self, failure_interval, junit_report):
    
    testCases = []
    testNum = 0
    
    logging.debug("Failure interval: " + str(failure_interval))
    logging.debug("Role name: "+ self.roleName)
    logging.debug("Junit Report: "+ junit_report)
    
    num_process_to_fail_simultaneously = 1
    cluster = Cluster()
    cluster = cluster.getServersByRole("hadoop-worker")
    serverArray = self.getServerArray(cluster)
    
    while True:
      start = time()
      failedCount = 0
      sleep(failure_interval)
      killedProcesses = {}
      while True:
        serversToCheck = sample(serverArray, num_process_to_fail_simultaneously)
        for hostname in serversToCheck:
          processNames = self.getRunningDataflowProcessNamesOnHost(cluster, hostname, self.roleName + "-*")
          processName = sample(processNames, 1)[0]
          if processName != '':
            logging.debug("Killing " + processName + " on " + hostname)
            killedProcesses[hostname] = processName
            self.killProcessOnHost(cluster, hostname, processName)
            failedCount = failedCount+1
          if failedCount == num_process_to_fail_simultaneously:
            break
        if failedCount == num_process_to_fail_simultaneously:
          break
      
      for hostname in killedProcesses.keys():
        processName = killedProcesses[hostname]
        #Create basis for test case
        tc = TestCase('Test'+str(testNum), processName+'FailureSimulator', time()-start, 
                      'Killing '+processName+" on host "+hostname, '')
        #If the process is still running, then try killing it one more time
        if(self.isProcessRunningOnHost(cluster, hostname, processName)):
          logging.debug("Killing "+processName + " on " +hostname+" one last time")
          self.killProcessOnHost(cluster, hostname, processName)
          #If the process is *still* running then report a failure
          if(cluster.isProcessRunningOnHost(processName, hostname)):
            tc.add_failure_info(processName+" is still running on"+hostname, "")
        testCases.append(tc)
        testNum+=1
        
      if(not junit_report == "" ):
        logging.debug("Writing junit report to: "+junit_report)
        if(not os.path.exists(os.path.dirname(junit_report))):
          os.makedirs(os.path.dirname(junit_report))
        f = open(junit_report,'w')
        ts = TestSuite(self.roleName+" Test Suite", testCases)
        f.write(TestSuite.to_xml_string([ts]))
        f.close()
    
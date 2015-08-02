from os.path import expanduser, join, abspath, dirname
from sys import path, stdout
from time import sleep
from random import sample
from tabulate import tabulate
import paramiko, re, string, logging
import logging
from itertools import cycle
#Make sure the cluster package is on the path correctly
path.insert(0, dirname(dirname(abspath(__file__))))

class Process(object):
  def __init__(self, role, hostname, homeDir, processIdentifier, sshKeyPath=join(expanduser("~"),".ssh/id_rsa")):
    self.role = role ;
    self.hostname = hostname;
    self.homeDir = homeDir;
    self.processIdentifier = processIdentifier;
    self.sshKeyPath = sshKeyPath
    
  def sshExecute(self, command, user = "neverwinterdp", maxRetries=10, retries=0, sleepTime=10):
    """
    SSH onto a machine, execute a command
    Returns [stdout,stderr]
    """
    try:
      key = paramiko.RSAKey.from_private_key_file(self.sshKeyPath)
      
      c = paramiko.SSHClient()
      c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      c.connect( hostname = self.hostname, username = user, pkey = key, timeout = 10 )
      stdin, stdout, stderr = c.exec_command(command)
      
      stdout = stdout.read()
      stderr = stderr.read()
      c.close()
    except:
      if retries < maxRetries:
        sleep(sleepTime)
        return self.sshExecute(command, user, maxRetries, retries+1, sleepTime)
      else:
        logging.error("Error connecting to "+str(self.hostname)+" as user "+str(user))
        print "Error connecting to "+str(self.hostname)+" as user "+str(user)
        raise
    #logging.debug("SSH execute stdout: "+stdout)
    #logging.debug("SSH execute stderr: "+stderr)
    
    return stdout,stderr
  
  def getReportDict(self):
    report = []
    running = "Running"
    if not self.isRunning():
      running = "None"
    dictionary = {
      "Role" : self.role,
      "Hostname": self.hostname,
      "HomeDir" : self.homeDir,
      "Status" : running,
      "ProcessIdentifier" : self.processIdentifier,
      "processID" : self.getRunningPid()
      }
    report.append(dictionary)
    logging.debug("Report Dict: "+str(dictionary))
    return report
  
  def getReportDictForVMAndScribengin(self):
    report = []
    running = "Running"
    if not self.isRunning():
      running = "None"
    pids = self.getRunningPid()
    if pids != "":
      for pid in pids.split(","):
        pid_and_name = pid.split(" ")
        dictionary = {
          "Role" : self.role,
          "Hostname": self.hostname,
          "HomeDir" : self.homeDir,
          "Status" : running
          }
        
        dictionary["ProcessIdentifier"] = pid_and_name[1]
        dictionary["processID"] = pid_and_name[0]
        report.append(dictionary)
    logging.debug("Report Dict for VM and Scribengin: "+str(dictionary))
    return report
  
  def getReport(self):
    report = self.getReportDict()
    result = tabulate([report.values()], headers=report.keys())
    logging.debug("Get Report: "+str(result))
    return result
    
  def report(self):
    print self.getReport()
  
  def isRunning(self):
    isRunning = len(self.getRunningPid()) > 0
    logging.debug("isRunning: "+str(isRunning))
    return isRunning
  
  def getRole(self):
    return self.role
    
  def kill(self):
    self.printProgress("Killing ")
    pids = self.getRunningPid()
    for pid in pids.split(","):
      self.sshExecute("kill -9 "+pid)
   
  def getProcessCommand(self):
    return "jps -m | grep -w '"+self.processIdentifier+"' | awk '{print $1 \" \" $2}'"
  
  def getRunningPid(self):
    command = "ps ax | grep -w '"+self.processIdentifier+"' | grep java | grep -v grep | awk '{print $1}'"
    stdout,stderr = self.sshExecute(command)
    return stdout.strip().replace("\n",",")
  
  def isDataDirExists(self):
    if self.sshExecute("if [ -d \"" + join(self.homeDir, "data") + "\" ]; then echo \"true\"; fi")[0].strip() == "true":
      return True
    else:
      return False
    
  def start(self):
    pass
  
  def shutdown(self):
    pass
  
  def clean(self):
    pass
  
  def setupClusterEnv(self, paramDict = {}):
    pass
  
  def replaceString(self, pattern, replaceStr, line):
    return re.sub(pattern, replaceStr, line.rstrip())
  
  def printProgress(self, printStr):
    string = printStr + self.getRole() + " on " + self.hostname
    logging.info(string)
    print string
    
############

class KafkaProcess(Process):
  def __init__(self, role, hostname):
    Process.__init__(self, role, hostname, "/opt/kafka", "Kafka")
   
  def setupClusterEnv(self, paramDict = {}):
    pass
  
  def findBetween(self, s, first, last ):
    try:
      start = s.index( first ) + len( first )
      end = s.index( last, start )
      return s[start:end]
    except ValueError:
      return ""
         
  def reassignReplicas(self, zkServer, new_brokers):
    logging.debug("Reassigning replicas started "+ str(new_brokers))
    zk_connect = ":2181,".join(zkServer) + ":2181"
    expand_json_path = ""
 
    retry = True
    while retry:
      describePath = join(self.homeDir, "bin/kafka-topics.sh --describe --zookeeper "+zk_connect)
      logging.debug("***********************Before reassigning replicas********************")
      stdout,stderr = self.sshExecute(describePath)
      logging.debug("STDOUT from executing "+describePath+": \n"+stdout)
      logging.debug("STDERR from executing "+describePath+": \n"+stderr)
      
      
      if not stderr:
        retry = False
        new_brokers = new_brokers.split(",")
        topics_json_list=[]
        topics_to_move_json = self.generateReassignmentJson(stdout, topics_json_list, new_brokers)
        #Create Json file
        if len(topics_json_list) > 0:
          expand_json_path = join(self.homeDir, "expand-cluster-reassignment.json")
          stdout,stderr = self.sshExecute("echo \"" + topics_to_move_json + "\" > " + expand_json_path)
          logging.debug("Topics to move JSON file: \n"+topics_to_move_json)
          logging.debug("STDOUT from executing "+expand_json_path+": \n"+stdout)
          logging.debug("STDERR from executing "+expand_json_path+": \n"+stderr)
          
          #execute reassignment
          executePath = join(self.homeDir, "bin/kafka-reassign-partitions.sh --zookeeper "+zk_connect+" --reassignment-json-file "+expand_json_path+" --execute") 
          stdout,stderr = self.sshExecute(executePath)
          logging.debug("STDOUT from executing "+executePath+": \n"+stdout)
          logging.debug("STDERR from executing "+executePath+": \n"+stderr)
          
          #Verify the status of the partition reassignment
          not_completed_successfully = True
          while not_completed_successfully:
            verifyPath = join(self.homeDir, "bin/kafka-reassign-partitions.sh --zookeeper "+zk_connect+" --reassignment-json-file "+expand_json_path+" --verify") 
            stdout,stderr = self.sshExecute(verifyPath)
            
            logging.debug("STDOUT from executing "+verifyPath+": \n"+stdout)
            logging.debug("STDERR from executing "+verifyPath+": \n"+stderr)
          
            for line in stdout.splitlines():
              if not re.match("Status of partition reassignment:.*", line):
                if re.match('.*completed successfully.*', line):
                  not_completed_successfully = False
                elif re.match('.*ERROR:.*', line):
                  not_completed_successfully = False
                  break
                else:
                  not_completed_successfully = True
                  break
    
            sleep(2)
          logging.debug("Reassignment Successfull....");
      logging.debug("***********************After reassigning replicas********************")
      stdout,stderr = self.sshExecute(describePath)
      logging.debug("STDOUT from executing "+describePath+": \n"+stdout)
      logging.debug("STDERR from executing "+describePath+": \n"+stderr)
  
             
  def generateReassignmentJson(self, stdout,topics_json_list,new_brokers):
    #generating json
    #topics_json_list=[]
    new_brokers = map(str, new_brokers)
    itert = cycle(new_brokers)
    topics_to_move_json = "{\\\"version\\\":1,\\\"partitions\\\":["
    for line in stdout.splitlines():
      if not re.match('.*ReplicationFactor.*', line):
        if re.match('.*Topic:.*', line):
          line = string.replace(line, "\t", " ")
          line = line + " end"
          #topic= re.search("(?<=\Topic:\s)(\w+)", line).group()
          topic = self.findBetween(line,"Topic:", "Partition:").strip()
          partition=re.search("(?<=\Partition:\s)(\w+)", line).group()
          replicas_list = re.compile(r'Replicas:\s*(.*?)\s*Isr:', re.DOTALL).findall(line)[0].split(",")
          if len(set(new_brokers).intersection(replicas_list))>0:
            raise ValueError("One of the new brokers is already in Replica list")
          isr_list = re.compile(r'Isr:\s*(.*?)\s*end', re.DOTALL).findall(line)[0].split(",")
        
          add_to_json = False
          while len(isr_list) <  len(replicas_list):
            add_to_json = True
            broker_to_add = itert.next()
            if broker_to_add[0] not in isr_list:
              isr_list.append(broker_to_add[0])
          if add_to_json:
            topics_json_list.append("{\\\"topic\\\":\\\""+str(topic)+"\\\",\\\"partition\\\":"+str(partition)+",\\\"replicas\\\":["+",".join(map(str, isr_list))+"]}")
        
    topics_to_move_json = topics_to_move_json + ",".join(topics_json_list) + "]}"
    return topics_to_move_json
    
  def start(self):
    self.printProgress("Starting ")
    return self.sshExecute(join(self.homeDir, "bin/kafka-server-start.sh")+" -daemon "+ join(self.homeDir, "config/server.properties"))
        
  def shutdown(self):
    self.printProgress("Stopping ")
    return self.sshExecute( join(self.homeDir, "bin/kafka-server-stop.sh") )
  
  def clean(self):
    self.printProgress("Cleaning data of ")
    return self.sshExecute("rm -rf "+join(self.homeDir, "data")+ " && rm -rf "+join(self.homeDir, "logs"))
    
############

class ZookeeperProcess(Process):
  def __init__(self, role, hostname):
    Process.__init__(self, role, hostname, "/opt/zookeeper", 'QuorumPeerMain')
    
  def setupClusterEnv(self, paramDict = {}):
    pass
    
  def start(self):
    self.printProgress("Starting ")
    return self.sshExecute("ZOO_LOG4J_PROP='INFO,ROLLINGFILE' ZOO_LOG_DIR="+join(self.homeDir,"logs")+" "+join(self.homeDir, "bin/zkServer.sh")+ " start")
    
  def shutdown(self):
    self.printProgress("Stopping ")
    return self.sshExecute( join(self.homeDir,"bin/zkServer.sh")+ " stop")
  
  def clean(self):
    self.printProgress("Cleaning data of ")
    return self.sshExecute("cd "+join(self.homeDir, "data")+ " && ls | grep -v 'myid' | xargs rm -rf && rm -rf "+join(self.homeDir, "logs")+" && rm -rf "+ join(self.homeDir, "zookeeper.out"))
 
############

class HadoopDaemonProcess(Process):
  def __init__(self, role, hostname, processIdentifier, hadoopDaemonScriptPath = "unknown"):
    Process.__init__(self, role, hostname, "/opt/hadoop", processIdentifier)
    self.hadoopDaemonScriptPath = hadoopDaemonScriptPath
  
  def setupClusterEnv(self, paramDict = {}):
    pass
    
  def start(self):
    self.printProgress("Starting ")
    return self.sshExecute(join(self.homeDir, self.hadoopDaemonScriptPath) + " start " + self.getRole())
    
  def shutdown(self):
    self.printProgress("Stopping ")
    return self.sshExecute(join(self.homeDir, self.hadoopDaemonScriptPath) + " stop " + self.getRole())
  
  def clean(self):
    self.printProgress("Cleaning data of ")
    return self.sshExecute("rm -rf "+ join(self.homeDir, "data") +" && rm -rf " + join(self.homeDir, "logs") +" && rm -rf " + join(self.homeDir, "vm") +" && yes | "+ join(self.homeDir, "bin/hdfs") + " namenode -format") 

############
class ScribenginProcess(Process):
  def getProcessCommand(self):
    return "jps -m | grep '"+self.processIdentifier+"' | awk '{print $1 \" \" $4}'"
  
############
class ScribenginMasterProcess(ScribenginProcess):
  def __init__(self, role, hostname):
    Process.__init__(self, role, hostname, "/opt/neverwinterdp/scribengin/bin/", "scribengin-master-*")
    self.hostname = hostname
  
  def setupClusterEnv(self, paramDict = {}):
    pass
  
  def getReportDict(self):
    return self.getReportDictForVMAndScribengin()
  
  def getRunningPid(self):
    command = "jps -m | grep '"+self.processIdentifier+"\|dataflow-master-*\|dataflow-worker-*' | awk '{print $1 \" \" $4}'"
    stdout,stderr = self.sshExecute(command)
    return stdout.strip().replace("\n",",")
  
  def start(self):
    self.printProgress("Starting ")
    stdout,stderr = self.sshExecute(join(self.homeDir, "shell.sh")+" scribengin start")
    logging.info("STDOUT from scribengin start: \n"+stdout)
    logging.info("STDERR from scribengin start: \n"+stderr)
    print "STDOUT from scribengin start: \n"+stdout
    print "STDERR from scribengin start: \n"+stderr
    
  def shutdown(self):
    self.printProgress("Stopping ")
    self.sshExecute(join(self.homeDir, "shell.sh")+" scribengin shutdown")
  
  def clean(self):
    pass 
  
  def kill(self):
    return self.sshExecute("pkill -9 java")

############
class VmMasterProcess(ScribenginProcess):
  def __init__(self, role, hostname):
    Process.__init__(self, role, hostname, "/opt/neverwinterdp/scribengin/bin/", "vm-master-*")
    
  def setupClusterEnv(self, paramDict = {}):
    pass
  
  def getReportDict(self):
    return self.getReportDictForVMAndScribengin()
  
  def getRunningPid(self):
    command = "jps -m | grep '"+self.processIdentifier+"' | awk '{print $1 \" \" $4}'"
    stdout,stderr = self.sshExecute(command)
    return stdout.strip().replace("\n",",")
  
  def start(self):
    self.printProgress("Starting ")
    stdout,stderr = self.sshExecute(join(self.homeDir, "shell.sh")+" vm start")
    logging.info("STDOUT from vm start: \n"+stdout)
    logging.info("STDERR from vm start: \n"+stderr)
    print "STDOUT from vm start: \n"+stdout
    print "STDERR from vm start: \n"+stderr
    
  def shutdown(self):
    self.printProgress("Stopping ")
    self.sshExecute(join(self.homeDir, "shell.sh")+" vm shutdown")
  
  def clean(self):
    pass 
  
  def kill(self):
    return self.sshExecute("pkill -9 java")

############
class DataflowMasterProcess(ScribenginProcess):
  def __init__(self, role, hostname, processIdentifier):
    Process.__init__(self, role, hostname, "/opt/neverwinterdp/scribengin/bin/", processIdentifier)
    self.hostname = hostname
    
  def setupClusterEnv(self, paramDict = {}):
    pass
  
  def getReportDict(self):
    pass
  
  def getRunningPid(self):
    pass
  
  def start(self):
    pass
    
  def shutdown(self):
    pass
  
  def clean(self):
    pass 
  
  def kill(self):
    pass

############
class DataflowWorkerProcess(ScribenginProcess):
  def __init__(self, role, hostname, processIdentifier):
    Process.__init__(self, role, hostname, "/opt/neverwinterdp/scribengin/bin/", processIdentifier)
    self.hostname = hostname
    
  def setupClusterEnv(self, paramDict = {}):
    pass
  
  def getReportDict(self):
    pass

  def getRunningPid(self):
    pass
  
  def start(self):
    pass
    
  def shutdown(self):
    pass
  
  def clean(self):
    pass 
  
  def kill(self):
    pass
 
class ElasticSearchProcess(Process): 
  def __init__(self, role, hostname):
    Process.__init__(self, role, hostname, "/opt/elasticsearch/", "com.neverwinterdp.es.Main")
  
  def setupClusterEnv(self, paramDict = {}):
    pass
  
  def getProcessCommand(self):
    return "jps -l | grep -w '"+self.processIdentifier+"' | awk '{print $1 \" \" $2}'"
  #  return "ps ax | grep "+self.processIdentifier+" | awk '{print $1 \" \" $27}' | grep -i elastic"
  
  def kill(self):
    self.printProgress("Killing ")
    stdout,stderr = self.sshExecute(self.getProcessCommand());
    pid_and_name = stdout.split(" ")
    self.sshExecute("kill -9 "+pid_and_name[0])

  #def getReportDict(self):
  #  pass

  #def getRunningPid(self):
  #  pass
  
  def start(self):
    if not self.isRunning():
      stdout,stderr = self.sshExecute(join(self.homeDir, join("bin", "elasticsearch.sh")))
      return stdout,stderr
    else:
      return None,None
    
  def shutdown(self):
    return self.kill()
  
  def clean(self):
    self.printProgress("Cleaning data of ")
    return self.sshExecute("rm -rf "+ join(self.homeDir, "data"));  
  
  #def kill(self):
  #  pass

class GrafanaProcess(Process):
  def __init__(self, role, hostname):
    Process.__init__(self, role, hostname, "/usr/sbin", "grafana-server")
  
  def getProcessCommand(self):
    return "ps ax | grep -w 'grafana-server' | grep /usr | awk '{print $1 \" \" $5}' | grep grafana"
  
  def setupClusterEnv(self, paramDict = {}):
    pass
  
  def shutdown(self):
    stdout,stderr = self.sshExecute("sudo service grafana-server stop")
    return stdout,stderr
  
  def clean(self):
    pass 
  
  def start(self):
    stdout,stderr = self.sshExecute("sudo service grafana-server start")
    return stdout,stderr
  
class KibanaProcess(Process):
  def __init__(self, role, hostname):
    Process.__init__(self, role, hostname, "/opt/kibana", "kibana")
  
  def getProcessCommand(self):
    return "ps ax | grep -w 'kibana' | awk '{print $1 \" \" $5}' | grep kibana | sed -e 's@/opt/kibana/bin/../node/bin/node@/opt/kibana/bin/kibana@'"
  
  def setupClusterEnv(self, paramDict = {}):
    pass
  
  def shutdown(self):
    stdout,stderr = self.sshExecute("sudo service kibana4 stop")
    return stdout,stderr
  
  def clean(self):
    pass 
  
  def start(self):
    stdout,stderr = self.sshExecute("sudo service kibana4 start")
    return stdout,stderr
  
  def kill(self):
    self.printProgress("Killing ")
    self.shutdown()
    
class InfluxdbProcess(Process):
  def __init__(self, role, hostname):
    Process.__init__(self, role, hostname, "/usr/bin", "influxdb")
  
  def getProcessCommand(self):
    return "ps ax | grep -w 'influxdb' | grep /usr | awk '{print $1 \" \" $5}' | grep influxdb"
  
  def setupClusterEnv(self, paramDict = {}):
    pass
  
  def shutdown(self):
    stdout,stderr = self.sshExecute("sudo /etc/init.d/influxdb start")
    return stdout,stderr
  
  def clean(self):
    pass 
  
  def start(self):
    stdout,stderr = self.sshExecute("sudo /etc/init.d/influxdb start")
    return stdout,stderr

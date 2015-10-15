from server.Server import *
from server.ServerSet import ServerSet
import re


class Cluster(ServerSet):
  """
  A class to help discover, store, sort, and communicate with Scribengin Servers
  """

  """Regexes to find servers from /etc/hosts"""
  serverRegexes = [
    re.compile('.*kafka-\d+.*'),
    re.compile('.*zookeeper-\d+.*'),
    re.compile('.*hadoop-worker-\d+.*'),
    re.compile('.*hadoop-master.*'),
    re.compile('.*elasticsearch-\d+.*'),
    re.compile('.*generic-\d+.*'),
    re.compile('.*monitoring-\d+.*'),
  ]
  
  def __init__(self, etcHostsPath="/etc/hosts"):
    """
    Initialize and immediately parse the /etc/hosts file
    """
    ServerSet.__init__(self, "cluster");
    self.parseEtcHosts(etcHostsPath)
    
      
  
  def parseEtcHosts(self, path="/etc/hosts"):
    """
    Parses the file in path (/etc/hosts) and searches for pattern of [ip address]\s+[hostname]
    Uses serverRegexes for server name regexes
    """
    kafkaServers = []
    zkList = []
    hadoopWorkers = []
    hadoopMasters = []
    elasticsearchServers = []
    genericServers = []
    f = open(path, 'r')
    for line in f:
      if any(regex.match(line) for regex in self.serverRegexes):
        hostname = line.rstrip().split()[1]
        #So we don't double parse the hosts when we have .private and .public hostnames (digital ocean)
        if not  re.search("public", hostname, re.IGNORECASE):
          if re.match("kafka.*", hostname, re.IGNORECASE) is not None:
            self.addServer(KafkaServer(hostname, "kafka"))
            kafkaServers.append(hostname)
          if re.match("zookeeper.*", hostname, re.IGNORECASE) is not None:
            zkList.append(hostname)
            self.addServer(ZookeeperServer(hostname, "zookeeper"))
          if re.match("hadoop-master.*", hostname, re.IGNORECASE) is not None:
            hadoopMasters.append(hostname)
            self.addServer(HadoopMasterServer(hostname))
          if re.match("hadoop-worker.*", hostname, re.IGNORECASE) is not None :
            hadoopWorkers.append(hostname)
            self.addServer(HadoopWorkerServer(hostname, "hadoop-worker"))
          if re.match("elasticsearch.*", hostname, re.IGNORECASE) is not None:
            self.addServer(ElasticSearchServer(hostname, "elasticsearch"))
            elasticsearchServers.append(hostname)
          if re.match("generic.*", hostname, re.IGNORECASE) is not None:
            self.addServer(GenericServer(hostname, "generic"))
            genericServers.append(hostname)
          #TODO Make/refactor monitoring server
          if re.match("monitoring.*", hostname, re.IGNORECASE) is not None:
            self.addServer(GenericServer(hostname, "generic"))
            genericServers.append(hostname)
          
    self.paramDict["kafkaServers"] = kafkaServers
    self.paramDict["zkList"] = zkList
    self.paramDict["hadoopWorkers"] = hadoopWorkers
    self.paramDict["hadoopMasters"] = hadoopMasters
    self.paramDict["elasticsearchServers"] = elasticsearchServers
    self.paramDict["genericServers"] = genericServers
    self.paramDict["all"] = kafkaServers + zkList + hadoopWorkers + hadoopMasters + elasticsearchServers

    self.createAnsibleInventory()

from os.path import abspath, dirname, join
from sys import path
from random import sample

path.insert(0, dirname(dirname(abspath(__file__))))
from ssh.ssh import ssh
from ansibleInventoryParser.ansibleInventoryParser import ansibleInventoryParser

class kafkaTool():
  def __init__(self, inventoryFilePath):
    ansibleParser = ansibleInventoryParser(inventoryFilePath)
    self.cluster = ansibleParser.parseInventoryFile()
    self.kafkaCluster = []
    self.ssh = ssh()

    for machine in self.cluster:
      if machine["group"].lower() == "kafka":
        self.kafkaCluster.append(machine)
    
  #Returns an array of all the broker IDs in the cluster
  def getBrokerIDs(self, kafkaConfigPath="/opt/kafka/config/server.properties"):
    brokerids = []
    for machine in self.kafkaCluster:
      stdout,stderr = self.ssh.sshExecute(machine["host"], "cat "+kafkaConfigPath+" | grep broker.id")
      try:
        ID = stdout.rstrip().split("=")[1]
        brokerids.append(int(ID))
      except:
        pass
    return brokerids
    
  #Gets all the broker IDs in the cluster
  #Finds the max, then returns the max+1
  def getNewBrokerID(self):
    return max(self.getBrokerIDs())+1
    
  #Increment your kafka broker to have a brand new ID for the cluster
  def setNewBrokerID(self, host, kafkaConfigPath="/opt/kafka/config/server.properties"):
    newId = self.getNewBrokerID()
    return self.ssh.sshExecute(host, r"sed -i 's/broker.id=[0-9]*/broker.id="+str(newId)+r"/' "+ kafkaConfigPath)
    
if __name__ == '__main__':
  x = kafkaTool("/tmp/scribengininventory_docker")
  print x.getBrokerIDs()
  print x.getNewBrokerID()
  #print x.setBrokerID(sample(x.kafkaCluster, 1)[0]["host"])
  print x.setNewBrokerID("kafka-1")

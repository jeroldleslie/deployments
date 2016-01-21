#! /bin/sh
""":"
exec python $0 ${1+"$@"}
"""


from os.path import join, expanduser, dirname, abspath
from sys import stdout
from time import sleep
from multiprocessing import Process
from pprint import pformat

from commons.ansibleRunner.ansibleRunner import ansibleRunner
from commons.ansibleInventoryParser.ansibleInventoryParser import ansibleInventoryParser
from commons.kafkaTool.kafkaTool import kafkaTool
from statusCommander import statusCommander



#Calling this in a threaded manner because if not
#it seems that click automatically calls exit and 
#kills the application in place
def getClusterStatus(inventory_file):
  p = Process(target=statusCommander.mastercommand, args=(["-i", inventory_file, "--no-debug"],))
  p.start()
  p.join()
  stdout.flush()


#Takes in a parsed inventory and the group you're looking for
#Returns a list of hostnames in that group
#Example:
#  getHostNames(parsedInv, "kafka")
#   ->returns -> ["kafka-1","kafka-2","kafka-3"]
def getHostNames(parsedInv, group):
  hosts = []
  for machine in parsedInv:
    if machine["group"].lower() == group:
      hosts.append(machine["host"])
  return hosts


#Main function
if __name__ == '__main__':

  #Ansible root directory is at ../../ansible
  ansible_root_dir = dirname(dirname(abspath(__file__)))+"/ansible"
  print "Ansible Root Dir: "+ansible_root_dir
  
  #Ansible inventory is at ~/inventory
  inventory_file = join(expanduser("~"),"inventory")
  print "Using inventory file at: "+inventory_file

  kafkaPlaybook = join(ansible_root_dir, "kafka.yml")
  zookeeperPlaybook = join(ansible_root_dir, "zookeeper.yml")

  #Parse the inventory file to get our cluster info
  runner = ansibleRunner()
  inventoryParser = ansibleInventoryParser(ansibleInventoryFilePath=inventory_file)
  parsedInv = inventoryParser.parseInventoryFile()

  #Get a list of hostnames for kafka and zookeeper
  kafkaMachines = getHostNames(parsedInv, "kafka")
  zookeeperMachines = getHostNames(parsedInv, "zookeeper")
  print "Kafka machines: "+pformat(kafkaMachines)
  print "Zookeeper machines: "+pformat(zookeeperMachines)


  kafka = kafkaTool(inventory_file)
  


  #Calls statusCommander to print out current status
  getClusterStatus(inventory_file)
  
  #####################################################################
  #force stop kafka-1
  runner.deploy(playbook = kafkaPlaybook, 
                inventory=inventory_file, 
                outputToStdout=True, 
                maxRetries=0,
                tags="force-stop",
                #If you want to kill ALL the kafka machines, you could easily do...
                #limit="",)
                #If you wanted to kill a specific 3 of them
                #limit="kafka-1,kafka-2,kafka-3",)
                limit="kafka-1",)

  #Clean kafka-1
  runner.deploy(playbook = kafkaPlaybook, 
                inventory=inventory_file, 
                outputToStdout=True, 
                maxRetries=0,
                tags="clean",
                limit="kafka-1",)

  #Set a new broker ID for kafka-1 (Its guaranteed to be unique)
  #New broker ID will = (the max broker id of the cluster) + 1
  kafka.setNewBrokerID("kafka-1")

  #Calls statusCommander to print out current status
  getClusterStatus(inventory_file)


  #Start kafka-1
  runner.deploy(playbook = kafkaPlaybook, 
                inventory=inventory_file, 
                outputToStdout=True, 
                maxRetries=0,
                tags="start",
                limit="kafka-1",)


  getClusterStatus(inventory_file)

  #####################################################################
  #force stop zookeeper-1
  runner.deploy(playbook = zookeeperPlaybook, 
                inventory=inventory_file, 
                outputToStdout=True, 
                maxRetries=0,
                tags="force-stop",
                limit="zookeeper-1",)

  #Clean zookeeper-1
  runner.deploy(playbook = zookeeperPlaybook, 
                inventory=inventory_file, 
                outputToStdout=True, 
                maxRetries=0,
                tags="clean",
                limit="zookeeper-1",)

  getClusterStatus(inventory_file)

  #Start zookeeper-1
  runner.deploy(playbook = zookeeperPlaybook, 
                inventory=inventory_file, 
                outputToStdout=True, 
                maxRetries=0,
                tags="start",
                limit="zookeeper-1",)

  getClusterStatus(inventory_file)







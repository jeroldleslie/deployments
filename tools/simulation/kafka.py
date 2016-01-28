from sys import path, stdout
from os.path import join, expanduser, dirname, abspath

from time import sleep
from multiprocessing import Process
from pprint import pformat

path.insert(0, dirname(dirname(abspath(__file__))))
from commons.ansibleRunner.ansibleRunner import ansibleRunner
from commons.ansibleInventoryParser.ansibleInventoryParser import ansibleInventoryParser
from commons.kafkaTool.kafkaTool import kafkaTool


class KafkaTool(object):
  def __init__(self, description):
    self.description = description 

    #Ansible root directory is at ../../ansible
    ansible_root_dir = dirname(dirname(dirname(abspath(__file__)))) + "/ansible"
    print "Ansible Root Dir: " + ansible_root_dir
    
    #Ansible inventory is at ~/inventory
    self.inventoryFile = join(expanduser("~"),"inventory")
    print "Using inventory file at: " + self.inventoryFile

    self.kafkaPlaybook = join(ansible_root_dir, "kafka.yml")
    self.zookeeperPlaybook = join(ansible_root_dir, "zookeeper.yml")

    #Parse the inventory file to get our cluster info
    self.ansibleRunner = ansibleRunner()

  def forceStop(self, limitHosts):
    self.ansibleRunner.deploy(playbook = self.kafkaPlaybook, inventory=self.inventoryFile, outputToStdout=True, maxRetries=0, tags="force-stop", limit=limitHosts);

  def start(self, limitHosts):
    self.ansibleRunner.deploy(playbook = self.kafkaPlaybook, inventory=self.inventoryFile, outputToStdout=True, maxRetries=0, tags="start", limit=limitHosts);

  def clean(self, limitHosts):
    self.ansibleRunner.deploy(playbook = self.kafkaPlaybook, inventory=self.inventoryFile, outputToStdout=True, maxRetries=0, tags="clean", limit=limitHosts);

  def restart(self, limitHosts):
    self.forceStop(limitHosts);
    self.start(limitHosts);

  def restartWithClean(self, limitHosts):
    self.forceStop(limitHosts);

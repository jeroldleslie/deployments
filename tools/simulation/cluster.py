#!/bin/bash

""":"
exec python $0 ${1+"$@"}
"""

import time
from time import sleep
from os.path import join, expanduser, dirname, abspath
from sys import stdout,  path
from multiprocessing import Process
from pprint import pformat
from datetime import datetime
from random import randint

from kafka import KafkaTool
from zookeeper import ZookeeperTool

path.insert(0, dirname(dirname(abspath(__file__))))
from commons.ansibleInventoryParser.ansibleInventoryParser import ansibleInventoryParser
from statusCommander import statusCommander

class ClusterChaos(object):
  def __init__(self, description):
    self.description = description 

    self.inventoryFile = join(expanduser("~"),"inventory")
    inventoryParser = ansibleInventoryParser(ansibleInventoryFilePath=self.inventoryFile)
    parsedInv = inventoryParser.parseInventoryFile()

    #Get a list of hostnames for kafka and zookeeper
    self.kafkaMachines     = self.getHostNames(parsedInv, "kafka")
    self.zookeeperMachines = self.getHostNames(parsedInv, "zookeeper")
    print "Kafka machines: "     + pformat(self.kafkaMachines)
    print "Zookeeper machines: " + pformat(self.zookeeperMachines)

  def getHostNames(self, parsedInv, group):
    hosts = []
    for machine in parsedInv:
      if machine["group"].lower() == group:
        hosts.append(machine["host"])
    return hosts

  def printClusterStatus(self):
    start = time.time();

    inventoryFile = "~/inventory"
    p = Process(target=statusCommander.mastercommand, args=(["-i", inventoryFile, "--no-debug"],))
    p.start()
    p.join()
    stdout.flush()

    end = time.time()
    print "Print the cluster status in %.2gs" % (end-start)

  def killCleanRestartKafka(self, selKafkaHost, failureDuration):
    kafkaTool = KafkaTool("Kafka chaos simulation");
    kafkaTool.forceStop(selKafkaHost);
    kafkaTool.clean(selKafkaHost);
    if failureDuration > 0:
      print "Wait for %d sec before  resume the kafka %s" % (failureDuration, selKafkaHost)
      sleep(failureDuration);
    kafkaTool.start(selKafkaHost);
    self.printClusterStatus();

  def randomKafkaChaos(self, numOfFailures, failurePeriod, failureDuration):
    count = 1;
    while count  <= numOfFailures:
      print "Wait for the next failure, wait time = %d" % (failurePeriod)
      sleep(failurePeriod);
      selHostIdx = randint(0, len(self.kafkaMachines)) - 1
      selKafkaHost = self.kafkaMachines[selHostIdx]; 
      print "Restart kafka %d time(s), select kafka host %s, failure duration %d sec " % (count, selKafkaHost, failureDuration)
      self.killCleanRestartKafka(selKafkaHost, failureDuration)
      count += 1;

  def killCleanRestartZookeeper(self, selZookeeperHost, failureDuration):
    zkTool = ZookeeperTool("Zookeeper tool");
    zkTool.forceStop(selZookeeperHost);
    zkTool.clean(selZookeeperHost);

    if failureDuration > 0:
      print "Wait for %d sec before  resume the zookeeper %s" % (failureDuration, selZookeeperHost)
      sleep(failureDuration);

    zkTool.start(selZookeeperHost);
    self.printClusterStatus();

  def randomZookeeperChaos(self, numOfFailures, failurePeriod, failureDuration):
    count = 1;
    while count  <= numOfFailures:
      print "Wait for the next failure, wait time = %d" % (failurePeriod)
      sleep(failurePeriod);
      selHostIdx = randint(0, len(self.zookeeperMachines)) - 1
      selZookeeperHost = self.zookeeperMachines[selHostIdx]; 
      print "Restart zookeeper %d time(s), select zookeeper host %s, failure duration %d sec " % (count, selZookeeperHost, failureDuration)
      self.killCleanRestartZookeeper(selZookeeperHost, failureDuration);
      count += 1;

  def randomMixChaos(self, numOfFailures, failurePeriod, failureDuration):
    count = 1;
    while count  <= numOfFailures:
      print "Wait for the next failure, wait time = %d" % (failurePeriod)
      sleep(failurePeriod);
      if count % 2 == 0:
        selHostIdx = randint(0, len(self.zookeeperMachines)) - 1
        selZookeeperHost = self.zookeeperMachines[selHostIdx]; 
        print "Restart zookeeper %d time(s), select zookeeper host %s, failure duration %d sec " % (count, selZookeeperHost, failureDuration)
        self.killCleanRestartZookeeper(selZookeeperHost, failureDuration);
      else :
        selHostIdx = randint(0, len(self.kafkaMachines)) - 1
        selKafkaHost = self.kafkaMachines[selHostIdx]; 
        print "Restart kafka %d time(s), select kafka host %s, failure duration %d sec " % (count, selKafkaHost, failureDuration)
        self.killCleanRestartKafka(selKafkaHost, failureDuration)

      count += 1;

#Main function
if __name__ == '__main__':
  clusterChaos = ClusterChaos("Run chaos simulation for the entire cluster"); 
  #clusterChaos.randomKafkaChaos(1,  10, 5);
  #clusterChaos.randomKafkaChaos(30, 300, 30);

  #clusterChaos.randomZookeeperChaos(1,  10, 5);
  #clusterChaos.randomZookeeperChaos(30, 300, 30);

  clusterChaos.randomMixChaos(50, 180, 30);

from scribengin.Base import Base
import digitalocean
import logging
from sys import path
from os.path import expanduser, join, abspath, dirname
import os
import time
from itertools import izip
import string
import sys 
import os 
import subprocess
import tempfile

path.insert(0, "../tools/cluster/")
from Cluster import Cluster

class Container(Base):
    
  startString="##SCRIBENGIN CLUSTER START##"
  endString="##SCRIBENGIN CLUSTER END##"
  #if droplet with that name exists start service.
  def start(self, containerName):
    containers = containerName.split(',')
    containerNames = [name[:name.index('-')] for name in containerName.split(',')]
    print "attempting to start "+ str(containerNames)
    images = [image for image in self.manager.get_images(private=False,type='snapshot') if '-' in image.name and image.name[:image.name.index('-')] in containerNames]
    droplets=[]
    existingDroplets = self.manager.get_all_droplets()
    
    for container in containers:
      if container in [droplet.name for droplet in existingDroplets]:
        print container
        for droplet in existingDroplets:
          if container == droplet.name:
            print container +" already exists "+ droplet.name
            print "attempting to start "+ droplet.name
            if droplet.status != 'active':
              droplet.power_on(return_dict=False).wait(10)
            else:
              print "droplet "+ droplet.name +" already exists and is powered on."
      else:
          print "No droplet called "+ container + " we need to create it"
          for snapshot in images:
            if snapshot.name[:snapshot.name.index('-')] == container[:container.index('-')]:
                self.createContainer(snapshot,container)

    self.updateLocalHostsFile(containerName)
    self.deploy(containerName)

  def createContainer(self, snapshot, containerName):
    print snapshot
    imageName=snapshot.name.index('-')
    baseDroplet =snapshot.name[0:imageName]
    logging.debug("containerName "+containerName)
    logging.debug("baseDroplet "+ baseDroplet)
    droplet =  super(Container, self).createDroplets(baseDroplet, containerName)
    #wait untill droplet is created
    super(Container, self).wait_until(droplet, 'active', 60, period=10)
    
    logging.debug("current status "+ str(droplet.status))
    droplet.rebuild(snapshot.id, return_dict=False).wait(10)
    
    return droplet
    
  def updateHostsFile(self, droplets):
    hostsFile ='/etc/hosts'
    
    hostString = self.startString
    hostString +='\n'
    for droplet in droplets:
      hostString += droplet.ip_address
      hostString += '  '
      hostString += droplet.name
      hostString += '\n' 

    hostString +=self.endString
    hostString += '\n' 

    with open(hostsFile) as inputFile:
      content = inputFile.read()

    out_file = open("testFile", "w")
    sub = subprocess.check_output(['sed', "/"+self.startString+"/,/"+self.endString+"/d", hostsFile])
    sub += hostString
    
    try:
      with open(hostsFile,'w') as outputFile:
        outputFile.write(sub)
    except IOError as exception:
      logging.error("Unable to open "+ hostsFile +" please ensure you have write permissions.")
      

  def updateRemoteHostsFiles(self, dropletsNames):
    #get all the droplets powered on
    hostsString = self.startString +'\n'

    existingDroplets = self.manager.get_all_droplets()
    droplets=[]
    for droplet in existingDroplets:
        if droplet.status=='active' and '-' in droplet.name and droplet.name[:droplet.name.index('-')] in self.validImageNames:
          droplets.append(droplet)
          hostsString += droplet.private_ip_address + (' ' * 5) + droplet.name
          hostsString += '\n'
          
    hostsString += self.endString + '\n'

    print hostsString    
    for droplet in droplets:
      self.updateThem(droplet, hostsString)
      
  def updateThem(self, droplet,hostsString):
    
    hosts ='''127.0.1.1 dropletName
127.0.0.1 localhost

# The following lines are desirable for IPv6 capable hosts
::1 ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
f02::1 ip6-allnodes
ff02::2 ip6-allrouters
ff02::3 ip6-allhosts
'''
    hosts=hosts.replace('dropletName', droplet.name)
    print hosts
    
    
  def updateLocalHostsFile(self, dropletsNames):
    print dropletsNames
    droplets= super(Container, self).getDropletsFromName(dropletsNames)
    self.updateHostsFile(droplets)     

  def stop(self, containerNames):
    print containerNames
    droplets= super(Container, self).getDropletsFromName(containerNames)
    for droplet in droplets:
      if droplet.status=='off':
        logging.debug("Droplet "+ droplet.name +" already powered off.")
      else:
        droplet.power_off()

  def clean(self, containerName):
    pass

  #TODO rename this
  def deploy(self, containerNames):
    cluster= Cluster()
    #TODO externalize these
    cluster.paramDict["zoo_cfg"] = '../../neverwinterdp-deployments/docker/scribengin/bootstrap/post-install/zookeeper/conf/zoo_sample.cfg'
    cluster.paramDict["server_config"] = '../../neverwinterdp-deployments/docker/scribengin/bootstrap/post-install/kafka/config/server.properties'
    
    droplets = super(Container, self).getDropletsFromName(containerNames)
    for droplet in droplets:
        print "Attempting to deploy "+ droplet.name
        if droplet.name.startswith("zookeeper"):
          cluster.startZookeeper()
        elif droplet.name.startswith("kafka"):
          cluster.startKafka()

  def status(self, containerName):
    pass
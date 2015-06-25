from scribengin.Base import Base
import digitalocean
from sys import path
from os.path import expanduser, join, abspath, dirname
import os
import time
from itertools import izip

path.insert(0, "../tools/cluster/")
from Cluster import Cluster
#create a droplet with name containerName e.g zookeeper-1
#start process
class Container(Base):

  def start(self, containerName):
    print "attempting to start "+ containerName
    containerNames = [name[:name.index('-')] for name in containerName.split(',')]
    print containerNames
    images = [image for image in self.manager.get_images(private=False,type='snapshot') if '-' in image.name and image.name[:image.name.index('-')] in containerNames]
    droplets=[]
    for snapshot, container in izip(images,containerName.split(',')):
      droplets.append(self.createContainer(snapshot,container))
      
      self.updateHostsFile(droplets)
    

  def createContainer(self, snapshot, containerName):
    print snapshot
    imageName=snapshot.name.index('-')
    baseDroplet =snapshot.name[0:imageName]
    print baseDroplet
    print "hahahahahahha containerName "+containerName
    print "hohoho baseDroplet "+ baseDroplet
    droplet =  super(Container, self).createDroplets(baseDroplet, containerName)
    #wait untill droplet is created

    print "current status "+ str(droplet.status)
    droplet.rebuild(snapshot.id, return_dict=False).wait(10)
    
    return droplet
    
  def updateHostsFile(self, droplets):
    hostsFile ='/etc/hosts'
    
    startString="##SCRIBENGIN CLUSTER START##"
    endString="##SCRIBENGIN CLUSTER END##"
    hostString = startString
    hostString +='\n'
    for droplet in droplets:
      hostString += droplet.ip_address
      hostString += '  '
      hostString += droplet.name
      hostString += '\n' 
    
    hostString +=endString
    
    print hostString
    
    with open(hostsFile) as input:
      content = input.read()
    print content
      

    
    
    
  def updateHosts(self, dropletsNames):
      droplets= super(Container, self).getDropletsFromName(dropletsNames)
      self.updateHostsFile(droplets)     

  def stop(self, containerName):
    pass

  def clean(self, containerName):
    pass

  def deploy(self, containerName):
    pass

  def status(self, containerName):
    cluster= Cluster()
    cluster.paramDict["zoo_cfg"] = '/home/anto/bitBucket/neverwinterdp-deployments/docker/scribengin/bootstrap/post-install/zookeeper/conf/zoo_sample.cfg'
    cluster.startZookeeper()
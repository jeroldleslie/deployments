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
    for snapshot, container in izip(images,containerName.split(',')):
      self.createContainer(snapshot,container)
    

  def createContainer(self, snapshot, containerName):
    print snapshot
    imageName=snapshot.name.index('-')
    baseDroplet =snapshot.name[0:imageName]
    print baseDroplet
    print "hahahahahahha "+containerName
    droplet =  digitalocean.Droplet(token=self.token,
                                    name=containerName,
                                    size_slug='512mb')
    droplet.create()
    #wait untill droplet is created
    print "wait until droplet is on"
    self.wait_until(droplet,'active', 90, 10)
    print "current status "+ str(droplet.status)
    droplet.rebuild(snapshot.id.id, return_dict=False).wait(10)
    
    
  """  latestImage=  images.pop()
    print latestImage.slug
    droplet = super(Container, self).createDroplets(containerName)[0]
    print "ndio hii "+ str(droplet)
    for action in droplet.get_actions():
      print action
    #droplet.load()
    #droplet.rebuild(latestImage.id, return_dict=False).wait(10)
    #droplet.rename(containerName+'-1')
    time.sleep(30)
    self.status(containerName)
    print droplet.status"""
    #add to etc/hosts
    

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
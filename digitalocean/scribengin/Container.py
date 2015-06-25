from scribengin.Base import Base
import digitalocean
from sys import path
from os.path import expanduser, join, abspath, dirname
import os
import time

path.insert(0, "/home/anto/bitBucket/neverwinterdp-deployments/tools/cluster/")
from Cluster import Cluster
#create a droplet with name containerName e.g zookeeper-1
#start process
class Container(Base):

  def start(self, containerName):
    print "attempting to start "+ containerName
    images = [image for image in sorted(self.manager.get_images(),key=lambda x: x.name) if image.name.startswith(containerName)]
    latestImage=  images.pop()
    print latestImage.slug
    droplet = super(Container, self).createDroplets(containerName)[0]
    print "ndio hii "+ str(droplet)
    for action in droplet.get_actions():
      print action
    droplet.load()
    droplet.rebuild(latestImage.id, return_dict=False).wait(10)
    droplet.rename(containerName+'-1')
    time.sleep(30)
    self.status(containerName)
    print droplet.status
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
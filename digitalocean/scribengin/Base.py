import digitalocean
import time
import os
import yaml
import logging

class Base(object):
    
  configsDir ='configs/'
  tokenFile = configsDir+'accesstoken'
  validImageNames=[]
    
  def __init__(self, neverwinterdp_home, playbook=''):
    self.neverwinterdp_home = neverwinterdp_home
    self.playbook= playbook
    with open(self.tokenFile) as f:
      self.token = f.readline()
    self.manager = digitalocean.Manager(token=self.token)
    #get a better way of doing it
    self.validImageNames = [i.split('.')[0] for i in os.listdir(self.configsDir)]
    logging.basicConfig(level=logging.DEBUG) 
    
  def createDroplets(self,dropletName, containerName):
      image = dropletName

      with open(self.configsDir + image + '.yml') as imageConfig:
        dropletConfig= yaml.load(imageConfig)
      #check input from config file is correct
      if containerName in [droplet.name for droplet in self.manager.get_all_droplets()] and image in self.validImageNames:
        print "Cannot build "+ image +" as it already exists. Try cleaning it first."
      else:
        droplet = digitalocean.Droplet(token=self.token, 
                                   name=containerName,
                                   region=dropletConfig['region'],
                                   image=dropletConfig['image'], 
                                   size_slug=dropletConfig['size'],
                                   backups=dropletConfig['backups'],
                                   private_networking=dropletConfig['private_networking'],
                                   ssh_keys=self.manager.get_all_sshkeys())
        droplet.create()
        #wait until droplet is created
        print "wait until droplet is on"
        print type(droplet)
        self.wait_until(droplet,'active', 90, 10)
        print "and now "+ str(droplet.status)
        
      return droplet
  
  
  def wait_until(self, droplet, status, timeout, period=5):
    print "Waiting until status becomes: " + status
    mustend = time.time() + timeout
    while time.time() < mustend:
      if droplet.load().status == status:
        print droplet.name +" status: "+ droplet.status
        return True
    print "we have to wait "+ str(period)
    time.sleep(period)
    return False

  def getDropletsFromName(self, dropletName):
    dropletNames= dropletName.split(',')
    droplets=[]
    for dropletName in dropletNames:
        droplet= next((droplet for droplet in self.manager.get_all_droplets() if droplet.name == dropletName), None)
        if droplet is not None:
          droplets.append(droplet)
    
    return droplets  


import digitalocean
import os
from _yaml import yaml
from os.path import expanduser
import time
import datetime
from scribengin.ansibleRunner import ansibleRunner
from scribengin.Base import Base
import logging

class Image(Base):

  #allow list of image names
  def clean(self,imageName):
    images= imageName.split(',')
    my_droplets = self.manager.get_all_droplets()
    droplets = [droplet for droplet in my_droplets if droplet.name in images]
    for droplet in droplets:
      print "attempting to delete: " +droplet.name +". id: "+ str(droplet.id)
      self.manager.get_droplet(droplet.id).destroy()

  #create image, throws exception if we have an image of same name
  def build(self, imageNames):
    logging.debug("in build")
    droplets= self.__createDroplets(imageNames)
    self.runAnsible(imageNames)
    snapshots= self.__takeSnapshots(droplets)
    self.__deleteDroplets(droplets)

  def __createDroplets(self,dropletNames):
    images =set(dropletNames.split(','))
    droplets=[]
    userData='''#!/bin/bash
        echo "Setup neverwinterdp user"
        useradd -m -d /home/neverwinterdp -s /bin/bash -c "neverwinterdp user" -p $(openssl passwd -1 neverwinterdp)  neverwinterdp
        echo "neverwinterdp ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
        chown -R neverwinterdp:neverwinterdp /opt
        cp -R /root/.ssh/ /home/neverwinterdp/
        chown -R neverwinterdp:neverwinterdp /home/neverwinterdp/.ssh
      '''
    for image in images:
      with open(self.configsDir + image + '.yml') as imageConfig:
        dropletConfig= yaml.load(imageConfig)
      #check input from config file is correct
      if image in [droplet.name for droplet in self.manager.get_all_droplets()] and image in self.validImageNames:
        print "Cannot build "+ image +" as it already exists. Try cleaning it first."
      else:
        droplet = digitalocean.Droplet(token=self.token, 
                                   name=dropletConfig['name'],
                                   region=dropletConfig['region'],
                                   image=dropletConfig['image'], 
                                   size_slug=dropletConfig['size'],
                                   backups=dropletConfig['backups'],
                                   private_networking=dropletConfig['private_networking'],
                                   user_data=userData,
                                   ssh_keys=self.manager.get_all_sshkeys())
        droplet.create()
        #wait untill droplet is created
        print "wait until droplet is on"
        super(Image, self).wait_until(droplet,'active', 60, 10)
        print "and now "+ str(droplet.status)
        droplets.append(droplet)
        
    return droplets

  def  __deleteDroplets(self, droplets):
    for droplet in droplets:
      droplet.destroy()

  def __runAnsible(self, droplets):
    runner = ansibleRunner(self.neverwinterdp_home)
    inventory = runner.createInventory(droplets)
    print "inventory "+ str( inventory)
    
    runner.runPlaybook(self.playbook)
    
  def runAnsible(self, dropletNames):
    print "in run ansible"
    droplets= super(Image, self).getDropletsFromName(dropletNames)
    for droplet in droplets:
      print "droplet status: "+ droplet.status
      if droplet.status != 'active':
        droplet.power_on()
        super(Image, self).wait_until(droplet, 'active', 60, 10)
      time.sleep(25) #just enough time to create neverwinterdp user
    self.__runAnsible(droplets)
  #TODO: delete previous snapshots before creating new one
  def __takeSnapshots(self, droplets):
    snapshots=[]
    for droplet in droplets:
      snapshot=droplet.take_snapshot(droplet.name+'-'+str(datetime.datetime.now()),return_dict=False, power_off=True).wait()
      snapshots.append(snapshot)
    return snapshots

  def takeSnapshots(self, dropletNames):
    print "in take snapshot."
    droplets = super(Image, self).getDropletsFromName(dropletNames)
    print "droplets "+str([droplet.name for droplet in droplets])
    
    self.deleteExistingSnaphots(dropletNames)

    return self.__takeSnapshots(droplets)

  def deleteExistingSnapshots(self,dropletNames):
    names = dropletNames.split(',')
    allExistingSnapshots= [snapshot for snapshot in sorted(self.manager.get_images(private=False),key=lambda x: x.name) if snapshot.name in dropletNames]
    for snapshot in allExistingSnapshots:
        print snapshot
        #snapshot.destroy()
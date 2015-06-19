import digitalocean
import os
from _yaml import yaml
from os.path import expanduser

class Image(object):
  
  configsDir ='configs/'
  tokenFile = configsDir+'accesstoken'
  validImageNames=[]

  def __init__(self):
    with open(self.tokenFile) as f:
      self.token = f.readline()
    self.manager = digitalocean.Manager(token=self.token)
    #get a better way of doing it
    self.validImageNames = [i.split('.')[0] for i in os.listdir(self.configsDir)] 

  #allow list of image names
  def clean(self,imageName):
    my_droplets = self.manager.get_all_droplets()
    droplet = next((droplet for droplet in my_droplets if droplet.name == imageName), None)
    if droplet is None:
      print "No droplet named "+ imageName
    else:
      print "attempting to delete "+ str(droplet.id)
      self.manager.get_droplet(droplet.id).destroy()


  #create image, throws exception if we have an image of same name
  def build(self, imageNames):
    droplets= self.__createDroplets(imageNames)
    #TODO run ansible on them
    snapshots= self.__takeSnapshots(droplets)
 
        
  def __createDroplets(self,dropletNames):
    images =set(dropletNames.split(','))
    droplets=[]
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
                                   ssh_keys=self.manager.get_all_sshkeys())
        droplet.create()
        droplets.append(droplet)
        
    return droplets

  def __takeSnapshots(self, droplets):
    snapshots=[]
    for droplet in droplets:
      snapshot=droplet.take_snapshot(droplet.name+'-'+str(5),power_off=True)
      snapshots.append(snapshot)
    
    return snapshots

  def takeSnapshots(self, dropletNames):
    dropletNames= dropletNames.split(',')
    droplets=[]
    for dropletName in dropletNames:
        droplet= next((droplet for droplet in self.manager.get_all_droplets() if droplet.name == dropletName), None)
        if droplet is not None:
          for action in droplet.get_actions():
            print droplet.name+" : "+ action.status
          droplets.append(droplet)
              
    return self.__takeSnapshots(droplets)

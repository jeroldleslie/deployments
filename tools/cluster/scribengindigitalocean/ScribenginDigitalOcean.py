import digitalocean, logging, subprocess, yaml, os, re, socket
from os.path import abspath, dirname, join, expanduser, realpath
from sys import path
from multiprocessing import Process
from time import sleep
from digitalocean.Region import Region
path.insert(0, dirname(dirname(abspath(__file__))))
from Cluster import Cluster
from server.Server import Server
from process.Process import Process as ScribeProcess
from scribenginansible.ScribenginAnsible import ScribenginAnsible
from digitalocean.baseapi import DataReadError

class ScribenginDigitalOcean():
  def __init__(self, digitalOceanToken=None, digitalOceanTokenFileLocation="~/.digitaloceantoken"):
    if "~/" in digitalOceanTokenFileLocation:
      digitalOceanTokenFileLocation = join( expanduser("~"), digitalOceanTokenFileLocation.replace("~/",""))
    
    self.token = digitalOceanToken
    if self.token is None:
      with open(digitalOceanTokenFileLocation) as tokenfile:
        self.token = tokenfile.read().strip()
    
    manager = digitalocean.Manager(token=self.token)
    self.defaultDropletConfig = { 
                   "region":"lon1",
                   "image":"ubuntu-14-04-x64",
                   "num" : 1,
                   "memory": "512mb",
                   "ssh_keys": manager.get_all_sshkeys(),
                   "private_networking" : "false",
                  }
    
    self.hostsFileStartString="##SCRIBENGIN CLUSTER START##"
    self.hostsFileEndString="##SCRIBENGIN CLUSTER END##"
    
    logging.debug("Token: "+self.token)



  def createAndWait(self, droplet, sleeptime=5, sshPort=22):
    logging.info("Creating: "+droplet.name)
    print "Creating: "+droplet.name
    droplet.create()
    
    status = None
    
    #Wait for droplet to be created
    while status != "active":
      try:
        drop = self.getDroplet(droplet.name)
        status = drop.load().status
      except DataReadError as e:
        pass
      logging.debug(droplet.name+": "+str(status))
      #Sleep is here to keep us from hitting the API Rate Limit
      sleep(sleeptime)
    
    #Wait for droplet to come up and be ready
    while status != "completed":
      drop = self.getDroplet(droplet.name)
      actions = drop.get_actions()
      for action in actions:
        action.load()
        # Once it shows completed, droplet is up and running
        status = action.status
        logging.debug(droplet.name+": "+str(status))
        #print droplet.name+": "+status.strip()
        if status.strip() is "completed":
          break 
        #Sleep is here to keep us from hitting the API Rate Limit
        sleep(sleeptime)
        
    #Wait for SSH to be reachable
    connected = False
    ip = self.getDropletIp(droplet.name)
    while connected is False:
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      try:
        s.connect((ip, sshPort))
        connected = True
        logging.debug(droplet.name+": SSH is now running!")
      except socket.error as e:
        logging.debug(droplet.name+": SSH is not running.")
        sleep(sleeptime)
      try:
        s.close()
      except:
        pass
  
  def createDropletSet(self, droplets):
    threads = []
    for droplet in droplets:
      t = Process(target=self.createAndWait, args=(droplet,))
      t.start()
      threads.append(t)
    
    for t in threads:
      t.join()
    
    
  
  def destroyDropletAndWait(self, droplet, sleeptime=5, maxRetries=60):
    if droplet is None:
      logging.debug("Droplet is none, returning")
      return
    logging.info("Destroying: "+droplet.name)
    print "Destroying: "+droplet.name
    
    retry = True
    while retry is True:
      try:
        droplet.destroy()
        retry = False
      except DataReadError as e:
        logging.debug("RETRYING "+droplet.name+": "+str(e))
        print "RETRYING "+droplet.name+": "+str(e)
        sleep(5)
      
    try:
      for i in range(0, maxRetries):
        status = droplet.load().status
        #Sleep is here to keep us from hitting the API Rate Limit
        sleep(sleeptime)
    except Exception as e:
      #Once we get an exception, then the droplet is gone
      logging.info(droplet.name+" DESTROYED")
      print droplet.name+" DESTROYED"
  
  
  def destroyAllScribenginDroplets(self, subdomain=None):
    threads = []
    manager = digitalocean.Manager(token=self.token)
    my_droplets = manager.get_all_droplets()
    for droplet in my_droplets:
      if any(regex.match(droplet.name) for regex in Cluster.serverRegexes):
        if subdomain is None or subdomain in droplet.name: 
          logging.debug("Destroying: "+droplet.name)
          t = Process(target=self.destroyDropletAndWait, args=(droplet,))
          t.start()
          threads.append(t)
    for t in threads:
      t.join()
  
  def loadMachineConfig(self, configLocation):
    config = yaml.load(open(configLocation, "r"))
    
    #Set default configuration params
    for machine in config:
      for key,value in self.defaultDropletConfig.items():
        machine.setdefault(key, value)
    logging.debug("DO Config: "+str(config))
    return config
  
  def launchContainers(self, configLocation, region=None, subdomain=None):
    config = self.loadMachineConfig(configLocation)
    droplets = []
    for machine in config:
      for i in range(1, machine["num"]+1):
        logging.debug("Creating "+machine["role"]+"-"+str(i))
        
        hostname = machine["role"]+"-"+str(i)
        omitNumberedName = ["hadoop-master",]
        if machine["role"] in omitNumberedName and machine["num"] == 1:
          hostname =machine["role"] 
        
        #If region is passed in, use that
        #Otherwise use what's set in the config
        digitalOceanRegion = region
        if digitalOceanRegion is None:
            digitalOceanRegion = machine["region"]
        
        #Add subdomain to hostname if its passed in
        if subdomain is not None:
          digitalOceanName=hostname+"."+subdomain
        else:
          digitalOceanName = hostname
          
        droplets.append(digitalocean.Droplet(token=self.token,
                                 name=digitalOceanName,
                                 region=digitalOceanRegion,
                                 image=machine["image"],
                                 size_slug=machine["memory"],
                                 backups=False,
                                 ssh_keys=machine["ssh_keys"],
                                 private_networking=machine['private_networking'],))
    self.createDropletSet(droplets)
    return droplets
  
  def getDropletIp(self, dropletName):
    hostAndIP = {}
    manager = digitalocean.Manager(token=self.token)
    my_droplets = manager.get_all_droplets()
    for droplet in my_droplets:
      if droplet.name == dropletName:
        logging.info(droplet.name+" : "+droplet.ip_address)
        return droplet.ip_address
  
  def getDroplet(self, dropletName):
    manager = digitalocean.Manager(token=self.token)
    all_droplets = manager.get_all_droplets()
    for droplet in all_droplets:
      if droplet.name == dropletName:
        return droplet
  
  def getScribenginHostsAndIPs(self, subdomain=None):
    hostAndIPs = []
    manager = digitalocean.Manager(token=self.token)
    my_droplets = manager.get_all_droplets()
    for droplet in my_droplets:
      if any(regex.match(droplet.name) for regex in Cluster.serverRegexes):
        if subdomain is None or subdomain in droplet.name:
          
          #If there is a subdomain involved, remove it
          dropletName = droplet.name
          if subdomain is not None:
            dropletName = dropletName.replace("."+subdomain, "")
          
          hostAndIPs.append(
                          {
                           "name": dropletName,
                           "ip"  : droplet.ip_address,
                           })
    logging.debug("Host and Ips: "+str(hostAndIPs))
    return hostAndIPs
  
  def writeAnsibleInventory(self, inventoryFileLocation="/tmp/scribengininventoryDO", 
                            ansibleSshUser="neverwinterdp", ansibleSshKey="~/.ssh/id_rsa",
                            subdomain=None):
    ans = ScribenginAnsible()
    ans.writeAnsibleInventory(self.getScribenginHostsAndIPs(subdomain),
                              inventoryFileLocation, ansibleSshUser,
                              ansibleSshKey)
    
  
  def getHostsString(self, subdomain=None):
    hostAndIps = self.getScribenginHostsAndIPs(subdomain)
    hostString = self.hostsFileStartString+"\n"
    for host in hostAndIps:
      hostString += host["ip"]+" "+host["name"]
      if subdomain is not None:
        hostString += " "+host["name"]+"."+subdomain+"\n"
      else:
        hostString += "\n"
    hostString +=self.hostsFileEndString+"\n"
    logging.debug("Hosts String: \n"+hostString)
    return hostString
    
    
  def updateRemoteHostsFile(self, subdomain=None, hostsFile='/etc/hosts', user="root", joinTimeout=60):
    cluster = Cluster()
    hostString = self.getHostsString(subdomain)
    
    threads = []
    for server in cluster.servers:
      #Insert localhost info into hostString. Example:
      ##SCRIBENGIN CLUSTER START##
      #127.0.0.1 localhost
      serverHostString = hostString
      #However, Zookeeper requires some black magic to get working
      #If localhost is defined, Zookeeper nodes won't connect to each other (issue with hostname resolution???)
      #https://issues.apache.org/jira/browse/ZOOKEEPER-2184
      #So if zookeeper is in the hostname, omit adding the localhost info
      if "zookeeper" not in server.getHostname():
        toAdd="\n127.0.0.1 localhost\n"
        serverHostString = hostString.replace(self.hostsFileStartString, self.hostsFileStartString+toAdd)
      #print serverHostString
      logging.debug("Executing on "+server.getHostname()+" : "+"echo '"+serverHostString+"'  > /etc/hosts")
      t = Process(target=server.sshExecute, args=("echo '"+serverHostString+"'  > /etc/hosts",user,False,))
      t.start()
      threads.append(t)
    
    for t in threads:
      t.join(joinTimeout)
  
  
  def updateLocalHostsFile(self, subdomain=None, hostsFile='/etc/hosts'):
    hostString = self.getHostsString(subdomain)
    
    with open(hostsFile) as inputFile:
      hostFileContent = inputFile.read()
    
    hostFileContent = re.sub(self.hostsFileStartString+r"\n(.*\n)+"+self.hostsFileEndString, "", hostFileContent, re.MULTILINE)
    
    logging.debug("Hosts File new content: \n"+hostFileContent+"\n"+hostString)
    
    outFile = open(hostsFile, "w")
    outFile.write(hostFileContent+"\n"+hostString)
    outFile.close()
    
    logging.debug("Runnging ssh-keygen -R")
    hostAndIps = self.getScribenginHostsAndIPs()
    for host in hostAndIps:
      command = "ssh-keygen -R "+host["name"] +" 2> /dev/null 1> /dev/null"
      os.system(command)
      
  #Must be executed *AFTER* updateLocalHostsFile is called on cluster
  def setupNeverwinterdpUser(self, user="root", serverName=None):
    userScript='''
        useradd -m -d /home/neverwinterdp -s /bin/bash -c "neverwinterdp user" -p $(openssl passwd -1 neverwinterdp)  neverwinterdp && 
        echo "neverwinterdp ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && 
        chown -R neverwinterdp:neverwinterdp /opt && 
        cp -R /root/.ssh/ /home/neverwinterdp/ && 
        chown -R neverwinterdp:neverwinterdp /home/neverwinterdp/.ssh
      '''
    logging.info("User script: "+userScript)
  
    if serverName is None:
      cluster = Cluster()
      threads = []
      for server in cluster.servers:
        logging.info("Executing user script on "+server.getHostname())
        t = Process(target=server.sshExecute, args=(userScript,user,))
        t.start()
        threads.append(t)

      for t in threads:
        t.join()

      return cluster
    else:
      server = Server(serverName)
      server.addProcess(ScribeProcess(serverName, self.getDropletIp(serverName), "~/", None))
      server.sshExecute(userScript,user)
      return server

      
  def deploy(self, neverwinterdpHome, 
             playbook=join(dirname(dirname(dirname(dirname(realpath(__file__))))), "ansible/scribenginCluster.yml"), 
             inventory="/tmp/scribengininventoryDO",
             outputToStdout=True,
             retry=0,
             retryLine=None,
             maxRetries=5):
    
    ans = ScribenginAnsible()
    ans.deploy(playbook, inventory, neverwinterdpHome, outputToStdout, retry, retryLine, maxRetries)
    
    
    

if __name__ == "__main__":
  config = [ 
            {"role": "kafka",
              "num" : 3,
              "memory": "16gb",
            },
            {"role": "zookeeper",
              "num" : 2,
              "memory": "8gb",
            },
            {"role": "hadoop-worker",
              "num" : 3,
              "memory": "16gb",
            },
            {"role": "hadoop-master",
              "num" : 1,
              "memory": "16gb",
            },
            {"role": "elasticsearch",
              "num" : 1,
              "memory": "16gb",
            },
            {"role": "monitoring",
              "num" : 2,
              "memory": "2gb",
            },
          ] 
   
   
  with open('digitalOceanConfigs/testConfig.yml', 'w') as yaml_file:
     yaml_file.write( yaml.dump(config, default_flow_style=False))

  
  

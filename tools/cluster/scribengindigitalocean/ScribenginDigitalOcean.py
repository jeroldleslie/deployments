import digitalocean, logging, subprocess, yaml, os, re
from os.path import abspath, dirname, join, expanduser, realpath
from sys import path
from multiprocessing import Process
from time import sleep
from digitalocean.Region import Region
path.insert(0, dirname(dirname(abspath(__file__))))
from Cluster import Cluster
from server.Server import Server
from process.Process import Process as ScribeProcess
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
                   "private_networking" : "true",
                  }
    
    self.hostsFileStartString="##SCRIBENGIN CLUSTER START##"
    self.hostsFileEndString="##SCRIBENGIN CLUSTER END##"
    
    logging.debug("Token: "+self.token)



  def createAndWait(self, droplet, sleeptime=5, maxRetries=12):
    logging.debug("Creating: "+droplet.name)
    print "Creating: "+droplet.name
    droplet.create()
    
    status = None
    retries = 0
    
    while status != "active":
      try:
        drop = self.getDroplet(droplet.name)
        status = drop.load().status
      except DataReadError as e:
        pass
      logging.debug(droplet.name+": "+str(status))
      retries+=1
      if retries > maxRetries:
        break
      #Sleep is here to keep us from hitting the API Rate Limit
      sleep(sleeptime)
  
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
    logging.debug("Destroying: "+droplet.name)
    print "Destroying: "+droplet.name
    
    retry = True
    while retry is True:
      try:
        droplet.destroy()
        retry = False
      except DataReadError as e:
        print "RETRYING "+droplet.name+": "+str(e)
        sleep(5)
      
    try:
      for i in range(0, maxRetries):
        status = droplet.load().status
        #Sleep is here to keep us from hitting the API Rate Limit
        sleep(sleeptime)
    except Exception as e:
      #Once we get an exception, then the droplet is gone
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
    return hostAndIPs
  
  def writeAnsibleInventory(self, inventoryFileLocation="/tmp/scribengininventoryDO", 
                            ansibleSshUser="neverwinterdp", ansibleSshKey="~/.ssh/id_rsa",
                            subdomain=None):
    inventory = ""
    hostsAndIps = self.getScribenginHostsAndIPs()
    groupList = ["monitoring",
                 "kafka",
                 "hadoop-master",
                 "hadoop-worker",
                 "zookeeper",
                 "elasticsearch",]
    for group in groupList:
      #Replace - with _ to differentiate groups from hostnames
      inventory += "\n["+group.replace("-","_")+"]\n"
      for host in hostsAndIps:
        if group in host["name"]:
          if subdomain is None or subdomain in host["name"]:
            if subdomain is None:
              inventory += host["name"]+" ansible_ssh_user="+ansibleSshUser+" ansible_ssh_private_key_file="+ansibleSshKey+"\n"
            else:
              inventory += host["name"].replace("."+subdomain, "")+" ansible_ssh_user="+ansibleSshUser+" ansible_ssh_private_key_file="+ansibleSshKey+"\n"
    
    f = open(inventoryFileLocation,'w')
    f.write(inventory)
    f.close()
    logging.debug("Ansible inventory contents: \n"+inventory)
  
  def getHostsString(self, subdomain=None):
    hostAndIps = self.getScribenginHostsAndIPs(subdomain)
    hostString = self.hostsFileStartString+"\n"
    for host in hostAndIps:
      hostString += host["ip"]+" "+host["name"]+"\n"
    hostString +=self.hostsFileEndString+"\n"
    return hostString
    
    
  def updateRemoteHostsFile(self, subdomain=None, hostsFile='/etc/hosts', user="root"):
    cluster = Cluster()
    hostString = self.getHostsString(subdomain)
    threads = []
    for server in cluster.servers:
      t = Process(target=server.sshExecute, args=("echo '"+hostString+"'  > /etc/hosts",user,False,))
      t.start()
      threads.append(t)
    
    for t in threads:
      t.join()
  
  
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
      command = "ssh-keygen -R "+host["name"] +" 2> /dev/null"
      os.system(command)
      
  
  
  #Must be executed *AFTER* updateLocalHostsFile is called on cluster
  def setupNeverwinterdpUser(self, user="root", serverName=None):
    if serverName is None:
      cluster = Cluster()
    else:
      cluster = Server(serverName)
      cluster.addProcess(ScribeProcess(serverName, self.getDropletIp(serverName), "~/", None))
    userScript='''
        useradd -m -d /home/neverwinterdp -s /bin/bash -c "neverwinterdp user" -p $(openssl passwd -1 neverwinterdp)  neverwinterdp && 
        echo "neverwinterdp ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && 
        chown -R neverwinterdp:neverwinterdp /opt && 
        cp -R /root/.ssh/ /home/neverwinterdp/ && 
        chown -R neverwinterdp:neverwinterdp /home/neverwinterdp/.ssh
      '''
    threads = []
    for server in cluster.servers:
      t = Process(target=server.sshExecute, args=(userScript,user,))
      t.start()
      threads.append(t)
    
    for t in threads:
      t.join()
      
    return cluster


  def deploy(self, neverwinterdpHome, 
             playbook=join(dirname(dirname(dirname(dirname(realpath(__file__))))), "ansible/scribenginCluster.yml"), 
             inventory="/tmp/scribengininventoryDO",
             outputToStdout=True,
             retry=0,
             retryLine=None,
             maxRetries=5):
    #ansible-playbook playbooks/scribenginCluster.yml -i scribengininventory --extra-vars "neverwinterdp_home_override=/path/to/NeverwinterDP"
    command = "ansible-playbook "+playbook+" -i "+inventory+" --extra-vars \"neverwinterdp_home_override="+neverwinterdpHome+"\""
    if retryLine is not None:
      command = command+" "+retryLine
    logging.debug("ansible-playbook command: "+command)
    
    #Outputs stdout/stderr to stdout while command is running
    toRetry = False
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    while(True):
      retcode = p.poll() #returns None while subprocess is running
      line = p.stdout.readline()
      if(outputToStdout):
        print line.rstrip()
      #Looking for "to retry, use: --limit @/Users/user/scribenginCluster.retry"
      if "to retry, use: --limit" in line :
        toRetry = True
        retryLine = line.split(":")[1]
      if(retcode is not None):
        break
    
    if(toRetry and retry < maxRetries):
      print "Retrying Ansible"
      self.deploy(neverwinterdpHome, playbook, inventory, outputToStdout, retry+1, retryLine)
    
    
    

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

  
  

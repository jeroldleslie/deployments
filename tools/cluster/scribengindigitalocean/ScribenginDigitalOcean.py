import digitalocean, logging, subprocess, yaml, os, re
from os.path import abspath, dirname, join, expanduser, realpath
from sys import path
from multiprocessing import Process
from time import sleep
path.insert(0, dirname(dirname(abspath(__file__))))
from Cluster import Cluster


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

  def createAndWait(self, droplet, sleeptime=5):
    logging.debug("Creating: "+droplet.name)
    print "Creating: "+droplet.name
    droplet.create()
    status = None
    while status != "active":
      try:
        status = droplet.load().status
      except DataReadError as e:
        print e.value
      logging.debug(droplet.name+": "+status)
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
    
    
  
  def destroyDroplet(self, droplet):
    logging.debug("Destroying: "+droplet.name)
    print "Destroying: "+droplet.name
    droplet.destroy()
  
  
  def destroyAllScribenginDroplets(self):
    threads = []
    manager = digitalocean.Manager(token=self.token)
    my_droplets = manager.get_all_droplets()
    for droplet in my_droplets:
      if any(regex.match(droplet.name) for regex in Cluster.serverRegexes):
        logging.debug("Destroying: "+droplet.name)
        t = Process(target=self.destroyDroplet, args=(droplet,))
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
  
  def launchContainers(self, configLocation):
    config = self.loadMachineConfig(configLocation)
    droplets = []
    for machine in config:
      for i in range(1, machine["num"]+1):
        logging.debug("Creating "+machine["role"]+"-"+str(i))
        
        hostname = machine["role"]+"-"+str(i)
        omitNumberedName = ["hadoop-master",]
        if machine["role"] in omitNumberedName and machine["num"] == 1:
          hostname =machine["role"] 
          
        
        droplets.append(digitalocean.Droplet(token=self.token,
                                 name=hostname,
                                 region=machine["region"],
                                 image=machine["image"],
                                 size_slug=machine["memory"],
                                 backups=False,
                                 ssh_keys=machine["ssh_keys"],
                                 private_networking=machine['private_networking'],))
    self.createDropletSet(droplets)
    return droplets
  
  
  def getScribenginHostsAndIPs(self):
    hostAndIPs = []
    manager = digitalocean.Manager(token=self.token)
    my_droplets = manager.get_all_droplets()
    for droplet in my_droplets:
      if any(regex.match(droplet.name) for regex in Cluster.serverRegexes):
        hostAndIPs.append(
                          {
                           "name": droplet.name,
                           "ip"  : droplet.ip_address,
                           })
    return hostAndIPs
  
  def writeAnsibleInventory(self, inventoryFileLocation="/tmp/scribengininventoryDO", 
                            ansibleSshUser="neverwinterdp", ansibleSshKey="~/.ssh/id_rsa"):
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
          inventory += host["name"]+" ansible_ssh_user="+ansibleSshUser+" ansible_ssh_private_key_file="+ansibleSshKey+"\n"
    
    f = open(inventoryFileLocation,'w')
    f.write(inventory)
    f.close()
    logging.debug("Ansible inventory contents: \n"+inventory)
  
  def getHostsString(self):
    hostAndIps = self.getScribenginHostsAndIPs()
    hostString = self.hostsFileStartString+"\n"
    for host in hostAndIps:
      hostString += host["ip"]+" "+host["name"]+"\n"
    hostString +=self.hostsFileEndString+"\n"
    return hostString
    
    
  def updateRemoteHostsFile(self, hostsFile='/etc/hosts', user="root"):
    cluster = Cluster()
    hostString = self.getHostsString()
    cluster.sshExecute("echo '"+hostString+"'  >> /etc/hosts", user, False)
  
  
  def updateLocalHostsFile(self, hostsFile='/etc/hosts'):
    hostString = self.getHostsString()
    
    with open(hostsFile) as inputFile:
      hostFileContent = inputFile.read()
    
    hostFileContent = re.sub(self.hostsFileStartString+r"\n(.*\n)+"+self.hostsFileEndString, "", hostFileContent, re.MULTILINE)
    
    logging.debug("Hosts File new content: \n"+hostFileContent+"\n"+hostString)
    
    outFile = open(hostsFile, "w")
    outFile.write(hostFileContent+"\n"+hostString)
    outFile.close()
      
  
  #Must be executed *AFTER* updateLocalHostsFile is called on cluster
  def setupNeverwinterdpUser(self, user="root"):
    cluster = Cluster()
    userScript='''
        useradd -m -d /home/neverwinterdp -s /bin/bash -c "neverwinterdp user" -p $(openssl passwd -1 neverwinterdp)  neverwinterdp && 
        echo "neverwinterdp ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && 
        chown -R neverwinterdp:neverwinterdp /opt && 
        cp -R /root/.ssh/ /home/neverwinterdp/ && 
        chown -R neverwinterdp:neverwinterdp /home/neverwinterdp/.ssh
      '''
    cluster.sshExecute(userScript, user)


  def deploy(self, neverwinterdpHome, 
             playbook=join(dirname(dirname(dirname(dirname(realpath(__file__))))), "ansible/scribenginCluster.yml"), 
             inventory="/tmp/scribengininventoryDO",
             outputToStdout=True):
    #ansible-playbook playbooks/scribenginCluster.yml -i scribengininventory --extra-vars "neverwinterdp_home_override=/path/to/NeverwinterDP"
    command = "ansible-playbook "+playbook+" -i "+inventory+" --extra-vars \"neverwinterdp_home_override="+neverwinterdpHome+"\""
    logging.debug("ansible-playbook command: "+command)
    
    #Outputs stdout/stderr to stdout while command is running
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    while(True):
      retcode = p.poll() #returns None while subprocess is running
      line = p.stdout.readline()
      if(outputToStdout):
        print line.rstrip()
      if(retcode is not None):
        break
    
    
    

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

  
  

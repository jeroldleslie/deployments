import logging, subprocess
from os.path import abspath, dirname, join, expanduser, realpath
from sys import path
path.insert(0, dirname(dirname(abspath(__file__))))
from Cluster import Cluster



class ScribenginAnsible():
  def __init__(self):
    pass
  
  def getHostsAndIpsFromCluster(self):
    import socket
    hostsAndIps = []
    c = Cluster()
    for server in c.servers:
      hostsAndIps.append({
                          "name":server.hostname,
                          "ip": socket.gethostbyname(server.hostname)
                          })
    return hostsAndIps
  
  
  ##hostsAndIps is expected to be an array of dictionaries with format -
  #[ {"name": host1, "ip":"1.2.3.4"}, {"name": host2, "ip":"1.2.3.5"}, ....  ]
  def writeAnsibleInventory(self, hostsAndIps=None, inventoryFileLocation="/tmp/scribengininventoryDO", 
                            ansibleSshUser="neverwinterdp", ansibleSshKey="~/.ssh/id_rsa"):
    inventory = ""
    groupList = ["monitoring",
                 "kafka",
                 "hadoop-master",
                 "hadoop-worker",
                 "zookeeper",
                 "elasticsearch",]
    
    if hostsAndIps is None:
      hostsAndIps = self.getHostsAndIpsFromCluster()
    
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
  
  
  def deploy(self, playbook, inventory, neverwinterdpHome=None,
             outputToStdout=True, retry=0, retryLine=None, maxRetries=5):
    command = "ansible-playbook "+playbook+" -i "+inventory
    if neverwinterdpHome is not None:
      command += " --extra-vars \"neverwinterdp_home_override="+neverwinterdpHome+"\""
      
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
      self.deploy(playbook, inventory, neverwinterdpHome, outputToStdout, retry+1, retryLine)


if __name__ == "__main__":
  x = ScribenginAnsible()
  x.writeAnsibleInventory()
  #path.append("../scribengindigitalocean")
  #from scribengindigitalocean.ScribenginDigitalOcean import ScribenginDigitalOcean
  #digitalOcean = ScribenginDigitalOcean()
  #x.writeAnsibleInventory(digitalOcean.getScribenginHostsAndIPs("richardtest"))
  
  
  
  
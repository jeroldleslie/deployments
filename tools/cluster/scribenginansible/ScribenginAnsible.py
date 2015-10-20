import logging, subprocess
from os.path import abspath, dirname, join, expanduser, realpath
from sys import path
path.insert(0, dirname(dirname(abspath(__file__))))

class ScribenginAnsible():
  def __init__(self):
    pass
  
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
    for group in groupList:
      #Replace - with _ to differentiate groups from hostnames
      inventory += "\n["+group.replace("-","_")+"]\n"
      for host in hostsAndIps:
        if group in host["name"]:
          if "ip" in host:
            inventory += host["ip"]+" ansible_ssh_user="+ansibleSshUser+" ansible_ssh_private_key_file="+ansibleSshKey+"\n"
          else:  
            inventory += host["name"]+" ansible_ssh_user="+ansibleSshUser+" ansible_ssh_private_key_file="+ansibleSshKey+"\n"
    
    f = open(inventoryFileLocation,'w')
    f.write(inventory)
    f.close()
    logging.debug("Ansible inventory written to "+inventoryFileLocation)
    logging.info("Ansible inventory contents: \n"+inventory)
  
  def get_extra_vars_string(self,extra_vars={}):
    result = ""
    for k in extra_vars:
      result +=  str(k)+"="+str(extra_vars[k]) +" "
    return result
  
  def deploy(self, playbook, inventory, neverwinterdpHome=None,
             outputToStdout=True, retry=0, retryLine=None, maxRetries=5, extra_vars={}):
    
    command = "ansible-playbook "+playbook+" -i "+inventory
    if neverwinterdpHome is not None:
      extra_vars["neverwinterdp_home_override"]=neverwinterdpHome
    
    command += " --extra-vars \""+self.get_extra_vars_string(extra_vars)+"\""
    
    if retryLine is not None:
      command = command+" "+retryLine
    logging.info("ansible-playbook command: "+command)
    
    #Outputs stdout/stderr to stdout while command is running
    toRetry = False
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    while(True):
      retcode = p.poll() #returns None while subprocess is running
      line = p.stdout.readline()
      logging.info(line.rstrip())
      #Check to make sure we're not DEBUG
      #If we're DEBUG, clustercommander is set to output to STDOUT as well
      #so this avoids printing messages out twice to STDOUT
      if(outputToStdout and logging.getLogger().getEffectiveLevel() is not logging.DEBUG):
        print line.rstrip()
      #Looking for "to retry, use: --limit @/Users/user/scribenginCluster.retry"
      if "to retry, use: --limit" in line :
        toRetry = True
        retryLine = line.split(":")[1]
      if(retcode is not None):
        break
    
    if(toRetry and retry < maxRetries):
      print "Retrying Ansible"
      logging.info("Retrying Ansible")
      self.deploy(playbook, inventory, neverwinterdpHome, outputToStdout, retry+1, retryLine)


if __name__ == "__main__":
  x = ScribenginAnsible()
  x.writeAnsibleInventory()
  #path.append("../scribengindigitalocean")
  #from scribengindigitalocean.ScribenginDigitalOcean import ScribenginDigitalOcean
  #digitalOcean = ScribenginDigitalOcean()
  #x.writeAnsibleInventory(digitalOcean.getScribenginHostsAndIPs("richardtest"))
  
  
  
  
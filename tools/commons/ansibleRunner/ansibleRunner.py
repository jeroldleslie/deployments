import logging, subprocess, os, sys
from os.path import abspath, dirname, join
from sys import path
path.insert(0, dirname(dirname(abspath(__file__))))

class ansibleRunner():
  def __init__(self):
    self.ansiblehome=join(self.module_path(),"..","..","..","ansible")
    os.chdir(self.ansiblehome) 
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
  
  def deploy(self, playbook, inventory,
             outputToStdout=True, retry=0, retryLine=None, maxRetries=5, extra_vars={},
             tags=None, limit=None, neverwinterdpHome=None):
    
    command = "ansible-playbook "+playbook
    
    if inventory.strip() != "":
       command += " -i "+inventory
       
    if neverwinterdpHome is not None:
      extra_vars["neverwinterdp_home_override"]=neverwinterdpHome
    
    extraVarsString = self.get_extra_vars_string(extra_vars)
    if extraVarsString is not None and extraVarsString:
      command += " --extra-vars \""+self.get_extra_vars_string(extra_vars)+"\""
    
    if tags is not None and tags:
      command += " -t "+tags
    
    if limit is not None and limit:
      command += " -l "+limit
    
    
    
    if retryLine is not None:
      command = command+" "+retryLine
    logging.info("ansible-playbook command: "+command)
    print command
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
      self.deploy(playbook=playbook, inventory=inventory, neverwinterdpHome=neverwinterdpHome, 
        outputToStdout=outputToStdout, retry=retry+1, retryLine=retryLine, extra_vars=extra_vars, 
        tags=tags, maxRetries=maxRetries)
    elif(toRetry and retry >= maxRetries):
      import sys
      sys.exit(-1)

  def we_are_frozen(self):
      # All of the modules are built-in to the interpreter, e.g., by py2exe
      return hasattr(sys, "frozen")
  
  def module_path(self):
      encoding = sys.getfilesystemencoding()
      if self.we_are_frozen():
          return os.path.dirname(unicode(sys.executable, encoding))
      return os.path.dirname(unicode(__file__, encoding))
  
if __name__ == "__main__":
  x = ansibleRunner()

  x.writeAnsibleInventory(inventoryFileLocation="/tmp/scribengininventory_docker")
  
  
  
  
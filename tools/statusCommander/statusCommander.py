#! /bin/sh
""":"
exec python $0 ${1+"$@"}
"""

import click,logging
from sys import stdout
from tabulate import tabulate
from os.path import abspath, dirname, join
from sys import path
from multiprocessing import Pool
              
#Make sure the commons package is on the path correctly
path.insert(0, dirname(dirname(abspath(__file__))))
from commons.ssh.ssh import ssh
from commons.ansibleInventoryParser.ansibleInventoryParser import ansibleInventoryParser


################################################################################################################
class statusCommandParams():

  defaultReplacementString = "%identifier%" 

  """
  Helper class to store command info
  command - the command to run on remote machine
  identifiers - process names to replace in command string
  quietIfNotRunning - if set to true, and if the process isn't running, it isn't displayed in the final output
  replacementString - string to place into the command in place of this string.  Default is statusCommandParams.defaultReplacementString
  Notes:
    the status algorithm replaces "%identifiers%" with process-identifiers
    The command is expected to return a string in this format - "[process id] [process name]"
  """
  def __init__(self, 
              command = "jps -m | grep -w '%identifier%' | awk '{print $1 \" \" $2}'",
              identifiers=[], 
              quietIfNotRunning=False,
              replacementString = defaultReplacementString ):
    self.command = command
    self.identifiers = identifiers
    self.quietIfNotRunning = quietIfNotRunning
    self.replacementString = replacementString

################################################################################################################



scribeJpsCommand = "jps -m | grep '"+statusCommandParams.defaultReplacementString+"' | awk '{print $1 \" \" $4}'"

#Each key corresponds to an ansible group read in from your ansible inventory
statusCommands = {
  "monitoring"   : [ statusCommandParams(identifiers = ["kibana"]) ],
  "elasticsearch": [ statusCommandParams(identifiers = ["Main"]) ],
  "hadoop_master": [ statusCommandParams(identifiers = ["SecondaryNameNode", "ResourceManager", "NameNode"]) ],
  "zookeeper"    : [ statusCommandParams(identifiers = ["QuorumPeerMain"]) ],
  "kafka"        : [ statusCommandParams(identifiers = ["Kafka"]) ],
  "hadoop_worker": [ statusCommandParams(identifiers = ["DataNode", "NodeManager"]),
                     statusCommandParams(command =  scribeJpsCommand, 
                                          identifiers = ["vm-scribengin-master"],
                                          quietIfNotRunning = True),
                     statusCommandParams(command =  scribeJpsCommand, 
                                          identifiers = ["vm-master"],
                                          quietIfNotRunning = True),
                     statusCommandParams(command =  scribeJpsCommand, 
                                          identifiers = ["dataflow-master-*"],
                                          quietIfNotRunning = True),
                     statusCommandParams(command =  scribeJpsCommand, 
                                          identifiers = ["dataflow-worker-*"],
                                          quietIfNotRunning = True),
                     statusCommandParams(command =  scribeJpsCommand, 
                                          identifiers = ["vm-log-generator-*"],
                                          quietIfNotRunning = True),

                   ],
}



def getSshOutput(host, command, identifier, group, quietIfNotRunning):
  """
  SSH's onto machine, runs command, returns result along with info about process/host
  """
  logging.debug("hostname: "+host+ " - command: "+command)
  s = ssh()
  out,err = s.sshExecute(host, command)
  logging.debug("\tstdout: "+out+ "\n\tstderr: "+err)
  
  result = []
  
  #Command can return multiple lines
  for line in out.strip().split("\n"):
    #Expecting format of "[ProcessID] [Process Name]"
    splitoutput = line.split()
    
    pid = None
    if len(splitoutput) > 1:
      pid = splitoutput[0]
      identifier = splitoutput[1]
    
    result.append({
            "host":host,
            "command":command,
            "pid":pid,
            "identifier": identifier,
            "group": group,
            "quietIfNotRunning": quietIfNotRunning,
          })
  return result

@click.command(help="Get your cluster's status based on your ansible inventory file!")
@click.option('--debug/--no-debug',      default=False, help="Turn debugging on")
@click.option('--logfile',               default='/tmp/statuscommander.log', help="Log file to write to")
@click.option('--threads',         '-t', default=15, help="Number of threads to run simultaneously")
@click.option('--timeout',         '-m', default=30, help="SSH timeout time (seconds)")
@click.option('--inventory-file',  '-i', default='inventory', help="Ansible inventory file to use")
def mastercommand(debug, logfile, threads, timeout, inventory_file):
  if debug:
      #Set logging file, overwrite file, set logging level to DEBUG
      logging.basicConfig(filename=logfile, filemode="w", level=logging.DEBUG)
      logging.getLogger().addHandler(logging.StreamHandler(stdout))
      click.echo('Debug mode is %s' % ('on' if debug else 'off'))
  else:
    #Set logging file, overwrite file, set logging level to INFO
    logging.basicConfig(filename=logfile, filemode="w", level=logging.INFO)
  
  #Asynchronously launch all the SSH threads to get status
  pool = Pool(processes=threads)
  asyncresults = []
  i = ansibleInventoryParser(inventory_file)
  for server in i.parseInventoryFile():
    #Go through and asynchronously run ssh commands to get process status
    try:
      for services in statusCommands[server["group"]]:
        for identifier in services.identifiers:
          command = services.command.replace(services.replacementString, identifier)
          asyncresults.append(pool.apply_async(getSshOutput, [server["host"], command, identifier, server["group"], services.quietIfNotRunning]))
    except KeyError:
      logging.error("No commands for ansible group: "+server["group"])
      print "No commands for ansible group: "+server["group"]
  
  #Get asynchronous results in order that they were added
  tableRows=[]
  currHost=""
  for async in asyncresults:
    results = async.get(timeout=timeout)
    for result in results:

      #Check to see if group has been added already to the table
      needToAppendGroup = True
      for row in tableRows:
        if row[0] == result["group"]:
          needToAppendGroup = False

      #Add group info to the table if its not been added yet
      if needToAppendGroup:
        tableRows.append([result["group"],result["host"],"","",""])
      #Otherwise just add the hostname, if and only if we haven't 
      #added this hostname already to this group
      elif currHost != result["host"]:
        tableRows.append(["",result["host"],"","",""])

      #Set results as "Running" if PID is valid, otherwise its stopped
      if result["pid"]:
        tableRows.append(["","",result["identifier"],result["pid"],"Running"])
      else:
        if  not result["quietIfNotRunning"]:
          tableRows.append(["","",result["identifier"],"----", "Stopped"])
      
      currHost = result["host"]
        
  
  #Print out table
  tableHeaders  = ["Role", "Hostname", "ProcessIdentifier", "ProcessID", "Status"]
  print tabulate(tableRows, headers=tableHeaders)
   

if __name__ == '__main__':
  mastercommand()
  
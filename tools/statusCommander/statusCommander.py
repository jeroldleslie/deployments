#! /bin/sh
""":"
exec python $0 ${1+"$@"}
"""

import click,logging, signal
from socket import gethostbyaddr, inet_aton
from sys import stdout
from tabulate import tabulate
from os.path import abspath, dirname, join, isfile, expanduser
from sys import path
from multiprocessing import Pool
from time import sleep
              
#Make sure the commons package is on the path correctly
path.insert(0, dirname(dirname(abspath(__file__))))
from commons.ssh.ssh import ssh
from commons.ansibleInventoryParser.ansibleInventoryParser import ansibleInventoryParser

#Handle a SIGINT/ctrl+c signal cleanly without messy error output
def signal_handler(signal, frame):
  global _pool
  if _pool:
    _pool.terminate()
  import sys
  sys.exit(0)

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


#_pool is to help us clean up threads when ctrl+c/SIGINT is entered
_pool = None

scribeJpsCommand = "jps -m | grep "+statusCommandParams.defaultReplacementString+" | awk '{print $1 \" \" $4}'"

#Each key corresponds to an ansible group read in from your ansible inventory
statusCommands = {
  "monitoring"   : [ statusCommandParams(identifiers = ["kibana"],
                                         command="ps ax | grep -w 'kibana' | awk '{print $1 \" \" $5}' | grep kibana | sed -e 's@/opt/kibana/bin/../node/bin/node@/opt/kibana/bin/kibana@'") ],
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
                                          identifiers = ["validator"],
                                          quietIfNotRunning = True),
                     statusCommandParams(command =  scribeJpsCommand, 
                                          identifiers = ["generator"],
                                          quietIfNotRunning = True),

                   ],
}



def getSshOutput(ip, host, command, identifier, group, quietIfNotRunning):
  """
  SSH's onto machine, runs command, returns result along with info about process/host
  """
  logging.debug("hostname: "+host+ " - IP: "+ip+" - command: "+command)
  s = ssh()
  out,err = s.sshExecute(ip, command)
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
            "ip" :ip,
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
@click.option('--timeout',         '-m', default=30, help="SSH timeout time (seconds)")
@click.option('--inventory-file',  '-i', default='~/inventory', help="Ansible inventory file to use")
@click.option('--monitor',         '-n', is_flag=True, help="Run continuously")
@click.option('--monitor-sleep',   '-s', default=10, help="How long to sleep between checks while monitoring")
@click.pass_context
def mastercommand(ctx, debug, logfile, timeout, inventory_file, monitor, monitor_sleep):
  global _pool
  if debug:
      #Set logging file, overwrite file, set logging level to DEBUG
      logging.basicConfig(filename=logfile, filemode="w", level=logging.DEBUG)
      logging.getLogger().addHandler(logging.StreamHandler(stdout))
      click.echo('Debug mode is %s' % ('on' if debug else 'off'))
  else:
    #Set logging file, overwrite file, set logging level to INFO
    logging.basicConfig(filename=logfile, filemode="w", level=logging.INFO)


  if inventory_file == "~/inventory":
    inventory_file=join( expanduser("~"), "inventory")

  #Check if inventory file exists
  if not isfile(inventory_file):
    logging.error(inventory_file+" is not a file!  -i option needs to point to a valid ansible inventory file")
    print inventory_file+" is not a file!  -i option needs to point to a valid ansible inventory file"
    from sys import exit
    exit(-1)

  i = ansibleInventoryParser(inventory_file)

  #Asynchronously launch all the SSH threads to get status
  pool = Pool(processes=len(i.parseInventoryFile()))
  #Set global _pool to pool in case we get a SIGINT/Ctrl+C
  _pool = pool
  asyncresults = []

  for server in i.parseInventoryFile():
    #Go through and asynchronously run ssh commands to get process status
    try:
      for services in statusCommands[server["group"]]:
        for identifier in services.identifiers:
          command = services.command.replace(services.replacementString, identifier)
          ip = server["host"]
          hostName=server["host"]
          if "ansible_host" in server:
            ip = server["ansible_host"]

          asyncresults.append(pool.apply_async(getSshOutput, [ip, hostName, command, identifier, server["group"], services.quietIfNotRunning]))
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

      #If hostname is IP, resolve hostname
      hostName = result["host"]
      if not hostName:
        try:
          inet_aton(result["ip"])
          hostName = str(gethostbyaddr(result["ip"])[0])
        except:
          pass

      #Add group info to the table if its not been added yet
      if needToAppendGroup:
        tableRows.append([result["group"],hostName,result["ip"],"","",""])
      #Otherwise just add the hostname, if and only if we haven't 
      #added this hostname already to this group
      elif currHost != hostName:
        tableRows.append(["",hostName,result["ip"],"","",""])

      #Set results as "Running" if PID is valid, otherwise its stopped
      if result["pid"]:
        tableRows.append(["","","",result["identifier"],result["pid"],"Running"])
      else:
        if  not result["quietIfNotRunning"]:
          tableRows.append(["","","",result["identifier"],"----", "Stopped"])
      
      currHost = hostName
        
  
  #Print out table
  tableHeaders  = ["Role", "Hostname", "IP", "ProcessIdentifier", "ProcessID", "Status"]
  print tabulate(tableRows, headers=tableHeaders)

  pool.terminate()
  pool.join()
  
  #If monitor==true, then monitor again after sleeping for monitor_sleep
  if monitor:
    print "\n\n*******************************************************************\n\n"
    sleep(monitor_sleep)
    ctx.invoke(mastercommand, debug=debug, logfile=logfile, timeout=timeout,
                inventory_file=inventory_file, monitor=monitor, monitor_sleep=monitor_sleep)

   

if __name__ == '__main__':
  signal.signal(signal.SIGINT, signal_handler)
  mastercommand()
  
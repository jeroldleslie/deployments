#! /bin/sh
""":"
exec python $0 ${1+"$@"}
"""

import click,logging, signal
from sys import stdout
from os.path import abspath, dirname, join, isfile
from sys import path
from multiprocessing import Pool
from time import sleep
              
#Make sure the commons package is on the path correctly
path.insert(0, dirname(dirname(abspath(__file__))))
from commons.ssh.ssh import ssh
from commons.ansibleInventoryParser.ansibleInventoryParser import ansibleInventoryParser


def getMaxThreads(inventory_file):
  """
  Returns number of hosts
  """
  i = ansibleInventoryParser(inventory_file)
  return len(i.parseInventoryFile())

def getSshOutput(host, command):
  """
  SSH's onto machine, runs command, returns result along with info about process/host
  """
  logging.debug("hostname: "+host+ " - command: "+command)
  s = ssh()
  out,err = s.sshExecute(host, command)
  logging.debug("\tstdout: "+out+ "\n\tstderr: "+err)
  
  return {"host":host,
          "command": command,
          "stdout" : out,
          "stderr" : err,
        }


def execRemote(group, command, timeout, threads):
  """
  SSH's onto machine, runs command, outputs STDOUT and STDERR
  """
  #Asynchronously launch all the SSH threads 
  pool = Pool(processes=threads)
  asyncresults = []
  
  #Go through and asynchronously run ssh commands to get logs
  for server in group:
    asyncresults.append(pool.apply_async(getSshOutput, [server["host"], command]))

  #Get asynchronous results in order that they were added
  tableRows=[]
  currHost=""
  for async in asyncresults:
    results = async.get(timeout=timeout)
    #Print formatted results
    print "*" * (len(results["host"]+" - "+results["command"])+3)
    print results["host"]+" - "+results["command"]
    print "*" * (len(results["host"]+" - "+results["command"])+3)
    print results["stdout"]
    if results["stderr"]:
      print "STDERR:"
      print results["stderr"]


def getGroup(group, inventory_file):
  """
  Returns only machines that belong to group
  """
  i = ansibleInventoryParser(inventory_file)
  result = []
  for entry in i.parseInventoryFile():
    if entry["group"] == group:
      result.append(entry)
  return result

def getAllHosts(inventory_file):
  """
  Returns all machines from inventory file
  """
  i = ansibleInventoryParser(inventory_file)
  result = []
  for entry in i.parseInventoryFile():
    result.append(entry)
  return result

@click.command(help="Get your cluster's status based on your ansible inventory file!")
@click.option('--debug/--no-debug',            default=False, help="Turn debugging on")
@click.option('--logfile',                     default='/tmp/statuscommander.log', help="Log file to write to")
@click.option('--group',  '-g',         required=True, help="Ansible group to execute on")
@click.option('--command',  '-c',       required=True, help="Command to execute")
@click.option('--inventory-file', '-i', required=True, default='inventory', help="Path to inventory file to use")
@click.option('--timeout', '-t',        default=30, help="SSH timeout time (seconds)")
def mastercommand(debug, logfile, group, command, inventory_file, timeout):
  if not isfile(inventory_file):
    logging.error(inventory_file+" is not a file!  -i option needs to point to a valid ansible inventory file")
    print inventory_file+" is not a file!  -i option needs to point to a valid ansible inventory file"
    from sys import exit
    exit(-1)

  if debug:
    #Set logging file, overwrite file, set logging level to DEBUG
    logging.basicConfig(filename=logfile, filemode="w", level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler(stdout))
    click.echo('Debug mode is %s' % ('on' if debug else 'off'))
  else:
    #Set logging file, overwrite file, set logging level to INFO
    logging.basicConfig(filename=logfile, filemode="w", level=logging.INFO)

  #special case for group=="hadoop" -> hadoop_worker+hadoop_master
  if group == "hadoop":
    execRemote(getGroup("hadoop_worker", inventory_file)+getGroup("hadoop_master", inventory_file), 
                  command, timeout, getMaxThreads(inventory_file))
  #Special case for group == "cluster"  --> returns all hosts in inventory file
  elif group == "cluster":
    execRemote(getAllHosts(inventory_file), command, timeout, getMaxThreads(inventory_file))
  else:
    execRemote(getGroup(group, inventory_file), command, timeout, getMaxThreads(inventory_file))
   

if __name__ == '__main__':
  mastercommand()
  
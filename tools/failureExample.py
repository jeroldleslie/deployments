#! /bin/sh
""":"
exec python $0 ${1+"$@"}
"""

import click,logging
from pprint import pformat
from sys import stdout

from os.path import abspath, dirname, join
from sys import path
from time import sleep
from random import sample
from multiprocessing import Process

from commons.ansibleRunner.ansibleRunner import ansibleRunner
from commons.ansibleInventoryParser.ansibleInventoryParser import ansibleInventoryParser
from commons.kafkaTool.kafkaTool import kafkaTool
from statusCommander import statusCommander

#Constants for tag names
_install_string    = "install"
_configure_string  = "configure"
_stop_string       = "stop"
_force_stop_string = "force-stop" 
_clean_string      = "clean"
_start_string      = "start"

#Calling this in a threaded manner because if not
#it seems that click automatically calls exit and 
#kills the application in place
def getClusterStatus(inventory_file):
  p = Process(target=statusCommander.mastercommand, args=(["-i", inventory_file, "--no-debug"],))
  p.start()
  p.join()
  stdout.flush()


@click.command(help="Failure simulation helper!\n")
@click.option('--debug/--no-debug',               default=False,                 help="Turn debugging on")
@click.option('--logfile',                        default='/tmp/failuresim.log', help="Log file to write to")
@click.option('--inventory-file',         '-i',   default='',                    help="Ansible inventory file to use")
@click.option('--service',                '-s',   default='',                    help="Which service to disrupt")
@click.option('--clean',                  '-c',   is_flag=True,                  help='Enable to Clean')
@click.option('--sleep-time',             '-t',   default=30,                    help='Seconds to sleep after killing')
@click.option('--ansible-root-dir', default=dirname(dirname(abspath(__file__)))+"/ansible", 
                                                                                 help="Root directory for Ansible")
@click.option('--profile-type',           '-p',   default="stability",           help='Which profile type to use')
@click.option('--ansible-output',         '-d',   is_flag=True,                  help='Enable output from ansible  to stdout')
def mastercommand(debug, logfile, inventory_file, service, clean, sleep_time,ansible_root_dir, profile_type, ansible_output):
  #Set up logging
  logger = logging.getLogger('failureSimulator')
  if debug:
  	#Log to a file
    logger.addHandler(logging.FileHandler(logfile, mode="w"))
    #Set logging level to DEBUG
    logger.setLevel(logging.DEBUG)
    #Make other loggers quiet
    click.echo('Debug mode is %s' % ('on' if debug else 'off'))
    logging.getLogger("paramiko").setLevel(logging.WARNING)
    logging.getLogger("statusCommander").setLevel(logging.ERROR)
  else:
  	#Log to a file
    logger.addHandler(logging.FileHandler(logfile, mode="w"))
    #Set Logging level to INFO
    logger.setLevel(logging.INFO)

  #Set which profile type to use when running ansible playbooks
  #will point ansible scripts to neverwinterdp-deployments/ansible/profile/[profile_type].yml
  #  i.e. stability, failure, default...
  extra_vars_dict = {}
  if (profile_type != ""):
    extra_vars_dict['profile_type'] = profile_type
  

  #Parse the inventory file to get our cluster info
  runner = ansibleRunner()
  inventoryParser = ansibleInventoryParser(ansibleInventoryFilePath=inventory_file)
  parsedInv = inventoryParser.parseInventoryFile()

  #If you want to print out a dictionary in a pretty format - uncomment this line - will work with any list/dictionary in python
  #print "Parsed Inventory:\n"+pformat(parsedInv)

  #Single out the group of machines we want
  #based on the ansible inventory group
  machinesToFail = []
  for machine in parsedInv:
    #machine["group"] corresponds to the ansible group we want to effect
    if machine["group"].lower() == service.lower():
      machinesToFail.append(machine)
  logger.debug("Machines to Effect: \n"+pformat(machinesToFail)+"\n")

  #If you wanted to specifically call out 
  #Hadoop worker+master machines for example
  hadoopMachines = []
  for machine in parsedInv:
    if machine["group"].lower() == "hadoop_master" or machine["group"].lower() == "hadoop_worker":
      hadoopMachines.append(machine)
  logger.debug("Hadoop Machines: \n"+pformat(hadoopMachines)+"\n")

  
  #Set which playbook we want to use, 
  #which we'll set to /path/to/ansible/dir/[service].yml
  playbook = join(ansible_root_dir, service+".yml")
  logger.debug("Playbook: "+playbook)
  
  #Randomly choose which machine to fail on
  machineToEffect = sample(machinesToFail, 1)[0]
  logger.debug("Machine to fail on: "+ machineToEffect["host"])

  #Call statusCommander to output cluster status
  getClusterStatus(inventory_file)

  
  logger.debug("Stopping process")
  runner.deploy(playbook = playbook, 
                inventory=inventory_file, 
                outputToStdout=ansible_output, 
                maxRetries=0,
                tags=_stop_string,
                extra_vars=extra_vars_dict,
                limit=machineToEffect["host"],)

  logger.debug("Force Stopping process")
  runner.deploy(playbook = playbook, 
                inventory=inventory_file, 
                outputToStdout=ansible_output, 
                maxRetries=0,
                tags=_force_stop_string,
                extra_vars=extra_vars_dict,
                limit=machineToEffect["host"],)

  logger.debug("Cleaning process")
  #Clean process if specified
  if clean:
    runner.deploy(playbook = playbook, 
                inventory=inventory_file, 
                outputToStdout=ansible_output, 
                maxRetries=0,
                tags=_clean_string,
                extra_vars=extra_vars_dict,
                limit=machineToEffect["host"],)        

  logger.debug("Sleeping for: "+str(sleep_time))
  sleep(sleep_time)
  

  #Increment the brokerID by 1 (guaranteed to be unique and new)
  logger.debug("Setting new broker ID for Kafka: "+machineToEffect["host"])
  kafka = kafkaTool(inventory_file)
  kafka.setNewBrokerID(machineToEffect["host"])

  #restart the process
  runner.deploy(playbook = playbook, 
                inventory=inventory_file, 
                outputToStdout=ansible_output, 
                maxRetries=0,
                tags=_start_string,
                extra_vars=extra_vars_dict,
                limit=machineToEffect["host"],)





if __name__ == '__main__':
  mastercommand()
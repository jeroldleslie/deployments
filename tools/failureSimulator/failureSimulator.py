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
#Make sure the commons package is on the path correctly
path.insert(0, dirname(dirname(abspath(__file__))))
from commons.ansibleRunner.ansibleRunner import ansibleRunner
from commons.ansibleInventoryParser.ansibleInventoryParser import ansibleInventoryParser
from statusCommander import statusCommander




#Constants for tag names
_install_string    = "install"
_configure_string  = "configure"
_stop_string       = "stop"
_force_stop_string = "force-stop" 
_clean_string      = "clean"
_start_string      = "start"


def getClusterStatus(inventory_file):
  p = Process(target=statusCommander.mastercommand, args=(["-i", inventory_file, "--no-debug"],))
  p.start()
  p.join()
  stdout.flush()


@click.command(help="Simulate failures on your poor unsuspecting cluster!\n")
@click.option('--debug/--no-debug',           default=False, help="Turn debugging on")
@click.option('--logfile',                    default='/tmp/failuresim.log', help="Log file to write to")
@click.option('--inventory-file',         '-i',   default='', help="Ansible inventory file to use")
@click.option('--service',                '-s',   default='', help="Which service to disrupt")
@click.option('--kill-method',            '-k',   default="kill",  type=click.Choice(['kill','stop']), help='Method of killing service')
@click.option('--clean',                  '-c',   is_flag=True,  help='Enable to Clean')
@click.option('--sleep-time',             '-t',   default=30,  help='Seconds to sleep after killing')
@click.option('--ansible-root-dir',           default=dirname(dirname(dirname(abspath(__file__))))+"/ansible", help="Root directory for Ansible")
@click.option('--profile-type',           '-p',   default="stability",  help='Which profile type to use')
@click.option('--output-status',          '-o',   is_flag=True,  help='Output status information')
@click.option('--ansible-output',           '-d',   is_flag=True,  help='Enable output from ansible  to stdout')
def mastercommand(debug, logfile, inventory_file, service, kill_method, clean, sleep_time,ansible_root_dir, profile_type, output_status, ansible_output):
  
  logger = logging.getLogger('failureSimulator')
  if debug:
    logger.addHandler(logging.FileHandler(logfile, mode="w"))
    logger.setLevel(logging.DEBUG)
    #logger.addHandler(logging.StreamHandler(stdout))
    click.echo('Debug mode is %s' % ('on' if debug else 'off'))
    logging.getLogger("paramiko").setLevel(logging.WARNING)
    logging.getLogger("statusCommander").setLevel(logging.ERROR)
  else:
    logger.addHandler(logging.FileHandler(logfile, mode="w"))
    logger.setLevel(logging.INFO)

  #Set which profile type to use
  extra_vars_dict = {}
  if (profile_type != ""):
    extra_vars_dict['profile_type'] = profile_type
  

  #Parse the inventory file
  runner = ansibleRunner()
  inventoryParser = ansibleInventoryParser(ansibleInventoryFilePath=inventory_file)
  parsedInv = inventoryParser.parseInventoryFile()


  #Single out the group of machines we want
  machinesToFail = []
  for machine in parsedInv:
    if machine["group"].lower() == service.lower():
      machinesToFail.append(machine)
  
  logger.debug("Machines to Effect: \n"+pformat(machinesToFail)+"\n")

  #Determine if we're force-stopping or stopping
  stop_tag = ""
  if kill_method == "kill":
    stop_tag = _force_stop_string
  else:
    stop_tag = _stop_string
  
  playbook = join(ansible_root_dir, service+".yml")
  
  #Loop forever
  while True:
    #Randomly choose which machine to fail on
    machineToEffect = sample(machinesToFail, 1)[0]
    logger.debug("Machine to fail on: "+ machineToEffect["host"])
    
    if(output_status):
      getClusterStatus(inventory_file)

    logger.debug("Stopping process")
    #Stop the process
    runner.deploy(playbook = playbook, 
                  inventory=inventory_file, 
                  outputToStdout=ansible_output, 
                  maxRetries=0,
                  tags=stop_tag,
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

    #restart the process
    runner.deploy(playbook = playbook, 
                  inventory=inventory_file, 
                  outputToStdout=ansible_output, 
                  maxRetries=0,
                  tags=_start_string,
                  extra_vars=extra_vars_dict,
                  limit=machineToEffect["host"],)

    if(output_status):
      getClusterStatus(inventory_file)

    logger.debug("Sleeping for: "+str(sleep_time))
    sleep(sleep_time)



if __name__ == '__main__':
  mastercommand()
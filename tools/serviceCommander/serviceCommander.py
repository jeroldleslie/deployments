#! /bin/sh
""":"
exec python $0 ${1+"$@"}
"""

import click,logging
from sys import stdout

from os.path import abspath, dirname, join
from sys import path
              
#Make sure the commons package is on the path correctly
path.insert(0, dirname(dirname(abspath(__file__))))
from commons.ansibleRunner.ansibleRunner import ansibleRunner

#Constants for tag names
_install_string    = "install"
_configure_string  = "configure"
_stop_string       = "stop"
_force_stop_string = "force-stop" 
_clean_string      = "clean"
_start_string      = "start"

#Here is our array for roles within the cluster
#When the --cluster command is passed in, these are the roles that are executed
#The order of this array DOES MATTER.  From left to right is the order in which the 
#  cluster will be started.  To stop/force-stop, the array will be reversed
_cluster_array     = [ "zookeeper", "kafka", "hadoop", "scribengin" ]



@click.command(help="Use Ansible to manage services in your cluster!\n")
@click.option('--debug/--no-debug',      default=False, help="Turn debugging on")
@click.option('--logfile',               default='/tmp/servicecommander.log', help="Log file to write to")

@click.option('--services',        '-e', default='', help="Services to impact input as a comma separated list")
@click.option('--subset',          '-l', default='', help="Further limit selected hosts with an additional pattern")
@click.option('--inventory-file',  '-i', default='inventory', help="Ansible inventory file to use")
@click.option('--cluster',         '-u', is_flag=True, help="Alternative to --services option, runs for entire cluster")

@click.option('--restart',         '-r', is_flag=True, help="restart services")
@click.option('--start',           '-s', is_flag=True, help="start services")
@click.option('--stop',            '-t', is_flag=True, help="stop services")
@click.option('--force-stop',      '-f', is_flag=True, help="kill services")
@click.option('--clean',           '-a', is_flag=True, help="clean services")
@click.option('--install',         '-n', is_flag=True, help="install services")
@click.option('--configure',       '-c', is_flag=True, help="configure services")
@click.option('--profile',         '-p', default='',   help="profile type for service configuration" )
@click.option('--ansible-root-dir',      default=dirname(dirname(dirname(abspath(__file__))))+"/ansible", help="Root directory for Ansible")
@click.option('--max-retries',     '-m', default=5, help="Max retries for running the playbook")
def mastercommand(debug, logfile, services, subset, inventory_file, cluster, restart, start, stop, force_stop, clean, install, configure, profile, ansible_root_dir, max_retries):
  if debug:
    #Set logging file, overwrite file, set logging level to DEBUG
    logging.basicConfig(filename=logfile, filemode="w", level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler(stdout))
    click.echo('Debug mode is %s' % ('on' if debug else 'off'))
  else:
    #Set logging file, overwrite file, set logging level to INFO
    logging.basicConfig(filename=logfile, filemode="w", level=logging.INFO)
  
  
  tagsToRun=[]
  if install:
    tagsToRun.append(_install_string)
  if configure:
    tagsToRun.append(_configure_string)
  if stop or restart:
    tagsToRun.append(_stop_string)
  if force_stop:
    tagsToRun.append(_force_stop_string)
  if clean:
    tagsToRun.append(_clean_string)
  if start or restart:
    tagsToRun.append(_start_string)
  
  
  #In case user passes in some services that aren't in _cluster_array, we don't want to omit them
  print set(services.split(","))
  services = filter(bool, services.split(","))
  print services
  nonClusterServices = list(set(services)-set(_cluster_array))
  print "nonClusterServices>>>>>>"
  print nonClusterServices
  if not nonClusterServices:
    print "getting inside" 
    nonClusterServices = None

  #_cluster_array is in order of which services to start first
  #So to prevent any mistakes, we can go through and prune the list of services to run
  #  based on which services are passed in
  if not cluster:
    index = 0
    while index < len(_cluster_array):
      if _cluster_array[index] not in services:
        del _cluster_array[index]
        index -=1
      index+=1
  
  print _cluster_array
  
  servicesToRun = _cluster_array
  print "before nonClusterServices"
  print servicesToRun
  print nonClusterServices
  if nonClusterServices:
    servicesToRun += nonClusterServices
  #The reversed list is the order to stop/force-stop
  servicesToRunReversed = list(reversed(servicesToRun))
  print "after nonClusterServices"
  print servicesToRun
  
  extra_vars={}
  if (profile != ""):
    extra_vars['profile_type'] = profile
  
  runner = ansibleRunner()

  #Go through each tag to run
  for tag in tagsToRun:
    #If we are stopping/force-stopping, we need to run in opposite order than if starting
    if tag == _stop_string or tag == _force_stop_string:
      services = servicesToRunReversed
    else:
      services = servicesToRun

    print services
    
    #Loop through each service/playbook
    for playbook in services :
      print "playbook before: "+ playbook
      playbook = join(ansible_root_dir, playbook)+".yml"
      print "playbook: " + playbook
      logging.debug("Running playbook: "+playbook)
      logging.debug("Tags: "+tag)
      logging.debug("Inventory: "+inventory_file)
      logging.debug("Max Retries: "+str(max_retries))
      logging.debug("Subset: "+str(subset))
      logging.debug("")

      runner.deploy(playbook = playbook, 
                  inventory=inventory_file, 
                  outputToStdout=True, 
                  maxRetries=max_retries,
                  tags=tag,
                  extra_vars=extra_vars,
                  limit=subset,)
   

if __name__ == '__main__':
  mastercommand()
  
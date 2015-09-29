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



@click.command(help="Use Ansible to manage services in your cluster!\n")
@click.option('--debug/--no-debug',      default=False, help="Turn debugging on")
@click.option('--logfile',               default='/tmp/servicecommander.log', help="Log file to write to")

@click.option('--services',        '-e', default='', help="Services to impact input as a comma separated list")
@click.option('--subset',          '-l', default='', help="Further limit selected hosts with an additional pattern")
@click.option('--inventory-file',  '-i', default='inventory', help="Ansible inventory file to use")

@click.option('--restart',         '-r', is_flag=True, help="restart services")
@click.option('--start',           '-s', is_flag=True, help="start services")
@click.option('--stop',       '-t',      is_flag=True, help="stop services")
@click.option('--force-stop',  '-f',     is_flag=True, help="kill services")
@click.option('--clean',  '-f',          is_flag=True, help="clean services")
@click.option('--install',  '-n',        is_flag=True, help="install services")
@click.option('--configure',  '-c',      is_flag=True, help="configure services")

@click.option('--ansible-root-dir',      default=dirname(dirname(dirname(abspath(__file__))))+"/ansible", help="Root directory for Ansible")
@click.option('--max-retries',     '-m', default=5, help="Max retries for running the playbook")
def mastercommand(debug, logfile, services, subset, inventory_file, restart, start, stop, force_stop, clean, install, configure, ansible_root_dir, max_retries):
  if debug:
      #Set logging file, overwrite file, set logging level to DEBUG
      logging.basicConfig(filename=logfile, filemode="w", level=logging.DEBUG)
      logging.getLogger().addHandler(logging.StreamHandler(stdout))
      click.echo('Debug mode is %s' % ('on' if debug else 'off'))
  else:
    #Set logging file, overwrite file, set logging level to INFO
    logging.basicConfig(filename=logfile, filemode="w", level=logging.INFO)
  
  
  tagsToRun=""
  if install:
    tagsToRun+="install,"
  if configure:
    tagsToRun+="configure,"
  if stop or restart:
    tagsToRun+="stop,"
  if force_stop:
    tagsToRun+="force-stop,"
  if clean:
    tagsToRun+="clean,"
  if start or restart:
    tagsToRun+="start,"
  tagsToRun=tagsToRun[:-1]
  tagsToRun="\""+tagsToRun+"\""


  runner = ansibleRunner()
  for playbook in services.split(",") :
    playbook = join(ansible_root_dir, playbook)+".yml"
    logging.debug("Running playbook: "+playbook)
    logging.debug("Tags: "+tagsToRun)
    logging.debug("Inventory: "+inventory_file)
    logging.debug("Max Retries: "+str(max_retries))
    logging.debug("Subset: "+str(subset))
    logging.debug("")
    

    runner.deploy(playbook = playbook, 
                inventory=inventory_file, 
                outputToStdout=True, 
                maxRetries=max_retries,
                tags=tagsToRun,
                limit=subset,)
   

if __name__ == '__main__':
  mastercommand()
  
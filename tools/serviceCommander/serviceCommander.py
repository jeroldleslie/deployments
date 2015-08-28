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


_debug = False
_logfile = ''


playbookMapping= {
                  "start"      : "start.yml",
                  "stop"       : "stop.yml",
                  "force_stop" : "force-stop.yml",
                  "clean"      : "clean.yml",
                  }


@click.command()
@click.option('--debug/--no-debug', default=False, help="Turn debugging on")
@click.option('--logfile',  default='/tmp/clustercommander.log', help="Log file to write to")
@click.option('--services',        '-e', default='', help="Services to impact input as a comma separated list")
@click.option('--subset',          '-l', default='', help="Further limit selected hosts with an additional pattern")
@click.option('--inventory-file',  '-i',   default='inventory', help="Ansible inventory file to use")
@click.option('--max-retries',     '-m',   default=5, help="Max retries for running the playbook")
@click.option('--restart',         '-r',  is_flag=True, help="restart services")
@click.option('--start',           '-s',       is_flag=True, help="start services")
@click.option('--stop',       '-t',       is_flag=True, help="stop services")
@click.option('--force-stop',  '-f',      is_flag=True, help="kill services")
@click.option('--clean',  '-f',      is_flag=True, help="clean services")
@click.option('--ansible-root-dir',   default=dirname(dirname(dirname(abspath(__file__))))+"/ansible", help="Root directory for Ansible")
def mastercommand(debug, logfile, services, subset, inventory_file, max_retries, restart, start, stop, force_stop, clean, ansible_root_dir):
  global _debug, _logfile, _neverwinterdp_home
  _debug = debug
  _logfile = logfile
  
  if _debug:
      #Set logging file, overwrite file, set logging level to DEBUG
      logging.basicConfig(filename=_logfile, filemode="w", level=logging.DEBUG)
      logging.getLogger().addHandler(logging.StreamHandler(stdout))
      click.echo('Debug mode is %s' % ('on' if debug else 'off'))
  else:
    #Set logging file, overwrite file, set logging level to INFO
    logging.basicConfig(filename=_logfile, filemode="w", level=logging.INFO)
  
    
  playbooksToRun=[]
  if stop or restart:
    playbooksToRun.append(playbookMapping["stop"])
  if force_stop:
    playbooksToRun.append(playbookMapping["force_stop"])
  if clean:
    playbooksToRun.append(playbookMapping["clean"])
  if start or restart:
    playbooksToRun.append(playbookMapping["start"])
    
  
  runner = ansibleRunner()
  for playbook in playbooksToRun:
    playbook = join(ansible_root_dir, playbook)
    logging.debug("Running playbook: "+playbook)
    runner.deploy(playbook = playbook, 
                inventory=inventory_file, 
                outputToStdout=True, 
                maxRetries=max_retries,
                tags=services,
                limit=subset,)
   

if __name__ == '__main__':
  #Parse commands and run
  mastercommand()
  
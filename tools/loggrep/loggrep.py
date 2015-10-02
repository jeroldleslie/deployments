#! /bin/sh
""":"
exec python $0 ${1+"$@"}
"""

import click,logging
from sys import stdout
from os.path import abspath, dirname, join, isfile
from sys import path
from multiprocessing import Pool

#Make sure the commons package is on the path correctly
path.insert(0, dirname(dirname(abspath(__file__))))
from commons.ssh.ssh import ssh
from commons.ansibleInventoryParser.ansibleInventoryParser import ansibleInventoryParser


_threads = 15
_timeout = 30
_inventory_file = "inventory"

def getGroup(group):
  """
  Returns only machines that belong to group
  """
  global _inventory_file
  i = ansibleInventoryParser(_inventory_file)
  result = []
  for entry in i.parseInventoryFile():
    if entry["group"] == group:
      result.append(entry)
  return result


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



def getLogs(group, command):
  """
  SSH's onto machine, runs command, outputs STDOUT and STDERR
  """
  global _threads, _timeout
  #Asynchronously launch all the SSH threads 
  pool = Pool(processes=_threads)
  asyncresults = []
  
  #Go through and asynchronously run ssh commands to get logs
  for server in group:
    asyncresults.append(pool.apply_async(getSshOutput, [server["host"], command]))

  #Get asynchronous results in order that they were added
  tableRows=[]
  currHost=""
  for async in asyncresults:
    results = async.get(timeout=_timeout)
    #Print formatted results
    print "*" * (len(results["host"]+" - "+results["command"])+3)
    print results["host"]+" - "+results["command"]
    print "*" * (len(results["host"]+" - "+results["command"])+3)
    print results["stdout"]
    if results["stderr"]:
      print "STDERR:"
      print results["stderr"]


def buildCommandString(find_folder, find_iname, grep_options, grep_string):
  return "find "+find_folder+" \\( -iname \""+find_iname+"\" \\) -exec grep "+grep_options+" '"+grep_string+"' {} \; -print"

@click.group(chain=True, help="Parse your cluster's logs!")
@click.option('--debug/--no-debug',      default=False, help="Turn debugging on")
@click.option('--logfile',               default='/tmp/clusterlog.log', help="Log file to write to")
@click.option('--threads',         '-t', default=15, help="Number of threads to run simultaneously")
@click.option('--timeout',         '-m', default=30, help="SSH timeout time (seconds)")
@click.option('--inventory-file',  '-i', default='inventory', help="Ansible inventory file to use")
def mastercommand(debug, logfile, threads, timeout, inventory_file):
  global _threads, _timeout, _inventory_file
  _threads = threads
  _timeout = timeout
  _inventory_file = inventory_file

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

@mastercommand.command(help="Get Kafka logs")
@click.option('--find-folder',  '-f', default="/opt/kafka/logs/", help="Folder to find logs")
@click.option('--find-iname',   '-n', default="*.log", help="Name to look for - (find's -iname option)")
@click.option('--grep-options', '-g', default="-i", help="Options for grep")
@click.option('--grep-string',  '-s', default="exception", help="What to grep for")
def kafka(find_folder, find_iname, grep_options, grep_string):
  getLogs(getGroup("kafka"), buildCommandString(find_folder, find_iname, grep_options, grep_string))


@mastercommand.command(help="Get Zookeeper logs")
@click.option('--find-folder',  '-f', default="/opt/zookeeper/logs/", help="Command to run to get logs")
@click.option('--find-iname',   '-n', default="zookeeper.*", help="Name to look for - (find's -iname option)")
@click.option('--grep-options', '-g', default="-i", help="Options for grep")
@click.option('--grep-string',  '-s', default="exception", help="What to grep for")
def zookeeper(find_folder, find_iname, grep_options, grep_string):
  getLogs(getGroup("zookeeper"), buildCommandString(find_folder, find_iname, grep_options, grep_string))


@mastercommand.command(help="Get Hadoop logs")
@click.option('--find-folder',  '-f', default="/opt/hadoop/logs/", help="Command to run to get logs")
@click.option('--find-iname',   '-n', default="*.log", help="Name to look for - (find's -iname option)")
@click.option('--grep-options', '-g', default="-i", help="Options for grep")
@click.option('--grep-string',  '-s', default="exception", help="What to grep for")
def hadoop(find_folder, find_iname, grep_options, grep_string):
  group = getGroup("hadoop_worker") + getGroup("hadoop_master")
  getLogs(group, buildCommandString(find_folder, find_iname, grep_options, grep_string))



@mastercommand.command(help="Get YARN App logs")
@click.option('--find-folder',  '-f', default="/opt/hadoop/vm/", help="Command to run to get logs")
@click.option('--find-iname',   '-n', default="stdout\" -o -iname \"stderr", help="Name to look for - (find's -iname option)")
@click.option('--grep-options', '-g', default="-i", help="Options for grep")
@click.option('--grep-string',  '-s', default="exception", help="What to grep for")
def yarnapp(find_folder, find_iname, grep_options, grep_string):
  getLogs(getGroup("hadoop_worker"), buildCommandString(find_folder, find_iname, grep_options, grep_string))



@mastercommand.command(help="Get YARN VM App logs")
@click.option('--find-folder',  '-f', default="/opt/hadoop/vm/", help="Command to run to get logs")
@click.option('--find-iname',   '-n', default="*.log", help="Name to look for - (find's -iname option)")
@click.option('--grep-options', '-g', default="-i", help="Options for grep")
@click.option('--grep-string',  '-s', default="exception", help="What to grep for")
def yarnvmapp(find_folder, find_iname, grep_options, grep_string):
  getLogs(getGroup("hadoop_worker"), buildCommandString(find_folder, find_iname, grep_options, grep_string))


@mastercommand.command(help="Get YARN logs")
@click.option('--find-folder',  '-f', default="/opt/hadoop/logs/", help="Command to run to get logs")
@click.option('--find-iname',   '-n', default=".*yarn*.log", help="Name to look for - (find's -iname option)")
@click.option('--grep-options', '-g', default="-i", help="Options for grep")
@click.option('--grep-string',  '-s', default="exception", help="What to grep for")
def yarn(find_folder, find_iname, grep_options, grep_string):
  group = getGroup("hadoop_worker") + getGroup("hadoop_master")
  getLogs(group, buildCommandString(find_folder, find_iname, grep_options, grep_string))



@mastercommand.command(help="Get Cluster logs")
@click.option('--grep-options', '-g', default="-i", help="Options for grep")
@click.option('--grep-string',  '-s', default="exception", help="What to grep for")
@click.pass_context
def cluster(ctx, grep_options, grep_string):
  ctx.invoke(zookeeper, grep_options=grep_options, grep_string=grep_string)
  ctx.invoke(kafka,     grep_options=grep_options, grep_string=grep_string)
  ctx.invoke(hadoop,    grep_options=grep_options, grep_string=grep_string)
  ctx.invoke(yarn,   grep_options=grep_options, grep_string=grep_string)
  ctx.invoke(yarnapp,   grep_options=grep_options, grep_string=grep_string)
  ctx.invoke(yarnvmapp,   grep_options=grep_options, grep_string=grep_string)




if __name__ == '__main__':
  mastercommand()



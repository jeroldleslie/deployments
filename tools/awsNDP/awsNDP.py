#! /bin/sh
""":"
exec python $0 ${1+"$@"}
"""

import click,logging, boto3
from sys import stdout,path
from os.path import abspath, dirname
from multiprocessing import Process
#Make sure the commons package is on the path correctly
path.insert(0, dirname(dirname(abspath(__file__))))
from commons.ssh.ssh import ssh

logger = None

def getAwsRegions():
  return ["us-east-1","us-west-2","us-west-1","eu-west-1",
            "eu-central-1","ap-southeast-1","ap-northeast-1",
            "ap-southeast-2","ap-northeast-2","sa-east-1"]

def getCluster(region):
  group = {}
  ec2 = boto3.resource('ec2', region_name=region)
  instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
  for instance in instances:
    for tag in instance.tags:
      if "Key" in tag  and tag["Key"].lower() == "name":
        groupKey = tag["Value"].rstrip('1234567890-').replace("-","_")
        if not groupKey in group:
          group[groupKey] = []
        group[groupKey].append( {
                      "name": tag["Value"],
                      "publicIP": instance.public_ip_address,
                      "privateIP": instance.private_ip_address,
                      "publicDNS": instance.public_dns_name,
                      })
  return group

def getHostsFile(region):
  logger = logging.getLogger('awsNDP')
  group = getCluster(region)
  result = "##SCRIBENGIN CLUSTER START##\n"
  for group,machines in group.iteritems():
    for machine in machines:
      result+= machine["privateIP"]+" "+machine["name"]+" "+machine["name"]+".private"+"\n"
      result+= machine["publicIP"]+" "+machine["name"]+".public\n"
  result += "##SCRIBENGIN CLUSTER END##\n"
  return result


def updateRemoteHostsFile(hostname,content,hostfile="/etc/hosts"):
  logger = logging.getLogger('awsNDP')
  s = ssh()
  out,err = s.sshExecute(hostname, "sudo sh -c \"echo '"+content+"' > "+hostfile+"\"")
  if out:
    print "STDOUT: "+out
  if err:
    print "STDERR: "+err
  logger.debug(hostname+": STDOUT: "+out)
  logger.debug(hostname+": STDERR: "+err)


@click.group(chain=True, help="AWS tool for NDP!")
@click.option('--debug/--no-debug',      default=False, help="Turn debugging on")
@click.option('--logfile',               default='/tmp/awsNDP.log', help="Log file to write to")
def mastercommand(debug, logfile):
  logger = logging.getLogger('awsNDP')
  if debug:
    logger.addHandler(logging.FileHandler(logfile, mode="w"))
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(stdout))
    click.echo('Debug mode is %s' % ('on' if debug else 'off'))
  else:
    logger.addHandler(logging.FileHandler(logfile, mode="w"))
    logger.setLevel(logging.INFO)


@mastercommand.command(help="Create ansible inventory file from AWS cluster")
@click.option('--region',    '-r',   default="us-west-2",  type=click.Choice(getAwsRegions()), help='AWS Region to connect to')
@click.option('--keypath',   '-k',   default="~/.ssh/id_rsa",  help='Path to SSH key')
@click.option('--user',      '-u',   default="neverwinterdp",  help='Username to use')
def ansibleinventory(region,keypath,user):
  logger = logging.getLogger('awsNDP')
  group = getCluster(region)
  for group,machines in group.iteritems():
    print "["+group+"]"
    id=1
    for machine in machines:
      print machine["name"]+" ansible_ssh_user="+str(user)+" ansible_ssh_private_key_file="+str(keypath)+" ansible_host="+str(machine["publicDNS"])+" id="+str(id)
      id= id+1
    print ""

@mastercommand.command(help="Create ansible inventory file from AWS cluster")
@click.option('--region',    '-r',   default="us-west-2",  type=click.Choice(getAwsRegions()), help='AWS Region to connect to')
def hostfile(region):
  print getHostsFile(region)

@mastercommand.command(help="Create ansible inventory file from AWS cluster and update remote /etc/hosts file")
@click.option('--region',    '-r',   default="us-west-2",  type=click.Choice(getAwsRegions()), help='AWS Region to connect to')
def updateremotehostfile(region):
  group = getCluster(region)
  hostFile  = "127.0.0.1 localhost localhost.localdomain localhost4 localhost4.localdomain4\n"
  hostFile += "::1 localhost localhost.localdomain localhost6 localhost6.localdomain6\n\n"
  hostFile += getHostsFile(region)
  logging.debug("Hostfile: \n"+hostFile)
  processes = []
  for group,machines in group.iteritems():
    for machine in machines:
      if machine["name"] != "kafka-test":
        print "Updating: "+machine["name"]
        p = Process(target=updateRemoteHostsFile, args=(machine["publicDNS"], hostFile))
        p.start()
        processes.append(p)

  for process in processes:
    process.join()




if __name__ == '__main__':
  mastercommand()
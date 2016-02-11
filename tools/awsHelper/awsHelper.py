#! /bin/sh
""":"
exec python $0 ${1+"$@"}
"""

import click,logging, boto3, re
from sys import stdout,path
from os.path import abspath, dirname, join, expanduser
#from os.path import abspath, dirname, join, expanduser, realpath
from multiprocessing import Process
#Make sure the commons package is on the path correctly
path.insert(0, dirname(dirname(abspath(__file__))))
from commons.ssh.ssh import ssh

logger = None
odysseyGroups=["kafka-broker", "kafka-zookeeper","gripper",
               "load-balancer","storm-zookeeper","storm-nimbus",
               "storm-supervisor","performance", "odyssey-monitoring"]
def getAwsRegions():
  return ["us-east-1","us-west-2","us-west-1","eu-west-1",
            "eu-central-1","ap-southeast-1","ap-northeast-1",
            "ap-southeast-2","ap-northeast-2","sa-east-1"]

def getCluster(region, identifier):
  identifiers=identifier.split(",")
  ec2 = boto3.resource('ec2', region_name=region)
  instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
  groupMap = {}
  for instance in instances:
    idf=""
    groupNames=[]
    for tag in instance.tags:
      if "Key" in tag: 
        if tag["Key"].lower() == "groups":  
          groupNames=tag["Value"].split(",")
        if tag["Key"].lower() == "name":
          nodename=tag["Value"]
        if tag["Key"].lower() == "identifier":
          idf=tag["Value"]
    if idf in identifiers:
      for groupKey in groupNames:
        if not groupKey in groupMap:
          groupMap[groupKey] = []
        groupMap[groupKey].append( {
              "name": nodename,
              "publicIP": instance.public_ip_address,
              "privateIP": instance.private_ip_address,
              "publicDNS": instance.public_dns_name,
              "identifier": idf,
              })
  return groupMap             

def getHostsFile(region, identifier):
  logger = logging.getLogger('awsHelper')
  group = getCluster(region, identifier)
  result = "##SCRIBENGIN CLUSTER START##\n"
  for group,machines in group.iteritems():
    for machine in machines:
      if machine["identifier"] == "neverwinterdp":
        result+= machine["privateIP"]+" "+machine["name"]+" "+machine["name"]+".private"+"\n"
        result+= machine["publicIP"]+" "+machine["name"]+".public\n"
  result += "##SCRIBENGIN CLUSTER END##\n"
  return result

def updateRemoteHostsFile(hostname,content,user,keypath,hostfile="/etc/hosts"):
  logger = logging.getLogger('awsNDP')
  s = ssh()
  out,err = s.sshExecute(hostname, "sudo sh -c \"echo '"+content+"' > "+hostfile+"\"",user,keypath)
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
@click.option('--identifier',    '-i',   default="odyssey", help='Identifier string to filter rewuired instances from AWS')
def ansibleinventory(region, keypath, user, identifier):
  logger = logging.getLogger('awsHelper')
  group = getCluster(region, identifier)
  inventory = ""
  for group,machines in group.iteritems():
    inventory += "\n["+group+"]\n"
    id=1
    for machine in machines:
      if group in odysseyGroups:
        inventory += str(machine["publicDNS"])+" id="+str(id)+"\n"
      else: 
        inventory += machine["name"]+" ansible_ssh_user="+str(user)+" ansible_ssh_private_key_file="+str(keypath)+" ansible_host="+str(machine["publicDNS"])+" id="+str(id)+"\n"
      id= id+1
  print inventory
  defaultInventory = open(join(expanduser("~"),"inventory"),'w+')
  defaultInventory.write(inventory)
  defaultInventory.close()
    
  print "Ansible inventory written to ~/inventory"
  logging.debug("Ansible inventory written to ~/inventory")  

@mastercommand.command(help="Update /etc/hosts file on remote machines in AWS")
@click.option('--region',    '-r',   default="us-west-2",  type=click.Choice(getAwsRegions()), help='AWS Region to connect to')
@click.option('--identifier',    '-i',   default="odyssey", help='Identifier string to filter rewuired instances from AWS')
@click.option('--keypath',   '-k',   default="~/.ssh/id_rsa", help='Path to aws private key which is downloaded from aws console.ex: /Users/whatever/Downloads/mykey.pem')
def updateremotehostfile(region,identifier,keypath):
  logger = logging.getLogger('awsHelper')
  group = getCluster(region,identifier)
  hostFile  = "127.0.0.1 localhost localhost.localdomain localhost4 localhost4.localdomain4\n"
  hostFile += "::1 localhost localhost.localdomain localhost6 localhost6.localdomain6\n\n"
  hostFile += getHostsFile(region,identifier)
  logger.debug("Hostfile: \n"+hostFile)
  print hostFile
  processes = []
  for group,machines in group.iteritems():
    for machine in machines:
      print "Updating: "+machine["name"]
      logger.debug("Updating: "+machine["name"])
      p = Process(target=updateRemoteHostsFile, args=(machine["publicDNS"], hostFile, "centos", keypath))
      p.start()
      processes.append(p)

  for process in processes:
    process.join()

if __name__ == '__main__':
  mastercommand()
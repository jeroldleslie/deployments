#! /bin/sh
""":"
exec python $0 ${1+"$@"}
"""

import click,logging, boto3, re
from sys import stdout,path
from os.path import abspath, dirname
from multiprocessing import Process
#Make sure the commons package is on the path correctly
path.insert(0, dirname(dirname(abspath(__file__))))
from commons.ssh.ssh import ssh

logger = None
hostVarsToOmit=["balancer"]
def getAwsRegions():
  return ["us-east-1","us-west-2","us-west-1","eu-west-1",
            "eu-central-1","ap-southeast-1","ap-northeast-1",
            "ap-southeast-2","ap-northeast-2","sa-east-1"]

def getCluster(region, identifier):
  ec2 = boto3.resource('ec2', region_name=region)
  instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
  groupMap = {}
  instanceCounterMap = {}
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
    if identifier==idf:
      for groupKey in groupNames:
        addWithoutHostVar=False
        try:
          hostVar=groupKey.split("-")[1]
          if hostVar=="zookeeper":
            hostVar="zoo"
          if not hostVar in hostVarsToOmit:
            hostVar+="_id"
            instanceID=0
            if not instanceCounterMap.get(hostVar) is None:
              instanceID = instanceCounterMap.get(hostVar)+1
            instanceCounterMap[hostVar]=instanceID
            if not groupKey in groupMap:
              groupMap[groupKey] = []
            groupMap[groupKey].append( {
              "name": tag["Value"],
              "publicIP": instance.public_ip_address,
              "privateIP": instance.private_ip_address,
              "publicDNS": instance.public_dns_name,
              "hostVar":hostVar+"="+str(instanceID)
              })
          else:
              addWithoutHostVar=True
        except IndexError:
          addWithoutHostVar=True
          if addWithoutHostVar == True:
            if not groupKey in groupMap:
              groupMap[groupKey] = []
            groupMap[groupKey].append( {
              "name": tag["Value"],
              "publicIP": instance.public_ip_address,
              "privateIP": instance.private_ip_address,
              "publicDNS": instance.public_dns_name,
              })
  return groupMap             

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
@click.option('--identifier',    '-i',   default="odyssey", help='Identifier string to filter rewuired instances from AWS')
def ansibleinventory(region, identifier):
  logger = logging.getLogger('awsHelper')
  group = getCluster(region, identifier)
  for group,machines in group.iteritems():
    print "["+group+"]"
    id=1
    for machine in machines:
      if "hostVar" in machine.keys():
        print str(machine["publicDNS"])+" "+machine["hostVar"]
      else:
        print str(machine["publicDNS"])
    print ""


if __name__ == '__main__':
  mastercommand()
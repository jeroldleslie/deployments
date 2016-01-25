#! /bin/sh
""":"
exec python $0 ${1+"$@"}
"""

import click,logging, boto3
from sys import stdout


logger = None

def getAwsRegions():
  return ["us-east-1","us-west-2","us-west-1","eu-west-1",
            "eu-central-1","ap-southeast-1","ap-northeast-1",
            "ap-southeast-2","ap-northeast-2","sa-east-1"]

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
def ansibleinventory(region):
  logger = logging.getLogger('awsNDP')
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
                      "privateIP": instance.private_ip_address
                      })
  for group,machines in group.iteritems():
    print "["+group+""
    id=1
    for machine in machines:
      print machine["name"]+" ansible_ssh_user=neverwinterdp ansible_ssh_private_key_file=~/.ssh/id_rsa ansible_host="+machine["publicIP"]+" id="+str(id)
      id= id+1
    print ""




if __name__ == '__main__':
  mastercommand()
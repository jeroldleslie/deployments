import click, logging, signal
from sys import stdout
from scribengin.Image import Image
from scribengin.Container import Container
#python digitalocean.py image --clean --build hadoopmaster, zookeeper, kafka
'''
  image 
     --clean            #destroy the snapshots
        name            #name of snapshot to be destroyed e.g hadoop-master, zookeeper, kibana
     --build            #create snapshots
        name            #name of config file to build. e.g kafka, zookeeper.
  container
    --start             #to start all use --cluster start
      name                #e.g hadoop-master, hadoop-worker-1, hadoop-worker*
    --stop                #to stop all use --cluster stop
      name                
    --clean                #restore to snapshot state
      name
    --deploy            #configure the container. e.g configure kafka
    --update-hosts
      name
    --status
      name
  cluster
    --deploy                #all containers in cluster
    --deploy-scribengin    #deploy scribengin to hadoop-master, and hadoop-workers
    --start                #start all containers in cluster
    --stop                    #stop containers in cluster
    --force-stop                #force stop
    --status                #get status of cluster
'''

'''
Image names
  hadoop-master
  hadoop-worker
  elasticsearch
  kibana
  zookeeper
  kafka


container names
  hadoop-master-1
  hadoop-worker-1
  hadoop-worker-2
  elasticsearch-1
  kibana-1
  zookeeper-1
  kafka-1
  kafka-2
'''



class DigitalOcean(object):
    
  @click.group(chain=True)
  def mastercommand():
    print "master command"

  @mastercommand.command("image", help="commands pertaining to digital-ocean images")
  @click.option('--clean',default='',help='destroy the images')
  @click.option('--build',default='',help='build the images')
  @click.option('--snapshot',default='',help='snapshot the images')
  @click.option('--ansible',default='',help='run the playbook against the droplet')
  @click.option('--playbook',default='../ansible/scribenginCluster.yml',help='the playbook to be run')
  @click.option('--neverwinterdp-home', required=True,help='neverwinterdp home')
  def image(clean, build,snapshot, ansible, playbook, neverwinterdp_home):
    print "in image "
    image = Image(neverwinterdp_home, playbook);
    if clean !='':
      image.clean(clean)
    elif build!='':
      image.build(build)
    elif snapshot!='':
      image.takeSnapshots(snapshot)
    elif ansible != '':
      image.runAnsible(ansible)

  @mastercommand.command("container", help="commands pertaining to digital-ocean droplets")
  @click.option('--start',default='',help='start the container')
  @click.option('--stop',default='',help='stop the container')
  @click.option('--clean',default='',help='clean the container')
  @click.option('--deploy',default='',help='deploy teh container')
  @click.option('--status',default='',help='get the status of the container')
  @click.option('--neverwinterdp-home', required=True,help='neverwinterdp home')
  def container(start, stop, clean, deploy, status, neverwinterdp_home):
    print "container commands."
    container = Container(neverwinterdp_home);
    if start!='':
      container.start(start)
    elif deploy !='':
      container.status(deploy)
    
    
      
  @mastercommand.command("cluster", help="commands pertaining to the digital-ocean scribengin cluster")
  @click.option('--start',default='',help='start the cluster')
  @click.option('--stop',default='',help='stop the cluster')
  @click.option('--clean',default='',help='clean the cluster')
  @click.option('--deploy',default='',help='deploy the cluster')
  @click.option('--deploy-scribengin',default='',help='deploy scribengin')
  @click.option('--status',default='',help='get the status of the cluster')
  def cluster(self, start, stop,deploy, deploy_scribengin,status):
    print "cluster commands"

if __name__ == "__main__":
  digitalOcean = DigitalOcean()
  digitalOcean.mastercommand()

import click, logging, signal
from sys import stdout
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
       --force                #force stop
    --status                #get status of cluster
'''

'''
Snapshot names
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
    

  @click.option('--clean',default='',help='destroy the images')
  @click.option('--build',default='',help='build the images')
  def image(self,clean, build):
    pass

  @click.option('--start',default='',help='start the container')
  @click.option('--stop',default='',help='stop the container')
  @click.option('--clean',default='',help='clean the container')
  @click.option('--deploy',default='',help='deploy teh container')
  @click.option('--status',default='',help='get the status of the container')
  def container(self, start, stop, clean, deploy, status):
    pass
  
  @click.option('--start',default='',help='start the cluster')
  @click.option('--stop',default='',help='stop the cluster')
  @click.option('--clean',default='',help='clean the cluster')
  @click.option('--deploy',default='',help='deploy the cluster')
  @click.option('--deploy-scribengin',default='',help='deploy scribengin')
  @click.option('--status',default='',help='get the status of the cluster')
  def cluster(self, start, stop,deploy, deploy_scribengin,status):
    pass      

if __name__ == "__main__":
    main()

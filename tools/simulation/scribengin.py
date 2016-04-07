from sys import path, stdout
from os.path import join, expanduser, dirname, abspath

from time import sleep
from multiprocessing import Process
from pprint import pformat
import subprocess

path.insert(0, dirname(dirname(abspath(__file__))))
from commons.ansibleRunner.ansibleRunner import ansibleRunner
from commons.ansibleInventoryParser.ansibleInventoryParser import ansibleInventoryParser

class ScribenginTool(object):
  def __init__(self):
    #Ansible root directory is at ../../ansible
    ansible_root_dir = dirname(dirname(dirname(abspath(__file__)))) + "/ansible"
    print "Ansible Root Dir: " + ansible_root_dir
    
    #Ansible inventory is at ~/inventory
    self.inventoryFile = join(expanduser("~"),"inventory")
    print "Using inventory file at: " + self.inventoryFile

    self.vmmasterPlaybook        = join(ansible_root_dir, "vmmaster.yml")
    self.vmmasterPlaybookToStart = join(ansible_root_dir, "vmmaster_start.yml")

    #Parse the inventory file to get our cluster info
    self.ansibleRunner = ansibleRunner()

  def forceStopVMMaster(self):
    #force stop vm-master
    self.ansibleRunner.deploy(playbook = self.vmmasterPlaybook, inventory=self.inventoryFile, outputToStdout=True, maxRetries=0, tags="force-stop")
    #wait to kill all containers in all hadoop-worker machines
    self.ansibleRunner.deploy(playbook = self.vmmasterPlaybook, inventory=self.inventoryFile, outputToStdout=True, maxRetries=0, tags="wait-to-kill")

  def startVMMaster(self):
    self.ansibleRunner.deploy(playbook = self.vmmasterPlaybookToStart, inventory=self.inventoryFile, outputToStdout=True, maxRetries=0, tags="start") 

  def restartVMMaster(self):
    self.forceStopVMMaster();
    self.startVMMaster();


  def submitTrackingDataflow(self):
    neverwinterdpHomeDir  = expanduser("~");
    neverwinterdpBuildDir = neverwinterdpHomeDir + "/NeverwinterDP/release/build/release/neverwinterdp" ;
    dataflowOpts=(
      "--dataflow-storage kafka --dataflow-num-of-worker 5 --dataflow-num-of-executor-per-worker 2 " +
      "--dataflow-tracking-window-size 50000 --dataflow-sliding-window-size 100 " +
      "--dataflow-default-parallelism 5 --dataflow-default-replication 3 ");

    script = neverwinterdpBuildDir + "/scribengin/bin/tracking/run-simple-tracking.sh" ;

    print "*********************************************************************************"
    print "Submit Tracking Datadataflow With Script:"
    print script + ' ' + dataflowOpts
    print "*********************************************************************************"

    subprocess.call([script, dataflowOpts]) 

  def trackingDataflowStatus(self):
    neverwinterdpHomeDir  = expanduser("~");
    neverwinterdpBuildDir = neverwinterdpHomeDir + "/NeverwinterDP/release/build/release/neverwinterdp" ;
    shellScript = neverwinterdpBuildDir + "/scribengin/bin/shell.sh" ;
    opts=("plugin com.neverwinterdp.scribengin.dataflow.tracking.TrackingMonitor --dataflow-id tracking --show-history-vm")

    print "*********************************************************************************"
    print "Tracking Dataflow Status:"
    print shellScript + ' ' + opts
    print "*********************************************************************************"
    args=[shellScript, "plugin", "com.neverwinterdp.scribengin.dataflow.tracking.TrackingMonitor", "--dataflow-id", "tracking", "--show-history-vm"];
    #subprocess.call([shellScript, opts]) 
    subprocess.call(args); 

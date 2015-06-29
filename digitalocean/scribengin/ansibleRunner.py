from ansible.playbook import PlayBook
from ansible.inventory import Inventory
from ansible import callbacks
from ansible import utils

from tempfile import NamedTemporaryFile
import os
from ansible.utils.template import template

class ansibleRunner(object):

  def __init__(self, neverwinterdp_home):
    self.neverwinterdp_home = neverwinterdp_home
    os.environ['ANSIBLE_HOST_KEY_CHECKING'] = 'False'

  def createInventory(self, droplets):
    print os.environ['ANSIBLE_HOST_KEY_CHECKING']
    #todo use a multimap
    servers = {}
    inventory=''

    for droplet in droplets:
      if not droplet.name in servers:
        servers[droplet.name]=[]
        inventory += '\n['+ droplet.name +']\n'
      servers[droplet.name].append(droplet.ip_address)
      inventory += droplet.ip_address+'\n'

    # Create a temporary file and write the inventory string to it
    self.hosts = NamedTemporaryFile(delete=False)
    self.hosts.write(inventory)
    self.hosts.close()

    return inventory

  def runPlaybook(self, playbook):
    utils.VERBOSITY = 0
    playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
    stats = callbacks.AggregateStats()
    runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)
    
    pb = PlayBook(
      playbook=playbook,
      host_list=self.hosts.name,
      callbacks=playbook_cb,
      runner_callbacks=runner_cb,
      stats=stats,
      extra_vars={'neverwinterdp_home_override':self.neverwinterdp_home}
    )
    playbook_cb.on_stats(pb.stats)
    return pb.run()
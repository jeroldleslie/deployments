from os.path import expanduser, join, abspath, dirname
from sys import path
from ansible.playbook import PlayBook

import ansible.runner 
import ansible.inventory 
from ansible import callbacks 
from ansible import utils 
import json
import os

class AnsibleRunner():
  def __init__(self):
    os.environ['ANSIBLE_HOST_KEY_CHECKING'] = 'False'
  
  def runPlaybook(self, inventory, playbook_path, extra_vars = {}):
    utils.VERBOSITY = 0
    playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
    stats = callbacks.AggregateStats()
    runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)
    
    pb = PlayBook(
      playbook=playbook_path,
      inventory = inventory,
      callbacks=playbook_cb,
      runner_callbacks=runner_cb,
      stats=stats,
      extra_vars=extra_vars
    )
    playbook_cb.on_stats(pb.stats)
    return pb.run()
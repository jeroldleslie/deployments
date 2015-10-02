import logging
from ansible.inventory.ini import InventoryParser

class ansibleInventoryParser(object):
  def __init__(self, ansibleInventoryFilePath="inventory"):
    self.ansibleInventoryFilePath = ansibleInventoryFilePath

  def parseInventoryFile(self):
    results=[]
    logging.debug("Ansible Inventory Path: "+self.ansibleInventoryFilePath)

    invParser = InventoryParser(filename=self.ansibleInventoryFilePath)
    for groupname, group in invParser.groups.iteritems():
      for host in group.hosts:
        results.append({ "group":groupname,
                          "host":host.name })

    logging.debug("Ansible inventory parsing results: "+str(results))
    return results

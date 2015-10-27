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
        toAppend = {"group":groupname,
                    "host":host.name}
        if "ansible_host" in host.get_variables():
          toAppend["ansible_host"] = host.get_variables()["ansible_host"]

        results.append(toAppend)

    logging.debug("Ansible inventory parsing results: "+str(results))
    return results


from os.path import expanduser, join
from sys import path
from time import sleep
import paramiko, logging

class ssh(object):
  def __init__(self, sshKeyPath=join(expanduser("~"),".ssh/id_rsa")):
    self.sshKeyPath = sshKeyPath
    
  def sshExecute(self, host, command, user = "neverwinterdp", maxRetries=10, retries=0, sleepTime=10, get_pty=True):
    """
    SSH onto a machine, execute a command
    Returns [stdout,stderr]
    """
    try:
      key = paramiko.RSAKey.from_private_key_file(self.sshKeyPath)
      
      c = paramiko.SSHClient()
      c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      c.connect( hostname = host, username = user, pkey = key, timeout = 10 )
      stdin, stdout, stderr = c.exec_command(command, get_pty=get_pty)
      
      stdout = stdout.read()
      stderr = stderr.read()
      c.close()
      return stdout,stderr
    except:
      if retries < maxRetries:
        sleep(sleepTime)
        return self.sshExecute(host, command, user, maxRetries, retries+1, sleepTime)
      else:
        logging.error("Error connecting to "+str(host)+" as user "+str(user))
        print "Error connecting to "+str(host)+" as user "+str(user)
        raise
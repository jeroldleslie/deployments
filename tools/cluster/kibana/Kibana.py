'''
Created on 06-Jul-2015

@author: peter jerold leslie
'''
import subprocess, os, sys, logging
from os.path import abspath, dirname, join, expanduser, realpath

class Kibana(object):

  def __init__(self, elasticsearch_url, temp_path):
    self.elasticsearch_url = elasticsearch_url
    self.temp_path = join(temp_path,"kibana.json")
    self.kibana_json_file_path=join(dirname(dirname(dirname(dirname(realpath(__file__))))), "ansible/roles/kibana_charts/files/kibana.json")
  
  def import_kibana_from_host(self):
    command = "elasticdump --input="+self.kibana_json_file_path+" --output="+self.elasticsearch_url+"/.kibana --type=data"
    logging.debug("Import kibana from host command: "+command)
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    print command
    output, err = p.communicate()
    print "*** Importing kibana data from host ***\n", output
    
  def import_kibana(self):
    command = "elasticdump --input=/opt/kibana/config/kibana.json --output="+self.elasticsearch_url+"/.kibana --type=data"
    logging.debug("Import kibana command: "+command)
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    print command
    output, err = p.communicate()
    print "*** Importing kibana data ***\n", output

  def export_kibana(self):
    command = "elasticdump --input='"+self.elasticsearch_url+"/.kibana' --output=$ --type=data > "+self.temp_path
    logging.debug("Export kibana command: "+command)
    readFile = open(self.temp_path)
    lines = readFile.readlines()
    lines = lines[:-1]
    readFile.close()
    
    print lines
    logging.info(lines)
    
    writeFile = open(self.kibana_json_file_path,'w')
    writeFile.writelines(lines)
    writeFile.close()

    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    output, err = p.communicate()
    print "*** Exporting kibana data ***\n", output
    logging.info("*** Exporting kibana data ***\n")
    logging.info(output)
    
        
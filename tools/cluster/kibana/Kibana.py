'''
Created on 06-Jul-2015

@author: peter jerold leslie
'''
import subprocess, os, sys
from os.path import abspath, dirname, join, expanduser, realpath

class Kibana(object):

  def __init__(self, elasticsearch_url, temp_path):
    self.elasticsearch_url = elasticsearch_url
    self.temp_path = temp_path
    self.kibana_json_file_path=join(dirname(dirname(dirname(dirname(realpath(__file__))))), "configs/bootstrap/post-install/kibana/config/kibana.json")
  
  def import_kibana_from_host(self):
    command = "elasticdump --input="+self.kibana_json_file_path+" --output="+self.elasticsearch_url+"/.kibana --type=data"
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    print command
    output, err = p.communicate()
    print "*** Importing kibana data from host ***\n", output
    
  def import_kibana(self):
    command = "elasticdump --input=/opt/kibana/config/kibana.json --output="+self.elasticsearch_url+"/.kibana --type=data"
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    print command
    output, err = p.communicate()
    print "*** Importing kibana data ***\n", output

  def export_kibana(self):
    command = "elasticdump --input='"+self.elasticsearch_url+"/.kibana' --output=$ --type=data > "+join(self.temp_path,"kibana.json")
    
    readFile = open("kibana.json")
    lines = readFile.readlines()
    lines = lines[:-1]
    readFile.close()
    
    print lines
    
    writeFile = open(self.kibana_json_file_path,'w')
    writeFile.writelines(lines)
    writeFile.close()

    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    output, err = p.communicate()
    print "*** Exporting kibana data ***\n", output
    
        
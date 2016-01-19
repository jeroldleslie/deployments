
#! /bin/sh
""":"
exec python $0 ${1+"$@"}
"""
'''
Created on 12-Jan-2016

@author: peter jerold leslie
'''

import click,logging, sys, socket
import traceback
from sys import stdout
from datetime import datetime
from time import sleep
import time, thread
from elasticsearch import Elasticsearch

current_milli_time = lambda: int(round(time.time() * 1000))
maxValue=0
doRun=True

# Define a function for the thread
def print_time( threadName, delay, sleep_time):
  
  print sleep_time
  nano=1.0e9
  while True:
    time.sleep(1)
    print "%s: %s" % ( "", time.ctime(time.time()) )

#Measure hiccup
def measure_hiccup( sleep_time ):
  global maxValue
  nano=1.0e9
  shortestObservedDeltaTimeNsec = long(sys.maxsize);
  while True:
    #Getting time before sleep and convert to nanoseconds 
    timeBeforeMeasurement = (time.time()/nano)
    
    #Sleep for given time
    sleep(sleep_time)
    
    #Getting time after sleep and convert to nanoseconds
    timeAfterMeasurement = (time.time()/nano)
    
    #Time difference between before and after sleep as deltaTimeNsec
    deltaTimeNsec=timeAfterMeasurement-timeBeforeMeasurement
    
    #convert deltaTimeNsec to seconds
    deltaTimeNsec=deltaTimeNsec*nano

        
    #Check if deltaTimeNsec is greater than sleep_time, if deltaTimeNsec is greater hiccup occured
    if deltaTimeNsec > sleep_time:
      hiccupTimeNsec=deltaTimeNsec-sleep_time
    else:
      hiccupTimeNsec=0
    
    #Convert hiccup to milliseconds  
    hiccupTimeMsec=int(hiccupTimeNsec*1000)
    
    #Get maximum values of the sample  
    if hiccupTimeMsec > maxValue:
      maxValue=hiccupTimeMsec
    #print maxValue
       

def push_to_elasticsearch(host, port, interval):  
  global maxValue 
  global doRun 
  index_name='neverwinterdp-monitor-mhiccup';
  # by default we connect to localhost:9200
  es = Elasticsearch([{
                       'host': host, 
                       'port': port 
                       },])

  mapping="{\"mappings\": {\"MHiccupInfo\": {\"properties\": {\"timestamp\":" 
  mapping+="{\"type\": \"date\",\"format\": \"dd/MM/yyyy HH:mm:ss\"},"
  mapping+="\"hostname\" : { \"type\" : \"string\", \"index\":\"not_analyzed\" }}}}}"
  print mapping

  index_body='''
  {
    "settings": {
      "index": {
         "analysis": {
        "analyzer": {
              "standard": {
                "type": "standard"
               }
            }
          }
        }
      },
      "mappings": {
        "MHiccupInfo": {
          "properties": {
            "timestamp": {
              "type": "date",
              "format": "dd/MM/yyyy HH:mm:ss"
             },
            "hostname" : { "type" : "string", "index":"not_analyzed" }
          }
        }
      }
    }''';
  # create an index in elasticsearch, ignore status code 400 (index already exists)
  try:
    print es.indices.create(index=index_name, ignore=400, body=mapping)
    print index_name + " created"
  except Exception, err:
    traceback.print_exc()
    print index_name + " already created"
    doRun=False
    
  while True:
    sleep(interval)
    format="%d/%m/%Y %H:%M:%S"
    now = datetime.utcnow()
    ltime = now.strftime(format) 
    _id=socket.gethostname()+","+ltime
    
    try:
      es.index(index=index_name, doc_type="MHiccupInfo", id=_id, body={"hostname": socket.gethostname(), "maxValue": maxValue, "timestamp": ltime})
    except Exception, err:
      traceback.print_exc()
      doRun=False
      
    maxValue=0


@click.command(help="Machine Hiccup!\n")
@click.option('--debug/--no-debug',      default=False, help="Turn debugging on")
@click.option('--logfile',               default='/tmp/mhiccup.log', help="Log file to write to")
@click.option('--elasticsearch-logfile',               default='/tmp/elasticsearch.log', help="Elasticsearch Log file to write to")
@click.option('--elasticsearch-host',    '-h',           default='elasticsearch-1', help="hostname of elasticsearch to connect")
@click.option('--elasticsearch-port',    '-p',           default=9200, help="port of elasticsearch to connect")
@click.option('--hiccup-sleep-time',     '-s', default=0.05, help="Hiccup Sleep time in seconds")
@click.option('--interval',     '-i', default=30, help="Time interval to push data to elasticsearch")
def mastercommand(debug, logfile, elasticsearch_logfile, elasticsearch_host, elasticsearch_port, hiccup_sleep_time, interval):
  if debug:
    #Set logging file, overwrite file, set logging level to DEBUG
    logging.basicConfig(filename=logfile, filemode="w", level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler(stdout))
    
    tracer = logging.getLogger('elasticsearch.trace')
    tracer.setLevel(logging.DEBUG)
    tracer.addHandler(logging.FileHandler(elasticsearch_logfile))

    click.echo('Debug mode is %s' % ('on' if debug else 'off'))
  else:
    #Set logging file, overwrite file, set logging level to INFO
    logging.basicConfig(filename=logfile, filemode="w", level=logging.INFO)
    tracer = logging.getLogger('elasticsearch.trace')
    tracer.setLevel(logging.INFO)
    tracer.addHandler(logging.FileHandler(elasticsearch_logfile))

  global doRun
  # Create two threads as follows
  try:
    #thread.start_new_thread( print_time, ("t-1", 1, hiccup_sleep_time) )
    thread.start_new_thread( measure_hiccup, (hiccup_sleep_time,) )
    thread.start_new_thread( push_to_elasticsearch, (elasticsearch_host, elasticsearch_port, interval) )
  except:
    print "Error: unable to start thread"
    traceback.print_exc()
    
  while doRun:
      pass
      
if __name__ == '__main__':
  mastercommand()
  
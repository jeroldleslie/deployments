import unittest, os
from os.path import dirname, abspath
from sys import path
path.insert(0, dirname(dirname(abspath(__file__))))
from Cluster import Cluster
from process.Process import KafkaProcess

class Test_Cluster(unittest.TestCase):
  def test_parseEtcHost(self):
    x = KafkaProcess("1","1")
    cluster = Cluster(etcHostsPath=os.path.join( os.path.dirname(os.path.realpath(__file__)),"testHostsFile"))
    print cluster.getNumServers()
    self.assertEqual(cluster.getNumServers(), 8, "Should parse 8 applicable host names out of the testHostsFile")

    self.assertEqual(cluster.getServersByRole("kafka").getNumServers(), 3)
    self.assertEqual(cluster.getServersByRole("zookeeper").getNumServers(), 1)
    self.assertEqual(cluster.getServersByRole("hadoop-master").getNumServers(), 1)
    self.assertEqual(cluster.getServersByRole("hadoop-worker").getNumServers(), 3)
                
    #cluster.report()
    

    
if __name__ == '__main__':
  unittest.main()